# recordatorios.py
from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import re
import json
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

def ejecutar_recordatorios():
    hoy = datetime.now()
    if hoy.weekday() == 5: 
        dias_a_sumar = 2
    else:
        dias_a_sumar = 1

    fecha_busqueda = (hoy + timedelta(days=dias_a_sumar)).strftime('%Y-%m-%d')
    fecha_obj = datetime.strptime(fecha_busqueda, '%Y-%m-%d')
    fecha_linda = fecha_obj.strftime('%d/%m/%Y')

    with sync_playwright() as p:
        
        # ==========================================
        # FASE 1: EXTRACCIÓN DE DATOS DEL CRM
        # ==========================================
        browser_crm = p.chromium.launch(headless=True) 
        page_crm = browser_crm.new_page()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingresando a Appro CRM...", flush=True)
        try:
            page_crm.goto("https://approcrm.com/")
            page_crm.fill("#txtusername", os.getenv("CRM_USER")) 
            page_crm.fill("#txtpassword", os.getenv("CRM_PASS"))
            page_crm.click("#btnLoginHtml") 
            page_crm.wait_for_load_state("networkidle")

            page_crm.goto("https://approcrm.com/wfCalendar.aspx")
            page_crm.wait_for_load_state("networkidle")
            page_crm.wait_for_timeout(3000)

            html = page_crm.content()
            match = re.search(r'var\s+events\s*=\s*(\[[\s\S]*?\]);', html)
            
            df_fecha = pd.DataFrame()
            if match:
                js_array = match.group(1)
                eventos = page_crm.evaluate(f"() => {js_array}")
                df = pd.DataFrame(eventos)
                
                df['start'] = df['start'].astype(str)
                df_fecha = df[df['start'].str.startswith(fecha_busqueda, na=False)].copy()
                print(f"✅ Datos extraídos. Turnos para el {fecha_linda}: {len(df_fecha)}", flush=True)
            
        except Exception as e:
            print(f"❌ Error al conectar con el CRM: {e}")
            browser_crm.close()
            return

        browser_crm.close() 

        if df_fecha.empty:
            print(f"📅 No hay turnos agendados para el {fecha_linda}. Fin del proceso.")
            return

        # ==========================================
        # FASE 2: ENVÍO MASIVO DE WHATSAPP
        # ==========================================
        archivo_memoria = "registro_enviados.json"
        memoria_enviados = {}
        
        if os.path.exists(archivo_memoria):
            with open(archivo_memoria, "r", encoding="utf-8") as f:
                try:
                    memoria_enviados = json.load(f)
                except json.JSONDecodeError:
                    pass

        directorio_sesion = "./sesion_whatsapp_nativa"
        
        browser_wsp = p.chromium.launch_persistent_context(
            user_data_dir=directorio_sesion,
            headless=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page_wsp = browser_wsp.pages[0] 

        # 🛡️ ESCUDO 1: Aceptar automáticamente cualquier cartel de "Abandonar página"
        page_wsp.on("dialog", lambda dialog: dialog.accept())

        print("Iniciando WhatsApp Web para recordatorios...", flush=True)
        try:
            page_wsp.goto("https://web.whatsapp.com/")
            page_wsp.wait_for_selector('#pane-side', timeout=60000)
            print("✅ Sesión activa de WhatsApp detectada.", flush=True)
        except:
            print("❌ Error al cargar WhatsApp o tiempo de espera agotado.")
            browser_wsp.close()
            return

        turnos_exitosos = 0
        turnos_fallidos = 0

        for index, fila in df_fecha.iterrows():
            nombre_cliente = fila.get('clieName', 'Cliente')
            try:
                hora_real = fila.get('clieAppointmentTime', '')
                
                telefono_crudo = str(fila.get('cliePhone', ''))
                numero_limpio = re.sub(r'\D', '', telefono_crudo)
                
                if not numero_limpio:
                    print(f"⚠️ Sin teléfono para {nombre_cliente}. Saltando...", flush=True)
                    continue

                texto_descripcion = str(fila.get('description', '')).replace('<br/>', '\n')
                lineas_desc = [linea.strip() for linea in texto_descripcion.split('\n') if linea.strip()]
                
                vehiculo = lineas_desc[1] if len(lineas_desc) > 1 else "tu vehículo"
                servicio_limpio = lineas_desc[-1].strip().title() if len(lineas_desc) > 0 else "Servicio"

                titulo = str(fila.get('title', ''))
                match_patente = re.search(r'\((.*?)\)', titulo)
                patente = match_patente.group(1) if match_patente else vehiculo.split('-')[-1].strip()

                etiqueta_memoria = f"{fecha_busqueda}_{patente}"
                if etiqueta_memoria in memoria_enviados:
                    print(f"⏭️ {nombre_cliente} ({patente}) YA recibió el aviso. Saltando...", flush=True)
                    continue

                mensaje = f"🤖 *Recordatorio automatizado*\nHola *{nombre_cliente}* 👋\n\nTe recordamos tu turno para el *{fecha_linda}* a las *{hora_real} hs*.\n🚗 Vehículo: {vehiculo}\n🔧 Tarea: {servicio_limpio}\n\nAnte cualquier inconveniente, no dudes en escribirnos.\n\nEste mensaje solo es de recordatorio. ¡Te esperamos en Lubricentro VIP!"
                texto_codificado = urllib.parse.quote(mensaje)
                
                if not numero_limpio.startswith('54'):
                    numero_limpio = '549' + numero_limpio

                url_wsp = f"https://web.whatsapp.com/send?phone={numero_limpio}&text={texto_codificado}"
                
                print(f"-> Conectando con {nombre_cliente}...", flush=True)
                page_wsp.goto(url_wsp)
                
                # 🛡️ ESCUDO 2: Aumentamos el timeout a 45s porque cargar un chat nuevo es pesado
                caja_mensaje = page_wsp.locator('footer div[contenteditable="true"]').first
                caja_mensaje.wait_for(state="visible", timeout=45000)
                
                # Le damos un respiro para que WSP procese el texto de la URL
                page_wsp.wait_for_timeout(3000) 
                
                caja_mensaje.click() 
                page_wsp.wait_for_timeout(500)
                page_wsp.keyboard.press("Enter")
                page_wsp.wait_for_timeout(3000) 
                
                print(f"✅ Enviado a {nombre_cliente}.", flush=True)
                turnos_exitosos += 1
                
                # Guardamos enseguida en el JSON por si se corta en el siguiente
                memoria_enviados[etiqueta_memoria] = {
                    "cliente": nombre_cliente,
                    "hora_turno": hora_real,
                    "vehiculo_completo": vehiculo,
                    "fecha_envio": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                with open(archivo_memoria, "w", encoding="utf-8") as f:
                    json.dump(memoria_enviados, f, indent=4, ensure_ascii=False)
                
                time.sleep(12)

            except Exception as e:
                # 🛡️ ESCUDO 3: Si falla (timeout o número inválido), apretamos ESC para cerrar popups y seguimos
                print(f"⚠️ Falló el envío a {nombre_cliente}. Posible número inválido o carga lenta.", flush=True)
                page_wsp.keyboard.press("Escape")
                turnos_fallidos += 1
                continue # Pasa al siguiente cliente sin morir
                
        print(f"\n🎉 ¡Proceso finalizado! ({turnos_exitosos} enviados, {turnos_fallidos} fallidos).", flush=True)
        browser_wsp.close()

if __name__ == "__main__":
    ejecutar_recordatorios()