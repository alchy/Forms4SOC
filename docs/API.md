# Forms4SOC – API dokumentace

REST API pro správu incidentů, šablon, uživatelů a nastavení. Veškerá komunikace probíhá přes JSON; autentizace je řešena httpOnly cookie.

**Interaktivní dokumentace:** http://localhost:8080/api/docs (Swagger UI) · http://localhost:8080/api/redoc

---

## Jak to funguje?

```
Prohlížeč / klient
    │
    │  HTTP požadavek + Cookie (forms4soc_token)
    ▼
FastAPI app  →  JWT middleware  →  route handler
    │
    ├── /api/v1/auth/*       – přihlášení / odhlášení / info o uživateli
    ├── /api/v1/cases/*      – CRUD incidentů + zámky
    ├── /api/v1/templates/*  – CRUD šablon (YAML workbooků)
    ├── /api/v1/settings/*   – nastavení aplikace (admin)
    └── /api/v1/users/*      – správa uživatelů (admin)
```

Endpointy označené **🔒** jsou dostupné pouze uživatelům s rolí `admin`.

---

## Autentizace

Přihlášením přes `POST /auth/login` se nastaví httpOnly cookie `forms4soc_token` (JWT).
Prohlížeč cookie přikládá automaticky ke každému dalšímu požadavku. Odhlášení cookie smaže.

```
POST /auth/login  →  nastaví cookie  →  všechny /api/v1/* endpointy
                                          (kromě /login a /logout)
```

> Přímé volání z externího klienta (curl, Python): pošli přihlašovací požadavek, ulož cookie a přikládej ji k dalším voláním.

> Podrobný popis celého přihlašovacího procesu, JWT, cookies a bezpečnostních doporučení viz [AUTH.md](AUTH.md).

---

## AUTH – `/api/v1/auth`

| Metoda | Endpoint | Popis | Auth |
|--------|----------|-------|------|
| POST | `/auth/login` | Přihlášení – nastaví httpOnly cookie | — |
| POST | `/auth/logout` | Odhlášení – smaže cookie | — |
| GET | `/auth/me` | Info o přihlášeném uživateli | ✓ |

### `POST /auth/login`

```json
// Tělo požadavku
{ "username": "admin", "password": "heslo" }

// Odpověď 200 – nastaví Cookie: forms4soc_token=<jwt>
{ "access_token": "<jwt>", "token_type": "bearer" }

// Odpověď 401 – nesprávné přihlašovací údaje
{ "detail": "Neplatné přihlašovací údaje" }
```

### `GET /auth/me`

```json
// Odpověď 200
{
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00"
}
```

---

## CASES – `/api/v1/cases`

Incidenty jsou JSON dokumenty uložené jako soubory v adresáři `data/events/` (konfigurovatelné). Každý incident vznikne klonováním šablony.

| Metoda | Endpoint | Popis | Auth |
|--------|----------|-------|------|
| GET | `/cases/` | Seznam všech incidentů (od nejnovějšího) | ✓ |
| POST | `/cases/` | Vytvoření incidentu ze šablony | ✓ |
| GET | `/cases/{case_id}` | Detail incidentu | ✓ |
| PATCH | `/cases/{case_id}` | Aktualizace stavu a/nebo dat | ✓ |
| DELETE | `/cases/{case_id}` | Smazání incidentu 🔒 | admin |
| POST | `/cases/{case_id}/lock` | Získání zámku pro editaci | ✓ |
| DELETE | `/cases/{case_id}/lock` | Uvolnění zámku | ✓ |

### Formát Case ID

```
UIB-DDMMYYYY-HHMM-RRRR

Příklad: UIB-06032026-0954-3712
```

### Stavy incidentu (`status`)

| Hodnota | Zobrazení v UI |
|---------|----------------|
| `open` | Přiřazeno |
| `in_progress` | V řešení |
| `closed` | Uzavřený |
| `false_positive` | False Positive |

### `POST /cases/` – vytvoření incidentu

```json
// Tělo požadavku
{ "template_id": "phishing-v2" }

// Odpověď 201
{
  "case_id": "UIB-05032026-1430-4281",
  "template_id": "phishing-v2",
  "status": "open",
  "created_by": "admin",
  "created_at": "2026-03-05T14:30:22+00:00",
  "updated_at": "2026-03-05T14:30:22+00:00",
  "locked_by": null,
  "data": { "sections": [...] }
}
```

### `PATCH /cases/{case_id}` – aktualizace

Všechna pole jsou volitelná – lze aktualizovat pouze status, pouze data, nebo oboje najednou.

```json
// Pouze status
{ "status": "in_progress" }

// Pouze data dokumentu
{ "data": { "sections": [...] } }

// Obojí najednou
{ "status": "closed", "data": { "sections": [...] } }
```

### Zámky (file locking)

Před editací doporučujeme získat zámek – zabrání souběžné editaci více uživateli.

```
POST  /cases/{id}/lock   →  200 OK (zámek získán) nebo 423 Locked (zamčeno jiným)
DELETE /cases/{id}/lock  →  204 No Content
```

```json
// POST /cases/{id}/lock – odpověď 200
{ "locked_by": "admin" }

// POST /cases/{id}/lock – odpověď 423
{
  "detail": {
    "message": "Incident je zamčen jiným uživatelem",
    "locked_by": "analyst1",
    "locked_at": "2026-03-05T14:30:22+00:00"
  }
}
```

> Admin může uvolnit zámek kohokoliv přes `DELETE /cases/{id}/lock`.

### Tisk

Stránka `/cases/{case_id}/print` zobrazí incident ve formátu optimalizovaném pro tisk. Tlačítko „Tisk / Uložit PDF" využije dialog prohlížeče (`Ctrl+P`). Stránka je dostupná bez samostatného API endpointu – otevři ji přímo v prohlížeči.

---

## TEMPLATES – `/api/v1/templates`

Šablony jsou YAML soubory v adresáři `data/workbooks/` (konfigurovatelné). Každá šablona definuje strukturu jednoho typu incidentu.

| Metoda | Endpoint | Popis | Auth |
|--------|----------|-------|------|
| GET | `/templates/` | Seznam všech šablon | ✓ |
| POST | `/templates/` | Vytvoření nové šablony 🔒 | admin |
| GET | `/templates/{template_id}` | Detail šablony | ✓ |
| GET | `/templates/{template_id}/source` | Zdrojový YAML (pro editor) 🔒 | admin |
| PUT | `/templates/{template_id}` | Uložení upraveného obsahu 🔒 | admin |
| DELETE | `/templates/{template_id}` | Smazání šablony 🔒 | admin |

### `GET /templates/` – příklad odpovědi

```json
[
  {
    "template_id": "phishing-v2",
    "name": "Podezřelý e-mail / Phishing",
    "version": "2.0",
    "category": "Phishing",
    "status": "active",
    "description": "...",
    "mitre_tactic": "Initial Access",
    "mitre_technique": "T1566",
    "data_sources": ["Inbound SMTP Mail Gateway", "Proxy", "SIEM"],
    "sections": [...],
    "filename": "phishing_v2.yaml"
  }
]
```

Dostupné šablony: `phishing-v2` (Phishing / podezřelý e-mail) · `ddos-vpn-v1` (DDoS na VPN) · `vanilla-v1` (výchozí kostra).

### `POST /templates/` – vytvoření šablony

```json
// Tělo požadavku
{ "filename": "ransomware_v1.yaml", "content": "..." }

// Odpověď 200
{ "ok": true, "template_id": "ransomware-v1", "filename": "ransomware_v1.yaml" }

// Odpověď 409 – soubor již existuje
// Odpověď 400 – neplatný YAML
```

### `PUT /templates/{template_id}` – uložení šablony

```json
// Tělo požadavku
{ "content": "{...}" }

// Odpověď 200
{ "ok": true, "filename": "ransomware_v1.yaml" }
```

---

## SETTINGS – `/api/v1/settings` 🔒

Nastavení aplikace – adresáře pro incidenty a šablony. Změny se projeví okamžitě (bez restartu).

| Metoda | Endpoint | Popis |
|--------|----------|-------|
| GET | `/settings/` | Aktuální nastavení |
| PATCH | `/settings/` | Aktualizace nastavení |

### Dostupné klíče

| Klíč | Popis | Výchozí hodnota |
|------|-------|-----------------|
| `incidents_dir` | Adresář pro JSON soubory incidentů | `data/events` |
| `templates_dir` | Adresář pro YAML šablony workbooků | `data/workbooks` |

### `PATCH /settings/`

```json
// Tělo požadavku
{
  "incidents_dir": "C:/SOC/incidents",
  "templates_dir": "C:/SOC/workbooks"
}

// Odpověď 200 – vrátí aktuální stav po změně
{
  "incidents_dir": "C:/SOC/incidents",
  "templates_dir": "C:/SOC/workbooks"
}
```

---

## USERS – `/api/v1/users` 🔒

Správa uživatelů. Admin může vytvářet, upravovat a mazat účty.

| Metoda | Endpoint | Popis |
|--------|----------|-------|
| GET | `/users/` | Seznam všech uživatelů |
| POST | `/users/` | Vytvoření uživatele |
| GET | `/users/{username}` | Detail uživatele |
| PATCH | `/users/{username}` | Aktualizace (role, stav, heslo) |
| DELETE | `/users/{username}` | Smazání uživatele |

### Role uživatelů

| Role | Oprávnění |
|------|-----------|
| `admin` | Plný přístup – správa uživatelů, nastavení, mazání incidentů, editor šablon |
| `analyst` | Vytváření a editace incidentů |

### `POST /users/` – vytvoření uživatele

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

### `PATCH /users/{username}` – aktualizace

```json
// Všechna pole jsou volitelná
{
  "role": "admin",
  "is_active": false,
  "password": "noveHeslo"
}
```

---

## Auth provider – konfigurace

Přepnutí poskytovatele autentizace v `.env`:

```ini
AUTH_PROVIDER=simple   # výchozí – username/password z SQLite DB
AUTH_PROVIDER=oauth    # OAuth2 (stub – nutno implementovat)
AUTH_PROVIDER=ldap     # LDAP/AD (stub – nutno implementovat)
```

Implementace: `app/auth/auth_provider.py` (ABC rozhraní) · `app/auth/simple_auth.py` (aktivní provider).

---

## Přehled HTTP stavových kódů

| Kód | Kdy nastane |
|-----|------------|
| `200 OK` | Úspěch (GET, PATCH, PUT) |
| `201 Created` | Incident nebo uživatel vytvořen |
| `204 No Content` | Smazání nebo uvolnění zámku |
| `400 Bad Request` | Neplatné tělo požadavku (např. neplatný YAML šablony) |
| `401 Unauthorized` | Chybí nebo vypršel JWT token |
| `403 Forbidden` | Nedostatečná oprávnění (vyžaduje admin) |
| `404 Not Found` | Incident nebo šablona nenalezena |
| `409 Conflict` | Soubor šablony již existuje |
| `415 Unsupported Media Type` | Chybí `Content-Type: application/json` |
| `423 Locked` | Incident zamčen jiným uživatelem |
