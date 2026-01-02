import sys
import procesar_correos
import procesar_excel

def menu():
    print("="*30)
    print("BOT DE FACTURACIÓN AUTOMÁTICA")
    print("="*30)
    print("1. Ejecutar TODO (Descargar + Excel)")
    print("2. Solo Descargar Correos")
    print("3. Solo Procesar PDFs a Excel")
    print("4. Salir")
    
    opcion = input("\nElige una opción (1-4): ")
    return opcion

if __name__ == "__main__":
    while True:
        opcion = menu()
        
        if opcion == '1':
            procesar_correos.ejecutar_bajada_correos()
            procesar_excel.procesar_archivos()
            
        elif opcion == '2':
            procesar_correos.ejecutar_bajada_correos()
            
        elif opcion == '3':
            procesar_excel.procesar_archivos()
            
        elif opcion == '4':
            print("Adios")
            sys.exit()
        else:
            print("Opción no válida.")
        
        input("\nPresiona ENTER para continuar...")