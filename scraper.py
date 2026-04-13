# scraper.py
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import os

# Cargamos las variables del archivo .env
load_dotenv()

# Ahora las traemos con os.getenv
NOMBRE_DEL_GRUPO = os.getenv("WSP_GROUP_NAME")
DIRECTORIO_SESION = "./sesion_whatsapp_nativa"
def enviar_mensaje_wsp(mensaje):
    """Abre WhatsApp Web usando la sesión guardada y envía un mensaje al grupo."""
    os.makedirs(DIRECTORIO_SESION, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=DIRECTORIO_SESION,
            headless=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = browser.pages[0] 

        print("Iniciando WhatsApp Web...", flush=True)
        page.goto("https://web.whatsapp.com/")
        try:
            print("⏳ Esperando a que cargue WhatsApp...", flush=True)
            page.wait_for_selector('#pane-side', timeout=60000)
            print("✅ Sesión activa detectada.", flush=True)
            
            # Buscador por rol
            caja_busqueda = page.locator('#side').get_by_role("textbox")
            print(f"Buscando el grupo: '{NOMBRE_DEL_GRUPO}'...", flush=True)
            caja_busqueda.click()
            caja_busqueda.fill(NOMBRE_DEL_GRUPO)
            page.wait_for_timeout(2000) 
            
            # Clic en el grupo
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