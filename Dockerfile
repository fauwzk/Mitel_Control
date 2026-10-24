FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    SCREEN_WIDTH=1680 \
    SCREEN_HEIGHT=720 \
    NOVNC_PORT=6080 \
    DATA_DIR=/data

# Xvfb (écran virtuel) + Mesa (OpenGL logiciel pour DearPyGui) + x11vnc/noVNC (accès navigateur)
# iputils-ping / net-tools : nécessaires à "Auto-Fetch MAC" (ping + arp)
RUN apt-get update && apt-get install -y --no-install-recommends \
        xvfb x11vnc novnc websockify \
        libgl1 libglx-mesa0 libgl1-mesa-dri libegl1 \
        libxrandr2 libxinerama1 libxcursor1 libxi6 libxkbcommon-x11-0 \
        iputils-ping net-tools \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py Museo-500.ttf dpg.ini endpoints.json docker-entrypoint.sh ./
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

VOLUME ["/data"]
EXPOSE 6080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
