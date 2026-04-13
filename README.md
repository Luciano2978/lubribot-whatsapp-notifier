# 🤖 LubriBot - Automatización de Calendario

Sistema de monitoreo y notificación de turnos para el CRM de Lubricentro VIP.

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

### Monitor Diurno (Turnos nuevos/cancelados)

```bash
python monitor.py
```

Revisa cambios cada 5 minutos durante la jornada.

**Tip:** Usar `pythonw monitor.py` para ejecutar sin ventana de consola. Para detener: cerrar proceso desde Administrador de Tareas.

### Reporte Nocturno (Agenda del día siguiente)

Automatizar `nocturno.py` en el Programador de Tareas de Windows (ej. 20:30 hs).

## 🛠️ Archivos Ignorados

Configurar `.gitignore` para excluir:
- `/sesion_whatsapp_nativa/` (sesión WhatsApp)
- `/descargas/` (descargas locales)
- `turnos_hoy.json` (estado diario)