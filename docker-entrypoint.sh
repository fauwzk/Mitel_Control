#!/bin/bash
set -e

if [ -z "$VNC_PASSWORD" ]; then
    echo "ERREUR : la variable VNC_PASSWORD doit être définie (accès navigateur protégé)." >&2
    exit 1
fi

# Données persistantes (inventaire, modèles, layout) dans le volume /data
mkdir -p "$DATA_DIR"
for f in endpoints.json dpg.ini; do
    [ -f "$DATA_DIR/$f" ] || cp "/app/$f" "$DATA_DIR/$f"
done
cd "$DATA_DIR"

rm -f /tmp/.X99-lock
Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24" -nolisten tcp &

for _ in $(seq 1 50); do
    [ -e /tmp/.X11-unix/X99 ] && break
    sleep 0.1
done

x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vncpass >/dev/null
x11vnc -display "$DISPLAY" -rfbauth /tmp/vncpass -forever -shared -localhost -quiet -rfbport 5900 &
websockify --web /usr/share/novnc "$NOVNC_PORT" localhost:5900 &

# Viewport plein écran sans décoration : aucun gestionnaire de fenêtres dans le conteneur
export VIEWPORT_X=0 VIEWPORT_Y=0 VIEWPORT_WIDTH="$SCREEN_WIDTH" VIEWPORT_HEIGHT="$SCREEN_HEIGHT" VIEWPORT_DECORATED=0

# Si l'app se ferme, le conteneur s'arrête et Docker le relance (restart: unless-stopped)
python /app/main.py &
wait -n
