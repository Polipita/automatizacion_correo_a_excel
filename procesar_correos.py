import imaplib
import io
import email
from email.header import decode_header
from datetime import datetime
from email.utils import parseaddr
from googleapiclient.http import MediaIoBaseUpload

import config
from auth_google import conectar_google

def limpiarTexto(texto):
    if not texto: return ""
    decoded_list = decode_header(texto)
    header_value, charset = decoded_list[0]
    if isinstance(header_value, bytes):
        try:
            return header_value.decode(charset or 'utf-8')
        except:
            return header_value.decode('utf-8', errors='ignore')
    return str(header_value)

def subir_a_drive(service, nombre_archivo, contenido_bytes):
    file_metadata = {
        'name': nombre_archivo,
        'parents': [config.ID_CARPETA_ENTRADA]  
    }
    media = MediaIoBaseUpload(io.BytesIO(contenido_bytes), 
                              mimetype='application/pdf', 
                              resumable=True)
    
    archivo = service.files().create(body=file_metadata, 
                                     media_body=media, 
                                     fields='id').execute()
    return archivo.get('id')

def ejecutar_bajada_correos():
    print("trayendo correos")
    
    # 1. CONEXIÓN A GOOGLE (Usando el módulo compartido)
    try:
        # conectar_google devuelve (drive, sheets), aquí solo queremos drive [0]
        drive_service, _ = conectar_google()
        print("conexión a Google Drive exitosa.")
    except Exception as e:
        print(f"error Auth Google: {e}")
        return

    # 2. CONEXIÓN AL CORREO (IMAP)
    try:
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
        mail.login(config.EMAIL, config.PASSWORD)
        mail.select("inbox")
    except Exception as e:
        print(f"error conectando al correo: {e}")
        return

    # 3. BUSCAR CORREOS DE HOY
    hoy = datetime.now().strftime("%d-%b-%Y")
    status, mensajes = mail.search(None, f'(UNSEEN ON {hoy})')

    if not mensajes[0]:
        print("no hay correos nuevos hoy.")
        return

    ids_correos = mensajes[0].split()
    print(f'correos nuevos encontrados: {len(ids_correos)}')

    # 4. PROCESAR CADA CORREO
    for num in ids_correos:
        try:
            status, data = mail.fetch(num, "(RFC822)")
            mensaje = email.message_from_bytes(data[0][1])

            asunto = limpiarTexto(mensaje.get("Subject"))
            from_raw = mensaje.get("From", "")
            nombre, correo_remitente = parseaddr(from_raw)
            correo_remitente = correo_remitente.lower()

            es_remitente_valido = correo_remitente in config.REMITENTES_PERMITIDOS
            
            print(f"procesando: '{asunto}' | de: {correo_remitente}")

            if es_remitente_valido:
                print("es remitente autorizado.")
                archivo_encontrado = False
                
                for parte in mensaje.walk():
                    content_disposition = str(parte.get("Content-Disposition"))

                    if parte.get_content_type() == "application/pdf" and "attachment" in content_disposition:
                        nombre_archivo = limpiarTexto(parte.get_filename())
                        
                        if nombre_archivo:
                            contenido_bytes = parte.get_payload(decode=True)
                            print(f"subiendo: {nombre_archivo}...")
                            
                            try:
                                file_id = subir_a_drive(drive_service, nombre_archivo, contenido_bytes)
                                print(f" se subio el archivo con id: {file_id}")
                                archivo_encontrado = True
                            except Exception as e:
                                print(f"error subiendo: {e}")
                
                if archivo_encontrado:
                    # marcamos como leído solo si guardamos el archivo
                    mail.store(num, '+FLAGS', '\\Seen')
            else:
                print("remitente no está en la lista blanca.")

        except Exception as e:
            print(f"error: {e}")

    mail.logout()
    print("termino")

if __name__ == "__main__":
    ejecutar_bajada_correos()