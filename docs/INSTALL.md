# Forms4SOC – Instalace a spuštění

## Požadavky

- Python 3.11 nebo novější
- Git

---

## Rychlá instalace

```bash
# 1. Klonování repozitáře
git clone https://github.com/vase-org/forms4soc.git
cd forms4soc

# 2. Vytvoření virtuálního prostředí
python -m venv .venv

# 3. Aktivace venv (Linux / macOS)
source .venv/bin/activate

# 3. Aktivace venv (Windows)
.venv\Scripts\activate

# 4. Instalace závislostí
pip install -r requirements.txt

# 5. Konfigurace (viz níže)
cp .env.example .env

# 6. Spuštění serveru
python start.py
```

Aplikace bude dostupná na **http://localhost:8080**

---

## Konfigurace (`.env`)

```ini
# Přihlašovací údaje prvního admin účtu (použijí se při prvním spuštění)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=zmente-toto-heslo

# JWT tajný klíč – vždy změňte!
JWT_SECRET_KEY=nahodny-dlouhy-retezec-min-32-znaku

# Port serveru (volitelné, výchozí 8080)
# APP_PORT=8080
```

> Po prvním spuštění se admin účet uloží do databáze. Heslo v `.env` se pak používá
> pouze pro vytvoření dalšího adminu, pokud by databáze neexistovala.

---

## Startovací skript

Soubor `start.py` v kořeni projektu:
- Automaticky najde uvicorn ve `.venv` (Windows i Linux/macOS)
- Spustí uvicorn server na portu 8080
- Databáze a adresáře se vytvoří automaticky při prvním spuštění

Parametry:
```bash
python start.py --port 8080 --host 0.0.0.0 --reload
```

> Na Windows lze server spustit také přímo: `.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8080`

---

## Adresářová struktura po instalaci

```
forms4soc/
├── app/                  – zdrojový kód aplikace
├── data/
│   ├── incidents/        – JSON soubory incidentů (vytvořeno automaticky)
│   ├── playbooks/        – JSON šablony
│   │   ├── phishing_v1.json
│   │   └── phishing_v2.json
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

## Aktualizace

```bash
git pull
pip install -r requirements.txt
python start.py
```

---

## Produkční nasazení (volitelné)

Pro produkční nasazení doporučujeme:
- Nastavit silný `JWT_SECRET_KEY` v `.env`
- Spustit za reverzním proxy (nginx, Caddy)
- Změnit výchozí heslo admina
- Zálohovat adresář `data/` (incidenty + databáze)
