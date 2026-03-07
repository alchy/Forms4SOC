# case_form.js – Developer Reference

`app/static/js/case_form.js` je čistě front-endový renderer JSON dokumentu incidentu do interaktivního HTML formuláře. Soubor nemá žádné externí závislosti (jen Bootstrap 5 CSS pro styly) a je možné ho přenést do jiného projektu s minimálními úpravami.

---

## Architektura

```
Backend (REST API)
    │  JSON dokument incidentu
    ▼
renderSections(sections, container)
    │  pro každou sekci → renderSection(section)
    ▼
switch(section.type) → render*() funkce
    │  sestaví DOM elementy (nikoli HTML string)
    ▼
Live binding: user input → mutace JS objektu → Uložit → JSON → API
```

Celý dokument incidentu je jeden velký JS objekt v paměti. Každý vstupní prvek při změně zapíše novou hodnotu přímo do tohoto objektu (`field.value = inp.value`). Při uložení se objekt serializuje přes `JSON.stringify` a odešle na backend. **DOM a datový objekt jsou vždy synchronní.**

---

## Integrace v jiném projektu

Potřebné závislosti:

```html
<!-- Bootstrap 5 CSS (styly) -->
<link rel="stylesheet" href="bootstrap.min.css">
<link rel="stylesheet" href="bootstrap-icons.min.css">

<!-- Bootstrap 5 JS (accordion) -->
<script src="bootstrap.bundle.min.js"></script>

<!-- Renderer -->
<script src="case_form.js"></script>
```

Minimální inicializace:

```javascript
// caseDocument = JSON objekt vrácený z API (struktura viz níže)
const container = document.getElementById('form-container');
renderSections(caseDocument.sections, container);

// Po uložení:
const payload = JSON.stringify(caseDocument);
```

---

## Struktura JSON dokumentu

```jsonc
{
  "case_id": "UIB-06032026-0954-3712",
  "template_id": "phishing_v2",
  "template_name": "Phishing v2",
  "status": "open",
  "sections": [ /* viz Typy sekcí níže */ ]
}
```

---

## Typy sekcí

Každá sekce má povinná pole `id`, `type`, `title`. Ostatní pole jsou volitelná a závisí na typu.

### `workbook_header`

Hlavička formuláře. Editovatelná pole jsou zobrazena prominentně nahoře, read-only pole jako kompaktní info grid pod čarou.

```jsonc
{
  "id": "header",
  "type": "workbook_header",
  "title": "Základní informace",
  "fields": [ /* viz Typy polí */ ]
}
```

### `form`

Obecný formulář. Pole jsou zobrazena jako dvousloupcový grid (label + input).

```jsonc
{
  "id": "evidence",
  "type": "form",
  "title": "Důkazy",
  "fields": [ /* viz Typy polí */ ]
}
```

### `closure_form`

Sémanticky odlišená forma uzavření (stejný rendering jako `form`), volitelně zobrazí informační box nad formulářem.

```jsonc
{
  "id": "closure",
  "type": "closure_form",
  "title": "Uzavření incidentu",
  "hint": "Vyplňte po uzavření.",
  "fields": [ /* viz Typy polí */ ]
}
```

### `classification`

Panel MITRE ATT&CK. Read-only pole (taktika, technika) jako info grid; editovatelná pole (sub-technika) jako form; klíč `data_sources` jako badge seznam.

```jsonc
{
  "id": "classification",
  "type": "classification",
  "title": "MITRE ATT&CK",
  "fields": [
    { "key": "tactic",        "label": "Taktika",     "type": "text",   "editable": false, "value": "Initial Access" },
    { "key": "technique",     "label": "Technika",    "type": "text",   "editable": false, "value": "T1566" },
    { "key": "sub_technique", "label": "Sub-technika","type": "select", "editable": true,
      "options": ["T1566.001", "T1566.002"], "value": null },
    { "key": "data_sources",  "label": "Data sources","type": "text",   "editable": false,
      "value": ["Email Gateway", "Proxy"] }
  ]
}
```

### `contact_table`

Tabulka kontaktů. Šablonové řádky mají část sloupců editovatelných; analytik může přidávat vlastní řádky.

```jsonc
{
  "id": "contacts",
  "type": "contact_table",
  "title": "Kontakty",
  "columns": ["role", "name", "phone", "note"],
  "column_labels": { "role": "Role", "name": "Jméno", "phone": "Telefon", "note": "Poznámka" },
  "editable_columns": ["note"],
  "allow_append": true,
  "append_row_template": { "role": null, "name": null, "phone": null, "note": null },
  "rows": [
    { "role": "CISO", "name": "Jan Novák", "phone": "+420 123 456 789", "note": null }
  ]
}
```

Pole `analyst_added: true` na řádku znamená, že ho přidal analytik – takový řádek je plně editovatelný a lze ho smazat.

### `assets_table`

Tabulka dotčených aktiv. Všechny buňky editovatelné; sloupce s `column_options` renderovány jako `<select>`.

```jsonc
{
  "id": "assets",
  "type": "assets_table",
  "title": "Dotčená aktiva",
  "hint": "Zahrňte všechna dotčená zařízení.",
  "columns": ["hostname", "ip", "type", "severity"],
  "column_labels": { "hostname": "Hostname", "ip": "IP adresa", "type": "Typ", "severity": "Závažnost" },
  "column_options": {
    "type":     ["Server", "Workstation", "Network device"],
    "severity": ["critical", "high", "medium", "low"]
  },
  "rows": []
}
```

### `action_table`

Tabulka akcí odezvy. Šablonové řádky (akce) mají editovatelný sloupec stavu; analytik může přidávat i mazat řádky.

```jsonc
{
  "id": "response",
  "type": "action_table",
  "title": "Akce odezvy",
  "columns": ["action", "status", "owner"],
  "column_labels": { "action": "Akce", "status": "Stav", "owner": "Zodpovídá" },
  "editable_columns": ["status"],
  "status_options": ["Čeká", "Probíhá", "Hotovo", "N/A"],
  "allow_append": true,
  "allow_delete": false,
  "append_row_template": { "action": null, "status": null, "owner": null },
  "hints": ["Akce vyplňte neprodleně po detekci."],
  "rows": [
    { "action": "Izolovat stanici", "status": null, "owner": null }
  ]
}
```

### `notification_table`

Shodná logika s `action_table` – pouze jiná data šablony. Renderer volá `renderActionTable` interně.

### `checklist`

Kontrolní seznam kroků organizovaných do skupin. Každý krok má checkbox a textové pole pro poznámku analytika.

```jsonc
{
  "id": "playbook",
  "type": "checklist",
  "title": "Postup vyšetřování",
  "step_groups": [
    {
      "title": "Triáž",
      "note": "max. 30 min",
      "hints": ["Ověřte autenticitu e-mailu před dalším krokem."],
      "classification_hints": ["True Positive: doménový spoofing detekován."],
      "steps": [
        {
          "id": "step-01",
          "action": "Stáhněte hlavičky e-mailu a analyzujte SPF/DKIM/DMARC.",
          "example": "Poznámka analytika...",
          "done": false,
          "analyst_note": null
        }
      ]
    }
  ],
  "result": {
    "title": "Výsledek triáže",
    "notifications": [
      { "condition": "True Positive", "actions": ["Eskalovat na L2", "Otevřít MIM"] }
    ],
    "fields": [ /* viz Typy polí */ ]
  }
}
```

`result` je volitelný blok na konci checklistu – zobrazí notifikační instrukce a formulářová pole výsledku.

`notifications` může být buď pole objektů `{ condition, actions[] }` (jako výše), nebo prosté pole stringů.

### `section_group`

Accordion kontejner sdružující více podsekci (`form` nebo `assets_table`). První podsekce je výchozně otevřena.

```jsonc
{
  "id": "forensics",
  "type": "section_group",
  "title": "Forenzní analýza",
  "subsections": [
    {
      "id": "email",
      "type": "form",
      "title": "E-mailová analýza",
      "always_expanded": false,
      "note": "volitelné",
      "fields": [ /* viz Typy polí */ ]
    }
  ]
}
```

`always_expanded: true` zobrazí podsekci bez možnosti sbalení (statický nadpis).

### `raci_table`

Read-only RACI tabulka. Buňky obsahující `"R"` jsou zvýrazněny červeně.

```jsonc
{
  "id": "raci",
  "type": "raci_table",
  "title": "RACI",
  "legend": "R=Responsible, A=Accountable, C=Consulted, I=Informed",
  "columns": ["role", "detection", "containment"],
  "column_labels": { "role": "Role", "detection": "Detekce", "containment": "Izolace" },
  "rows": [
    { "role": "SOC Analyst L1", "detection": "R", "containment": "C" }
  ]
}
```

---

## Typy polí (`fields[]`)

Každé pole má povinná klíče `key`, `label`, `type`, `editable`, `value`.

| Klíč | Typ | Popis |
|------|-----|-------|
| `key` | string | Unikátní identifikátor pole v rámci sekce |
| `label` | string | Popisek zobrazený v UI |
| `type` | `text` \| `textarea` \| `select` \| `datetime` | Typ vstupního prvku |
| `editable` | bool | `false` → zobrazí se jako read-only text |
| `value` | any \| null | Aktuální hodnota; `null` = nevyplněno |
| `example` | string | Placeholder text ve vstupu |
| `hint` | string | Nápověda zobrazená pod labelem |
| `options` | string[] | Seznam možností pro `type: select` |
| `option_hints` | `{opt: hint}` | Nápověda pod selectem pro konkrétní vybranou možnost |
| `auto_value` | string | `"case_id"` → backend automaticky vyplní hodnotu při vytvoření |

Příklady:

```jsonc
{ "key": "case_title",  "label": "Název případu", "type": "text",
  "editable": true, "value": null, "example": "Phishing na uživatele X" }

{ "key": "severity", "label": "Závažnost", "type": "select",
  "editable": true, "value": "high",
  "options": ["critical", "high", "medium", "low"],
  "option_hints": { "critical": "Kritický dopad na provoz" } }

{ "key": "detected_at", "label": "Čas detekce", "type": "datetime",
  "editable": true, "value": "2026-03-07T09:54" }

{ "key": "description", "label": "Popis", "type": "textarea",
  "editable": true, "value": null }

{ "key": "case_id", "label": "ID případu", "type": "text",
  "editable": false, "value": "UIB-07032026-0954-3712", "auto_value": "case_id" }
```

---

## API funkcí

### Render pipeline

| Funkce | Parametry | Popis |
|--------|-----------|-------|
| `renderSections(sections, container)` | `sections: array`, `container: HTMLElement` | Vstupní bod – vymaže kontejner a naplní ho vyrenderovanými sekcemi |
| `renderSection(section)` | `section: object` | Obalí obsah do karty a dispatchne na příslušný `render*` |
| `renderForm(fields)` | `fields: array` | Dvousloupcový grid label + input |
| `renderWorkbookHeader(section)` | `section: object` | Hlavička s editovatelnými poli nahoře a info gridem dole |
| `renderClassification(section)` | `section: object` | MITRE panel: info grid + editable select + badge seznam |
| `renderContactTable(section)` | `section: object` | Tabulka kontaktů s inline edity |
| `renderAssetsTable(section)` | `section: object` | Tabulka aktiv se selecty a inline edity |
| `renderActionTable(section)` | `section: object` | Tabulka akcí se stavovým selectem |
| `renderNotificationTable(section)` | `section: object` | Alias pro `renderActionTable` |
| `renderChecklist(section)` | `section: object` | Skupiny kroků s checkboxy a textarea |
| `renderSectionGroup(section)` | `section: object` | Bootstrap accordion pro podsekce |
| `renderRaciTable(section)` | `section: object` | Read-only tabulka s R-highlighting |
| `renderFieldInput(field)` | `field: object` | Vrátí odpovídající DOM vstupní prvek pro pole |

### Helper funkce

| Funkce | Parametry | Popis |
|--------|-----------|-------|
| `el(tag, cls, html)` | `tag: string`, `cls?: string`, `html?: string` | Factory pro DOM element; `html` je automaticky sanitizováno |
| `setHTML(element, html)` | `element: HTMLElement`, `html: string` | Bezpečné přiřazení innerHTML přes `sanitizeHTML` |
| `sanitizeHTML(html)` | `html: string` | DOMParser sandbox – odstraní script/iframe/on* atributy |
| `buildTableHead(columns, columnLabels, extraCol)` | `columns: string[]`, `columnLabels?: object`, `extraCol?: bool` | Sestaví `<thead>`; `extraCol=true` přidá prázdný sloupec pro akce |
| `makeDeleteBtn(onClick)` | `onClick: function` | Tlačítko smazat (ikona koše) s navázaným callbackem |
| `renderFieldRow(field, labelCls, rowMb)` | `field: object`, `labelCls?: string`, `rowMb?: string` | Bootstrap grid řádek label + input; výchozí: `'form-label text-secondary small mb-0'`, `'mb-2'` |
| `renderInfoGrid(fields, colCls, gridCls)` | `fields: array`, `colCls?: string`, `gridCls?: string` | Grid read-only polí (label + hodnota); výchozí: `'col-md-4 col-lg-3'`, `'row g-2'` |
| `buildOptions(sel, options, currentValue)` | `sel: HTMLSelectElement`, `options: string[]`, `currentValue: any` | Přidá `<option>` elementy a označí vybranou hodnotu |

---

## Rozšíření – přidání nového typu sekce

1. Napište render funkci:

```javascript
function renderMySection(section) {
    const wrap = el('div');
    // ... sestavení DOM ...
    return wrap;
}
```

2. Zaregistrujte ji v `renderSection()`:

```javascript
case 'my_section': body.appendChild(renderMySection(section)); break;
```

3. Definujte JSON strukturu sekce a přidejte příklad do šablony.

---

## Bezpečnostní model

Veškerý HTML obsah pocházející z JSON (labely, tituly, hinty, texty kroků) prochází `sanitizeHTML()`, která:

- parsuje HTML v izolovaném `DOMParser` dokumentu (skripty se **nespustí**),
- odstraní elementy `<script>`, `<iframe>`, `<object>`, `<embed>`, `<link>`, `<meta>`,
- odstraní všechny atributy začínající `on` (event handlery) a `href="javascript:"`.

Hodnoty zadané analytikem (`.value` inputů a textarea) **nikdy nevstupují do `innerHTML`** – jsou čteny a zapisovány přes DOM `.value` property, která neparsuje HTML.
