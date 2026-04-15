# telegram_bot.py
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.sync_api import sync_playwright

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def scrape_turnos_hoy():
    fecha_hoy_crm = datetime.now().strftime('%d-%m-%Y')
    turnos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://approcrm.com/")
        page.fill("#txtusername", os.getenv("CRM_USER"))
        page.fill("#txtpassword", os.getenv("CRM_PASS"))
        page.click("#btnLoginHtml")
        page.wait_for_load_state("networkidle")

        page.goto("https://approcrm.com/wfCalendar.aspx")
        page.wait_for_load_state("networkidle")

        eventos = page.evaluate("() => { return typeof events !== 'undefined' ? events : []; }")
        browser.close()

    for turno in eventos:
        turno_id = str(turno.get('id', ''))
        fecha_turno = turno.get('clieAppointmentDate')

        if turno_id and fecha_turno == fecha_hoy_crm:
            desc_raw = turno.get('description', '')
            lineas = [l.strip() for l in desc_raw.split('<br/>') if l.strip()]

            vehiculo = lineas[1] if len(lineas) > 1 else "Vehículo"
            tarea = lineas[-1] if len(lineas) > 0 else ""

            if "NADA" in vehiculo.upper():
                vehiculo = re.sub(r'-?\s*NADA\w*', ' (Sin info de patente)', vehiculo, flags=re.IGNORECASE)

            turnos.append({
                "hora": turno.get('clieAppointmentTime', ''),
                "cliente": turno.get('clieName', 'N/A'),
                "vehiculo": vehiculo,
                "box": turno.get('titleModal', 'Box N/A'),
                "tarea": tarea
            })

    turnos.sort(key=lambda x: x['hora'])
    return turnos


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🤖 *LubriBot activo\\!*\n\n"
        f"Tu Chat ID es: `{chat_id}`\n\n"
        f"Comandos disponibles:\n"
        f"/turnos \\- Ver todos los turnos de hoy\n"
        f"/estado \\- Resumen rápido del día",
        parse_mode="MarkdownV2"
    )


async def cmd_turnos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Consultando el CRM, un momento...")
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            turnos = await loop.run_in_executor(pool, scrape_turnos_hoy)

        fecha_hoy = datetime.now().strftime('%d/%m/%Y')

        if not turnos:
            await update.message.reply_text(
                f"📅 No hay turnos agendados para hoy ({fecha_hoy})."
            )
            return

        mensaje = f"🤖 *LubriBot*\n\n*Turnos de hoy {fecha_hoy}:*\n\n"

        boxes = {}
        for t in turnos:
            boxes.setdefault(t['box'], []).append(t)

        for box, lista in boxes.items():
            mensaje += f"🛠️ *{box}*\n"
            for t in lista:
                mensaje += f"⏰ {t['hora']} hs — 👤 {t['cliente']}\n"
                mensaje += f"   🚗 {t['vehiculo']}\n"
                mensaje += f"   📋 {t['tarea']}\n"
            mensaje += "\n"

        mensaje += f"📊 *Total: {len(turnos)} turno(s)*"

        await update.message.reply_text(mensaje, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error al consultar el CRM: {e}")


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Chequeando estado...")
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            turnos = await loop.run_in_executor(pool, scrape_turnos_hoy)

        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        hora_consulta = datetime.now().strftime('%H:%M')

        if not turnos:
            texto = f"📅 *{fecha_hoy}* — Sin turnos agendados.\n🕐 Consultado a las {hora_consulta}"
        else:
            primero = turnos[0]
            ultimo = turnos[-1]
            texto = (
                f"📊 *Estado al {hora_consulta}*\n\n"
                f"📅 Fecha: {fecha_hoy}\n"
                f"🔢 Total turnos: *{len(turnos)}*\n"
                f"🌅 Primero: {primero['hora']} hs — {primero['cliente']}\n"
                f"🌆 Último: {ultimo['hora']} hs — {ultimo['cliente']}"
            )

        await update.message.reply_text(texto, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🤖 LubriBot Telegram iniciando...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("turnos", cmd_turnos))
    app.add_handler(CommandHandler("estado", cmd_estado))

    print("✅ Bot activo. Esperando comandos...")
    app.run_polling()