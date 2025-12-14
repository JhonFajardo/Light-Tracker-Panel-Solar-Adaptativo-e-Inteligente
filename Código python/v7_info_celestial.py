import serial
import time
import datetime
import sys
import pytz 
import math
import ephem  # <--- NUEVA LIBRERÍA
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN DE CONEXIÓN ---
PORT = '/dev/rfcomm0' 
BAUD_RATE = 9600

# --- CONFIGURACIÓN DE ZOOM (Rango del Servo) ---
AZIMUT_AMANECER = 60   
AZIMUT_ATARDECER = 300 
SERVO_MAX_DEG = 270 

# Ubicaciones
LOCATIONS = {
    1: {"name": "Bogotá",    "coords": (4.7110, -74.0721),   "tz": "America/Bogota",    "elevation": 2640},
    2: {"name": "Madrid",    "coords": (40.4168, -3.7038),   "tz": "Europe/Madrid",     "elevation": 650},
    3: {"name": "Sídney",    "coords": (-33.8688, 151.2093), "tz": "Australia/Sydney",  "elevation": 58},
    4: {"name": "Tokio",     "coords": (35.6762, 139.6503),  "tz": "Asia/Tokyo",        "elevation": 40},
    5: {"name": "Alaska",    "coords": (61.2181, -149.9003), "tz": "America/Anchorage", "elevation": 30},
    6: {"name": "Polo Sur",  "coords": (-90.0000, 0.0000),   "tz": "Antarctica/South_Pole", "elevation": 2800}
}

# Cuerpos Celestes Disponibles
CELESTIAL_BODIES = {
    1: "Luna",
    2: "Marte",
    3: "Júpiter",
    4: "Saturno",
    5: "Venus"
}

def map_azimut(real_az):
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

# --- FUNCIÓN PARA CALCULAR POSICIÓN CELESTE ---
def obtener_posicion_cuerpo(nombre_cuerpo, lat, lon, elev, fecha_hora_utc):
    obs = ephem.Observer()
    obs.lat = str(lat) # ephem espera strings para grados
    obs.lon = str(lon)
    obs.elevation = elev
    obs.date = fecha_hora_utc
    
    cuerpo = None
    if nombre_cuerpo == "Luna": cuerpo = ephem.Moon()
    elif nombre_cuerpo == "Marte": cuerpo = ephem.Mars()
    elif nombre_cuerpo == "Júpiter": cuerpo = ephem.Jupiter()
    elif nombre_cuerpo == "Saturno": cuerpo = ephem.Saturn()
    elif nombre_cuerpo == "Venus": cuerpo = ephem.Venus()
    
    cuerpo.compute(obs)
    
    # ephem devuelve radianes, convertir a grados
    az = math.degrees(cuerpo.az)
    alt = math.degrees(cuerpo.alt)
    
    return az, alt

# --- MODOS ANTERIORES (Resumidos para brevedad) ---
def modo_automatico(bt_serial):
    print("\n--- MODO SOL: TIEMPO REAL ---")
    for k, v in LOCATIONS.items(): print(f"{k}. {v['name']}")
    try:
        opc = int(input("Opción: "))
        if opc not in LOCATIONS: return
        loc = LOCATIONS[opc]
        tz = pytz.timezone(loc["tz"])
        while True:
            ahora = datetime.datetime.now(tz)
            real_az = get_azimuth(loc["coords"][0], loc["coords"][1], ahora)
            real_el = int(max(0, get_altitude(loc["coords"][0], loc["coords"][1], ahora)))
            servo_az = map_azimut(real_az)
            trama = enviar_trama(bt_serial, servo_az, real_el, ahora.strftime("%H%M%S"), opc)
            print(f"Sol en {loc['name']}: Az:{int(real_az)}° El:{real_el}°")
            time.sleep(1) 
    except KeyboardInterrupt: pass

def modo_manual(bt_serial):
    # (Igual al anterior)
    print("\n--- MODO MANUAL ---")
    try:
        while True:
            ahora = datetime.datetime.now()
            in_az = input("Azimut (0-270): ")
            in_el = input("Elevación (0-90): ")
            try:
                enviar_trama(bt_serial, int(in_az), int(in_el), ahora.strftime("%H%M%S"), 7)
            except: pass
    except KeyboardInterrupt: pass

def modo_simulacion_sol(bt_serial):
    # (Igual al anterior, solo cambia la llamada en el menu)
    # ... codigo de simulacion solar ...
    print("Simulación solar no incluida en este snippet para ahorrar espacio, usa la versión anterior si la necesitas.")
    pass

# --- NUEVO: MODO CELESTE ---
def modo_celeste(bt_serial):
    print("\n--- RASTREADOR DE CUERPOS CELESTES ---")
    print("Este modo usa la librería astronómica Ephem.")
    
    # 1. Elegir Ubicación
    print("\n¿Desde dónde observamos?")
    for k, v in LOCATIONS.items(): print(f"{k}. {v['name']}")
    try:
        op_loc = int(input("Ubicación: "))
        if op_loc not in LOCATIONS: return
        loc = LOCATIONS[op_loc]
    except: return

    # 2. Elegir Cuerpo
    print("\n¿Qué cuerpo deseas rastrear?")
    for k, v in CELESTIAL_BODIES.items(): print(f"{k}. {v}")
    try:
        op_body = int(input("Cuerpo: "))
        if op_body not in CELESTIAL_BODIES: return
        body_name = CELESTIAL_BODIES[op_body]
    except: return

    # 3. Elegir Tipo de Rastreo
    print("\n¿Tipo de Rastreo?")
    print("1. Tiempo Real (Para dejarlo toda la noche)")
    print("2. Simulación Rápida (Ver movimiento de las próximas 12h)")
    op_mode = input(">> ")

    # Configuración de tiempo inicial
    tz = pytz.timezone(loc["tz"])
    ahora_utc = datetime.datetime.now(datetime.timezone.utc)
    
    if op_mode == '2':
        # En simulación, usamos una variable que avanza rápido
        tiempo_simulado = ahora_utc
        print(f"\nSimulando movimiento de {body_name}...")
    else:
        print(f"\nRastreando {body_name} en tiempo real...")

    try:
        while True:
            # Definir el tiempo a calcular
            if op_mode == '1': # Real
                calculo_time = datetime.datetime.now(datetime.timezone.utc)
                hora_display = datetime.datetime.now(tz)
                delay = 1
            else: # Simulación
                calculo_time = tiempo_simulado
                hora_display = tiempo_simulado.astimezone(tz)
                delay = 0.1
                tiempo_simulado += datetime.timedelta(minutes=10) # Avanzar 10 min por ciclo

            # CÁLCULO ASTRONÓMICO
            az_real, el_real = obtener_posicion_cuerpo(
                body_name, loc["coords"][0], loc["coords"][1], loc["elevation"], calculo_time
            )

            # Mapeo a Servo
            # NOTA: Los planetas pueden estar en 360 grados, map_azimut maneja el amanecer/atardecer solar
            # Para cuerpos nocturnos, a veces queremos verlos completos.
            # Usaremos map_azimut para mantener la lógica de "ventana de visión" de tu ventana física.
            servo_az = map_azimut(az_real)
            servo_el = int(max(0, el_real)) # Si está bajo el horizonte, poner 0

            # Enviar
            hora_str = hora_display.strftime("%H%M%S")
            # Usamos ID 7 para que salga "MANUAL" o podríamos reusar el ID de ciudad
            # Reusamos ID de ciudad para ver el nombre de la zona
            enviar_trama(bt_serial, servo_az, servo_el, hora_str, op_loc)

            print(f"[{body_name}] {hora_display.strftime('%H:%M')} | Az:{int(az_real)}° (Servo {servo_az}) | El:{int(el_real)}°")
            
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nVolviendo al menú...")

def main():
    try:
        print(f"Conectando a {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado.\n")
        
        while True:
            print("\n=== SISTEMA DE RASTREO UNIVERSAL V6 ===")
            print("1. Rastrear el SOL (Automático)")
            print("2. Control Manual")
            print("3. Simulación Solar (6AM-6PM)")
            print("4. Rastrear CUERPO CELESTE (Luna/Planetas)")
            print("0. Salir")
            op = input(">> ")
            if op == '1': modo_automatico(bt_serial)
            elif op == '2': modo_manual(bt_serial)
            # elif op == '3': modo_simulacion_sol(bt_serial) # (Descomenta si pegaste la funcion anterior)
            elif op == '4': modo_celeste(bt_serial)
            elif op == '0': break
                
    except Exception as e: print(f"Error: {e}")
    finally:
        if 'bt_serial' in locals() and bt_serial.is_open: bt_serial.close()

if __name__ == "__main__":
    main()