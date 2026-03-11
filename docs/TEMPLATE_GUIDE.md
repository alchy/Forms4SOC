# Forms4SOC – Průvodce tvorbou YAML šablon

Šablony jsou YAML soubory uložené v adresáři `data/workbooks/` (konfigurovatelné v sekci Nastavení).
Každý soubor definuje jeden SOC workbook – strukturu dokumentu incidentu, instrukce a kontrolní seznamy.

Průvodce pro SOC analytiky (bez nutnosti znalosti YAML): [WORKBOOK_AUTHORING.md](WORKBOOK_AUTHORING.md)

---

## Jak to funguje?

```
data/workbooks/phishing_v2.yaml      – šablona (commitována v gitu)
    │
    │  Backend při vytvoření incidentu:
    │  1. normalizace šablony (doplnění výchozích hodnot, rozbalení zkratek)
    │  2. hluboká kopie sections
    │  3. example: → is_example: true + value/analyst_note; value → example (placeholder)
    │  4. auto_value pole vyplněna (case_id, template_name, ...)
    ▼
data/events/UIB-DDMMYYYY-HHMM-RRRR.json  – incident (mimo git)
    │
    │  Frontend: Forms4SOC.render(sections, container)
    ▼
Prohlížeč – interaktivní formulář
```

Šablona je **read-only vzor** – při zakládání incidentu se vždy vytváří hluboká kopie.
Šablonové soubory nikdy neobsahují data vyplněná analytikem.

---

## Minimální šablona

```yaml
template_id: moje-sablona-v1
name: Název šablony
version: '1.0'
category: Phishing
status: active
description: Stručný popis účelu šablony.
mitre_tactic: Initial Access
mitre_technique: T1566
mitre_subtechnique: T1566.001
data_sources:
  - SIEM
  - Proxy
sections: []
```

### Klíče šablony

| Klíč | ✓ | Typ | Popis |
|------|:-:|-----|-------|
| `template_id` | ✓ | string | Unikátní identifikátor – použit při vytvoření incidentu |
| `name` | ✓ | string | Zobrazovaný název šablony v UI |
| `version` | ✓ | string | Verze šablony (např. `'2.0'`) |
| `category` | ✓ | string | Kategorie incidentu (např. `Phishing`, `Malware`) |
| `status` | ✓ | string | `active` \| `draft` \| `deprecated` |
| `sections` | ✓ | array | Seznam sekcí dokumentu (viz níže) |
| `description` | | string | Popis účelu šablony |
| `mitre_tactic` | | string | MITRE ATT&CK taktika |
| `mitre_technique` | | string | MITRE ATT&CK technika (např. `T1566`) |
| `mitre_subtechnique` | | string | Sub-technika šablony – slouží jako metadata; v `classification` sekci se sub-technika řeší jako editovatelný `select` |
| `data_sources` | | array | Doporučené zdroje dat – zobrazeny jako badge seznam |

---

## Normalizace šablony – zkrácený zápis

Backend při načtení šablony automaticky doplní chybějící výchozí hodnoty. Díky tomu lze šablony psát výrazně stručněji.

### Výchozí hodnoty polí (`fields`)

| Klíč | Výchozí | Popis |
|------|---------|-------|
| `type` | `text` | Nemusíš uvádět pro jednořádkový textový vstup |
| `editable` | `true` | Nemusíš uvádět pokud je pole editovatelné |
| `value` | `null` | Nemusíš uvádět pokud výchozí hodnota je prázdná |

Stejné pole – plný a zkrácený zápis:

```yaml
# Plný zápis
- key: reporter_name
  label: Jméno oznamovatele
  type: text
  editable: true
  value: null

# Zkrácený zápis (ekvivalentní)
- key: reporter_name
  label: Jméno oznamovatele
```

### Výchozí hodnoty kroků checklistu (`steps`)

| Klíč | Výchozí | Popis |
|------|---------|-------|
| `done` | `false` | Neuvádět |
| `analyst_note` | `null` | Neuvádět pokud není ukázka |
| `id` | auto | Generuje se ze sekce + skupiny + pořadí |

Kroky bez nápovědy nebo ukázky lze zapsat jako prostý řetězec:

```yaml
steps:
  # Zkrácený zápis
  - Ověř záhlaví e-mailu (SPF, DKIM, DMARC).
  - Prověř hash přílohy na VirusTotal.

  # Plný zápis – nutný pro example, hints nebo classification_hints na kroku
  - action: Zjisti hash přílohy.
    example: 'SHA256: 3a1f2b…'
```

### Auto-generovaná ID sekcí, skupin a kroků

Pokud sekce, skupina nebo krok nemají klíč `id`, systém ho vygeneruje automaticky ze slugu `title` (nebo `type`). Manuální zadání `id` je volitelné – použij ho pouze pokud potřebuješ stabilní referenci.

```yaml
# Bez id – vygeneruje se automaticky jako "analyza_lateral_movement"
- title: Analýza lateral movement
  steps:
    - Ověř přihlášení ze zasaženého účtu.
```

---

## Přehled typů sekcí

| `type` | Popis |
|--------|-------|
| `workbook_header` | Hlavička incidentu – editovatelná pole + read-only metadata |
| `classification` | MITRE ATT&CK klasifikace a zdroje dat |
| `contact_table` | Tabulka kontaktů pro investigaci a eskalaci |
| `section_group` | Accordion kontejner pro více podsekce |
| `form` | Formulář s libovolnými poli; volitelný `hint` zobrazí modrý box |
| `assets_table` | Tabulka dotčených aktiv s dynamickým přidáváním řádků |
| `checklist` | Kontrolní seznam kroků s poznámkami analytika |
| `action_table` | Tabulka akcí Odezva nebo komunikační matice |
| `raci_table` | Read-only RACI matice |

---

## Formulářová pole (`fields`)

Pole se používají v sekcích `workbook_header`, `form` a podsekci `form` uvnitř `section_group`.

```yaml
# Minimální pole (type=text, editable=true, value=null jsou výchozí)
- key: reporter_name
  label: Jméno oznamovatele

# Read-only pole s automaticky vyplněnou hodnotou
- key: ticket_id
  label: Ticket ID
  editable: false
  auto_value: case_id
```

### Klíče pole

| Klíč | ✓ | Typ | Popis |
|------|:-:|-----|-------|
| `key` | ✓ | string | Unikátní klíč v rámci sekce |
| `label` | ✓ | string | Popisek zobrazený v UI |
| `type` | | string | Typ vstupního prvku – výchozí `text` (viz tabulka níže) |
| `editable` | | bool | `true` = analytik může editovat; `false` = read-only. Výchozí `true` |
| `value` | | any | Výchozí hodnota; pokud chybí nebo je `null`, pole je prázdné |
| `hint` | | string | Nápověda pod labelem (nikdy jako placeholder) |
| `example` | | any | Ukázková hodnota; normalizátor rozbalí na `is_example: true` + `value`. Nepodporováno v `contact_table`. |
| `auto_value` | | string | Automaticky vyplní backend při vytvoření (viz tabulka níže) |

### Typy polí (`type`)

| `type` | Widget | Popis |
|--------|--------|-------|
| `text` | `<input type="text">` | Jednořádkový textový vstup (výchozí) |
| `textarea` | `<textarea>` | Víceřádkový textový vstup |
| `datetime` | `<input type="datetime-local">` | Datum a čas |
| `select` | `<select>` | Výběr z předem definovaných možností |

### `select` – rozšíření

```yaml
- key: severity
  label: Závažnost
  type: select
  options:
    - critical
    - high
    - medium
    - low
  option_hints:
    critical: Okamžité ohrožení provozu
    high: Závažný incident s potvrzeným dopadem
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `options[]` | ✓ | Seznam možností dropdownu |
| `option_hints{}` | | Nápověda zobrazená pod selectem pro konkrétní vybranou možnost |

### Hodnoty `auto_value`

| Hodnota | Automaticky vyplní |
|---------|-------------------|
| `case_id` | ID incidentu (UIB-...) |
| `template_name` | `name` ze šablony |
| `template_version` | `version` ze šablony |
| `template_status` | `status` ze šablony |
| `template_mitre_tactic` | `mitre_tactic` ze šablony |
| `template_mitre_technique` | `mitre_technique` ze šablony |
| `template_data_sources` | `data_sources` jako CSV řetězec |
| `last_saved` | Timestamp posledního uložení (konfigurovaná timezone, formát `YYYY-MM-DDTHH:MM`) |

> Pole s `auto_value: last_saved` se aktualizuje při **každém uložení** incidentu. Timezone se čte z konfigurace (`TIMEZONE` v `.env`), výchozí hodnota je `Europe/Prague`.

---

## `example` – příkladové hodnoty

Klíč `example` definuje ukázku vyplnění. Při načtení šablony ho normalizátor rozbalí na
`is_example: true` + `value` (u polí) nebo `analyst_note` (u kroků).
Při vytvoření incidentu se hodnota přesune do klíče `example` v JSON dokumentu a zobrazí se jako placeholder.

Použití v poli formuláře:
```yaml
- key: description
  label: Popis události
  type: textarea
  example: Uživatel obdržel podezřelý e-mail s přílohou.
```

Použití v kroku checklistu:
```yaml
- action: Zjisti hash přílohy.
  example: 'SHA256: 3a1f2b…'
```

Výsledek: pole nebo krok se zobrazí prázdné s placeholderem nastaveným na příkladovou hodnotu.

---

## Typ `workbook_header`

Povinná první sekce každého workbooku. Editovatelná pole zobrazena prominentně nahoře; read-only pole (case_id, last_saved) zobrazena jako kompaktní info-grid pod čarou.

Hlavička obsahuje pouze nezbytná pole – nepřidávej metadata šablony (název workbooku, verze, autor), ta jsou uložena v datech incidentu a dostupná přes API.

```yaml
- id: header
  type: workbook_header
  title: Hlavička
  fields:
    - key: case_title
      label: Stručný popis události
      type: textarea
      example: Příklad vyplnění
      hint: Výstižný popis pro odlišení od ostatních případů

    - key: incident_coordinator
      label: Koordinátor incidentu
      hint: Analytik zodpovědný za koordinaci. Lze vyplnit tlačítkem Převzít.

    - key: last_saved
      label: Datum poslední aktualizace
      editable: false
      auto_value: last_saved
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce (auto-generováno pokud chybí) |
| `type` | ✓ | `workbook_header` |
| `title` | ✓ | Nadpis karty |
| `fields[]` | ✓ | Editovatelná pole prominentně nahoře; read-only pole jako info-grid pod čarou |

---

## Typ `classification`

Panel s MITRE ATT&CK informacemi. Tactic a Technique jsou read-only (dané šablonou); Sub-technique je editovatelný `select` – analytik vyplní po Posouzení, kdy je znám konkrétní vektor útoku.

```yaml
- id: classification
  type: classification
  title: Klasifikace
  fields:
    - key: mitre_tactic
      label: MITRE Tactic
      editable: false
      auto_value: template_mitre_tactic
    - key: mitre_technique
      label: MITRE Technique
      editable: false
      auto_value: template_mitre_technique
    - key: mitre_subtechnique
      label: MITRE Sub-technique
      type: select
      options:
        - T1566.001 – Spearphishing Attachment
        - T1566.002 – Spearphishing Link
    - key: data_sources
      label: Zdroje dat
      editable: false
      auto_value: template_data_sources
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `classification` |
| `title` | ✓ | Nadpis karty |
| `fields[]` | ✓ | Pole MITRE; `data_sources` se zobrazí jako badge seznam |

---

## Typ `contact_table`

Tabulka kontaktů pro investigaci a eskalaci. Analytik edituje vybrané sloupce a může přidávat vlastní řádky.

```yaml
- id: contacts
  type: contact_table
  title: Kontaktní matice
  columns:
    - system_role
    - name
    - email
    - phone
    - when_to_contact
  column_labels:
    system_role: Systém / role
    name: Jméno
    email: E-mail
    phone: Telefon
    when_to_contact: Kdy kontaktovat
  editable_columns:
    - name
    - email
    - phone
  allow_append: true
  append_row_template:
    system_role: null
    name: null
    email: null
    phone: null
    when_to_contact: null
  rows:
    - system_role: CISO
      name: Ing. Jan Novák
      email: ciso@firma.cz
      phone: +420 123 456 789
      when_to_contact: Severity High / Critical
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `contact_table` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Pořadí sloupců |
| `column_labels{}` | ✓ | Zobrazované názvy sloupců |
| `rows[]` | ✓ | Předvyplněné řádky (může být `[]`) |
| `editable_columns[]` | | Sloupce editovatelné inline v šablonových řádcích |
| `allow_append` | | `true` = analytik přidá řádek tlačítkem `+` |
| `append_row_template{}` | ◐ | Povinný pokud `allow_append: true` |

> Řádky `contact_table` **nepodporují** `example`. Hodnoty jsou předvyplněné jako běžný editovatelný text.

---

## Typ `section_group`

Accordion kontejner sdružující více podsekce. Podporované typy podsekce: `form`, `assets_table`.

```yaml
- id: incident_context
  type: section_group
  title: Kontext UIB
  subsections:
    - id: common_data
      type: form
      title: Společné údaje
      note: Vyplní SOC Analytik
      always_expanded: true
      fields:
        - key: detection_source
          label: Zdroj detekce

    - id: affected_assets
      type: assets_table
      title: Dotčená aktiva
      always_expanded: true
      columns:
        - asset_name
        - asset_ip
        - asset_type
      column_labels:
        asset_name: Název
        asset_ip: IP
        asset_type: Typ
      column_options:
        asset_type:
          - Server
          - Workstation
          - Mailbox
      rows: []
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `section_group` |
| `title` | ✓ | Nadpis karty |
| `subsections[]` | ✓ | Seznam podsekce (accordion panely) |
| `subsections[].id` | | Identifikátor podsekce |
| `subsections[].type` | ✓ | `form` nebo `assets_table` |
| `subsections[].title` | ✓ | Nadpis accordion panelu |
| `subsections[].note` | | Šedý text vpravo od nadpisu panelu |
| `subsections[].always_expanded` | | `true` = panel nelze sbalit |

---

## Typ `form`

Formulář s libovolnými poli zobrazený jako dvousloupcový grid. Volitelný klíč `hint` zobrazí modrý informační box nad formulářem – vhodné pro uzavírací sekce nebo upozornění.

```yaml
- id: reported_by
  type: form
  title: Hlášeno osobou
  note: Vyplní SOC Analytik — přeskoč pokud jde o automatizovanou detekci
  fields:
    - key: reported_at
      label: Datum a čas nahlášení
      type: datetime
    - key: reporter_name
      label: Jméno oznamovatele
    - key: description
      label: Popis slovy oznamovatele
      type: textarea
```

Příklad uzavírací sekce s `hint`:

```yaml
- id: closure
  type: form
  title: Klasifikace a uzavření
  hint: Před uzavřením ověř, že oznamovatel byl informován o výsledku šetření.
  fields:
    - key: final_classification
      label: Klasifikace výsledku
      type: select
      options:
        - True Positive
        - False Positive
        - Benign True Positive
    - key: root_cause
      label: Root Cause
      type: textarea
    - key: closed_at
      label: Datum uzavření
      type: datetime
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `form` |
| `title` | ✓ | Nadpis karty |
| `fields[]` | ✓ | Formulářová pole |
| `description` | | Podnadpis v záhlaví karty |
| `note` | | Metadata ukládaná do dat; zobrazí je accordion v `section_group` |
| `hint` | | HTML text zobrazený jako modrý informační box nad formulářem |

---

## Typ `assets_table`

Tabulka dotčených aktiv. Všechny buňky jsou editovatelné; analytik může přidávat i mazat řádky.
Sloupce v `column_options` se zobrazí jako `<select>`; ostatní jako textový vstup.

```yaml
- id: affected_assets
  type: assets_table
  title: Dotčená aktiva
  hint: Pokud je aktivum součástí regulované služby → ihned informuj CISO.
  columns:
    - asset_name
    - fqdn
    - asset_ip
    - asset_type
    - regulated_service
    - contacts
  column_labels:
    asset_name: Název aktiva
    fqdn: FQDN
    asset_ip: IP adresa nebo subnet
    asset_type: Typ aktiva
    regulated_service: Regulovaná služba
    contacts: Kontakty
  column_options:
    asset_type:
      - Endpoint
      - Server
      - Mailbox
      - Informační systém
      - Síťový prvek
    regulated_service:
      - Ano
      - Ne
  rows: []
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `assets_table` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Pořadí sloupců |
| `column_labels{}` | ✓ | Zobrazované názvy sloupců |
| `rows[]` | ✓ | Předvyplněné řádky (obvykle `[]`) |
| `column_options{}` | | Sloupce renderované jako `<select>` místo textového pole |
| `hint` | | Oranžový výstražný box nad tabulkou |
| `always_expanded` | | Pouze uvnitř `section_group` – `true` = podsekci nelze sbalit |

---

## Typ `checklist`

Kontrolní seznam kroků organizovaný do skupin. Analytik označuje kroky jako splněné a zapisuje poznámky.

```yaml
- id: triage_investigation
  type: checklist
  title: Posouzení, třídění a rozhodování
  step_groups:
    - title: Analýza e-mailu
      note: Přeskoč pokud není relevantní
      hints:
        - Pokud byla příloha otevřena na více zařízeních → rozšiř scope.
      classification_hints:
        - Hash detekován na TI a příloha otevřena → True Positive, High
        - Hash na TI nedetekován → zvaž False Positive
      steps:
        # Zkrácený zápis – jednoduchý krok bez nápovědy nebo ukázky
        - Ověř záhlaví e-mailu (SPF, DKIM, DMARC).

        # Plný zápis – krok s ukázkou analyst_note
        - action: Zjisti hash přílohy.
          example: 'SHA256: příklad…'
```

### Klíče `step_group`

| Klíč | ✓ | Typ | Popis |
|------|:-:|-----|-------|
| `id` | | string | Identifikátor skupiny (auto-generováno ze slugu `title` pokud chybí) |
| `title` | ✓ | string | Název skupiny kroků |
| `steps[]` | ✓ | array | Kroky skupiny |
| `note` | | string | Šedý podnadpis za názvem skupiny |
| `hints[]` | | array | Operační nápovědy – šedé boxy s ikonou ℹ |
| `classification_hints[]` | | array | Klasifikační vodítka True/False Positive – žluté boxy |
| `condition` | | string | Informativní podmínka zobrazení (nevynucuje logiku) |

### Klíče kroku (`steps[]`)

Krok lze zapsat jako prostý řetězec nebo jako mapování:

| Klíč | ✓ | Typ | Popis |
|------|:-:|-----|-------|
| `action` | ✓ | string | Text instrukce (povinný jen v plném zápisu) |
| `id` | | string | Identifikátor kroku – auto-generováno pokud chybí |
| `done` | | bool | Výchozí stav checkboxu – výchozí `false`, nemusíš uvádět |
| `analyst_note` | | string \| null | Předvyplněná poznámka – výchozí `null`, nemusíš uvádět |
| `example` | | string | Ukázka poznámky; normalizátor rozbalí na `is_example: true` + `analyst_note` |

---

## Typ `action_table`

Univerzální tabulka pro akce Odezvy i komunikační matice. Sloupce v `editable_columns` se renderují jako dropdown (pokud je definováno `status_options`) nebo jako volný textový vstup.

Příklad tabulky akcí Odezvy:

```yaml
- id: response_actions
  type: action_table
  title: Odezva
  description: U každé akce zaznamenej stav. Pokud akce není relevantní, napiš N/A.
  columns:
    - action
    - responsible_role
    - cooperation
    - status
  column_labels:
    action: Akce
    responsible_role: Zodpovědná role
    cooperation: Součinnost
    status: Stav
  editable_columns:
    - status
  status_options:
    - Provedeno
    - Probíhá
    - Čeká
    - N/A
    - Není nutné provést
  allow_append: true
  allow_delete: true
  append_row_template:
    action: null
    responsible_role: null
    cooperation: null
    status: null
  rows:
    - action: Počítač izolován od sítě
      responsible_role: SOC Analytický tým
      cooperation: Správce AV/EDR · IT Helpdesk
      status: null
```

Příklad komunikační matice (bez `status_options` – volný textový vstup):

```yaml
- id: communication
  type: action_table
  title: Komunikace a notifikace
  columns:
    - recipient
    - communication_method
    - sla
    - note
  column_labels:
    recipient: Příjemce
    communication_method: Způsob komunikace
    sla: SLA pro notifikaci
    note: Poznámka / stav
  editable_columns:
    - note
  hints:
    - Oznamovatele informuj vždy – bez ohledu na výsledek klasifikace.
  rows:
    - recipient: Vlastník dotčeného aktiva
      communication_method: E-mail / telefon
      sla: Do 30 min od Posouzení
      note: null
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `action_table` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Pořadí sloupců |
| `column_labels{}` | ✓ | Zobrazované názvy sloupců |
| `rows[]` | ✓ | Předdefinované řádky |
| `editable_columns[]` | ✓ | Sloupce editovatelné analytikem |
| `status_options[]` | | Pokud definováno → dropdown pro `status_column`; ostatní editovatelné sloupce zůstávají textovým vstupem |
| `status_column` | | Název sloupce, který se renderuje jako dropdown se `status_options`. Výchozí: `status` |
| `allow_append` | | `true` = analytik přidá vlastní řádek |
| `allow_delete` | | `true` = analytik smaže libovolný řádek |
| `append_row_template{}` | ◐ | Povinný pokud `allow_append: true` |
| `hints[]` | | Informační texty zobrazené pod tabulkou |

> **Konvence formulace akcí:** používej oznamovací tvrzení popisující co bylo provedeno (např. „Blokována doména odesílatele na mail serveru"), nikoli imperativ.

> **Dropdown pouze pro status sloupec:** `status_options` se aplikuje výhradně na sloupec pojmenovaný v `status_column` (výchozí `status`). Ostatní sloupce v `editable_columns` (např. `action`, `cooperation`) se vždy renderují jako textový vstup, i když je `status_options` definováno.

---

## Typ `raci_table`

Read-only RACI matice. Buňky obsahující `R` jsou zvýrazněny tučně červeně.

```yaml
- id: raci
  type: raci_table
  title: RACI matice
  legend: R = Responsible · A = Accountable · C = Consulted · I = Informed
  columns:
    - activity
    - koordinator
    - cirt
    - ciso
    - garant
  column_labels:
    activity: Aktivita
    koordinator: Koordinátor incidentu
    cirt: CIRT
    ciso: CISO
    garant: Garant aktiva
  rows:
    - activity: Posouzení, třídění a rozhodování
      koordinator: R, A
      cirt: R
      ciso: C
      garant: C
    - activity: Klasifikace a uzavření
      koordinator: R, A
      cirt: C
      ciso: I
      garant: I
```

| Klíč | ✓ | Popis |
|------|:-:|-------|
| `id` | | Unikátní identifikátor sekce |
| `type` | ✓ | `raci_table` |
| `title` | ✓ | Nadpis karty |
| `columns[]` | ✓ | Pořadí sloupců |
| `column_labels{}` | ✓ | Zobrazované názvy sloupců |
| `rows[]` | ✓ | Řádky matice |
| `legend` | | Legenda zkratek zobrazená nad tabulkou |

### Konvence hodnot RACI

| Hodnota | Popis |
|---------|-------|
| `R` | Responsible – provádí aktivitu |
| `A` | Accountable – zodpovídá za výsledek |
| `C` | Consulted – poskytuje součinnost |
| `I` | Informed – informován o výsledku |
| `I (Critical)` | Informován pouze při Severity Critical |
| `–` | Není zapojen |

---

## Standardní sekce Klasifikace a uzavření

Všechny workbooky obsahují sekci uzavření s těmito standardními poli **v tomto pořadí**. Šablonově specifická pole přidej **za** `ucl_notification_required` a **před** `root_cause`.

| `key` | `label` | `type` |
|-------|---------|--------|
| `final_classification` | Klasifikace výsledku | `select` |
| `impact_level` | Úroveň dopadu | `select` |
| `nukib_notification_required` | Povinnost hlášení NÚKIB | `select` |
| `ucl_notification_required` | Povinnost hlášení ÚCL | `select` |
| *(šablonově specifická pole)* | | |
| `impact_primary_service` | Dostupnost primárních služeb organizace | `select` |
| `impact_scope` | Rozsah zasažených uživatelů / systémů | `select` |
| `impact_duration` | Doba výpadku / narušení (dostupnost) | `select` |
| `impact_data` | Dopad na data (důvěrnost / integrita) | `select` |
| `root_cause` | Root Cause | `textarea` |
| `actions_taken` | Popis přijatých opatření | `textarea` |
| `recommendations` | Doporučení pro zlepšení | `textarea` |
| `related_service_requests` | Související servisní požadavky | `textarea` |
| `reporter_notified` | Oznamovatel informován | `select` |
| `closed_at` | Datum uzavření | `datetime` |

### Úroveň dopadu – škála a podmínky notifikace

| Úroveň | Popis | Povinnost hlášení NÚKIB |
|--------|-------|------------------------|
| **Nízká** | Omezený nebo lokální dopad. Žádný dopad na regulovanou službu. | Není vyžadována |
| **Střední** | Postihuje důležité systémy, ale klíčové procesy pokračují. Nezasahuje aktiva regulované služby. | Není vyžadována |
| **Vysoká** | Významný dopad na klíčové procesy. Při zasažení aktiv regulované služby splňuje kritéria KBI. | Zvážit / Povinná |
| **Kritická** | Katastrofický dopad, úplný kolaps regulované služby. Jde vždy o KBI. | Povinná (ZOKB §8) |

Lhůty hlášení NÚKIB dle vyhl. č. 82/2018 Sb.: **do 24 h** (první hlášení) · **do 72 h** (detailní hlášení) · **do 30 dní** (závěrečná zpráva).

---

## Souhrn speciálních klíčů

| Klíč | Umístění | Popis |
|------|----------|-------|
| `example: "..."` | pole, kroky checklistu | Ukázka vyplnění; normalizátor rozbalí a při klonování se stane placeholderem. Nepodporováno v `contact_table`. |
| `auto_value` | pole | Automaticky vyplněno při vytvoření incidentu; `last_saved` se navíc aktualizuje při každém uložení (viz tabulka výše) |
| `always_expanded: true` | podsekce v `section_group` | Podsekce se nezbaluje |
| `allow_append: true` | tabulky | Analytik přidá řádek tlačítkem `+` |
| `allow_delete: true` | tabulky | Analytik smaže libovolný řádek |
| `append_row_template` | tabulky | Struktura prázdného přidávaného řádku |
| `editable_columns` | tabulky | Sloupce editovatelné analytikem |
| `column_options` | `assets_table` | Sloupce renderované jako `<select>` místo textového pole |
| `status_options` | `action_table` | Hodnoty dropdownu Stav; bez tohoto klíče = volný textový vstup |
| `classification_hints` | `step_group` | Klasifikační vodítka – žluté boxy |
| `hints` | `step_group`, `action_table` | Operační nápovědy – šedé boxy |
| `hint` | `form`, `assets_table` | Alert box nad sekcí (`form` = modrý; `assets_table` = oranžový) |
| `condition` | podsekce, `step_group` | Informativní podmínka zobrazení (nevynucuje logiku) |
| `note` | podsekce, `step_group` | Poznámka zobrazená v záhlaví accordion panelu |
