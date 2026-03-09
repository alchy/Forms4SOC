# Forms4SOC

SOC Incident Management Portal – webová aplikace pro správu bezpečnostních incidentů dle SOC playbooků.

## Co to je

Forms4SOC umožňuje SOC analytikům zakládat, vyplňovat a uzavírat incidenty podle předdefinovaných JSON šablon (playbooků). Každý incident je strukturovaný formulář vycházející z příslušného playbooku – s triage checklisty, tabulkami aktiv, containment akcemi a RACI maticí.

## Klíčové funkce

- Vytváření incidentů ze SOC playbooků (JSON šablony)
- Strukturované formuláře: checklist Triage & Investigace, tabulka aktiv, Containment & Remediation, RACI matice
- Zamykání incidentů při editaci (file locking, zabraňuje souběžné editaci)
- Auto-save při změně stavu incidentu
- Přehled incidentů s řazením dle priority stavu a filtry
- Tisk incidentu do PDF přes dialog prohlížeče
- Správa uživatelů (role: admin / analyst)
- Konfigurace adresářů přes GUI
- Konfigurovatelný název a verze aplikace přes `.env`
- REST API s JWT autentizací

## Rychlý start

```bash
git clone https://github.com/alchy/Forms4SOC.git
cd Forms4SOC
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # upravte JWT_SECRET_KEY a ADMIN_PASSWORD
python scripts/download_vendors.py
python start.py
```

Aplikace bude dostupná na **http://localhost:8080** (výchozí přihlášení: `admin` / `admin`).

## Dokumentace

- [Instalace a nasazení](docs/INSTALL.md) – lokální spuštění, systemd service, nginx reverse proxy
- [API reference](docs/API.md) – přehled všech REST endpointů
- [Web rendering](docs/WEB_RENDERING.md) – Jinja2 šablony, layout, globální proměnné
- [Průvodce šablonami](docs/TEMPLATE_GUIDE.md) – jak psát a upravovat JSON playbook šablony

## Tech stack

- **Backend**: FastAPI + Uvicorn (Python 3.11+)
- **Frontend**: Jinja2 + Bootstrap 5 (server-side rendering)
- **Auth**: JWT (PyJWT), httpOnly cookie `forms4soc_token`
- **DB**: SQLite – uživatelé + nastavení (aiosqlite)
- **Storage**: JSON soubory (incidenty), JSON/YAML soubory (šablony/playbooks)
- **JS knihovny**: jQuery, DataTables, Bootstrap Icons, Ace Editor
