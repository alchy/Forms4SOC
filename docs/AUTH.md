# Konfigurace a autentizace

Tento dokument popisuje, jak Forms4SOC zpracovává přihlášení, ukládá hesla, vydává tokeny
a ověřuje každý chráněný požadavek. Určeno pro: vývojáře rozšiřující backend, administrátory
nasazující aplikaci, bezpečnostní auditory.

---

## Co to je a k čemu slouží?

Autentizace zajišťuje, že ke každému incidentu i konfiguraci přistupuje pouze oprávněný
analytik nebo administrátor. Implementace staví na třech pilířích:

- **Konfigurace** – `pydantic-settings` čte `.env` soubor při startu a vystaví `Settings` singleton přístupný v celé aplikaci.
- **Uložení hesel** – hesla se nikdy neukládají v plaintextu; používá se bcrypt.
- **Session** – po úspěšném přihlášení backend vydá JWT jako httpOnly cookie. Platnost tokenu se ověřuje při každém chráněném požadavku.

---

## Jak to funguje?

```
Prohlížeč: POST /api/v1/auth/login  { username, password }
    │
    ▼
SimpleAuthProvider.authenticate()
    │  načte řádek z SQLite users
    │  zkontroluje is_active
    │  bcrypt.checkpw(password, hashed_password)
    │
    ├─ selhání → asyncio.sleep(1) → HTTP 401
    │
    ▼
create_access_token(sub=username, role=role)
    │  HS256, podepsáno JWT_SECRET_KEY
    │  claim exp = now + JWT_EXPIRE_MINUTES
    ▼
Set-Cookie: forms4soc_token=<JWT>; HttpOnly; SameSite=Lax; Max-Age=<sekundy>
    │
    ▼
Každý chráněný požadavek:
    │  require_auth čte cookie forms4soc_token
    │  decode_token: ověří podpis + exp
    │  vrátí User objekt jako FastAPI Depends
    ▼
require_admin: zkontroluje role == "admin", jinak HTTP 403
```

---

## Rychlý start – přihlášení a první chráněný požadavek

```bash
# 1. Přihlásit se – cookie se uloží do cookie-jar
curl -c cookies.txt -X POST http://localhost:8080/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'

# 2. Použít cookie – chráněný endpoint
curl -b cookies.txt http://localhost:8080/api/v1/cases/
```

Výsledek: první příkaz vrátí HTTP 200 s `{"access_token": "...", "token_type": "bearer"}` a
nastaví cookie `forms4soc_token`. Druhý příkaz vrátí seznam incidentů.

> **Pozor:** Výchozí heslo `admin/admin` je pouze pro první spuštění. Před nasazením do produkce změň `ADMIN_PASSWORD` v `.env` **a** smaž (nebo vyčisti) SQLite databázi, aby se nový hash zaseedoval. Viz sekci [Seedování administrátora](#seedování-administrátora).

---

## Krok za krokem – co se stane při přihlášení

### 1. Odeslání přihlašovacích údajů

Prohlížeč odešle HTTP POST s tělem ve formátu JSON:

```json
{ "username": "analyst1", "password": "moje-heslo" }
```

Data putují **výhradně přes šifrovaný kanál (HTTPS)**. Uvicorn ve výchozím stavu naslouchá
na HTTP – nasazení za reverzní proxy (nginx, Caddy) s TLS je povinné pro produkci.

Formulář na `/login` toto tělo sestaví JavaScriptem a odešle `fetch()` voláním.
Heslo nikdy neopustí prohlížeč jako část URL ani jako query parametr.

### 2. Ověření hesla (bcrypt)

`SimpleAuthProvider.authenticate()` v `app/auth/simple_auth.py`:

1. Načte řádek `users` z SQLite podle `username`.
2. Zkontroluje `is_active == 1` – deaktivovaný účet dostane HTTP 401.
3. Zavolá `verify_password(plain, hashed)` z `app/core/security.py`:

```python
def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

bcrypt porovnání je záměrně pomalé (cost factor ≈ 12 rund). Útočník s ukradenou DB
potřebuje výrazně více času na prolomení než u MD5 nebo SHA.

### 3. Vydání JWT

Po úspěšném ověření `auth.py` zavolá `create_access_token()`:

```python
def create_access_token(sub: str, role: str) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

Token je podepsán algoritmem **HS256** klíčem `JWT_SECRET_KEY`. Obsahuje tři claimy:

| Claim | Obsah |
|-------|-------|
| `sub` | username přihlášeného uživatele |
| `role` | `"admin"` nebo `"analyst"` |
| `exp` | Unix timestamp expirace (UTC) |

### 4. Nastavení cookie

Token se uloží jako httpOnly cookie – JavaScript v prohlížeči k němu nemá přístup,
což eliminuje riziko krádeže přes XSS:

```python
response.set_cookie(
    key="forms4soc_token",
    value=token,
    httponly=True,
    samesite="lax",
    max_age=settings.jwt_expire_minutes * 60,  # sekundy
)
```

| Atribut | Hodnota | Důvod |
|---------|---------|-------|
| `httponly` | `True` | JavaScript nemůže číst cookie |
| `samesite` | `"lax"` | Blokuje CSRF při cross-site požadavcích |
| `max_age` | `jwt_expire_minutes × 60` | Prohlížeč smaže cookie po expiraci |

### 5. Ověření cookie při každém požadavku

`require_auth` (FastAPI `Depends`) v `app/core/security.py` čte cookie a volá `decode_token()`:

```python
def decode_token(token: str) -> TokenPayload:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return TokenPayload(sub=payload["sub"], role=payload["role"])
```

PyJWT automaticky ověří:
- **Podpis** – zda token nebyl pozměněn (HMAC-SHA256 s `JWT_SECRET_KEY`).
- **Expirace** – zda aktuální čas nepřekročil `exp`. Pokud ano, vyvolá `ExpiredSignatureError`.

Každá výjimka PyJWT se zachytí a vrátí HTTP 401 s prázdnou odpovědí – žádná detailní chybová
zpráva, která by pomohla útočníkovi.

---

## Konfigurace přes `.env`

`app/config.py` používá `pydantic-settings`. Při importu modulu se soubor `.env` načte
**jednou** do `Settings` singletonu. Pozdější změna `.env` souboru za běhu aplikace nemá
žádný efekt – je nutný restart.

```
# .env – příklad produkčního nastavení
JWT_SECRET_KEY=nahrad-silnym-nahodnym-retezcem-min-32-znaku
JWT_EXPIRE_MINUTES=480
AUTH_PROVIDER=simple
ADMIN_USERNAME=admin
ADMIN_PASSWORD=bezpecne-heslo
DATABASE_PATH=data/forms4soc.db
```

| Proměnná | Výchozí hodnota | Popis |
|----------|----------------|-------|
| `JWT_SECRET_KEY` | `change-me-in-production-...` | Podpisový klíč JWT – **musí být změněn** |
| `JWT_ALGORITHM` | `HS256` | Algoritmus podpisu |
| `JWT_EXPIRE_MINUTES` | `480` (8 hodin) | Platnost tokenu |
| `AUTH_PROVIDER` | `simple` | `simple` / `oauth` / `ldap` |
| `ADMIN_USERNAME` | `admin` | Uživatelské jméno seed admina |
| `ADMIN_PASSWORD` | `admin` | Heslo seed admina (viz níže) |
| `DATABASE_PATH` | `data/forms4soc.db` | Cesta k SQLite souboru |

---

## Seedování administrátora

`init_db()` v `app/core/database.py` se spustí při každém startu aplikace a vytvoří tabulky
`users` a `settings`, pokud neexistují. Admin účet se zaseeduje **pouze tehdy, když je tabulka
`users` zcela prázdná**:

```python
count = await db.execute("SELECT COUNT(*) FROM users")
row = await count.fetchone()
if row[0] == 0:
    hashed = hash_password(settings.admin_password)
    await db.execute("INSERT INTO users ...", (settings.admin_username, hashed, "admin", 1))
```

Heslo z `.env` se **vždy** uloží jako bcrypt hash – nikdy v plaintextu.

### Co se stane po změně `ADMIN_PASSWORD` v `.env`

Změna `.env` ovlivní databázi **pouze při prvním spuštění na prázdné DB**. Pokud tabulka
`users` již obsahuje řádky, seed se přeskočí a nové heslo se do DB nepropíše.

Postup pro reset hesla admina v produkci:

```bash
# Možnost A – přes API (doporučeno, nevyžaduje výpadek)
curl -b cookies.txt -X PATCH http://localhost:8080/api/v1/users/1 \
     -H "Content-Type: application/json" \
     -d '{"password": "nove-bezpecne-heslo"}'

# Možnost B – smazání DB (způsobí výpadek, ztrátu nastavení)
rm data/forms4soc.db
# Nastav ADMIN_PASSWORD v .env, pak restart aplikace
```

### Cesty `incidents_dir` a `templates_dir` v SQLite

Tyto nastavení se seedují pomocí `INSERT OR IGNORE` – tj. zapíší se do `settings` tabulky
**pouze jednou** (při prvním spuštění). Následné změny `.env` je **neaktualizují**.

Změna cest za běhu: `/settings` v admin GUI nebo přímou editací SQLite `settings` tabulky.

---

## Bezpečnostní doporučení

### `JWT_SECRET_KEY`

Výchozí klíč `"change-me-in-production-..."` je veřejně znám z repozitáře. Útočník
s tímto klíčem může podepsat libovolný JWT a získat přístup k aplikaci bez hesla.

Vygeneruj silný klíč před prvním nasazením:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Klíč udrž tajný – nikdy ho nevkládej do verzovacího systému. `.env` je v `.gitignore`.

### Platnost tokenu (`JWT_EXPIRE_MINUTES`)

Výchozích 480 minut (8 hodin) odpovídá délce pracovní směny. Po expiraci musí analytik
znovu zadat heslo. Zkrátit lze beze změny kódu, pouze úpravou `.env`.

Při odhlášení (`POST /api/v1/auth/logout`) backend smaže cookie – token přestane být odesílán.
Token samotný ale zůstane technicky platný do `exp`. Aplikace neimplementuje seznam
odvolaných tokenů (token blacklist) – pokud je nutná okamžitá revokace, změň `JWT_SECRET_KEY`
(invaliduje **všechny** aktivní sessions).

### Ochrana proti brute-force

Při neúspěšném přihlášení backend čeká `asyncio.sleep(1)` před vrácením HTTP 401.
Jedno vlákno tak může otestovat nejvýše ~60 hesel za minutu. Útočník s paralelními
požadavky z jedné IP může toto obejít – pro produkční nasazení exponované do sítě zvažte
přidání rate limiteru per-IP (např. `slowapi`).

### Deaktivace uživatele

`is_active = 0` v `users` tabulce zablokuje přihlášení okamžitě, ale neodvolá existující
cookie vydané před deaktivací. Opět platí: pro okamžité vyřazení změň `JWT_SECRET_KEY`.

### HTTPS

Bez TLS cookie cestuje sítí nešifrovaně a může být zachycena (man-in-the-middle).
Atribut `Secure` na cookie není nastaven – doporučujeme přidat po nasazení za HTTPS proxy.

---

## Přehled funkcí a tříd

| Identifikátor | Soubor | Popis |
|---|---|---|
| `Settings` | `app/config.py` | pydantic-settings singleton; načteno z `.env` při importu |
| `hash_password(plain)` | `app/core/security.py` | bcrypt hash hesla |
| `verify_password(plain, hashed)` | `app/core/security.py` | bcrypt porovnání |
| `create_access_token(sub, role)` | `app/core/security.py` | vydá HS256 JWT s `exp` |
| `decode_token(token)` | `app/core/security.py` | ověří podpis + exp, vrátí `TokenPayload` |
| `require_auth` | `app/core/security.py` | FastAPI Depends – čte cookie, vrátí `User` nebo HTTP 401 |
| `require_admin` | `app/core/security.py` | FastAPI Depends – navazuje na `require_auth`, HTTP 403 pokud role != admin |
| `SimpleAuthProvider.authenticate()` | `app/auth/simple_auth.py` | DB lookup + bcrypt ověření |
| `init_db()` | `app/core/database.py` | vytvoří tabulky, zaseeduje admina a cesty |
| `POST /api/v1/auth/login` | `app/api/v1/auth.py` | přijme credentials, vrátí token + nastaví cookie |
| `POST /api/v1/auth/logout` | `app/api/v1/auth.py` | smaže cookie |
| `GET /api/v1/auth/me` | `app/api/v1/auth.py` | vrátí profil přihlášeného uživatele |
