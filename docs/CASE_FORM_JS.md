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
CaseForm.render(sections, container)
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
        CaseForm.render(doc.sections, document.getElementById('form-container'));

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

### 2. Zavolejte `CaseForm.render`

```javascript
const container = document.getElementById('form-container');
CaseForm.render(document.sections, container);
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

### Formulář (`form`)

Nejjednodušší sekce. Pole jsou zobrazena jako dvousloupcový grid – label vlevo, input vpravo. Volitelný klíč `hint` zobrazí modrý informační box nad formulářem (vhodné pro uzavírací sekce, varování nebo regulatorní upozornění).

```jsonc
{
  "id": "reported_by",
  "type": "form",
  "title": "Hlášeno osobou",
  "note": "Vyplní SOC Analytik — přeskoč pokud jde o automatizovanou detekci",
  "fields": [
    { "key": "reported_at",         "label": "Datum a čas nahlášení",    "type": "datetime", "editable": true, "value": null },
    { "key": "reporter_name",       "label": "Jméno oznamovatele",        "type": "text",     "editable": true, "value": null, "example": "Jan Novák" },
    { "key": "reporter_department", "label": "Oddělení",                  "type": "text",     "editable": true, "value": null, "example": "Účetní oddělení" },
    { "key": "description",         "label": "Popis slovy oznamovatele",  "type": "textarea", "editable": true, "value": null }
  ]
}
```

Příklad uzavírací sekce s `hint`:

```jsonc
{
  "id": "closure",
  "type": "form",
  "title": "Klasifikace a uzavření",
  "hint": "Před uzavřením ověř, že oznamovatel byl informován o výsledku šetření.",
  "fields": [
    { "key": "final_classification", "label": "Klasifikace výsledku", "type": "select", "editable": true, "value": null,
      "options": ["True Positive", "False Positive", "Benign True Positive"] },
    { "key": "impact_level", "label": "Úroveň dopadu", "type": "select", "editable": true, "value": null,
      "options": ["Nízká", "Střední", "Vysoká", "Kritická"],
      "option_hints": {
        "Vysoká":   "Při zasažení regulované služby zakládá povinnost hlášení NÚKIB.",
        "Kritická": "Vždy Kybernetický bezpečnostní incident (KBI)."
      }},
    { "key": "root_cause",      "label": "Root Cause",               "type": "textarea", "editable": true, "value": null },
    { "key": "actions_taken",   "label": "Přijatá opatření",          "type": "textarea", "editable": true, "value": null },
    { "key": "recommendations", "label": "Doporučení pro zlepšení",   "type": "textarea", "editable": true, "value": null },
    { "key": "closed_at",       "label": "Datum uzavření",            "type": "datetime", "editable": true, "value": null }
  ]
}
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"form"` |
| `title` | ✓ | Nadpis karty |
| `fields[]` | ✓ | Formulářová pole – viz tabulka klíčů polí níže |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `note` | | Metadata (ukládají se do dat; v kartě se nezobrazují – zobrazuje je accordion v `section_group`) |
| `hint` | | HTML text zobrazený jako modrý informační box nad formulářem |

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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"workbook_header"` |
| `title` | ✓ | Nadpis karty |
| `fields[]` | ✓ | Formulářová pole – editovatelná zobrazena prominentně nahoře, read-only jako info grid pod čarou |
| `description` | | Podnadpis v pravé části hlavičky karty |

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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"contact_table"` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky (může být `[]`) |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `editable_columns[]` | | Sloupce inline-editovatelné v šablonových řádcích; ostatní jsou read-only |
| `allow_append` | | `true` → zobrazí tlačítko „Přidat řádek" |
| `append_row_template{}` | ◐ | Povinný pokud `allow_append: true`; vzor prázdného řádku |

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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"assets_table"` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky (může být `[]`) |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `column_options{}` | | `{ sloupec: [možnosti] }` – sloupce renderované jako `<select>` |
| `hint` | | Oranžový výstražný box nad tabulkou |
| `always_expanded` | | Pouze uvnitř `section_group` – `true` = podsekci nelze sbalit |

### Tabulka akcí (`action_table`)

Univerzální tabulka pro akce odezvy i komunikační matice. Analytik mění stav každé akce z dropdown seznamu (`status_options`), nebo edituje sloupce volným textem (bez `status_options`). Může přidávat vlastní řádky (`allow_append`) a mazat řádky (`allow_delete`).

Příklad tabulky akcí odezvy (se stavovým dropdownem):

```jsonc
{
  "id": "response_actions",
  "type": "action_table",
  "title": "Akce odezvy",
  "columns": ["action", "responsible_role", "cooperation", "status"],
  "column_labels": { "action": "Akce", "responsible_role": "Zodpovědná role", "cooperation": "Součinnost", "status": "Stav" },
  "editable_columns": ["status"],
  "status_options": ["Provedeno", "Probíhá", "Čeká", "N/A", "Není nutné provést"],
  "allow_append": true,
  "allow_delete": true,
  "append_row_template": { "action": null, "responsible_role": null, "cooperation": null, "status": null },
  "hints": ["Pokud akce není relevantní, napiš N/A."],
  "rows": [
    { "action": "Počítač izolován od sítě",             "responsible_role": "SOC Analytický tým", "cooperation": "Správce AV/EDR", "status": null },
    { "action": "Blokována doména odesílatele na mail serveru", "responsible_role": "SOC Analytický tým", "cooperation": "Správce Exchange", "status": null }
  ]
}
```

Příklad komunikační matice (bez stavového dropdownu – volný textový vstup):

```jsonc
{
  "id": "communication",
  "type": "action_table",
  "title": "Komunikace a notifikace",
  "columns": ["recipient", "communication_method", "sla", "note"],
  "column_labels": { "recipient": "Příjemce", "communication_method": "Způsob", "sla": "SLA", "note": "Poznámka / stav" },
  "editable_columns": ["note"],
  "hints": [
    "SLA je orientační – vždy ověř požadavky dle platné legislativy (NIS2, GDPR).",
    "Oznamovatele informuj vždy, bez ohledu na výsledek klasifikace."
  ],
  "rows": [
    { "recipient": "Vlastník dotčeného aktiva", "communication_method": "E-mail / telefon", "sla": "Do 30 min od Posouzení", "note": null },
    { "recipient": "CISO / Management",         "communication_method": "E-mail / telefon", "sla": "Do 1 h (High / Critical)", "note": null },
    { "recipient": "Oznamovatel události",       "communication_method": "E-mail / telefon", "sla": "Po uzavření incidentu", "note": null }
  ]
}
```

> Pokud `status_options` není definováno, sloupce v `editable_columns` se renderují jako volný textový vstup místo dropdownu.

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"action_table"` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky |
| `editable_columns[]` | ✓ | Sloupce editovatelné analytikem |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `status_options[]` | | Pokud definováno, `editable_columns` se renderují jako dropdown; jinak volný textový vstup |
| `allow_append` | | `true` → tlačítko „Přidat akci" |
| `allow_delete` | | `true` → tlačítko Smazat u všech řádků (nejen analytikových) |
| `append_row_template{}` | ◐ | Povinný pokud `allow_append: true`; vzor prázdného řádku |
| `hints[]` | | Informační texty zobrazené pod tabulkou |

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
      "id": "triage",
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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"checklist"` |
| `title` | ✓ | Nadpis karty |
| `step_groups[]` | ✓ | Skupiny kroků |
| `step_groups[].id` | ✓ | Identifikátor skupiny |
| `step_groups[].title` | ✓ | Nadpis skupiny |
| `step_groups[].steps[]` | ✓ | Kroky skupiny |
| `steps[].id` | ✓ | Identifikátor kroku |
| `steps[].action` | ✓ | Text kroku (HTML bezpečně sanitizován) |
| `steps[].done` | ✓ | Výchozí stav checkboxu – vždy `false` v šabloně |
| `steps[].analyst_note` | ✓ | Výchozí poznámka – vždy `null` v šabloně |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `step_groups[].note` | | Šedý podnadpis za nadpisem skupiny |
| `step_groups[].hints[]` | | Šedé informační boxy (operační nápovědy) |
| `step_groups[].classification_hints[]` | | Žluté boxy s klasifikačními vodítky True/False Positive |
| `steps[].example` | | Placeholder v textarea poznámky analytika |
| `steps[].is_example` | | `true` → `analyst_note` je placeholder, smaže se při klonování |
| `result{}` | | Blok výsledku na konci checklistu |
| `result.title` | ◐ | Povinný pokud `result` definován |
| `result.fields[]` | ◐ | Formulářová pole výsledku – povinný pokud `result` definován |
| `result.notifications[]` | | `string[]` nebo `[{ condition, actions[] }]` |

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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"section_group"` |
| `title` | ✓ | Nadpis karty |
| `subsections[]` | ✓ | Seznam podsekci (accordion panely) |
| `subsections[].id` | ✓ | Identifikátor podsekce |
| `subsections[].type` | ✓ | `"form"` nebo `"assets_table"` |
| `subsections[].title` | ✓ | Nadpis accordion panelu |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `subsections[].note` | | Šedý text vpravo od nadpisu panelu |
| `subsections[].always_expanded` | | `true` = panel nelze sbalit (statický nadpis, vždy otevřen) |

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

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce |
| `type` | ✓ | `"raci_table"` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky |
| `description` | | Podnadpis v pravé části hlavičky karty |
| `legend` | | Text popisující zkratky R/A/C/I, zobrazen nad tabulkou |

> Buňky, jejichž hodnota obsahuje podřetězec `"R"`, jsou zvýrazněny tučně červeně – tzn. i hodnota `"R, A"` se zvýrazní.

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
| `hint` | Nápověda zobrazená pod labelem (nikdy jako placeholder) |
| `options` | Seznam možností pro typ `select` – povinný pokud `type: "select"` |
| `option_hints` | Nápověda pod selectem pro konkrétní možnost: `{ "high": "Výrazné omezení" }` |
| `auto_value` | Backend vyplní automaticky: `"case_id"`, `"template_name"`, `"template_version"`, `"template_status"`, `"template_mitre_tactic"`, `"template_mitre_technique"`, `"template_data_sources"` |
| `is_example` | `true` → hodnota z šablony se zobrazí jako placeholder; při klonování do nového případu se vymaže (pole zůstane prázdné) |

Pokud je `editable: false`, pole se zobrazí jako read-only text (šedě, bez inputu). Hodnota `null` znamená nevyplněno.

---

## Povinné a volitelné klíče

Rychlá reference pro tvorbu JSON šablon. ✓ = povinné, prázdno = volitelné.

### Společné klíče (všechny typy sekcí)

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Unikátní identifikátor sekce v dokumentu |
| `type` | ✓ | Typ sekce – viz přehled výše |
| `title` | ✓ | Nadpis karty |
| `description` | | Podnadpis v pravé části hlavičky karty |

### `workbook_header` a `form`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `fields[]` | ✓ | Pole formulářových polí (může být `[]`) |
| `note` | | Šedý text za nadpisem (např. „přeskoč pokud...") – ukládá se do dat, renderer ho nezobrazuje v kartě, ale může ho zobrazit podsekce v `section_group` |
| `hint` | | HTML text zobrazený jako modrý informační box nad formulářem (`form` only) |

### Klíče každého pole (`fields[]`)

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `key` | ✓ | Unikátní identifikátor pole v rámci sekce |
| `label` | ✓ | Popisek vlevo od inputu |
| `type` | ✓ | `text` \| `textarea` \| `select` \| `datetime` |
| `editable` | ✓ | `false` → zobrazí se jako read-only text |
| `value` | ✓ | Aktuální hodnota; `null` = nevyplněno |
| `options[]` | (pro `select`) | Povinný pokud `type: "select"` |
| `example` | | Placeholder text ve vstupu |
| `hint` | | Nápověda pod labelem |
| `option_hints{}` | | Nápověda dle vybrané možnosti v selectu |
| `auto_value` | | Automaticky vyplněno backendem (viz tabulka typů polí) |
| `is_example` | | `true` → hodnota slouží jako placeholder, smaže se při klonování |

### `contact_table`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky (může být `[]`) |
| `editable_columns[]` | | Sloupce editovatelné inline v šablonových řádcích |
| `allow_append` | | `true` → tlačítko „Přidat řádek" |
| `append_row_template{}` | (pokud `allow_append`) | Vzor pro nový prázdný řádek |

Řádky přidané analytikem (interní flag `analyst_added: true`) jsou vždy plně editovatelné a mají tlačítko Smazat.

### `assets_table`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky (může být `[]`) |
| `column_options{}` | | `{ sloupec: [možnosti] }` – sloupce renderované jako `<select>` |
| `hint` | | Oranžový výstražný box nad tabulkou |
| `always_expanded` | | Při použití uvnitř `section_group`: `true` = podsekce nelze sbalit |

### `section_group`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `subsections[]` | ✓ | Seznam podsekci (accordion panely) |
| `subsections[].id` | ✓ | Identifikátor podsekce |
| `subsections[].type` | ✓ | `form` nebo `assets_table` |
| `subsections[].title` | ✓ | Nadpis accordion panelu |
| `subsections[].note` | | Šedý text vpravo od nadpisu |
| `subsections[].always_expanded` | | `true` = podsekce bez možnosti sbalení |

### `checklist`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `step_groups[]` | ✓ | Skupiny kroků |
| `step_groups[].id` | ✓ | Identifikátor skupiny |
| `step_groups[].title` | ✓ | Nadpis skupiny |
| `step_groups[].steps[]` | ✓ | Kroky skupiny |
| `step_groups[].note` | | Šedý podnadpis za nadpisem skupiny |
| `step_groups[].hints[]` | | Šedé informační boxy (operační nápovědy) |
| `step_groups[].classification_hints[]` | | Žluté boxy s klasifikačními vodítky |
| `result{}` | | Blok výsledku na konci checklistu |
| `result.title` | (pokud `result`) | Nadpis bloku výsledku |
| `result.fields[]` | (pokud `result`) | Formulářová pole výsledku |
| `result.notifications[]` | | `string[]` nebo `[{ condition, actions[] }]` |

Klíče každého kroku (`steps[]`):

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | ✓ | Identifikátor kroku |
| `action` | ✓ | Text kroku (HTML bezpečně sanitizován) |
| `done` | ✓ | Výchozí stav checkboxu (`false`) |
| `analyst_note` | ✓ | Výchozí hodnota poznámky (`null`) |
| `example` | | Placeholder v textarea poznámky |
| `is_example` | | `true` → `analyst_note` slouží jako placeholder, smaže se při klonování |

### `action_table`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky |
| `editable_columns[]` | ✓ | Sloupce editovatelné analytikem |
| `status_options[]` | | Pokud definováno, `editable_columns` se renderují jako dropdown; jinak volný textový vstup |
| `allow_append` | | `true` → tlačítko „Přidat akci" |
| `allow_delete` | | `true` → tlačítko Smazat u všech řádků |
| `append_row_template{}` | (pokud `allow_append`) | Vzor pro nový řádek |
| `hints[]` | | Informační texty pod tabulkou |

### `raci_table`

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `columns[]` | ✓ | Seřazený seznam klíčů sloupců |
| `column_labels{}` | ✓ | Mapování `key → nadpis sloupce` |
| `rows[]` | ✓ | Řádky tabulky |
| `legend` | | Text popisující zkratky R/A/C/I, zobrazen nad tabulkou |

Buňky, jejichž hodnota obsahuje podřetězec `"R"` (substring), jsou zvýrazněny tučně červeně – takže např. `"R, A"` je červeně zvýrazněno také.

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

**2. Zaregistrujte ji přes `CaseForm.registerRenderer`:**

```javascript
CaseForm.registerRenderer('timeline', renderTimelineSection);
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

`case_form.js` je zabalený do IIFE a vystavuje jediný globální objekt `CaseForm`. Žádné interní funkce nejsou viditelné z okolního kódu.

**Veřejné API:**

```javascript
// Vykreslí formulář do kontejneru
CaseForm.render(sections, container);

// Registruje vlastní typ sekce – bez úpravy case_form.js
CaseForm.registerRenderer('timeline', function(section) {
    const wrap = el('div'); // el() není dostupné zvenčí – viz níže
    // ...
    return wrap;
});
```

> **Poznámka k interním helperům:** Funkce jako `el()`, `setHTML()`, `makeDeleteBtn()` jsou interní a nejsou součástí veřejného API. Pokud je potřebuješ ve vlastním rendereru, přidej je do `registerRenderer` callback jako closure, nebo si je definuj mimo `case_form.js`. Alternativně lze přidat `helpers` do veřejného API – stačí rozšířit `return { ... }` na konci souboru.

Pokud bys v budoucnu chtěl přejít na ES modul (pro npm nebo bundler), stačí nahradit IIFE za `export`:

```javascript
export function render(sections, container) { ... }
export function registerRenderer(type, fn) { ... }
```

---

## Přehled funkcí

### Veřejné API (`CaseForm.*`)

| Funkce | Popis |
|--------|-------|
| `CaseForm.render(sections, container)` | Hlavní vstupní bod – vykreslí sekce do kontejneru |
| `CaseForm.registerRenderer(type, fn)` | Registruje vlastní renderer pro nový typ sekce |

### Interní renderery (volané přes registr)

Tyto funkce nejsou součástí veřejného API, ale jsou volány interně podle `section.type`. Lze je přepsat přes `CaseForm.registerRenderer`.

| Interní funkce | Typ sekce |
|----------------|-----------|
| `renderWorkbookHeader(section)` | `workbook_header`, `playbook_header` |
| `renderClassification(section)` | `classification` |
| `renderContactTable(section)` | `contact_table` |
| `renderSectionGroup(section)` | `section_group` |
| `renderFormSection(section)` | `form` |
| `renderAssetsTable(section)` | `assets_table` |
| `renderChecklist(section)` | `checklist` |
| `renderActionTable(section)` | `action_table` |
| `renderRaciTable(section)` | `raci_table` |

### Interní helpery

| Funkce | Popis |
|--------|-------|
| `el(tag, cls?, html?)` | Factory pro DOM element; `html` je sanitizováno |
| `setHTML(element, html)` | Bezpečné přiřazení innerHTML |
| `sanitizeHTML(html)` | DOMParser sandbox – odstraní nebezpečné elementy a atributy |
| `buildTableHead(columns, labels?, extraCol?)` | Sestaví `<thead>` tabulky |
| `makeDeleteBtn(onClick)` | Tlačítko smazat s callbackem |
| `renderFieldRow(field, labelCls?, rowMb?)` | Grid řádek label + input |
| `renderInfoGrid(fields, colCls?, gridCls?)` | Grid read-only hodnot |
| `buildOptions(sel, options, currentValue)` | Naplní `<select>` options |
| `renderFieldInput(field)` | DOM widget pro jedno pole |
