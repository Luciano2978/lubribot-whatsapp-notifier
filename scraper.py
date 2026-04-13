# scraper.py
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import threading # 👈 Importamos la librería de hilos (nativa de Python)

# Cargamos las variables del archivo .env
load_dotenv()

NOMBRE_DEL_GRUPO = os.getenv("WSP_GROUP_NAME")
DIRECTORIO_SESION = "./sesion_whatsapp_nativa"

def _enviar_wsp_hilo(mensaje):
    """Esta es la función interna que hace el trabajo sucio en un carril separado"""
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
def enviar_mensaje_wsp(mensaje):
    """
    Función principal. Lanza WhatsApp en un hilo (Thread) separado 
    para evitar el error de 'asyncio loop' al abrir navegadores seguidos.
    """
    hilo = threading.Thread(target=_enviar_wsp_hilo, args=(mensaje,))
    hilo.start()
    hilo.join()
    
    # 👇 NUEVA LÓGICA: Detección automática del primer inicio
    es_primera_vez = False
    if not os.path.exists(DIRECTORIO_SESION) or len(os.listdir(DIRECTORIO_SESION)) == 0:
        es_primera_vez = True
        print("⚠️ Primera ejecución detectada: Se mostrará el navegador para escanear el QR.", flush=True)
    
    os.makedirs(DIRECTORIO_SESION, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=DIRECTORIO_SESION,
            headless=not es_primera_vez, # 👈 Automático: False la primera vez, True el resto de los días
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