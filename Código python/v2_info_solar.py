import serial
import time
import datetime
import sys
import pytz 
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN ---
# En Linux suele ser /dev/rfcomm0. En Windows COMx.
PORT = '/dev/rfcomm0' 
BAUD_RATE = 9600

# --- BASE DE DATOS DE UBICACIONES ---
LOCATIONS = {
    1: {"name": "Bogotá",    "coords": (4.7110, -74.0721),   "tz": "America/Bogota"},
    2: {"name": "Madrid",    "coords": (40.4168, -3.7038),   "tz": "Europe/Madrid"},
    3: {"name": "Sídney",    "coords": (-33.8688, 151.2093), "tz": "Australia/Sydney"},
    4: {"name": "Tokio",     "coords": (35.6762, 139.6503),  "tz": "Asia/Tokyo"},
    5: {"name": "Alaska",    "coords": (61.2181, -149.9003), "tz": "America/Anchorage"},
    6: {"name": "Polo Sur",  "coords": (-90.0000, 0.0000),   "tz": "Antarctica/South_Pole"}
}

def enviar_datos(bt_serial, location, id_loc):
    lat, lon = location["coords"]
    timezone = pytz.timezone(location["tz"])
    nombre = location["name"]
    
    print(f"\n--- Enviando datos para: {nombre} ---")
    print("Presiona Ctrl+C para cambiar de ciudad.\n")

    try:
        while True:
            # 1. Obtener hora en la zona horaria seleccionada
            ahora = datetime.datetime.now(timezone)
            
            # 2. Calcular Solar
            az = int(get_azimuth(lat, lon, ahora))
            el_calc = get_altitude(lat, lon, ahora)
            el = int(max(0, el_calc)) # Si es negativo (noche), poner 0
            
            # 3. Preparar datos de Tiempo (HHMMSS)
            hora_str = ahora.strftime("%H%M%S")
            
            # 4. Formatear Trama: AxxxEyyyHhhmmssIi
            # Ejemplo: A180E045H143000I1
            trama = f"A{az:03d}E{el:03d}H{hora_str}I{id_loc}"
            
            # 5. Enviar
            bt_serial.write(trama.encode('utf-8'))
            
            # Log en pantalla
            print(f"[{nombre}] {ahora.strftime('%H:%M:%S')} -> {trama}")
            
            time.sleep(1) # Actualizar cada segundo

    except KeyboardInterrupt:
        print("\nDeteniendo envío...")
        time.sleep(0.5)
        # El retorno lleva de vuelta al menú

def menu():
    bt_serial = None
    try:
        print(f"Abriendo puerto {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("¡Conexión FPGA Establecida!\n")

        while True:
            print("-" * 30)
            print(" SELECCIONA UNA ZONA")
            print("-" * 30)
            for k, v in LOCATIONS.items():
                print(f"{k}. {v['name']}")
            print("0. Salir")

            try:
                opc = int(input("\nOpción: "))
                if opc == 0: break
                if opc in LOCATIONS:
                    enviar_datos(bt_serial, LOCATIONS[opc], opc)
                else:
                    print("Opción inválida.")
            except ValueError:
                print("Digita un número.")
                
    except serial.SerialException as e:
        print(f"Error Serial: {e}")
        print("Recuerda ejecutar: sudo rfcomm bind 0 <MAC>")
    except KeyboardInterrupt:
        print("\nSalida forzada.")
    finally:
        if bt_serial and bt_serial.is_open:
            bt_serial.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    menu()