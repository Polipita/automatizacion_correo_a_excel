import os
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = 'credenciales/credentials.json'
TOKEN_FILE = 'token.json'

IMAP_SERVER = os.getenv('IMAP_SERVER')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

ID_CARPETA_ENTRADA = os.getenv('ID_CARPETA_ENTRADA')
ID_CARPETA_PROCESADOS = os.getenv('ID_CARPETA_PROCESADOS')
ID_HOJA_CALCULO = os.getenv('ID_HOJA_CALCULO')

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]
remitentes_extraidos =  os.getenv('REMITENTES_PERMITIDOS','')
if remitentes_extraidos:
    REMITENTES_PERMITIDOS = set(remitentes_extraidos.split(','))
else:
    REMITENTES_PERMITIDOS = set()