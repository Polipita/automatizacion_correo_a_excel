# Sistema de Automatización de Procesamiento de Facturas (RPA)

Este proyecto implementa un flujo de trabajo automatizado (pipeline) para Automatización de Facturas (RPA) con Google Cloud

Sistema automatizado que procesa facturas PDF recibidas por correo, extrae datos clave y los sincroniza con Google Sheets, gestionando el archivado de documentos para evitar duplicados.

## ⚡ Funcionalidades
* **Detección Automática:** Monitorea la entrada de nuevos PDFs en Google Drive.
* **Extracción de Datos:** Obtiene RUC, Fechas y Totales usando Regex y PyMuPDF.
* **Integridad de Datos:** Mueve archivos procesados a una carpeta "Histórico" para evitar duplicidad.
* **Reporte en Nube:** Inserta datos en Google Sheets con ID autoincremental en tiempo real.

## 🛠️ Stack Tecnológico
* **Python** (Lógica principal)
* **Google Drive API & Sheets API** (Integración Cloud)
* **PyMuPDF / Regex** (OCR y Parsing)

## 📸 Flujo del Proceso
<img width="571" height="265" alt="image" src="https://github.com/user-attachments/assets/dade6241-c4b7-4c37-8748-8dcf42fb127c" />

---
*Proyecto Personal desarrollado por Polipita*
