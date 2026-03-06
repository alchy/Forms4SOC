# Forms4SOC – Instalace a spuštění

## Požadavky

- Python 3.11 nebo novější
- Git

---

## Rychlá instalace (Linux / macOS)

```bash
# 1. Klonování repozitáře
git clone https://github.com/alchy/Forms4SOC.git
cd Forms4SOC

# 2. Vytvoření virtuálního prostředí a instalace závislostí
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Konfigurace
cp .env.example .env
# Upravte .env – zejména JWT_SECRET_KEY a ADMIN_PASSWORD

# 4. Spuštění serveru (lokálně)
python start.py
```

Aplikace bude dostupná na **http://localhost:8080**

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python start.py
```

---

## Konfigurace (`.env`)

```ini
# JWT tajný klíč – VŽDY změňte před nasazením!
# Generace: openssl rand -hex 32
JWT_SECRET_KEY=nahodny-dlouhy-retezec-min-32-znaku

# Přihlašovací údaje prvního admin účtu (použijí se při prvním spuštění)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin

# Doba platnosti JWT tokenu v minutách (výchozí: 480 = 8 hodin)
# JWT_EXPIRE_MINUTES=480

# Cesta k SQLite databázi (výchozí: data/forms4soc.db)
# DATABASE_PATH=data/forms4soc.db

# Výchozí adresáře – lze změnit také v GUI → Nastavení
# DEFAULT_INCIDENTS_DIR=data/events
# DEFAULT_TEMPLATES_DIR=data/workbooks
```

> Po prvním spuštění se admin účet uloží do databáze. Hodnoty `ADMIN_USERNAME`
> a `ADMIN_PASSWORD` v `.env` se použijí znovu jen pokud databáze neexistuje.

Adresáře pro ukládání UIB a šablon lze nastavit přímo v GUI
(sekce **Nastavení** → Admin menu) – výchozí hodnoty jsou `data/events/` a `data/workbooks/`.

---

## Startovací skript

Soubor `start.py` v kořeni projektu:
- Automaticky najde uvicorn ve `.venv` (Linux i Windows)
- Spustí uvicorn server na portu 8080
- Databáze a adresáře se vytvoří automaticky při prvním spuštění

Parametry:
```bash
# Lokální přístup (výchozí)
python start.py

# Přístup ze sítě
python start.py --host 0.0.0.0 --port 8080

# Vývojový režim s automatickým reloadem
python start.py --reload
```

---

## Adresářová struktura po instalaci

```
Forms4SOC/
├── app/                  – zdrojový kód aplikace
├── data/
│   ├── events/           – JSON soubory UIB (vytvořeno automaticky)
│   ├── workbooks/        – JSON šablony
│   │   ├── phishing_v2.json
│   │   ├── ddos_vpn_v1.json
│   │   └── vanilla_v1.json
│   ├── tisk/             – PDF exporty (vytvořeno automaticky)
│   └── forms4soc.db      – SQLite databáze (vytvořena automaticky)
├── docs/                 – dokumentace
│   ├── API.md
│   ├── INSTALL.md
│   └── TEMPLATE_GUIDE.md
├── .env                  – konfigurace (vytvořit dle .env.example)
├── requirements.txt
└── start.py              – startovací skript
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

## Bezpečnostní opatření

Aplikace obsahuje následující bezpečnostní vrstvy aktivní ve výchozím nastavení:

| Opatření | Popis |
|---|---|
| JWT httpOnly cookie | Auth token je uložen v httpOnly cookie (nedostupná z JavaScriptu), `samesite=lax` |
| SecurityMiddleware | Každý POST/PUT/PATCH na `/api/v1/*` musí mít `Content-Type: application/json` – blokuje CSRF útoky přes HTML formuláře (HTTP 415) |
| Security response headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` |
| `X-Requested-With` | Všechna AJAX volání přes `apiFetch` odesílají `X-Requested-With: XMLHttpRequest` |
| Role-based access | Adminové endpointy (`/api/v1/users`, `/api/v1/settings`, správa šablon) vyžadují roli `admin` |

**Doporučení pro produkční nasazení:**
- Nastavte silný `JWT_SECRET_KEY` (min. 32 znaků, generace: `openssl rand -hex 32`)
- Provozujte za HTTPS reverse proxy (nginx) – viz sekce níže
- Změňte výchozí heslo admina ihned po prvním přihlášení

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
# Vytvořit systémového uživatele (bez login shellu)
sudo useradd -r -s /sbin/nologin -d /opt/forms4soc forms4soc

# Klonovat do /opt
sudo git clone https://github.com/alchy/Forms4SOC.git /opt/forms4soc
sudo chown -R forms4soc:forms4soc /opt/forms4soc
cd /opt/forms4soc

# Nainstalovat závislosti
sudo -u forms4soc python3 -m venv .venv
sudo -u forms4soc .venv/bin/pip install -r requirements.txt

# Konfigurace
sudo -u forms4soc cp .env.example .env
sudo nano .env   # nastavit JWT_SECRET_KEY a ADMIN_PASSWORD
```

### 2. systemd service

Vytvořte soubor `/etc/systemd/system/forms4soc.service`:

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
```

Logy:
```bash
sudo journalctl -u forms4soc -f
```

### 3. Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name forms4soc.vas-soc.cz;

    # Přesměrovat HTTP na HTTPS
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
