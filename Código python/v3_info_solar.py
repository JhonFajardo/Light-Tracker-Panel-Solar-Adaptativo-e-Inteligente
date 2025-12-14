import serial
import time
import datetime
import sys
import pytz 
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN ---
PORT = '/dev/rfcomm0'  # En Linux
# PORT = 'COMx'        # En Windows
BAUD_RATE = 9600

# Base de datos de ciudades (IDs 1-6)
LOCATIONS = {
    1: {"name": "Bogotá",    "coords": (4.7110, -74.0721),   "tz": "America/Bogota"},
    2: {"name": "Madrid",    "coords": (40.4168, -3.7038),   "tz": "Europe/Madrid"},
    3: {"name": "Sídney",    "coords": (-33.8688, 151.2093), "tz": "Australia/Sydney"},
    4: {"name": "Tokio",     "coords": (35.6762, 139.6503),  "tz": "Asia/Tokyo"},
    5: {"name": "Alaska",    "coords": (61.2181, -149.9003), "tz": "America/Anchorage"},
    6: {"name": "Polo Sur",  "coords": (-90.0000, 0.0000),   "tz": "Antarctica/South_Pole"}
}

def enviar_trama(bt_serial, az, el, hora_str, id_loc):
    # Formato: AxxxEyyyHhhmmssIn
    trama = f"A{az:03d}E{el:03d}H{hora_str}I{id_loc}"
    bt_serial.write(trama.encode('utf-8'))
    return trama

def modo_automatico(bt_serial):
    print("\n--- MODO AUTOMÁTICO ---")
    print("Elige una ciudad:")
    for k, v in LOCATIONS.items():
        print(f"{k}. {v['name']}")
    
    try:
        opc = int(input("Opción: "))
        if opc not in LOCATIONS: return
        
        loc = LOCATIONS[opc]
        tz = pytz.timezone(loc["tz"])
        
        print(f"\nRastreando sol en {loc['name']}... (Ctrl+C para salir)")
        
        while True:
            ahora = datetime.datetime.now(tz)
            az = int(get_azimuth(loc["coords"][0], loc["coords"][1], ahora))
            el = int(max(0, get_altitude(loc["coords"][0], loc["coords"][1], ahora)))
            
            # Hora actual de la ciudad
            hora_str = ahora.strftime("%H%M%S")
            
            trama = enviar_trama(bt_serial, az, el, hora_str, opc)
            print(f"[{loc['name']}] {trama}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nSaliendo al menú...")

def modo_manual(bt_serial):
    print("\n--- MODO MANUAL ---")
    print("Ingresa los ángulos. (Ctrl+C para salir)")
    
    # ID 7 reservado para "MANUAL"
    ID_MANUAL = 7 
    
    try:
        while True:
            # Pedimos hora del sistema para que el reloj de la FPGA siga vivo
            ahora = datetime.datetime.now()
            hora_str = ahora.strftime("%H%M%S")
            
            print("-" * 20)
            in_az = input("Azimut (0-180): ")
            in_el = input("Elevación (0-90): ")
            
            # Validación simple
            try:
                az = int(in_az)
                el = int(in_el)
                
                # Enviar una ráfaga de datos (para asegurar que llegue)
                trama = enviar_trama(bt_serial, az, el, hora_str, ID_MANUAL)
                print(f"Enviado: {trama}")
                
            except ValueError:
                print("Error: Ingresa solo números enteros.")
                
    except KeyboardInterrupt:
        print("\nSaliendo al menú...")

def main():
    try:
        print(f"Conectando a {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado.\n")
        
        while True:
            print("\n=== SOLAR TRACKER CONTROL ===")
            print("1. Modo Automático (Simulación)")
            print("2. Modo Manual (Consola)")
            print("0. Salir")
            
            opcion = input("Elige: ")
            
            if opcion == '1':
                modo_automatico(bt_serial)
            elif opcion == '2':
                modo_manual(bt_serial)
            elif opcion == '0':
                break
            else:
                print("Opción inválida")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'bt_serial' in locals() and bt_serial.is_open:
            bt_serial.close()

if __name__ == "__main__":
    main()