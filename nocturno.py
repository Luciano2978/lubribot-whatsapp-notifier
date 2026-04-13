# nocturno.py
from playwright.sync_api import sync_playwright
import pandas as pd
import os
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import subprocess

load_dotenv()
def extraer_datos_calendario():
    os.makedirs("./descargas", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Iniciando sesión en Appro CRM...", flush=True)
        page.goto("https://approcrm.com/")
        # Usamos las variables del .env
        page.fill("#txtusername", os.getenv("CRM_USER")) 
        page.fill("#txtpassword", os.getenv("CRM_PASS"))
        page.click("#btnLoginHtml")
        page.wait_for_load_state("networkidle")

        print("Descargando Excel del calendario...", flush=True)
        page.goto("https://approcrm.com/wfCalendar.aspx")
        page.wait_for_load_state("networkidle")

        with page.expect_download() as download_info:
            page.click(".fc-btnExcel-button") 
            
        download = download_info.value
        ruta_archivo = "./descargas/calendario_appro.xlsx"
        download.save_as(ruta_archivo)
        browser.close()

    try:
        df = pd.read_excel(ruta_archivo)
        print("✅ Excel descargado y leído correctamente.")
        return df
    except Exception as e:
        print(f"❌ Error al leer el Excel: {e}")
        return None

def preparar_resumen_grupo(df):
    hoy = datetime.now()
    # En Python, weekday() devuelve 5 para el Sábado.
    if hoy.weekday() == 5:
        dias_a_sumar = 2 # Saltamos al Lunes
    else:
        dias_a_sumar = 1 # Al día siguiente normalmente

    fecha_busqueda = (hoy + timedelta(days=dias_a_sumar)).strftime('%Y-%m-%d')
    fecha_obj = datetime.strptime(fecha_busqueda, '%Y-%m-%d')
    fecha_titulo_formateada = fecha_obj.strftime('%d/%m/%Y')

    df['Inicio'] = pd.to_datetime(df['Inicio'], errors='coerce')
    fecha_target = (datetime.now() + timedelta(days=dias_a_sumar)).date()

    df_fecha = df[df['Inicio'].dt.date == fecha_target].copy()
    
    if df_fecha.empty:
        print(f"📅 No hay turnos agendados para el {fecha_busqueda}.")
        mensaje = f"Soy LubriBot 🤖\n\n📅 Para el día {fecha_titulo_formateada} no hay turnos agendados por el momento."
        return mensaje
        
    df_fecha['Descripción'] = df_fecha['Descripción'].astype(str).str.replace('<br/>', '\n', regex=False)
    df_fecha['Hora_Real'] = df_fecha['Título'].astype(str).str[:5]
    df_fecha = df_fecha.sort_values(by=['Cliente', 'Hora_Real'])
    
    mensaje = f"Soy LubriBot 🤖\n\n*Agenda de Turnos* {fecha_titulo_formateada}:\n\n"
    
    for box, grupo in df_fecha.groupby('Cliente'):
        mensaje += f"🛠️ *{str(box).strip()}*\n"
        
        for _, fila in grupo.iterrows():
            hora_real = fila['Hora_Real']
            
            texto_descripcion = str(fila['Descripción'])
            lineas_desc = [linea.strip() for linea in texto_descripcion.split('\n') if linea.strip()]
            
            nombre = lineas_desc[0] if len(lineas_desc) > 0 else "Cliente"
            vehiculo = lineas_desc[1] if len(lineas_desc) > 1 else "Vehículo"
            
            # --- Lógica de Patente NADA replicada acá también ---
            if "NADA" in vehiculo.upper():
                vehiculo = re.sub(r'-?\s*NADA\w*', ' (Sin info de patente)', vehiculo, flags=re.IGNORECASE)
            
            fecha_y_hora = lineas_desc[2] if len(lineas_desc) > 2 else f"{fecha_busqueda} {hora_real}"
            
            if len(fecha_y_hora) >= 10 and fecha_y_hora[4] == '-' and fecha_y_hora[7] == '-':
                anio = fecha_y_hora[0:4]
                mes = fecha_y_hora[5:7]
                dia = fecha_y_hora[8:10]
                resto_hora = fecha_y_hora[10:] 
                fecha_y_hora = f"{dia}/{mes}/{anio}{resto_hora}"
            
            ultima_linea = lineas_desc[-1] if len(lineas_desc) > 0 else ""
            tarea_limpia = re.sub(r'\d{10}', '', ultima_linea).replace('-', '').strip().title()
            
            mensaje += f"⏰ {hora_real} hs\n"
            mensaje += f"👤 {nombre}\n"
            mensaje += f"🚗 {vehiculo}\n"
            mensaje += f"{fecha_y_hora}\n\n"
            mensaje += f"🔧 {tarea_limpia}\n"
            mensaje += "〰️〰️〰️〰️〰️〰️\n"
            
        mensaje += "\n" 

    return mensaje

if __name__ == "__main__":
    print("🤖 Iniciando LubriBot Nocturno...", flush=True)
    df_crudo = extraer_datos_calendario()
    
    if df_crudo is not None:
        mensaje_final = preparar_resumen_grupo(df_crudo)
        
        print("\n--- RESUMEN A ENVIAR ---")
        print(mensaje_final)
        print("------------------------\n")
        
        # Llamamos a la función compartida del scraper.py
        with open("mensaje_temp.txt", "w", encoding="utf-8") as f:
            f.write(mensaje_final.strip())
        subprocess.run(["python", "scraper.py"])
    else:
        print("❌ Operación cancelada. No hay datos para procesar.")