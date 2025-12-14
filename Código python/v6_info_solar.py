import serial
import time
import datetime
import sys
import pytz 
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN DE CONEXIÓN ---
PORT = '/dev/rfcomm0'  # Linux
# PORT = 'COM5'        # Windows
BAUD_RATE = 9600

# --- CONFIGURACIÓN DE ZOOM (Rango del Servo) ---
AZIMUT_AMANECER = 60   # 0% del servo
AZIMUT_ATARDECER = 300 # 100% del servo
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
    """ Mapea el azimut real al rango de 270 grados del servo """
    if real_az < AZIMUT_AMANECER: return 0
    elif real_az > AZIMUT_ATARDECER: return SERVO_MAX_DEG
    
    span_sol = AZIMUT_ATARDECER - AZIMUT_AMANECER
    recorrido = real_az - AZIMUT_AMANECER
    servo_angle = (recorrido * SERVO_MAX_DEG) / span_sol
    return int(servo_angle)

def enviar_trama(bt_serial, az_servo, el, hora_str, id_loc):
    trama = f"A{az_servo:03d}E{el:03d}H{hora_str}I{id_loc}"
    bt_serial.write(trama.encode('utf-8'))
    return trama

def modo_automatico(bt_serial):
    print("\n--- MODO AUTOMÁTICO (Tiempo Real) ---")
    print("Elige una ciudad:")
    for k, v in LOCATIONS.items(): print(f"{k}. {v['name']}")
    
    try:
        opc = int(input("Opción: "))
        if opc not in LOCATIONS: return
        
        loc = LOCATIONS[opc]
        tz = pytz.timezone(loc["tz"])
        
        print(f"\nRastreando en {loc['name']}... (Ctrl+C para salir)")
        while True:
            ahora = datetime.datetime.now(tz)
            real_az = get_azimuth(loc["coords"][0], loc["coords"][1], ahora)
            real_el = int(max(0, get_altitude(loc["coords"][0], loc["coords"][1], ahora)))
            
            servo_az = map_azimut(real_az)
            hora_str = ahora.strftime("%H%M%S")
            
            trama = enviar_trama(bt_serial, servo_az, real_el, hora_str, opc)
            print(f"[{loc['name']}] {ahora.strftime('%H:%M:%S')} | AzReal:{int(real_az)}° -> Servo:{servo_az}° | El:{real_el}°")
            time.sleep(1) 
            
    except KeyboardInterrupt: print("\nSaliendo...")

def modo_manual(bt_serial):
    print("\n--- MODO MANUAL ---")
    try:
        while True:
            ahora = datetime.datetime.now()
            hora_str = ahora.strftime("%H%M%S")
            in_az = input("Ángulo Servo Azimut (0-270): ")
            in_el = input("Ángulo Elevación (0-90): ")
            try:
                az, el = int(in_az), int(in_el)
                trama = enviar_trama(bt_serial, az, el, hora_str, 7)
                print(f"Enviado: {trama}")
            except ValueError: print("Error numérico.")
    except KeyboardInterrupt: print("\nSaliendo...")

# --- NUEVA FUNCIÓN: SIMULACIÓN DE DÍA ---
def modo_simulacion(bt_serial):
    print("\n--- MODO SIMULACIÓN (6AM - 6PM) ---")
    print("Este modo recorrerá todo el día de hoy en cámara rápida.")
    print("Elige una ciudad:")
    for k, v in LOCATIONS.items(): print(f"{k}. {v['name']}")
    
    try:
        opc = int(input("Opción: "))
        if opc not in LOCATIONS: return
        
        loc = LOCATIONS[opc]
        tz = pytz.timezone(loc["tz"])
        
        # Obtener fecha de hoy en esa zona
        fecha_hoy = datetime.datetime.now(tz).date()
        
        # Configurar inicio (6:00 AM) y fin (6:00 PM)
        hora_inicio = datetime.time(6, 0, 0)
        hora_fin = datetime.time(18, 0, 0)
        
        # Crear objetos datetime completos
        tiempo_simulado = datetime.datetime.combine(fecha_hoy, hora_inicio)
        tiempo_simulado = tz.localize(tiempo_simulado) # Asignar zona horaria
        
        tiempo_limite = datetime.datetime.combine(fecha_hoy, hora_fin)
        tiempo_limite = tz.localize(tiempo_limite)

        print(f"\nIniciando simulación para: {loc['name']} (Fecha: {fecha_hoy})")
        print("Presiona Ctrl+C para detener.")

        while tiempo_simulado <= tiempo_limite:
            # 1. Calcular posición solar para la hora simulada
            real_az = get_azimuth(loc["coords"][0], loc["coords"][1], tiempo_simulado)
            real_el = int(max(0, get_altitude(loc["coords"][0], loc["coords"][1], tiempo_simulado)))
            
            # 2. Mapear al servo
            servo_az = map_azimut(real_az)
            
            # 3. Formatear hora simulada para la LCD
            hora_str = tiempo_simulado.strftime("%H%M%S")
            
            # 4. Enviar a FPGA
            enviar_trama(bt_serial, servo_az, real_el, hora_str, opc)
            
            # 5. Mostrar en consola
            print(f"Simulando: {tiempo_simulado.strftime('%H:%M')} | Az:{int(real_az)}° El:{real_el}°")
            
            # 6. Avanzar el tiempo (Saltos de 10 minutos)
            tiempo_simulado += datetime.timedelta(minutes=10)
            
            # 7. Velocidad de la animación (0.15s reales = 10 min simulados)
            time.sleep(0.15)

        print("\nSimulación finalizada. El sol se ha puesto.")
        time.sleep(2)

    except KeyboardInterrupt: print("\nSimulación cancelada.")

def main():
    try:
        print(f"Conectando a {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado.\n")
        
        while True:
            print("\n=== SOLAR TRACKER V5 DEMO ===")
            print("1. Modo Automático (Tiempo Real)")
            print("2. Modo Manual")
            print("3. Simulación Día Completo (6AM - 6PM)")
            print("0. Salir")
            op = input(">> ")
            if op == '1': modo_automatico(bt_serial)
            elif op == '2': modo_manual(bt_serial)
            elif op == '3': modo_simulacion(bt_serial)
            elif op == '0': break
                
    except Exception as e: print(f"Error: {e}")
    finally:
        if 'bt_serial' in locals() and bt_serial.is_open: bt_serial.close()

if __name__ == "__main__":
    main()