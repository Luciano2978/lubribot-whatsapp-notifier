# monitor.py
from playwright.sync_api import sync_playwright
import json
import os
import time
import re
from datetime import datetime
from scraper import enviar_mensaje_wsp

ARCHIVO_MEMORIA = "turnos_hoy.json"
MINUTOS_ESPERA = 5

def cargar_memoria():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r") as f:
            datos = json.load(f)
            # Verificamos que sea el día de hoy y que la estructura sea la nueva (dict)
            if datos.get("fecha") == fecha_hoy:
                turnos = datos.get("turnos_guardados", {})
                if isinstance(turnos, dict):
                    return turnos
    return {} # Si es otro día o no hay archivo, devolvemos diccionario vacío

def guardar_memoria(turnos_dict):
    datos = {
        "fecha": datetime.now().strftime('%Y-%m-%d'),
        "turnos_guardados": turnos_dict
    }
    with open(ARCHIVO_MEMORIA, "w") as f:
        json.dump(datos, f, indent=4) # indent=4 para que el JSON quede legible si lo abrís

def monitorear_turnos_nuevos():
    turnos_en_memoria = cargar_memoria()
    turnos_actuales_dict = {}
    fecha_hoy_crm = datetime.now().strftime('%d-%m-%Y')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context()
        page = context.new_page()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Revisando CRM...")
        
        page.goto("https://approcrm.com/")
        # Usamos las variables del .env
        page.fill("#txtusername", os.getenv("CRM_USER")) 
        page.fill("#txtpassword", os.getenv("CRM_PASS"))
        page.click("#btnLoginHtml")
        page.wait_for_load_state("networkidle")

        page.goto("https://approcrm.com/wfCalendar.aspx")
        page.wait_for_load_state("networkidle")

        eventos = page.evaluate("() => { return typeof events !== 'undefined' ? events : []; }")
        
        # Armamos un diccionario con la "foto" actual del CRM
        for turno in eventos:
            turno_id = str(turno.get('id', ''))
            fecha_turno = turno.get('clieAppointmentDate')
            
            if turno_id and fecha_turno == fecha_hoy_crm:
                # Extraemos y limpiamos los datos acá para guardarlos prolijos
                desc_raw = turno.get('description', '')
                lineas = [l.strip() for l in desc_raw.split('<br/>') if l.strip()]
                
                vehiculo = lineas[1] if len(lineas) > 1 else "Vehículo"
                tarea = lineas[-1] if len(lineas) > 0 else ""
                
                if "NADA" in vehiculo.upper():
                    vehiculo = re.sub(r'-?\s*NADA\w*', ' (Sin info de patente)', vehiculo, flags=re.IGNORECASE)
                
                # Guardamos todos los datos que necesitamos para el mensaje
                turnos_actuales_dict[turno_id] = {
                    "hora": turno.get('clieAppointmentTime', ''),
                    "cliente": turno.get('clieName', 'N/A'),
                    "vehiculo": vehiculo,
                    "box": turno.get('titleModal', 'Box N/A'),
                    "tarea": tarea
                }
        
        browser.close()

        ids_memoria = set(turnos_en_memoria.keys())
        ids_actuales = set(turnos_actuales_dict.keys())
        
        ids_nuevos = ids_actuales - ids_memoria
        ids_cancelados = ids_memoria - ids_actuales

        hubo_cambios = False
        mensaje_final = ""
        
        # 1. Procesar Turnos Nuevos
        if ids_nuevos:
            hubo_cambios = True
            mensaje_final += "Soy LubriBot 🤖\n\n🚨 *¡NUEVO TURNO PARA HOY!* 🚨\n\n"
            
            # Ordenamos los nuevos por hora
            turnos_nuevos_lista = [turnos_actuales_dict[i] for i in ids_nuevos]
            turnos_nuevos_lista.sort(key=lambda x: x['hora'])
            
            for t in turnos_nuevos_lista:
                mensaje_final += f"⏰ {t['hora']} hs\n"
                mensaje_final += f"👤 {t['cliente']}\n"
                mensaje_final += f"🚗 {t['vehiculo']}\n"
                mensaje_final += f"🛠️ {t['box']} - {t['tarea']}\n"
                mensaje_final += "〰️〰️〰️〰️〰️〰️\n"
            mensaje_final += "\n" # Espacio por si también hay cancelados en el mismo chequeo

        # 2. Procesar Turnos Cancelados
        if ids_cancelados:
            hubo_cambios = True
            mensaje_final += "Soy LubriBot 🤖\n\n❌ *¡TURNO CANCELADO!* ❌\n\n"
            
            # Ordenamos los cancelados por hora (sacamos los datos de la memoria)
            turnos_cancelados_lista = [turnos_en_memoria[i] for i in ids_cancelados]
            turnos_cancelados_lista.sort(key=lambda x: x['hora'])
            
            for t in turnos_cancelados_lista:
                mensaje_final += f"⏰ {t['hora']} hs\n"
                mensaje_final += f"👤 {t['cliente']}\n"
                mensaje_final += f"🚗 {t['vehiculo']}\n"
                mensaje_final += f"🛠️ {t['box']} - {t['tarea']}\n"
                mensaje_final += "〰️〰️〰️〰️〰️〰️\n"

        # --- ENVÍO Y ACTUALIZACIÓN ---
        if hubo_cambios:
            # 👇 NUEVA LÓGICA: Resumen total al final del mensaje
            total_hoy = len(ids_actuales)
            mensaje_final += f"\n📊 *Total de turnos para hoy:* {total_hoy}"
            
            print(f"\nCambios detectados. Total hoy: {total_hoy}. Enviando WhatsApp...")
            enviar_mensaje_wsp(mensaje_final.strip())
            guardar_memoria(turnos_actuales_dict)
        else:
            print("-> Sin novedades.")

if __name__ == "__main__":
    print("🤖 Iniciando LubriBot Monitor...")
    while True:
        try:
            monitorear_turnos_nuevos()
        except Exception as e:
            print(f"❌ Error en el ciclo de monitoreo: {e}")
        
        print(f"⏳ Esperando {MINUTOS_ESPERA} minutos para la próxima revisión...\n")
        time.sleep(MINUTOS_ESPERA * 60)