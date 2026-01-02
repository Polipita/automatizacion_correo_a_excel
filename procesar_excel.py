import io
import re
import fitz
from googleapiclient.http import MediaIoBaseDownload

# IMPORTACIONES PROPIAS
import config
from auth_google import conectar_google

def limpiar_texto_doble(texto_sucio):
    
    lineas_limpias = []
    for linea in texto_sucio.split('\n'):
        palabras = linea.split()
        palabras_limpias = []
        for palabra in palabras:
            
            if len(palabra) > 1 and len(palabra) % 2 == 0:
                mitad = len(palabra) // 2
                parte1 = palabra[:mitad]
                parte2 = palabra[mitad:]
                if parte1 == parte2:
                    palabras_limpias.append(parte1)
                else:
                    palabras_limpias.append(palabra)
            else:
                palabras_limpias.append(palabra)
        
        lineas_limpias.append(" ".join(palabras_limpias))
    
    return "\n".join(lineas_limpias)

def extraer_detalle_factura(stream_pdf):
    texto_sucio = ""
    with fitz.open(stream=stream_pdf, filetype="pdf") as doc:
        for pagina in doc:
            texto_sucio += pagina.get_text(sort=True)
    
    texto_limpio = limpiar_texto_doble(texto_sucio)

    cabecera = {'RUC': 'No detectado', 'Total': '0.00', 'Fecha': 'No detectada', 'Flete': '0.00'}
    
    try:
        ruc_match = re.search(r'DOC.*?IDENTIDAD.*?(\d{11})', texto_limpio, re.IGNORECASE | re.DOTALL)
        if not ruc_match:
            ruc_match = re.search(r'R\.?U\.?C.*?(\d{11})', texto_limpio, re.IGNORECASE)
        if ruc_match: cabecera['RUC'] = ruc_match.group(1)

        fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto_limpio)
        if fecha_match: cabecera['Fecha'] = fecha_match.group(1)

        
        total_match = re.search(r'IMPORTE\s+A\s+PAGAR.*?(\d+[.,]\d{2})', texto_limpio, re.IGNORECASE | re.DOTALL)
        if total_match:
            cabecera['Total'] = total_match.group(1).replace(',', '')

        flete_match = re.search(r'(?:FLETE|DESPACHO|ENVIO)', texto_limpio, re.IGNORECASE)
        if flete_match:
            precio_flete = re.search(r'(?:FLETE|DESPACHO|ENVIO).{0,50}?(\d+[.,]\d{2})', texto_limpio, re.IGNORECASE | re.DOTALL)
            cabecera['Flete'] = precio_flete.group(1) if precio_flete else "Revisar"

    except Exception as e:
        print(f"⚠️ Error Cabecera: {e}")

    productos = []
    lineas = texto_limpio.split('\n')
    

    i = 0
    while i < len(lineas):
        linea_actual = lineas[i].strip()
        
        #buscamos el precio y la cantidades de los productos que van 2 x 10.0
        match_prod = re.search(r'(\d+)\s+X\s+(\d+[.,]\d{2})', linea_actual)
        
        if match_prod and i > 0:
            #separamos los grupos encontrados (2)(10.0)
            cantidad = match_prod.group(1)
            precio_unit = match_prod.group(2)
            
            #para sacar la informacion del producto retrocedemos una linea
            linea_desc = lineas[i-1].strip()
            
            partes = linea_desc.split()
            if len(partes) > 2:
                if partes[0].isdigit() and len(partes[0]) > 4:
                    partes.pop(0) #si tiene codigo lo eliminamos
                if re.match(r'\d+[.,]\d{2}', partes[-1]):
                    partes.pop(-1)
            
            nombre = " ".join(partes)
            
            # Guardamos
            productos.append({
                'Nombre': nombre,
                'Cantidad': cantidad,
                'PrecioUnit': precio_unit
            })
        i += 1

    return cabecera, productos


def mover_a_procesados(service, file_id):
    #obtenemos el archivo actual
    file = service.files().get(fileId=file_id, fields='parents').execute()
    padres_antiguos = ",".join(file.get('parents'))
    
    #movermos a la nueva carpeta elimando el otro
    service.files().update(
        fileId=file_id,
        addParents=config.ID_CARPETA_PROCESADOS,
        removeParents=padres_antiguos,
        fields='id, parents'
    ).execute()

def procesar_archivos():
    print("iniciando Script...")
    try:
        drive, sheets = conectar_google()
        hoja = sheets.open_by_key(config.ID_HOJA_CALCULO).sheet1
        
        col_ids = hoja.col_values(1)
        siguiente_id = 101 if len(col_ids) < 2 else int(col_ids[-1]) + 1

        query = f"'{config.ID_CARPETA_ENTRADA}' in parents and mimeType = 'application/pdf' and trashed = false"
        archivos = drive.files().list(q=query).execute().get('files', [])

        if not archivos:
            print("no se encontro facturas nuevas.")
            return

        print(f"se encontro {len(archivos)} archivos...")

        for archivo in archivos:
            print(f"analizando: {archivo['name']}...")
            #obtenemos todo esos archvios en memoria ram
            req = drive.files().get_media(fileId=archivo['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, req)
            done = False
            while not done: _, done = downloader.next_chunk()
            fh.seek(0)
            
            cabecera, lista_productos = extraer_detalle_factura(fh.read())
            
            link = f"https://drive.google.com/file/d/{archivo['id']}/view"
            
            if lista_productos:
                print(f"se encontraron {len(lista_productos)} productos.")
                for item in lista_productos:
                    
                    # calculamos el total por producto
                    try:
                        cant_num = float(item['Cantidad'])
                        prec_num = float(item['PrecioUnit'].replace(',', ''))
                        
                        subtotal_linea = cant_num * prec_num
                        
                        subtotal_str = "{:.2f}".format(subtotal_linea)
                    except ValueError:
                        subtotal_str = "0.00"

                    # falta agregar flete(opcional), luego mejoramos
                    fila = [
                        siguiente_id,
                        cabecera['RUC'],
                        cabecera['Fecha'],
                        item['Nombre'],
                        item['Cantidad'],
                        item['PrecioUnit'],     
                        subtotal_str,           
                        cabecera['Total'],
                        link
                    ]
                    hoja.append_row(fila)
            else:
                print("no se detectaron productos, guardando genérico.")
                fila = [siguiente_id, cabecera['RUC'], cabecera['Fecha'], "VARIOS / NO DETECTADO", 
                        1, cabecera['Total'], cabecera['Total'], cabecera['Total'], link]
                hoja.append_row(fila)
            
            siguiente_id += 1
            mover_a_procesados(drive, archivo['id'])
            print("archivado.")
            
    except Exception as e:
        print(f"ocurrió un error fatal: {e}")

if __name__ == "__main__":
    procesar_archivos()