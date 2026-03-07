# Forms4SOC – Instalace a spuštění

Forms4SOC je webová aplikace pro správu SOC incidentů. Analytici vyplňují strukturované formuláře incidentů (UIB) přímo v prohlížeči; šablony workbooků definují, jaké sekce a pole každý typ incidentu obsahuje.

**Závislosti:** Python 3.11 nebo novější, Git.

---

## Jak to funguje?

```
data/workbooks/*.json   – JSON šablony workbooků (commitovány v gitu)
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
```

> Po prvním spuštění se admin účet uloží do databáze. Hodnoty `ADMIN_USERNAME` a `ADMIN_PASSWORD` se použijí znovu jen pokud databáze neexistuje.

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
│   ├── workbooks/        – JSON šablony workbooků
│   │   ├── phishing_v2.json
│   │   ├── ddos_vpn_v1.json
│   │   └── vanilla_v1.json
│   ├── tisk/             – PDF exporty (vytvořeno automaticky)
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
git pull
source .venv/bin/activate
pip install -r requirements.txt
python start.py
```

---

## Produkční nasazení na Linuxu

### 1. Příprava

```bash
# Systémový uživatel bez login shellu
sudo useradd -r -s /sbin/nologin -d /opt/forms4soc forms4soc

# Klonovat do /opt
sudo git clone https://github.com/alchy/Forms4SOC.git /opt/forms4soc
sudo chown -R forms4soc:forms4soc /opt/forms4soc
cd /opt/forms4soc

# Závislosti
sudo -u forms4soc python3 -m venv .venv
sudo -u forms4soc .venv/bin/pip install -r requirements.txt

# Konfigurace
sudo -u forms4soc cp .env.example .env
sudo nano .env   # nastavit JWT_SECRET_KEY a ADMIN_PASSWORD
```

### 2. systemd service

Vytvořte `/etc/systemd/system/forms4soc.service`:

```ini
[Unit]
Description=Forms4SOC – SOC Incident Forms
After=network.target

[Service]
Type=simple
User=forms4soc
WorkingDirectory=/opt/forms4soc
ExecStart=/opt/forms4soc/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --log-level info
Restart=on-failure
RestartSec=5
EnvironmentFile=/opt/forms4soc/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable forms4soc
sudo systemctl start forms4soc
sudo systemctl status forms4soc

# Logy
sudo journalctl -u forms4soc -f
```

### 3. Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name forms4soc.vas-soc.cz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name forms4soc.vas-soc.cz;

    ssl_certificate     /etc/letsencrypt/live/forms4soc.vas-soc.cz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/forms4soc.vas-soc.cz/privkey.pem;

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
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Záloha dat

Veškerá data aplikace jsou v adresáři `data/`:

```bash
# Jednorázová záloha
tar -czf forms4soc-backup-$(date +%Y%m%d).tar.gz /opt/forms4soc/data/

# Cron – denní záloha
0 2 * * * tar -czf /backup/forms4soc-$(date +\%Y\%m\%d).tar.gz /opt/forms4soc/data/
```
