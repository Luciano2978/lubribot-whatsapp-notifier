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
    # --- LÓGICA DE FECHAS (Salto de fin de semana) ---
    hoy = datetime.now()
    if hoy.weekday() == 5: # 5 es Sábado
        dias_a_sumar = 2   # Saltamos al Lunes
    else:
        dias_a_sumar = 1   # Al día siguiente

    fecha_busqueda = (hoy + timedelta(days=dias_a_sumar)).strftime('%Y-%m-%d')
    fecha_obj = datetime.strptime(fecha_busqueda, '%Y-%m-%d')
    fecha_linda = fecha_obj.strftime('%d/%m/%Y')

    # 👇 UNA SOLA BURBUJA DE PLAYWRIGHT PARA EVITAR EL ERROR ASYNCIO 👇
    with sync_playwright() as p:
        
        # ==========================================
        # FASE 1: EXTRACCIÓN DE DATOS DEL CRM
        # ==========================================
        browser_crm = p.chromium.launch(headless=True) 
        page_crm = browser_crm.new_page()

        print("Ingresando a Appro CRM...", flush=True)
        page_crm.goto("https://approcrm.com/")
        page_crm.fill("#txtusername", os.getenv("CRM_USER")) 
        page_crm.fill("#txtpassword", os.getenv("CRM_PASS"))
        page_crm.click("#btnLoginHtml") 
        page_crm.wait_for_load_state("networkidle")

        print("Extrayendo turnos del calendario...", flush=True)
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
        
        browser_crm.close() # Cerramos el CRM, pero seguimos dentro del bloque 'p'

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
        
        # Usamos headless=True para que no aparezca el navegador en pantalla
        browser_wsp = p.chromium.launch_persistent_context(
            user_data_dir=directorio_sesion,
            headless=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page_wsp = browser_wsp.pages[0] 

        print("Iniciando WhatsApp Web para recordatorios...", flush=True)
        page_wsp.goto("https://web.whatsapp.com/")
        try:
            page_wsp.wait_for_selector('#pane-side', timeout=60000)
            print("✅ Sesión activa de WhatsApp detectada.", flush=True)
        except:
            print("❌ Error al cargar WhatsApp.")
            browser_wsp.close()
            return

        for index, fila in df_fecha.iterrows():
            try:
                hora_real = fila.get('clieAppointmentTime', '')
                nombre_cliente = fila.get('clieName', 'Cliente')
                
                telefono_crudo = str(fila.get('cliePhone', ''))
                numero_limpio = re.sub(r'\D', '', telefono_crudo)
                
                if not numero_limpio:
                    print(f"⚠️ Sin teléfono registrado para {nombre_cliente}. Saltando...", flush=True)
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
                    print(f"⏭️ {nombre_cliente} YA recibió el aviso para el {fecha_linda}. Saltando...", flush=True)
                    continue

                mensaje = f"🤖 *Recordatorio automatizado*\nHola *{nombre_cliente}* 👋\n\nTe recordamos tu turno para el *{fecha_linda}* a las *{hora_real} hs*.\n🚗 Vehículo: {vehiculo}\n🔧 Tarea: {servicio_limpio}\n\nAnte cualquier inconveniente, no dudes en escribirnos.\n\nEste mensaje solo es de recordatorio. ¡Te esperamos en Lubricentro VIP!"
                texto_codificado = urllib.parse.quote(mensaje)
                
                if not numero_limpio.startswith('54'):
                    numero_limpio = '549' + numero_limpio

                url_wsp = f"https://web.whatsapp.com/send?phone={numero_limpio}&text={texto_codificado}"
                
                print(f"Abriendo chat con {nombre_cliente}...", flush=True)
                page_wsp.goto(url_wsp)
                
                caja_mensaje = page_wsp.locator('footer div[contenteditable="true"]').first
                caja_mensaje.wait_for(state="visible", timeout=25000)
                page_wsp.wait_for_timeout(3000) 
                
                print(f"Enviando mensaje a {numero_limpio}...", flush=True)
                caja_mensaje.click() 
                page_wsp.wait_for_timeout(500)
                page_wsp.keyboard.press("Enter")
                page_wsp.wait_for_timeout(3000) 
                print(f"✅ Enviado a {nombre_cliente}.", flush=True)
                
                memoria_enviados[etiqueta_memoria] = {
                    "cliente": nombre_cliente,
                    "hora_turno": hora_real,
                    "vehiculo_completo": vehiculo,
                    "fecha_envio": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                with open(archivo_memoria, "w", encoding="utf-8") as f:
                    json.dump(memoria_enviados, f, indent=4, ensure_ascii=False)
                
                print("⏳ Pausa antibloqueo de 10 segundos...", flush=True)
                time.sleep(10)

            except Exception as e:
                print(f"❌ Error con el turno de {nombre_cliente}: {e}", flush=True)
                
        print("🎉 ¡Todos los envíos finalizados!", flush=True)
        browser_wsp.close()

if __name__ == "__main__":
    ejecutar_recordatorios()