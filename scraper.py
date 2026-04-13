# scraper.py
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

NOMBRE_DEL_GRUPO = os.getenv("WSP_GROUP_NAME")
DIRECTORIO_SESION = "./sesion_whatsapp_nativa"

def enviar_mensaje_wsp(mensaje):
    es_primera_vez = False
    if not os.path.exists(DIRECTORIO_SESION) or len(os.listdir(DIRECTORIO_SESION)) == 0:
        es_primera_vez = True
        print("⚠️ Primera ejecución detectada: Se mostrará el navegador para escanear el QR.", flush=True)
    
    os.makedirs(DIRECTORIO_SESION, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=DIRECTORIO_SESION,
            headless=not es_primera_vez, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = browser.pages[0] 

        print("Iniciando WhatsApp Web...", flush=True)
        page.goto("https://web.whatsapp.com/")
        try:
            print("⏳ Esperando a que cargue WhatsApp...", flush=True)
            if es_primera_vez:
                print("📱 POR FAVOR, ESCANEÁ EL CÓDIGO QR CON TU CELULAR AHORA.", flush=True)
                
            page.wait_for_selector('#pane-side', timeout=60000)
            print("✅ Sesión activa detectada.", flush=True)
            
            caja_busqueda = page.locator('#side').get_by_role("textbox")
            print(f"Buscando el grupo: '{NOMBRE_DEL_GRUPO}'...", flush=True)
            caja_busqueda.click()
            caja_busqueda.fill(NOMBRE_DEL_GRUPO)
            page.wait_for_timeout(2000) 
            
            page.locator(f'span[title="{NOMBRE_DEL_GRUPO}"]').first.click()
            page.wait_for_timeout(2000) 
            
            print("Pegando el mensaje...", flush=True)
            caja_mensaje = page.locator('#main').get_by_role("textbox").last
            caja_mensaje.click()
            
            page.keyboard.insert_text(mensaje)
            page.wait_for_timeout(1500)
            
            print("Enviando...", flush=True)
            caja_mensaje.click()
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000) 
            print("🎉 ¡Mensaje enviado al grupo con éxito!", flush=True)

        except Exception as e:
            print(f"❌ Error durante el envío: {e}")
            
        browser.close()

# 👇 ESTO ES LO NUEVO: Se ejecuta solo si lo llamamos desde afuera
if __name__ == "__main__":
    archivo_temp = "mensaje_temp.txt"
    if os.path.exists(archivo_temp):
        with open(archivo_temp, "r", encoding="utf-8") as f:
            texto_a_enviar = f.read()
        
        enviar_mensaje_wsp(texto_a_enviar)
        
        # Borramos el archivo temporal para dejar limpio
        os.remove(archivo_temp)
    else:
        print("❌ No se encontró el archivo de mensaje temporal.")