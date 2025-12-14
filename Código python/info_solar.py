import serial
import time
import datetime
import sys
import pytz # Librería para zonas horarias
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN DEL PUERTO ---
PORT = '/dev/rfcomm0' 
BAUD_RATE = 9600

# --- BASE DE DATOS DE UBICACIONES ---
# Formato: "Nombre": (Latitud, Longitud, ZonaHoraria)
LOCATIONS = {
    1: {"name": "Bogotá, Colombia",   "coords": (4.7110, -74.0721),   "tz": "America/Bogota"},
    2: {"name": "Madrid, España",     "coords": (40.4168, -3.7038),   "tz": "Europe/Madrid"},
    3: {"name": "Sídney, Australia",  "coords": (-33.8688, 151.2093), "tz": "Australia/Sydney"},
    4: {"name": "Tokio, Japón",       "coords": (35.6762, 139.6503),  "tz": "Asia/Tokyo"},
    5: {"name": "Anchorage, Alaska",  "coords": (61.2181, -149.9003), "tz": "America/Anchorage"},
    6: {"name": "Polo Sur (Antártida)","coords": (-90.0000, 0.0000),  "tz": "Antarctica/South_Pole"}
}

def enviar_datos_solares(bt_serial, location):
    lat, lon = location["coords"]
    tz_name = location["tz"]
    timezone = pytz.timezone(tz_name)
    
    print(f"\n--- Rastreando sol en: {location['name']} ---")
    print("Presiona Ctrl+C para volver al menú principal.\n")

    try:
        while True:
            # 1. Obtener hora actual EN LA ZONA HORARIA DE LA CIUDAD ELEGIDA
            ahora = datetime.datetime.now(timezone)
            
            # 2. Calcular posición solar
            azimut_calc = get_azimuth(lat, lon, ahora)
            elevacion_calc = get_altitude(lat, lon, ahora)
            
            # 3. Limpieza de datos
            if elevacion_calc < 0:
                elevacion_calc = 0
            
            az = int(azimut_calc)
            el = int(elevacion_calc)

            # 4. Formatear trama: AxxxEyyy (Corrección 3 dígitos aplicada)
            trama = f"A{az:03d}E{el:03d}"
            
            # 5. Enviar por Bluetooth
            bt_serial.write(trama.encode('utf-8'))
            
            # Feedback en consola
            print(f"[{location['name']}] Hora local: {ahora.strftime('%H:%M:%S')} | Enviando: {trama}")
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nDeteniendo transmisión...")
        time.sleep(1)
        # No cerramos el programa, el 'return' nos lleva de vuelta al menú

def menu_principal():
    bt_serial = None
    try:
        print(f"Conectando al puerto {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("¡Conexión Bluetooth exitosa!\n")

        while True:
            print("="*40)
            print(" SELECCIONA UNA UBICACIÓN PARA SIMULAR")
            print("="*40)
            for key, val in LOCATIONS.items():
                print(f"{key}. {val['name']}")
            print("0. Salir")
            
            try:
                opcion = int(input("\nIngresa el número y presiona Enter: "))
                
                if opcion == 0:
                    print("Saliendo. ¡Adiós!")
                    break
                elif opcion in LOCATIONS:
                    # Iniciar la transmisión para la ciudad elegida
                    enviar_datos_solares(bt_serial, LOCATIONS[opcion])
                else:
                    print("Opción no válida. Intenta de nuevo.")
            except ValueError:
                print("Por favor, ingresa un número válido.")

    except serial.SerialException as e:
        print(f"\n[ERROR CRÍTICO] No se pudo abrir el puerto {PORT}.")
        print(f"Detalle: {e}")
    except KeyboardInterrupt:
        print("\nPrograma terminado forzosamente.")
    finally:
        if bt_serial and bt_serial.is_open:
            bt_serial.close()
            print("Puerto cerrado.")

if __name__ == "__main__":
    menu_principal()