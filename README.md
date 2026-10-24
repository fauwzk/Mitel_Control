# Mitel_Control

Un utilitaire vibecodé pour gérer les téléphones Mitel SIP sans écrire a la main

## Hébergement Docker (accès navigateur)

L'application (DearPyGui) tourne dans un écran virtuel du conteneur et est exposée via noVNC.

```bash
cp .env.example .env   # puis définir VNC_PASSWORD
docker compose up -d --build
```

Ouvrir `http://<serveur>:6080/vnc.html?autoconnect=1&resize=scale`.

- Les données (inventaire, modèles JSON, layout) sont persistées dans le volume `mitel-data` (`/data`).
- Le serveur doit pouvoir joindre les téléphones et le serveur SFTP/TFTP.
- « Auto-Fetch MAC » (ARP) nécessite `network_mode: host` (voir `docker-compose.yml`).
- Pour une exposition sur Internet, placer un reverse proxy HTTPS (Caddy, Traefik, nginx) devant le port 6080 : le flux noVNC n'est pas chiffré.
