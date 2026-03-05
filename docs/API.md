# Forms4SOC – Evidence API

> Interaktivní dokumentace: http://localhost:8000/api/docs (Swagger UI)
> ReDoc: http://localhost:8000/api/redoc

---

## Autentizace

Všechny `/api/v1/*` endpointy (kromě `/auth/login`) vyžadují platný JWT token.
Token je nastaven jako **httpOnly cookie** (`forms4soc_token`) při přihlášení.

---

## Endpointy

### AUTH – `/api/v1/auth`

| Metoda | Endpoint         | Popis                                  | Auth |
|--------|-----------------|----------------------------------------|------|
| POST   | `/login`        | Přihlášení, vrátí JWT token + nastaví cookie | Ne |
| POST   | `/logout`       | Odhlášení, smaže cookie               | Ne   |
| GET    | `/me`           | Info o přihlášeném uživateli           | Ano  |

**POST /login – tělo požadavku:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**POST /login – odpověď:**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

---

### TEMPLATES – `/api/v1/templates`

| Metoda | Endpoint          | Popis                            | Auth |
|--------|------------------|----------------------------------|------|
| GET    | `/`              | Seznam všech SOC šablon          | Ano  |
| GET    | `/{template_id}` | Detail konkrétní šablony         | Ano  |

**GET /templates/ – příklad odpovědi:**
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
    "sections": [],
    "filename": "phishing_v1.json"
  }
]
```

---

### CASES – `/api/v1/cases`

| Metoda | Endpoint       | Popis                                | Auth |
|--------|---------------|--------------------------------------|------|
| GET    | `/`           | Seznam všech incidentů               | Ano  |
| POST   | `/`           | Vytvoření incidentu ze šablony       | Ano  |
| GET    | `/{case_id}`  | Detail incidentu                     | Ano  |

**POST /cases/ – tělo požadavku:**
```json
{
  "template_id": "phishing-v1",
  "title": "Podezřelý e-mail od neznámého odesílatele",
  "severity": "high"
}
```

**POST /cases/ – příklad odpovědi (201 Created):**
```json
{
  "id": 1,
  "case_id": "INC-2026-0001",
  "template_id": "phishing-v1",
  "title": "Podezřelý e-mail od neznámého odesílatele",
  "severity": "high",
  "status": "open",
  "created_by": "admin",
  "created_at": "2026-03-05T10:00:00+00:00",
  "updated_at": "2026-03-05T10:00:00+00:00",
  "data": {"template_id": "phishing-v1"}
}
```

---

## Auth provider – konfigurace

Přepnutí providera v `.env`:
```
AUTH_PROVIDER=simple   # výchozí – username/password z .env
AUTH_PROVIDER=oauth    # OAuth2 (stub – nutno implementovat)
AUTH_PROVIDER=ldap     # LDAP/AD (stub – nutno implementovat)
```

Implementace: `app/auth/auth_provider.py` (ABC rozhraní), `app/auth/simple_auth.py` (aktivní).
