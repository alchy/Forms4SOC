# case_form.js – Průvodce pro nové uživatele

Tento dokument provede prvním setkáním s `case_form.js` – od toho, k čemu knihovna slouží, přes rychlý start, až po tvorbu vlastních formulářů a jejich rozšiřování.

---

## Co je case_form.js a k čemu slouží?

`case_form.js` je klientský renderer, který ze strukturovaného JSON dokumentu sestaví interaktivní HTML formulář přímo v prohlížeči. Nevyžaduje žádný server-side templating – dostane JSON, vykreslí formulář, a po vyplnění vrátí zpět upravený JSON.

Vznikl pro potřeby **Forms4SOC** – webové aplikace pro správu SOC incidentů – kde každý incident je popsán JSON dokumentem s pevnou strukturou (šablonou). Analytik otevře incident v prohlížeči, formulář se automaticky vykreslí podle šablony, analytik data doplní, a uloží. Knihovna se ale neváže na SOC doménu a lze ji použít kdekoli, kde potřebujete renderovat strukturované datové formuláře z JSON.

**Závislosti:** Bootstrap 5 (CSS + JS pro accordion), Bootstrap Icons. Žádné další knihovny.

---

## Jak to funguje?

Princip je záměrně jednoduchý:

```
JSON dokument (sekce s poli)
        │
        ▼
renderSections(sections, container)
        │  pro každou sekci zavolá odpovídající render* funkci
        ▼
DOM elementy (karty, tabulky, inputy, checkboxy...)
        │
        ▼
Analytik edituje pole → změna se okamžitě zapíše zpět do JS objektu
        │
        ▼
Při uložení: JSON.stringify(dokument) → odeslat na backend
```

Klíčová vlastnost: **formulář a datový objekt jsou neustále synchronní.** Každý input, select nebo checkbox má při změně navázaný handler, který přímo mutuje odpovídající hodnotu v JS objektu (`field.value = inp.value`). Při uložení stačí celý objekt serializovat – není třeba formulář ručně číst.

---

## Rychlý start

Minimální stránka, která vykreslí formulář z JSON:

```html
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="vendor/bootstrap/css/bootstrap.min.css">
    <link rel="stylesheet" href="vendor/bootstrap-icons/bootstrap-icons.min.css">
</head>
<body class="container py-4">

    <div id="form-container"></div>

    <button id="save-btn" class="btn btn-primary mt-3">Uložit</button>

    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="case_form.js"></script>
    <script>
        // Dokument přijde z API – zde simulujeme jednoduchý příklad
        const doc = {
            sections: [
                {
                    id: "info",
                    type: "form",
                    title: "Základní informace",
                    fields: [
                        { key: "title",    label: "Název",    type: "text",     editable: true, value: null, example: "Popis události" },
                        { key: "severity", label: "Závažnost",type: "select",   editable: true, value: null, options: ["critical","high","medium","low"] },
                        { key: "notes",    label: "Poznámky", type: "textarea", editable: true, value: null }
                    ]
                }
            ]
        };

        // Vyrenderuj formulář
        renderSections(doc.sections, document.getElementById('form-container'));

        // Po kliknutí Uložit máme aktuální data přímo v doc
        document.getElementById('save-btn').addEventListener('click', () => {
            console.log(JSON.stringify(doc, null, 2));
            // fetch('/api/save', { method: 'POST', body: JSON.stringify(doc), ... })
        });
    </script>
</body>
</html>
```

Po načtení stránky se zobrazí karta s nadpisem „Základní informace" a třemi poli. Po vyplnění a kliknutí Uložit je v `doc.sections[0].fields[*].value` aktuální hodnota od uživatele.

---

## Váš první formulář krok za krokem

### 1. Připravte JSON dokument

Dokument má seznam `sections`. Každá sekce má `id`, `type` a `title`, plus data specifická pro daný typ.

```jsonc
{
  "sections": [
    {
      "id": "header",
      "type": "workbook_header",
      "title": "Incident – základní data",
      "fields": [
        { "key": "case_id",    "label": "ID",        "type": "text", "editable": false, "value": "INC-001" },
        { "key": "case_title", "label": "Název",     "type": "text", "editable": true,  "value": null, "example": "Stručný popis incidentu" },
        { "key": "severity",   "label": "Závažnost", "type": "select", "editable": true, "value": null,
          "options": ["critical","high","medium","low"],
          "option_hints": { "critical": "Přímý dopad na provoz", "high": "Výrazné omezení" } }
      ]
    }
  ]
}
```

### 2. Zavolejte `renderSections`

```javascript
const container = document.getElementById('form-container');
renderSections(document.sections, container);
```

Výsledek: karta s nadpisem „Incident – základní data". Pole `case_id` je zobrazeno jako read-only text (šedě, bez inputu), `case_title` jako textový input s placeholderem, `severity` jako dropdown s nápovědou pod selectem.

### 3. Přečtěte data po vyplnění

Protože formulář mutuje přímo objekt `document`, stačí po uložení:

```javascript
const dataToSend = JSON.stringify(document);
```

Není třeba procházet DOM a číst hodnoty inputů – jsou vždy zapsány zpět do JS objektu.

### 4. Přidejte další sekce

Sekce se přidávají jednoduše do pole `sections`. Každá se vykreslí jako samostatná karta pod sebou:

```jsonc
{
  "sections": [
    { "id": "header",   "type": "workbook_header", ... },
    { "id": "evidence", "type": "form",             "title": "Důkazy", "fields": [...] },
    { "id": "assets",   "type": "assets_table",     "title": "Dotčená aktiva", ... },
    { "id": "playbook", "type": "checklist",         "title": "Postup vyšetřování", ... }
  ]
}
```

---

## Přehled typů sekcí

### Formulář (`form`, `closure_form`)

Nejjednodušší sekce. Pole jsou zobrazena jako dvousloupcový grid – label vlevo, input vpravo. `closure_form` je totožná, ale může mít volitelný informační box nahoře (klíč `hint`).

```jsonc
{
  "id": "details",
  "type": "form",
  "title": "Detaily incidentu",
  "fields": [
    { "key": "source_ip",   "label": "Zdrojová IP",   "type": "text",     "editable": true, "value": null },
    { "key": "detected_at", "label": "Čas detekce",   "type": "datetime", "editable": true, "value": null },
    { "key": "description", "label": "Popis",          "type": "textarea", "editable": true, "value": null }
  ]
}
```

### Hlavička (`workbook_header`)

Speciální varianta formuláře určená pro úvodní kartu incidentu. Read-only pole (jako `case_id` nebo verze šablony) jsou zobrazena kompaktně jako info-grid pod čarou; editovatelná pole jsou viditelná prominentněji nahoře.

```jsonc
{
  "id": "header",
  "type": "workbook_header",
  "title": "Základní informace",
  "fields": [
    { "key": "case_title", "label": "Název incidentu", "type": "text",  "editable": true,  "value": null },
    { "key": "case_id",    "label": "ID případu",       "type": "text",  "editable": false, "value": "INC-001" },
    { "key": "template",   "label": "Šablona",          "type": "text",  "editable": false, "value": "Phishing v2" }
  ]
}
```

### Kontaktní tabulka (`contact_table`)

Tabulka pro eskalační kontakty. Část sloupců je editovatelná inline (bez ohraničení, průhledné pozadí). Analytik může přidávat vlastní řádky přes tlačítko „Přidat řádek", pokud je `allow_append: true`. Šablonové řádky (předdefinované kontakty) nelze smazat.

```jsonc
{
  "id": "contacts",
  "type": "contact_table",
  "title": "Eskalační kontakty",
  "columns": ["role", "name", "phone", "note"],
  "column_labels": { "role": "Role", "name": "Jméno", "phone": "Telefon", "note": "Poznámka" },
  "editable_columns": ["note"],
  "allow_append": true,
  "append_row_template": { "role": null, "name": null, "phone": null, "note": null },
  "rows": [
    { "role": "CISO", "name": "Jan Novák", "phone": "+420 111 222 333", "note": null }
  ]
}
```

### Tabulka aktiv (`assets_table`)

Tabulka dotčených systémů a zařízení. Všechny buňky jsou editovatelné. Sloupce uvedené v `column_options` se zobrazí jako dropdown; ostatní jako volný textový vstup. Analytik může přidávat i mazat řádky.

```jsonc
{
  "id": "assets",
  "type": "assets_table",
  "title": "Dotčená aktiva",
  "hint": "Zahrňte všechna kompromitovaná zařízení.",
  "columns": ["hostname", "ip", "type", "severity"],
  "column_labels": { "hostname": "Hostname", "ip": "IP", "type": "Typ", "severity": "Závažnost" },
  "column_options": {
    "type":     ["Server", "Workstation", "Network device", "Cloud"],
    "severity": ["critical", "high", "medium", "low"]
  },
  "rows": []
}
```

### Tabulka akcí (`action_table`, `notification_table`)

Předdefinovaný seznam akcí odezvy. Analytik mění stav každé akce z dropdown seznamu (`status_options`). Může přidávat vlastní akce (`allow_append`) a mazat řádky (`allow_delete`). `notification_table` je identická sekce – rozdíl je jen v datech šablony (používá se pro sledování notifikací namísto akcí).

```jsonc
{
  "id": "response_actions",
  "type": "action_table",
  "title": "Akce odezvy",
  "columns": ["action", "owner", "status"],
  "column_labels": { "action": "Akce", "owner": "Zodpovídá", "status": "Stav" },
  "editable_columns": ["status"],
  "status_options": ["Čeká", "Probíhá", "Hotovo", "N/A"],
  "allow_append": true,
  "allow_delete": false,
  "append_row_template": { "action": null, "owner": null, "status": null },
  "hints": ["Stav průběžně aktualizujte."],
  "rows": [
    { "action": "Izolovat kompromitovanou stanici", "owner": null, "status": null },
    { "action": "Resetovat přihlašovací údaje",     "owner": null, "status": null }
  ]
}
```

### Checklist (`checklist`)

Krok-za-krokem průvodce vyšetřováním. Kroky jsou organizovány do pojmenovaných skupin. Každý krok má:
- **checkbox** – označení hotovo / hotovo
- **textové pole** – poznámka analytika k danému kroku
- **hints** – provozní nápovědy (šedé boxy)
- **classification_hints** – vodítka True/False Positive (žluté boxy)

Na konci checklistu může být volitelný blok `result` s notifikacemi a formulářovými poli výsledku.

```jsonc
{
  "id": "investigation",
  "type": "checklist",
  "title": "Postup vyšetřování",
  "step_groups": [
    {
      "title": "1. Triáž",
      "note": "max. 15 minut",
      "hints": ["Před zahájením ověřte dostupnost logů v SIEM."],
      "classification_hints": ["Pokud SPF/DKIM/DMARC selhal → pravděpodobně True Positive."],
      "steps": [
        {
          "id": "s01",
          "action": "Stáhněte hlavičky e-mailu a ověřte SPF/DKIM/DMARC záznamy.",
          "example": "Sem zapište výsledek analýzy...",
          "done": false,
          "analyst_note": null
        },
        {
          "id": "s02",
          "action": "Zkontrolujte odesílatele vůči blacklistům.",
          "example": "",
          "done": false,
          "analyst_note": null
        }
      ]
    }
  ],
  "result": {
    "title": "Výsledek triáže",
    "notifications": [
      { "condition": "True Positive", "actions": ["Eskalovat na L2", "Zahájit MIM"] },
      { "condition": "False Positive", "actions": ["Uzavřít jako FP", "Informovat uživatele"] }
    ],
    "fields": [
      { "key": "verdict", "label": "Verdikt", "type": "select", "editable": true, "value": null,
        "options": ["True Positive", "False Positive", "Nerozhodné"] }
    ]
  }
}
```

### Accordion skupin (`section_group`)

Sdružuje více podsekci do Bootstrap accordionu. Každá podsekce je samostatný skládací panel. První podsekce je výchozně otevřena. Podsekce mohou být typu `form` nebo `assets_table`. Chcete-li podsekci trvale otevřenou (bez možnosti sbalení), nastavte `always_expanded: true`.

```jsonc
{
  "id": "forensics",
  "type": "section_group",
  "title": "Forenzní analýza",
  "subsections": [
    {
      "id": "email_analysis",
      "type": "form",
      "title": "E-mailová analýza",
      "note": "vyplňte pokud je relevantní",
      "fields": [
        { "key": "email_sender",  "label": "Odesílatel",    "type": "text",     "editable": true, "value": null },
        { "key": "email_subject", "label": "Předmět",       "type": "text",     "editable": true, "value": null },
        { "key": "email_body",    "label": "Obsah / popis", "type": "textarea", "editable": true, "value": null }
      ]
    },
    {
      "id": "ioc",
      "type": "assets_table",
      "title": "Indikátory kompromitace (IOC)",
      "always_expanded": true,
      "columns": ["type", "value", "note"],
      "column_labels": { "type": "Typ", "value": "Hodnota", "note": "Poznámka" },
      "column_options": { "type": ["IP", "Domain", "Hash", "URL", "Email"] },
      "rows": []
    }
  ]
}
```

### RACI tabulka (`raci_table`)

Pouze pro čtení. Zobrazuje matici odpovědností. Buňky obsahující `"R"` (Responsible) jsou zvýrazněny tučně červeně.

```jsonc
{
  "id": "raci",
  "type": "raci_table",
  "title": "RACI – odpovědnosti",
  "legend": "R=Responsible, A=Accountable, C=Consulted, I=Informed",
  "columns": ["role", "detection", "containment", "eradication", "reporting"],
  "column_labels": {
    "role": "Role", "detection": "Detekce", "containment": "Izolace",
    "eradication": "Odstranění", "reporting": "Reporting"
  },
  "rows": [
    { "role": "SOC L1",  "detection": "R",   "containment": "C", "eradication": "I", "reporting": "I" },
    { "role": "SOC L2",  "detection": "A",   "containment": "R", "eradication": "R", "reporting": "C" },
    { "role": "CISO",    "detection": "I",   "containment": "I", "eradication": "A", "reporting": "R" }
  ]
}
```

---

## Typy polí – přehled

| `type` | Widget | Popis |
|--------|--------|-------|
| `text` | `<input type="text">` | Jednořádkový textový vstup |
| `textarea` | `<textarea>` | Víceřádkový textový vstup |
| `select` | `<select>` | Dropdown ze seznamu `options` |
| `datetime` | `<input type="datetime-local">` | Výběr data a času |
| *(libovolný)* | `<input type="text">` | Neznámý typ se chová jako `text` |

Každé pole má povinné klíče `key`, `label`, `type`, `editable`, `value`. Volitelné klíče:

| Klíč | Popis |
|------|-------|
| `example` | Placeholder text ve vstupu |
| `hint` | Nápověda zobrazená pod labelem |
| `options` | Seznam možností pro typ `select` |
| `option_hints` | Nápověda pod selectem pro konkrétní možnost: `{ "high": "Výrazné omezení" }` |
| `auto_value` | `"case_id"` → backend vyplní automaticky při vytvoření případu |

Pokud je `editable: false`, pole se zobrazí jako read-only text (šedě, bez inputu). Hodnota `null` znamená nevyplněno.

---

## Ukládání dat

Po vyplnění formuláře analytik klikne Uložit. V tento moment stačí serializovat celý datový objekt – `field.value` hodnoty jsou vždy aktuální:

```javascript
async function saveCase(caseDocument) {
    const resp = await fetch(`/api/v1/cases/${caseDocument.case_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseDocument)
    });
    if (!resp.ok) throw new Error('Uložení selhalo');
}
```

Nemusíte procházet DOM a číst hodnoty inputů – to by byla chyba. Veškerá data jsou živá v JS objektu od okamžiku, kdy uživatel pole změnil.

---

## Přidání vlastního typu sekce

Pokud potřebujete sekci, která neodpovídá žádnému existujícímu typu, přidejte ji ve dvou krocích:

**1. Napište render funkci:**

```javascript
function renderTimelineSection(section) {
    const wrap = el('div');
    (section.events || []).forEach(event => {
        const row = el('div', 'd-flex gap-3 mb-2');
        const time = el('div', 'text-muted small', event.time);
        const desc = el('div', '', event.description);
        row.appendChild(time);
        row.appendChild(desc);
        wrap.appendChild(row);
    });
    return wrap;
}
```

**2. Zaregistrujte ji v `renderSection()` (v souboru `case_form.js`):**

```javascript
case 'timeline': body.appendChild(renderTimelineSection(section)); break;
```

**3. Použijte v JSON šabloně:**

```jsonc
{
  "id": "timeline",
  "type": "timeline",
  "title": "Časová osa",
  "events": [
    { "time": "09:14", "description": "Phishingový e-mail přijat" },
    { "time": "09:47", "description": "Uživatel kliknul na odkaz" }
  ]
}
```

---

## Bezpečnostní model

Veškerý HTML obsah pocházející z JSON (labely, tituly, hinty, texty kroků) prochází funkcí `sanitizeHTML()` před vložením do DOM. Tato funkce:

- parsuje HTML v izolovaném `DOMParser` dokumentu – skripty a styly se v tomto kontextu **nespustí**,
- odstraní elementy `<script>`, `<iframe>`, `<object>`, `<embed>`, `<link>`, `<meta>`,
- odstraní všechny atributy začínající `on` (tj. `onclick`, `onmouseover` apod.) a `href="javascript:"`.

Hodnoty zadané analytikem (obsah inputů a textarea) **nikdy nevstupují do `innerHTML`** – jsou čteny a zapisovány přes DOM `.value` property, která HTML neparsuje. Není tedy potřeba sanitizovat analytikovy vstupy na straně frontendu.

---

## Portabilita a použití jako knihovna

V současné podobě jsou všechny funkce `case_form.js` globální (v `window`). Pro použití jako přenositelná knihovna ve více projektech existují dvě snadné cesty:

**Varianta A – namespace objekt (minimální změna):**

Celý soubor se zabalí do IIFE a vystaví jediný globální objekt:

```javascript
const CaseForm = (() => {
    // ... všechny interní funkce ...

    // Veřejné API
    return {
        render: renderSections,
        registerRenderer: (type, fn) => { renderers[type] = fn; }
    };
})();

// Použití:
CaseForm.render(doc.sections, container);
CaseForm.registerRenderer('timeline', renderTimelineSection);
```

**Varianta B – ES modul (moderní přístup):**

```javascript
// case_form.js
export function render(sections, container) { ... }
export function registerRenderer(type, fn) { ... }

// Použití v jiném projektu:
import { render } from './case_form.js';
render(doc.sections, container);
```

Klíčová změna pro oba přístupy: nahrazení `switch(section.type)` v `renderSection()` slovníkem rendererů (`Map` nebo prostý objekt), do kterého lze přidávat externí renderery bez úpravy souboru knihovny:

```javascript
const renderers = {
    form:          renderForm,
    workbook_header: renderWorkbookHeader,
    // ... ostatní built-in renderery ...
};

function renderSection(section) {
    const renderFn = renderers[section.type];
    body.appendChild(renderFn ? renderFn(section) : renderFallback(section));
}

function registerRenderer(type, fn) {
    renderers[type] = fn;
}
```

Tato změna je malá (cca 10 řádků), zpětně kompatibilní, a výrazně usnadňuje rozšiřování bez zásahu do kódu knihovny.

---

## Přehled veřejných funkcí

| Funkce | Popis |
|--------|-------|
| `renderSections(sections, container)` | Hlavní vstupní bod – vykreslí sekce do kontejneru |
| `renderSection(section)` | Vykreslí jednu sekci jako kartu |
| `renderForm(fields)` | Formulář z pole polí |
| `renderWorkbookHeader(section)` | Hlavička s info gridem |
| `renderClassification(section)` | MITRE ATT&CK panel |
| `renderContactTable(section)` | Kontaktní tabulka |
| `renderAssetsTable(section)` | Tabulka aktiv |
| `renderActionTable(section)` | Tabulka akcí / notifikací |
| `renderChecklist(section)` | Checklist s kroky |
| `renderSectionGroup(section)` | Accordion podsekci |
| `renderRaciTable(section)` | Read-only RACI tabulka |
| `renderFieldInput(field)` | DOM widget pro jedno pole |
| `renderFieldRow(field, labelCls?, rowMb?)` | Grid řádek label + input |
| `renderInfoGrid(fields, colCls?, gridCls?)` | Grid read-only hodnot |
| `buildOptions(sel, options, currentValue)` | Naplnění `<select>` options |
| `sanitizeHTML(html)` | XSS-bezpečná sanitizace HTML stringu |
