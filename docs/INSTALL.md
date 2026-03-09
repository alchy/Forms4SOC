# Forms4SOC – Instalace a spuštění

Forms4SOC je webová aplikace pro správu SOC incidentů. Analytici vyplňují strukturované formuláře incidentů (UIB) přímo v prohlížeči; šablony workbooků definují, jaké sekce a pole každý typ incidentu obsahuje.

**Závislosti:** Python 3.11 nebo novější, Git.

---

## Jak to funguje?

```
data/workbooks/*.yaml   – YAML šablony workbooků (commitovány v gitu)
data/events/*.json      – JSON soubory incidentů (mimo git)
data/forms4soc.db       – SQLite databáze (users + settings)

       ┌─────────────────┐
       │   start.py      │  spustí uvicorn na portu 8080
       └────────┬────────┘
                │
       ┌────────▼────────┐
       │   FastAPI app   │  REST API + Jinja2 web routes
       └────────┬────────┘
                │
       ┌────────▼────────┐
       │   Prohlížeč     │  Bootstrap 5, forms4soc.js renderer
       └─────────────────┘
```

Všechna data jsou lokální – žádný cloud, žádná externí databáze. Záloha = záloha adresáře `data/`.

---

## Rychlá instalace

### Linux / macOS

```bash
# 1. Klonování repozitáře
git clone https://github.com/alchy/Forms4SOC.git
cd Forms4SOC

# 2. Virtuální prostředí a závislosti
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Konfigurace
cp .env.example .env
# Uprav .env – zejména JWT_SECRET_KEY a ADMIN_PASSWORD

# 4. Stažení vendor knihoven (Bootstrap, DataTables, jQuery, Ace Editor)
python scripts/download_vendors.py

# 5. Spuštění
python start.py
```

Aplikace bude dostupná na **http://localhost:8080**.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\download_vendors.py
python start.py
```

---

## Konfigurace (`.env`)

Soubor `.env` je vytvořen z `.env.example`. Povinné klíče:

```ini
# JWT tajný klíč – VŽDY změňte před nasazením!
# Generace: openssl rand -hex 32
JWT_SECRET_KEY=nahodny-dlouhy-retezec-min-32-znaku

# Přihlašovací údaje prvního admin účtu (použijí se jen při prvním spuštění)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
```

Volitelné klíče:

```ini
# Doba platnosti JWT tokenu v minutách (výchozí: 480 = 8 hodin)
# JWT_EXPIRE_MINUTES=480

# Cesta k SQLite databázi (výchozí: data/forms4soc.db)
# DATABASE_PATH=data/forms4soc.db

# Výchozí adresáře – lze změnit také v GUI → Nastavení
# DEFAULT_INCIDENTS_DIR=data/events
# DEFAULT_TEMPLATES_DIR=data/workbooks

# Branding aplikace – název, verze a podtitulek
# Hodnoty se při prvním spuštění uloží do SQLite; lze pak upravit v GUI → Nastavení
# APP_NAME=Forms4SOC
# APP_VERSION=0.2.0
# APP_SUBTITLE=SOC Incident Management Portal
```

> Po prvním spuštění se admin účet uloží do databáze. Hodnoty `ADMIN_USERNAME` a `ADMIN_PASSWORD` se použijí znovu jen pokud databáze neexistuje. Podrobnosti o seedování a resetu hesla viz [AUTH.md](AUTH.md).

---

## Startovací skript

`start.py` automaticky najde uvicorn ve `.venv` (Linux i Windows) a spustí server.

```bash
# Lokální přístup (výchozí)
python start.py

# Přístup ze sítě
python start.py --host 0.0.0.0 --port 8080

# Vývojový režim s automatickým reloadem
python start.py --reload
```

---

## Výchozí přihlášení

```
URL:      http://localhost:8080
Uživatel: admin
Heslo:    admin   (nebo dle .env → ADMIN_PASSWORD)
```

> Heslo doporučujeme změnit ihned po prvním přihlášení v sekci **Uživatelé** (admin menu).

---

## Adresářová struktura po instalaci

```
Forms4SOC/
├── app/                  – zdrojový kód aplikace
├── data/
│   ├── events/           – JSON soubory UIB (vytvořeno automaticky)
│   ├── workbooks/        – YAML šablony workbooků
│   │   ├── phishing_v2.yaml
│   │   ├── phishing_v3.yaml
│   │   ├── ddos_vpn_v1.yaml
│   │   └── vanilla_v1.yaml
│   └── forms4soc.db      – SQLite databáze (vytvořena automaticky)
├── docs/                 – tato dokumentace
├── scripts/
│   └── download_vendors.py  – stažení JS/CSS knihoven
├── .env                  – konfigurace (vytvořit dle .env.example)
├── requirements.txt
└── start.py              – startovací skript
```

---

## Bezpečnostní opatření

Aplikace obsahuje následující vrstvy aktivní ve výchozím nastavení:

| Opatření | Popis |
|---|---|
| JWT httpOnly cookie | Auth token uložen v httpOnly cookie `forms4soc_token` – nedostupná z JavaScriptu, `samesite=lax` |
| SecurityMiddleware | Každý POST/PUT/PATCH na `/api/v1/*` musí mít `Content-Type: application/json` – blokuje CSRF přes HTML formuláře (HTTP 415) |
| Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` |
| `X-Requested-With` | Všechna AJAX volání přes `apiFetch` odesílají `X-Requested-With: XMLHttpRequest` |
| Role-based access | Admin endpointy (users, settings, správa šablon) vyžadují roli `admin` |

**Doporučení pro produkční nasazení:**
- Nastavte silný `JWT_SECRET_KEY` (min. 32 znaků)
- Provozujte za HTTPS reverse proxy (nginx) – viz sekce níže
- Změňte výchozí heslo admina

---

## Aktualizace

```bash
cd /opt/forms4soc/app
sudo -u forms4soc git pull
sudo -u forms4soc .venv/bin/pip install -r requirements.txt
sudo systemctl restart forms4soc
```

### Přepnutí na jinou větev

```bash
cd /opt/forms4soc/app
sudo -u forms4soc git fetch
sudo -u forms4soc git checkout <nazev-vetve>
sudo -u forms4soc .venv/bin/pip install -r requirements.txt
sudo -u forms4soc .venv/bin/python scripts/download_vendors.py
sudo systemctl restart forms4soc
```

---

## Produkční nasazení na Linuxu (Rocky Linux 9 / RHEL)

Ověřeno na **Rocky Linux 9.2**. Postup je stejný pro RHEL 9, AlmaLinux 9 a kompatibilní distribuce. Na Debian/Ubuntu nahraď `dnf` za `apt` a `python3.11` může být dostupný přímo bez přidání repozitáře.

### 1. Systémové závislosti

Rocky Linux 9 dodává Python 3.9 jako výchozí. Python 3.11 je dostupný v AppStream repozitáři:

```bash
dnf install -y git python3.11 python3.11-pip
python3.11 --version   # ověření: Python 3.11.x
```

### 2. Uživatel a adresář

Aplikace běží pod vlastním uživatelem `forms4soc` s omezenými právy:

```bash
useradd -m -s /bin/bash -d /opt/forms4soc forms4soc
```

### 3. Klonování repozitáře

```bash
sudo -u forms4soc git clone https://github.com/alchy/Forms4SOC.git /opt/forms4soc/app
```

### 4. Virtuální prostředí a závislosti

```bash
sudo -u forms4soc python3.11 -m venv /opt/forms4soc/app/.venv
sudo -u forms4soc bash -c "cd /opt/forms4soc/app && .venv/bin/pip install -r requirements.txt"
```

### 5. Konfigurace

```bash
sudo -u forms4soc cp /opt/forms4soc/app/.env.example /opt/forms4soc/app/.env

# Generovat silný JWT klíč
openssl rand -hex 32

# Upravit .env
nano /opt/forms4soc/app/.env
```

Nastav minimálně `JWT_SECRET_KEY` na vygenerovaný klíč a změň `ADMIN_PASSWORD`.

### 6. Stažení vendor knihoven

```bash
sudo -u forms4soc bash -c "cd /opt/forms4soc/app && .venv/bin/python scripts/download_vendors.py"
```

Stáhne Bootstrap, Bootstrap Icons, jQuery, DataTables a Ace Editor do `app/static/vendor/`.

### 7. systemd service

Vytvořte `/etc/systemd/system/forms4soc.service`:

```ini
[Unit]
Description=Forms4SOC - SOC Incident Management
After=network.target

[Service]
Type=simple
User=forms4soc
Group=forms4soc
WorkingDirectory=/opt/forms4soc/app
ExecStart=/opt/forms4soc/app/.venv/bin/python start.py
Restart=on-failure
RestartSec=5

# Omezení práv
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectHome=yes
ReadWritePaths=/opt/forms4soc/app/data

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable forms4soc
systemctl start forms4soc
systemctl status forms4soc

# Logy
journalctl -u forms4soc -f
```

### 8. Nginx jako reverse proxy

Instalace:

```bash
dnf install -y nginx
```

#### Varianta A – Self-signed certifikát (testovací prostředí)

```bash
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/forms4soc.key \
  -out /etc/nginx/ssl/forms4soc.crt \
  -subj "/C=CZ/ST=Czech Republic/L=Prague/O=SOC/CN=forms4soc"
chmod 600 /etc/nginx/ssl/forms4soc.key
```

#### Varianta B – Let's Encrypt (produkce s vlastní doménou)

```bash
dnf install -y certbot python3-certbot-nginx
certbot --nginx -d forms4soc.vas-soc.cz
```

#### Konfigurace nginx

Odstraňte výchozí server block z `/etc/nginx/nginx.conf` (sekce `server { listen 80; ... }` uvnitř bloku `http`) a vytvořte `/etc/nginx/conf.d/forms4soc.conf`:

```nginx
# Přesměrování HTTP → HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS reverse proxy pro Forms4SOC
server {
    listen 443 ssl;
    server_name _;

    # Self-signed certifikát (pro produkci nahraď cestami Let's Encrypt)
    ssl_certificate     /etc/nginx/ssl/forms4soc.crt;
    ssl_certificate_key /etc/nginx/ssl/forms4soc.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

```bash
nginx -t
systemctl enable nginx
systemctl start nginx
```

### 9. SELinux (Rocky Linux / RHEL)

Na systémech s aktivním SELinux (výchozí stav na RHEL/Rocky) nginx nesmí bez povolení navazovat síťová spojení. Bez tohoto nastavení nginx vrací **502 Bad Gateway**:

```bash
setsebool -P httpd_can_network_connect 1
```

Ověření:

```bash
curl -sk https://127.0.0.1/ -o /dev/null -w "%{http_code}"
# Očekávaný výsledek: 302 (přesměrování na login)
```

### 10. První přihlášení a změna hesla

Přihlas se na `https://<IP-serveru>` výchozími přihlašovacími údaji:

```
Uživatel: admin
Heslo:    admin   (nebo dle ADMIN_PASSWORD v .env)
```

Po přihlášení okamžitě změň heslo: **menu vpravo nahoře → Uživatelé → upravit účet admin**.

> Výchozí heslo `admin` je funkční pouze do první změny. Po změně se hodnota `ADMIN_PASSWORD` v `.env` již nepoužívá – heslo je uloženo jako bcrypt hash v databázi.

### 11. Zálohy

Vytvoř zálohovací skript `/opt/forms4soc/backup.sh`:

```bash
#!/bin/bash
# Forms4SOC – zálohovací skript
set -euo pipefail

BACKUP_DIR="/opt/forms4soc/backups"
APP_DIR="/opt/forms4soc/app"
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE="${BACKUP_DIR}/forms4soc_${DATE}.tar.gz"
KEEP_DAYS=30

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Spouštím zálohu Forms4SOC..."

tar -czf "${ARCHIVE}" \
    --ignore-failed-read \
    "${APP_DIR}/data" \
    "${APP_DIR}/.env" \
    /etc/nginx/conf.d/forms4soc.conf \
    /etc/nginx/ssl/forms4soc.crt \
    /etc/nginx/ssl/forms4soc.key \
    /etc/systemd/system/forms4soc.service

SIZE=$(du -sh "${ARCHIVE}" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Záloha vytvořena: ${ARCHIVE} (${SIZE})"

# Rotace – smaž zálohy starší než KEEP_DAYS dní
DELETED=$(find "${BACKUP_DIR}" -name "forms4soc_*.tar.gz" -mtime +${KEEP_DAYS} -print -delete | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Smazáno ${DELETED} starých záloh (>${KEEP_DAYS} dní)"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hotovo."
```

```bash
# Vytvořit adresář pro zálohy a nastavit práva
mkdir -p /opt/forms4soc/backups
chmod +x /opt/forms4soc/backup.sh

# Provést první zálohu
/opt/forms4soc/backup.sh

# Nastavit cron – denní záloha ve 2:00, log do souboru
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/forms4soc/backup.sh >> /opt/forms4soc/backups/backup.log 2>&1") | crontab -
```

Záloha obsahuje: data aplikace (`data/`), konfiguraci (`.env`), nginx konfiguraci a SSL certifikát, systemd service soubor. Zálohy starší 30 dní se automaticky mažou. Log zálohování: `/opt/forms4soc/backups/backup.log`.

---

## Checklist po dokončení instalace

Po provedení všech kroků ověř:

- [ ] Aplikace běží: `systemctl is-active forms4soc`
- [ ] Nginx běží: `systemctl is-active nginx`
- [ ] HTTPS odpovídá: `curl -sk https://127.0.0.1/ -o /dev/null -w "%{http_code}"` → `302`
- [ ] SELinux povolen: `setsebool -P httpd_can_network_connect 1`
- [ ] Silný JWT klíč nastaven v `.env`
- [ ] Admin heslo změněno v GUI aplikace
- [ ] Vendor knihovny staženy: `ls app/static/vendor/`
- [ ] První záloha provedena: `ls /opt/forms4soc/backups/`
- [ ] Cron nastaven: `crontab -l`
