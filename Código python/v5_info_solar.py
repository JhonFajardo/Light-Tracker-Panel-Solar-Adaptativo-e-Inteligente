import serial
import time
import datetime
import sys
import pytz 
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN DE CONEXIÓN ---
PORT = '/dev/rfcomm0'  # Linux
BAUD_RATE = 9600

# --- CONFIGURACIÓN DE "ZOOM" DE MOVIMIENTO ---
# Define el rango útil donde quieres que el servo se mueva de 0 a 100%
# Ajusta estos valores según por dónde sale y se oculta el sol en tu ventana.
AZIMUT_AMANECER = 60   # Ángulo donde definimos que es "0" para el servo
AZIMUT_ATARDECER = 300 # Ángulo donde definimos que es el tope del servo (270)

# Rango total del servo físico (Grados)
SERVO_MAX_DEG = 270 

# Ubicaciones
LOCATIONS = {
    1: {"name": "Bogotá",    "coords": (4.7110, -74.0721),   "tz": "America/Bogota"},
    2: {"name": "Madrid",    "coords": (40.4168, -3.7038),   "tz": "Europe/Madrid"},
    3: {"name": "Sídney",    "coords": (-33.8688, 151.2093), "tz": "Australia/Sydney"},
    4: {"name": "Tokio",     "coords": (35.6762, 139.6503),  "tz": "Asia/Tokyo"},
    5: {"name": "Alaska",    "coords": (61.2181, -149.9003), "tz": "America/Anchorage"},
    6: {"name": "Polo Sur",  "coords": (-90.0000, 0.0000),   "tz": "Antarctica/South_Pole"}
}

def map_azimut(real_az):
    """
    Convierte el Azimut Real (Geográfico) a Ángulo del Servo (Físico)
    para aprovechar todo el rango de movimiento de 270 grados.
    """
    # 1. Si es antes del amanecer, mantener en 0
    if real_az < AZIMUT_AMANECER:
        return 0
    # 2. Si es después del atardecer, mantener en tope
    elif real_az > AZIMUT_ATARDECER:
        return SERVO_MAX_DEG
    
    # 3. Calcular proporción
    # Cuántos grados de sol hay en total en nuestra ventana
    span_sol = AZIMUT_ATARDECER - AZIMUT_AMANECER
    # Cuántos grados llevamos recorridos
    recorrido = real_az - AZIMUT_AMANECER
    
    # Regla de 3:
    servo_angle = (recorrido * SERVO_MAX_DEG) / span_sol
    
    return int(servo_angle)

def enviar_trama(bt_serial, az_servo, el, hora_str, id_loc):
    # Enviamos az_servo (0-270) en lugar del azimut real
    trama = f"A{az_servo:03d}E{el:03d}H{hora_str}I{id_loc}"
    bt_serial.write(trama.encode('utf-8'))
    return trama

def modo_automatico(bt_serial):
    print("\n--- MODO AUTOMÁTICO (Rango Extendido) ---")
    print(f"Mapeando sol de {AZIMUT_AMANECER}° a {AZIMUT_ATARDECER}° -> Servo 0-270°")
    print("Elige una ciudad:")
    for k, v in LOCATIONS.items():
        print(f"{k}. {v['name']}")
    
    try:
        opc = int(input("Opción: "))
        if opc not in LOCATIONS: return
        
        loc = LOCATIONS[opc]
        tz = pytz.timezone(loc["tz"])
        
        while True:
            ahora = datetime.datetime.now(tz)
            
            # Obtener datos reales
            real_az = get_azimuth(loc["coords"][0], loc["coords"][1], ahora)
            real_el = get_altitude(loc["coords"][0], loc["coords"][1], ahora)
            real_el = int(max(0, real_el))
            
            # --- MAPEO INTELIGENTE ---
            servo_az = map_azimut(real_az)
            
            hora_str = ahora.strftime("%H%M%S")
            trama = enviar_trama(bt_serial, servo_az, real_el, hora_str, opc)
            
            print(f"[{loc['name']}] Real Az:{int(real_az)}° -> Servo:{servo_az}° | El:{real_el}°")
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\nSaliendo...")

def modo_manual(bt_serial):
    print("\n--- MODO MANUAL ---")
    try:
        while True:
            ahora = datetime.datetime.now()
            hora_str = ahora.strftime("%H%M%S")
            
            in_az = input("Ángulo Servo Azimut (0-270): ")
            in_el = input("Ángulo Elevación (0-90): ")
            
            try:
                az = int(in_az)
                el = int(in_el)
                trama = enviar_trama(bt_serial, az, el, hora_str, 7)
                print(f"Moviendo a: {trama}")
            except ValueError:
                print("Error numérico.")
    except KeyboardInterrupt:
        print("\nSaliendo...")

def main():
    try:
        print(f"Conectando a {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado.\n")
        
        while True:
            print("\n=== SOLAR TRACKER V4 ===")
            print("1. Modo Automático (Con Zoom de Movimiento)")
            print("2. Modo Manual")
            print("0. Salir")
            op = input(">> ")
            if op == '1': modo_automatico(bt_serial)
            elif op == '2': modo_manual(bt_serial)
            elif op == '0': break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'bt_serial' in locals() and bt_serial.is_open:
            bt_serial.close()

if __name__ == "__main__":
    main()