
# 🤖 LubriBot - Automatización de Calendario

Sistema integral de monitoreo, reporte y recordatorio automático de turnos para el CRM de Lubricentro VIP.

Incluye tres módulos principales:

- **Monitor Diurno (`monitor.py`)**: Detecta y notifica en tiempo real nuevos turnos y cancelaciones del día actual en el grupo de WhatsApp.
- **Reporte Nocturno (`nocturno.py`)**: Envía cada noche un resumen con la agenda completa del día siguiente al grupo de WhatsApp.
- **Recordatorios Automáticos (`recordatorios.py`)**: Envía mensajes individuales de recordatorio por WhatsApp a cada cliente con turno para el día siguiente (salta fines de semana automáticamente).

## 📋 Requisitos Previos

1. Instalar **Python 3.10** o superior
    - ⚠️ **IMPORTANTE:** Durante la instalación, marcar la casilla "Add Python to PATH"
2. Descargar o clonar este repositorio

## 🚀 Instalación y Configuración

### 1. Instalar dependencias

Abrir terminal (CMD o PowerShell) en la carpeta del proyecto:

```bash
pip install -r requirements.txt
```

### 2. Instalar navegador Playwright

```bash
python -m playwright install chromium
```

### 3. Primer inicio - Escaneo de QR

Ejecutar el monitor por primera vez para vincular WhatsApp:

```bash
python monitor.py
```

**Nota:** Se abrirá una ventana para escanear el código QR. La sesión se guardará en `/sesion_whatsapp_nativa/`.


## ⚙️ Uso Diario

### 1. Monitor Diurno (Turnos nuevos/cancelados)

Detecta automáticamente nuevos turnos y cancelaciones para el día actual y los notifica en el grupo de WhatsApp configurado.

Ejecutar manualmente o dejar corriendo:

```bash
python monitor.py
```

Revisa cambios cada 5 minutos durante la jornada.

**Tip:** Usar `pythonw monitor.py` para ejecutar sin ventana de consola. Para detener: cerrar proceso desde Administrador de Tareas.

---

### 2. Reporte Nocturno (Agenda del día siguiente)

Genera y envía un resumen con todos los turnos agendados para el día siguiente al grupo de WhatsApp. Ideal para automatizar con el Programador de Tareas de Windows (ejemplo: 20:30 hs):

```bash
python nocturno.py
```

---

### 3. Recordatorios Automáticos a Clientes

Envía mensajes individuales de WhatsApp a cada cliente con turno para el día siguiente, usando el número registrado en el CRM. Salta fines de semana automáticamente.

Ejecutar manualmente o automatizar (recomendado: después del reporte nocturno):

```bash
python recordatorios.py
```

---

### Detalles adicionales

- El envío de mensajes al grupo se realiza mediante el archivo `scraper.py` (no requiere intervención manual tras el primer escaneo de QR).
- El sistema almacena el estado de turnos y recordatorios enviados para evitar duplicados.
- La sesión de WhatsApp Web se guarda en `/sesion_whatsapp_nativa/`.


## 🛠️ Archivos Ignorados

Configurar `.gitignore` para excluir:
- `/sesion_whatsapp_nativa/` (sesión WhatsApp)
- `/descargas/` (descargas locales)
- `turnos_hoy.json` (estado diario)
- `registro_enviados.json` (registro de recordatorios enviados)
- `mensaje_temp.txt` (archivo temporal de mensajes)