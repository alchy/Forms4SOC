# Forms4SOC – API dokumentace

> Interaktivní dokumentace: http://localhost:8080/api/docs (Swagger UI)
> ReDoc: http://localhost:8080/api/redoc

---

## Autentizace

Všechny `/api/v1/*` endpointy (kromě `/auth/login` a `/auth/logout`) vyžadují platný JWT token.
Token je nastaven jako **httpOnly cookie** (`forms4soc_token`) při přihlášení a automaticky přikládán prohlížečem ke každému požadavku.

Endpointy označené 🔒 vyžadují roli **admin**.

---

## AUTH – `/api/v1/auth`

| Metoda | Endpoint  | Popis | Auth |
|--------|-----------|-------|------|
| POST | `/login`  | Přihlášení – vrátí JWT token a nastaví httpOnly cookie | — |
| POST | `/logout` | Odhlášení – smaže cookie | — |
| GET  | `/me`     | Info o přihlášeném uživateli | ✓ |

**POST /auth/login**
```json
// Tělo požadavku
{ "username": "admin", "password": "heslo" }

// Odpověď 200
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

## TEMPLATES – `/api/v1/templates`

| Metoda | Endpoint | Popis | Auth |
|--------|----------|-------|------|
| GET | `/` | Seznam všech SOC šablon | ✓ |
| GET | `/{template_id}` | Detail konkrétní šablony | ✓ |

**GET /templates/ – příklad odpovědi**
```json
[
  {
    "template_id": "phishing-v1",
    "name": "Podezřelý e-mail / Phishing",
    "version": "1.0",
    "category": "Phishing",
    "status": "active",
    "description": "...",
    "mitre_tactic": "Initial Access",
    "mitre_technique": "T1566",
    "mitre_subtechnique": "T1566.001",
    "data_sources": ["Inbound SMTP Mail Gateway", "Proxy", "SIEM"],
    "sections": [...],
    "filename": "phishing_v1.json"
  },
  {
    "template_id": "phishing-v2",
    "name": "Podezřelý e-mail / Phishing v2",
    "version": "2.0",
    ...
    "filename": "phishing_v2.json"
  }
]
```

Dostupné šablony: `phishing-v1` (původní), `phishing-v2` (sloučená Triage & Investigace, rozšířená tabulka aktiv).

---

## CASES – `/api/v1/cases`

| Metoda | Endpoint | Popis | Auth |
|--------|----------|-------|------|
| GET    | `/`                      | Seznam všech incidentů (řazeno od nejnovějšího) | ✓ |
| POST   | `/`                      | Vytvoření incidentu ze šablony | ✓ |
| GET    | `/{case_id}`             | Detail incidentu | ✓ |
| PATCH  | `/{case_id}`             | Aktualizace stavu a/nebo dat incidentu | ✓ |
| DELETE | `/{case_id}`             | Smazání incidentu 🔒 | admin |
| POST   | `/{case_id}/lock`        | Získání zámku pro editaci | ✓ |
| DELETE | `/{case_id}/lock`        | Uvolnění zámku | ✓ |

### Formát Case ID

```
SOC-IN-DDMMYYYY-HHMMSS-{username}

Příklad: SOC-IN-05032026-143022-admin
```

### Stavy incidentu (`status`)

| Hodnota | Zobrazení |
|---|---|
| `open` | Přiřazeno |
| `in_progress` | V řešení |
| `closed` | Uzavřený |
| `false_positive` | False Positive |

**POST /cases/ – vytvoření incidentu**
```json
// Tělo požadavku
{ "template_id": "phishing-v1" }

// Odpověď 201
{
  "case_id": "SOC-IN-05032026-143022-admin",
  "template_id": "phishing-v1",
  "status": "open",
  "created_by": "admin",
  "created_at": "2026-03-05T14:30:22+00:00",
  "updated_at": "2026-03-05T14:30:22+00:00",
  "locked_by": null,
  "data": { ... }
}
```

**PATCH /cases/{case_id} – aktualizace**
```json
// Pouze status
{ "status": "in_progress" }

// Pouze data dokumentu
{ "data": { ... } }

// Obojí najednou
{ "status": "closed", "data": { ... } }
```

### Zámky (file locking)

Před editací incidentu je nutné získat zámek. Zámek zabrání souběžné editaci více uživateli.

**POST /cases/{case_id}/lock**
```json
// Odpověď 200 – zámek získán
{ "locked_by": "admin" }

// Odpověď 423 – zamčeno jiným uživatelem
{
  "detail": {
    "message": "Incident je zamčen jiným uživatelem",
    "locked_by": "analyst1",
    "locked_at": "2026-03-05T14:30:22+00:00"
  }
}
```

**DELETE /cases/{case_id}/lock** – uvolní zámek (admin může uvolnit komukoliv)
```
Odpověď: 204 No Content
```

### Tisk

Tlačítko **Tisk** v seznamu incidentů i v detailu incidentu otevírá `/cases/{case_id}/print` v nové záložce. Stránka zobrazí celý obsah incidentu ve formátu optimalizovaném pro tisk a umožní uložit jako PDF přes dialog prohlížeče (`Ctrl+P`).

---

## SETTINGS – `/api/v1/settings` 🔒

| Metoda | Endpoint | Popis |
|--------|----------|-------|
| GET    | `/`      | Aktuální nastavení |
| PATCH  | `/`      | Aktualizace nastavení |

**Dostupné klíče nastavení:**

| Klíč | Popis | Výchozí hodnota |
|---|---|---|
| `incidents_dir` | Adresář pro ukládání JSON souborů incidentů | `data/incidents` |
| `templates_dir` | Adresář pro načítání JSON šablon | `data/playbooks` |

**PATCH /settings/**
```json
// Tělo požadavku
{
  "incidents_dir": "C:/SOC/incidents",
  "templates_dir": "C:/SOC/playbooks"
}

// Odpověď 200 – vrátí aktuální nastavení
{
  "incidents_dir": "C:/SOC/incidents",
  "templates_dir": "C:/SOC/playbooks"
}
```

---

## USERS – `/api/v1/users` 🔒

| Metoda | Endpoint | Popis |
|--------|----------|-------|
| GET    | `/`              | Seznam všech uživatelů |
| POST   | `/`              | Vytvoření uživatele |
| GET    | `/{username}`    | Detail uživatele |
| PATCH  | `/{username}`    | Aktualizace uživatele (role, stav, heslo) |
| DELETE | `/{username}`    | Smazání uživatele |

**Role uživatelů:**

| Role | Popis |
|---|---|
| `admin` | Plný přístup vč. správy uživatelů, nastavení a mazání incidentů |
| `analyst` | Vytváření a editace incidentů |

**POST /users/ – vytvoření uživatele**
```json
// Tělo požadavku
{ "username": "analyst1", "password": "heslo", "role": "analyst" }

// Odpověď 201
{
  "id": 2,
  "username": "analyst1",
  "role": "analyst",
  "is_active": true,
  "created_at": "2026-03-05T14:30:22"
}
```

**PATCH /users/{username}**
```json
// Všechny parametry jsou volitelné
{
  "role": "admin",
  "is_active": false,
  "password": "noveHeslo"
}
```

---

## Auth provider – konfigurace

Přepnutí providera v `.env`:
```
AUTH_PROVIDER=simple   # výchozí – username/password z SQLite DB
AUTH_PROVIDER=oauth    # OAuth2 (stub – nutno implementovat)
AUTH_PROVIDER=ldap     # LDAP/AD (stub – nutno implementovat)
```

Implementace: `app/auth/auth_provider.py` (ABC rozhraní), `app/auth/simple_auth.py` (aktivní).
