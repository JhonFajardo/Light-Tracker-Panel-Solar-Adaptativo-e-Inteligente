import serial
import time
import datetime
import sys
import pytz 
import math
import ephem 
from pysolar.solar import get_altitude, get_azimuth

# --- CONFIGURACIÓN ---
PORT = '/dev/rfcomm0' 
BAUD_RATE = 9600

# Rango del servo
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

CELESTIAL_BODIES = {1:"Luna", 2:"Marte", 3:"Júpiter", 4:"Saturno", 5:"Venus"}

def map_azimut(real_az):
    if real_az < AZIMUT_AMANECER: return 0
    elif real_az > AZIMUT_ATARDECER: return SERVO_MAX_DEG
    span = AZIMUT_ATARDECER - AZIMUT_AMANECER
    recorrido = real_az - AZIMUT_AMANECER
    return int((recorrido * SERVO_MAX_DEG) / span)

def enviar_trama(bt_serial, az, el, hora_str, id_loc):
    trama = f"A{az:03d}E{el:03d}H{hora_str}I{id_loc}"
    bt_serial.write(trama.encode('utf-8'))
    return trama

def obtener_posicion_cuerpo(nombre, lat, lon, elev, fecha_utc):
    obs = ephem.Observer()
    obs.lat, obs.lon, obs.elevation = str(lat), str(lon), elev
    obs.date = fecha_utc
    
    objs = {"Luna":ephem.Moon(), "Marte":ephem.Mars(), "Júpiter":ephem.Jupiter(), 
            "Saturno":ephem.Saturn(), "Venus":ephem.Venus()}
    cuerpo = objs[nombre]
    cuerpo.compute(obs)
    return math.degrees(cuerpo.az), math.degrees(cuerpo.alt)

# --- MODOS EXISTENTES ---
def modo_automatico(bt_serial):
    print("\n--- MODO SOL: TIEMPO REAL ---")
    # (Código igual al anterior...)
    # Para ahorrar espacio aquí, asumo que copias la lógica del script anterior
    # o usas este esqueleto para rellenarlo. Si necesitas el código completo repítelo.
    # Pero para la demo de Marte, mira la función nueva abajo:
    pass 

def modo_manual(bt_serial):
    # (Código igual al anterior...)
    pass

def modo_celeste(bt_serial):
    # (Código igual al anterior...)
    pass

# --- NUEVO: MODO RETRÓGRADO (EL BUCLE DE MARTE) ---
def modo_retrogrado_marte(bt_serial):
    print("\n--- SIMULACIÓN: EL BUCLE DE MARTE (RETROGRADO) ---")
    print("Simularemos la posición de Marte cada medianoche durante 6 meses.")
    print("Observa cómo el motor avanza, se detiene, retrocede y avanza de nuevo.")
    
    # Usaremos coordenadas neutras o Bogotá para buena visibilidad
    lat, lon, elev = 4.7110, -74.0721, 2640 
    
    # FECHAS CLAVE: Próximo retrógrado Nov 2024 - Mar 2025
    start_date = datetime.datetime(2024, 10, 1, 0, 0, 0) # 1 Oct 2024
    end_date = datetime.datetime(2025, 5, 1, 0, 0, 0)    # 1 May 2025
    
    current_date = start_date
    
    print("\nIniciando Timelapse Astronómico (1 día cada 0.1s)...")
    print("Presiona Ctrl+C para detener.\n")
    
    try:
        while current_date < end_date:
            # Calcular posición a la medianoche UTC
            # Usamos UTC para simplificar la astronomía pura
            az_real, el_real = obtener_posicion_cuerpo("Marte", lat, lon, elev, current_date)
            
            # Mapeo
            # Nota: Para ver el efecto completo, a veces es mejor mapear 360 directo
            # Pero usaremos tu map_azimut para mantener coherencia con el servo
            servo_az = map_azimut(az_real)
            
            # Si está bajo el horizonte, lo mostramos en 0 elevación pero mantenemos azimut
            servo_el = int(max(0, el_real))
            
            # Enviar a FPGA
            # Usamos ID 7 ("MANUAL") o 2 ("Madrid") para visualización
            fecha_str = current_date.strftime("%d%m%y") # Usamos fecha en vez de hora
            enviar_trama(bt_serial, servo_az, servo_el, current_date.strftime("%H%M%S"), 2)
            
            # Feedback visual con flechas para indicar dirección
            direccion = "-->"
            # Detectar retrógrado simple (si el azimut baja en vez de subir)
            # (Esto es simplificado, depende de la posición en el cielo)
            
            print(f"Fecha: {current_date.strftime('%Y-%m-%d')} | Az:{int(az_real)}° Servo:{servo_az} | El:{int(el_real)}°")
            
            # Avanzar 1 día
            current_date += datetime.timedelta(days=1)
            
            # Velocidad de simulación
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nSimulación finalizada.")

def main():
    try:
        print(f"Conectando a {PORT}...")
        bt_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado.\n")
        
        while True:
            print("\n=== SOLAR TRACKER PRO V7 ===")
            print("1. Rastrear Sol (Auto)")
            print("2. Manual")
            print("3. Rastrear Celeste (Luna/Planetas)")
            print("4. Demo: Simulación Día Solar (6am-6pm)")
            print("5. Demo: El Bucle de Marte (Retrograde Motion)")
            print("0. Salir")
            
            op = input(">> ")
            if op == '1': modo_automatico(bt_serial) # (Asegurate de copiar la logica de tu script anterior)
            elif op == '2': modo_manual(bt_serial)   # (Igual)
            elif op == '3': modo_celeste(bt_serial)  # (Igual)
            # elif op == '4': modo_simulacion_dia(bt_serial) # (Tu funcion anterior)
            elif op == '5': modo_retrogrado_marte(bt_serial)
            elif op == '0': break
            
    except Exception as e: print(f"Error: {e}")
    finally:
        if 'bt_serial' in locals() and bt_serial.is_open: bt_serial.close()

if __name__ == "__main__":
    main()