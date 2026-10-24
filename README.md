# Mitel_Control

Un utilitaire vibecodé pour gérer les téléphones Mitel SIP sans écrire a la main

Application web (Flask) : éditeur de fichiers `.cfg` par modèle, synchronisation SFTP, inventaire des postes, reboot à distance et conversion de fonds d'écran.

## Lancer en local

```bash
pip install -r requirements.txt
python app.py
```

Puis ouvrir http://127.0.0.1:8000. Sans `APP_PASSWORD`, aucune authentification n'est demandée.

## Hébergement Docker

```bash
cp .env.example .env   # définir APP_PASSWORD et SECRET_KEY
docker compose up -d --build
```

Ouvrir `http://<serveur>:8000` et se connecter avec `APP_PASSWORD`.

- Les données (inventaire `endpoints.json`, modèles `phone_models/`) sont persistées dans le volume `mitel-data` (`/data`).
- Le serveur doit pouvoir joindre les téléphones et le serveur SFTP/TFTP.
- « Auto-Fetch MAC » (ARP) nécessite `network_mode: host` (voir `docker-compose.yml`).
- Pour une exposition sur Internet, placer un reverse proxy HTTPS (Caddy, Traefik, nginx) devant le port 8000 et passer `SESSION_COOKIE_SECURE=1`.
- Les identifiants SFTP et le mot de passe web des téléphones ne sont jamais stockés côté serveur : ils sont envoyés à chaque action.
