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

## Redémarrage des postes

Le bouton « Reboot » essaie successivement :

1. la page *Reset* de l'interface web du téléphone (`/reset.html`, identifiant `admin` + « Phone web password ») ;
2. la commande XML `Command: Reset` : le téléphone ne l'exécute que si l'IP du serveur figure dans `xml application post list` (onglet Global → *XML & action URIs*).

Chaque méthode est tentée en HTTP puis en HTTPS, et le redémarrage n'est annoncé que si le poste passe réellement hors ligne. En cas d'échec, le message indique ce que chaque tentative a renvoyé.
