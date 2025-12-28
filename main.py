import imaplib
import os
import email
from email.header import decode_header
from datetime import datetime
from dotenv import load_dotenv
from email.utils import parseaddr


load_dotenv()

IMAP_SERVER = os.getenv('IMAP_SERVER')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
hoy = datetime.now().strftime("%d-%b-%Y")
lista_blanca = {"dogsmanga455@gmail.com",
                "hualpablas5@gmail.com"}

CARPETA = 'C:/ProjectsPython/automatizacion_correo_a_excel/archivos'
os.makedirs(CARPETA, exist_ok=True)

def limpiarTexto(texto):
    if not texto: return ""
    decoded_list = decode_header(texto) #[(b'\xc2\xa1Atenci\xc3\xb3n!', 'utf-8'),(),...] 
    header_value, charset = decoded_list[0] #[(b'\xc2\xa1Atenci\xc3\xb3n!', 'utf-8')] solo el primero
    if isinstance(header_value,bytes):
        try:
            return header_value.decode(charset or 'utf-8')
        except:
            return header_value.decode('utf-8',errors='ignore')
    return str(header_value)



mensaje_total =[]
def procesar_correo():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status, mensajes = mail.search(None, f'(UNSEEN ON {hoy})')
    #[b'21 22 23']
    ids_correos = mensajes[0].split()
                #b'21 22 23' => [b'21',b'22',b'23']
    print(mensajes)
    print(mensajes[0])
    print(f'Correos no leidos: {len(ids_correos)}. Filtrando...')

    for num in ids_correos:
        status, data = mail.fetch(num, "(RFC822)")
        #[(b'1 (RFC822 {5000}', b'Return-Path: <x@gmail.com>\r\nReceived: from ...\r\nSubject: =?utf-8?b?RmFjdHVyYQ==?=\r\n\r\nHola, adjunto factura...')]
        mensaje = email.message_from_bytes(data[0][1])
        #de 0 y 1, a un objeto mensaje con metodos (pero sigue codificado)

        asunto = limpiarTexto(mensaje.get("Subject"))
        from_raw = mensaje.get("From", "")
        nombre, correo_remitente = parseaddr(from_raw)
        correo_remitente = correo_remitente.lower()

        es_remitente_valido = correo_remitente in lista_blanca

        print(f"Procesando: {asunto} | De: {from_raw}")

        if es_remitente_valido:
            print("  ✅ APROBADO: Cumple filtros de seguridad.")
            
            archivo_encontrado = False
            for parte in mensaje.walk():
                # Content-Disposition ayuda a saber si es un adjunto real y no una imagen de firma
                content_disposition = str(parte.get("Content-Disposition"))

                if parte.get_content_type() == "application/pdf" and "attachment" in content_disposition:
                    nombre_archivo = limpiarTexto(parte.get_filename())
                    
                    if nombre_archivo:
                        ruta = os.path.join(CARPETA, nombre_archivo)
                        with open(ruta, "wb") as f:
                            f.write(parte.get_payload(decode=True))
                        print(f"  📥 PDF Guardado: {nombre_archivo}")
                        archivo_encontrado = True
            
            if archivo_encontrado:
                # Solo marcamos como LEÍDO si guardamos algo exitosamente
                mail.store(num, '+FLAGS', '\\Seen')
        else:
            print("  ❌ IGNORADO: No es de confianza o no es una factura.")

    mail.logout()
    
if __name__ == "__main__":
    procesar_correo()