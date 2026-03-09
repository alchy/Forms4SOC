# Forms4SOC – Web rendering a Jinja2 šablony

Webová část aplikace používá server-side rendering přes Jinja2 šablony. Prohlížeč dostane hotové HTML; JavaScript pak řeší dynamické operace (načítání dat z API, DataTables, formuláře).

---

## Architektura

```
Prohlížeč
    │  GET /cases  (HTTP + Cookie)
    ▼
FastAPI – web/routes.py
    │  TemplateResponse("cases.html", context)
    ▼
Jinja2 Engine
    │  base.html ← cases.html (extends)
    ▼
Hotové HTML → Prohlížeč
    │
    │  JS: fetch /api/v1/cases/ → DataTables, apiFetch helpers
    ▼
REST API (app/api/v1/)
```

---

## Soubory

| Soubor | Role |
|--------|------|
| `app/web/routes.py` | FastAPI router pro web stránky – vrací `TemplateResponse` |
| `app/templates/base.html` | Základní layout (navbar + app-shell) |
| `app/templates/login.html` | Přihlašovací stránka (standalone, nerozšiřuje base.html) |
| `app/templates/dashboard.html` | Dashboard |
| `app/templates/cases.html` | Seznam UIB (DataTables + filtry) |
| `app/templates/case_detail.html` | Detail/editace UIB |
| `app/templates/templates_list.html` | Seznam šablon workbooků |
| `app/templates/template_editor.html` | Editor JSON/YAML šablon (Ace Editor) |
| `app/templates/settings.html` | Nastavení aplikace (admin) |
| `app/templates/admin_users.html` | Správa uživatelů (admin) |
| `app/static/js/main.js` | Globální JS helper (`apiFetch`) |
| `app/static/js/case_form.js` | Renderer sekcí formuláře UIB |
| `app/static/css/custom.css` | Vlastní CSS (app-shell layout, sidebar, filtry) |

---

## Dědičnost šablon

Všechny stránky (kromě `login.html`) rozšiřují `base.html`:

```
base.html
├── navbar (block navbar)
├── .app-shell
│   ├── sidebar (block sidebar)  ← definuje každá child šablona
│   └── .app-main (block content)
└── scripts (block scripts)
```

`login.html` je samostatná stránka – nepoužívá `base.html`.

---

## Jinja2 globální proměnné

Proměnné dostupné automaticky ve **všech** šablonách bez nutnosti předávat je v každém route handleru:

| Proměnná | Zdroj | Příklad hodnoty |
|----------|-------|-----------------|
| `{{ app_name }}` | `config.py` → `.env` `APP_NAME` | `Forms4SOC` |
| `{{ app_version }}` | `config.py` → `.env` `APP_VERSION` | `0.2.0` |
| `{{ app_subtitle }}` | `config.py` → `.env` `APP_SUBTITLE` | `SOC Incident Management Portal` |

Nastavení probíhá v `web/routes.py` při startu aplikace:

```python
templates.env.globals.update({
    "app_name":    app_settings.app_name,
    "app_version": app_settings.app_version,
    "app_subtitle": app_settings.app_subtitle,
})
```

Hodnoty jsou seedy do SQLite při prvním spuštění (`init_db`) a lze je změnit přes `PATCH /api/v1/settings/`. Změna v GUI se projeví v API okamžitě; v Jinja2 templates až po restartu serveru (globals se nastavují jednou při startu z `config.py`).

### Lokální proměnné šablony

Každý web route handler předává do šablony lokální kontext:

| Proměnná | Typ | Popis |
|----------|-----|-------|
| `user` | `dict` (`username`, `role`) | Přihlášený uživatel; `None` na login stránce |
| `case_id` | `str` | ID incidentu (pouze `case_detail.html`) |
| `templates` | `list[SOCTemplate]` | Seznam šablon (dashboard, templates_list) |
| `settings` | `dict[str, str]` | Aktuální nastavení z SQLite (pouze settings.html) |
| `print_mode` | `bool` | Tiskový režim (pouze case_detail přes `/print`) |

---

## Layout (App Shell Pattern)

Aplikace používá **app-shell pattern** pro fixní layout bez překryvů sidebar/obsah:

```
<body>                          ← d-flex flex-column, height: 100%
  <nav class="navbar">          ← přirozená výška, nikdy nescrolluje
  <div class="app-shell">       ← flex: 1, min-height: 0 (zbývající výška viewportu)
    <nav class="sidebar">       ← flex-shrink: 0, overflow-y: auto
    <main class="app-main">     ← flex: 1, overflow-y: auto (scrolluje obsah)
```

Klíčové CSS vlastnosti (`custom.css`):

```css
html, body { height: 100%; overflow: hidden; display: flex; flex-direction: column; }
.app-shell  { display: flex; flex: 1; min-height: 0; overflow: hidden; }
.sidebar    { flex-shrink: 0; overflow-y: auto; }
.app-main   { flex: 1; min-width: 0; min-height: 0; overflow-y: auto; }
```

`min-height: 0` je kritické – bez něj flex items ignorují `overflow-y` a neomezují svou výšku, čímž roztahují stránku mimo viewport.

---

## Přehled UIB – cases.html

Stránka načítá incidenty asynchronně přes `GET /api/v1/cases/` a renderuje je pomocí DataTables.

### Pořadí sloupců

| Index | Sloupec | Popis |
|-------|---------|-------|
| 0 | Vytvořeno | Datum a čas vytvoření (`created_at`) |
| 1 | Stav | Badge se stavem (`open`, `in_progress`, `on_hold`, `closed`) |
| 2 | ID | Case ID ve formátu `UIB-DDMMYYYY-HHMM-RRRR` |
| 3 | Popis události | Hodnota pole `case_title` z hlavičky formuláře |
| 4 | Šablona | Název playbooku |
| 5 | Koordinátor | Hodnota pole `incident_coordinator` z hlavičky |
| 6 | Zámek | Kdo má incident otevřený (`locked_by`) |
| 7 | *(skrytý)* | Priorita stavu pro řazení (1–4) |
| 8 | Akce | Tisk, Otevřít, admin: Odemknout/Smazat |

### Řazení

Primární: sloupec 7 (priorita stavu) ASC → aktivní incidenty nahoře.
Sekundární: sloupec 0 (datum) DESC → nejnovější první v rámci stejného stavu.

| Stav | Priorita |
|------|----------|
| Přiřazeno (`open`) | 1 |
| V řešení (`in_progress`) | 2 |
| Pozastaveno (`on_hold`) | 3 |
| Uzavřený (`closed`) | 4 |

### Filtry

Tlačítka nad tabulkou volají `dt.column(1).search(regex)` – filtrují DataTables column 1 (Stav) pomocí regulárního výrazu `^Label$`.

---

## Detail UIB – case_detail.html

Stránka načítá incident přes `GET /api/v1/cases/{case_id}` a renderuje sekce formuláře pomocí `app/static/js/case_form.js`.

### Zámek a read-only mode

| Stav | Chování |
|------|---------|
| Incident odemčen | Stránka automaticky požádá o zámek (`POST /lock`) |
| Zamčeno mnou | Formulář je editovatelný, zobrazí se banner s informací |
| Zamčeno jiným | Formulář je read-only (`setReadOnly(true)`) |

Tlačítko **Uložit** uloží data a ponechá zámek (uživatel zůstane na stránce).
Tlačítko **Uložit a odejít** uloží data, uvolní zámek (`DELETE /lock`) a přesměruje na seznam.

### Auto-save

Změna pole `status` (select stavu) spouští okamžité uložení přes `PATCH /api/v1/cases/{case_id}` – bez nutnosti kliknout Uložit.

---

## Statické soubory

```
app/static/
├── css/
│   └── custom.css          – vlastní styly (app-shell, sidebar, filtry, badge, tabulky)
├── js/
│   ├── main.js             – apiFetch() helper (přidává cookie + X-Requested-With hlavičku)
│   └── case_form.js        – renderer sekcí UIB (playbook_header, checklist, action_table, ...)
└── vendor/                 – staženo přes scripts/download_vendors.py
    ├── bootstrap/
    ├── bootstrap-icons/
    ├── jquery/
    ├── datatables/
    └── ace/                – Ace Editor (template_editor.html)
```

---

## Web routes – přehled

| URL | Šablona | Auth |
|-----|---------|------|
| `/` | — | přesměrování na `/dashboard` nebo `/login` |
| `/login` | `login.html` | — |
| `/logout` | — | — (smaže cookie) |
| `/dashboard` | `dashboard.html` | ✓ |
| `/cases` | `cases.html` | ✓ |
| `/cases/{case_id}` | `case_detail.html` | ✓ |
| `/cases/{case_id}/print` | `case_detail.html` (print_mode=True) | ✓ |
| `/templates` | `templates_list.html` | ✓ |
| `/templates/new` | `template_editor.html` | admin |
| `/templates/{id}/edit` | `template_editor.html` | admin |
| `/settings` | `settings.html` | admin |
| `/admin/users` | `admin_users.html` | admin |
