# Panel de monitoreo del sistema operativo

Aplicación web desarrollada con asistencia de IA (Claude) que muestra en tiempo real el estado del servidor donde se ejecuta: CPU (total y por núcleo), memoria RAM y swap, disco, tráfico de red, uptime y los procesos que más consumen.

## Arquitectura

```
Navegador (HTML + JS + Chart.js)
        │  GET /api/stats cada 2 s
        ▼
Gunicorn + Flask (app.py)  ──►  psutil  ──►  /proc del sistema operativo
        │
   Contenedor Docker (python:3.12-slim)
        │
   Servidor / VM Linux
```

- **Backend:** Flask expone `/api/stats` (JSON), `/health` y `/`.
- **psutil** lee las métricas directamente del kernel (en Linux, desde `/proc`).
- **Frontend:** una página con tarjetas, barras de color según carga y gráficos en vivo.
- **Despliegue:** Docker + Gunicorn, reinicio automático con `restart: unless-stopped`.

## Conceptos de Sistemas Operativos que ilustra
Gestión de procesos (PID, estado, consumo), planificación de CPU (uso por núcleo y carga promedio), gestión de memoria (RAM y swap), sistema de archivos (uso de disco), E/S de red y tiempo de actividad del sistema.

## Ejecutar en local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py        # abrir http://localhost:5000
```

## Ejecutar con Docker
```bash
docker compose up -d --build     # abrir http://IP_DEL_SERVIDOR
```

## Despliegue en un servidor Linux (VPS / VM)
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
git clone <URL_DE_TU_REPOSITORIO> panel-so && cd panel-so
sudo docker compose up -d --build
```
Abrir el puerto 80 en el firewall del proveedor y entrar a `http://IP_PUBLICA`.

## Uso de la IA
Herramienta: Claude (Anthropic). Prompts usados (completa con los tuyos):
1. Pedí la idea y el plan de trabajo para la tarea.
2. Pedí el backend con Flask y psutil.
3. Pedí el frontend con gráficos en tiempo real.
4. Pedí el Dockerfile y las instrucciones de despliegue.

**Reflexión (edita con tus palabras):** la IA aceleró la escritura del código y la configuración de Docker; yo probé la aplicación, revisé que las métricas coincidieran con herramientas como `top`/`htop`, y la desplegué en el servidor.

## Capturas
(Agrega aquí capturas del panel funcionando en el servidor.)
