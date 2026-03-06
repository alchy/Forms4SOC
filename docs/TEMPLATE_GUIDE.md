# Forms4SOC – Průvodce tvorbou JSON šablon

Šablony jsou JSON soubory uložené v adresáři `data/workbooks/` (konfigurovatelné v sekci Nastavení).
Každý soubor definuje jeden SOC workbook – strukturu dokumentu incidentu, instrukce a kontrolní seznamy.

Dostupné šablony: `phishing_v1.json` (původní), `phishing_v2.json` (sloučená Triage & Investigace, rozšířená tabulka aktiv), `ddos_vpn_v1.json` (DDoS útok na VPN Cisco AnyConnect).

---

## Minimální šablona

```json
{
  "template_id": "moje-sablona-v1",
  "name": "Název šablony",
  "version": "1.0",
  "category": "Phishing",
  "status": "active",
  "description": "Stručný popis účelu šablony.",
  "mitre_tactic": "Initial Access",
  "mitre_technique": "T1566",
  "mitre_subtechnique": "T1566.001",
  "data_sources": ["SIEM", "Proxy"],
  "sections": []
}
```

### Povinné klíče šablony

| Klíč | Typ | Popis |
|---|---|---|
| `template_id` | string | Unikátní identifikátor, použitý při vytvoření incidentu |
| `name` | string | Zobrazovaný název šablony |
| `version` | string | Verze šablony (např. `"1.0"`) |
| `category` | string | Kategorie incidentu (např. `"Phishing"`, `"Malware"`) |
| `status` | string | `active` \| `draft` \| `deprecated` |
| `sections` | array | Seznam sekcí dokumentu (viz níže) |

### Volitelné klíče šablony

| Klíč | Typ | Popis |
|---|---|---|
| `description` | string | Popis účelu šablony |
| `mitre_tactic` | string | MITRE ATT&CK taktika |
| `mitre_technique` | string | MITRE ATT&CK technika (např. `"T1566"`) |
| `mitre_subtechnique` | string | Sub-technika šablony (např. `"T1566.001"`) – slouží jako metadata šablony; v sekci `classification` se sub-technika řeší jako editovatelný `select`, který analytik vyplní až po Triage & Investigaci |
| `data_sources` | array of strings | Doporučené zdroje dat pro investigaci – zobrazeny jako samostatné badge |

---

## Sekce (`sections`)

Každá sekce má `id`, `title` a `type`. Typ určuje způsob renderování.

```json
{
  "id": "moje_sekce",
  "title": "Název sekce",
  "type": "form",
  "description": "Volitelný popis sekce zobrazený v záhlaví karty"
}
```

### Přehled typů sekcí

| `type` | Popis |
|---|---|
| `workbook_header` | Hlavička incidentu – editovatelná pole + read-only metadata workbooku |
| `classification` | Panel s MITRE informacemi a zdroji dat. Tactic a Technique jsou read-only (primární indikátory dané šablonou); Sub-technique je editovatelný `select` – analytik vyplní po Triage & Investigaci, kdy je znám konkrétní vektor útoku |
| `contact_table` | Tabulka kontaktů pro investigaci a eskalaci |
| `section_group` | Kontejner pro více podsekce zobrazených jako accordion |
| `form` | Formulář s libovolnými poli |
| `closure_form` | Formulář uzavření incidentu (shodná struktura s `form`) |
| `assets_table` | Tabulka dotčených aktiv s dynamickým přidáváním řádků |
| `checklist` | Kontrolní seznam kroků s poznámkami analytika |
| `action_table` | Tabulka akcí containment / remediation s editovatelným stavem |
| `notification_table` | Tabulka komunikace a notifikací (shodná struktura s `action_table`) |
| `raci_table` | Read-only RACI matice |

---

## Formulářová pole (`fields`)

Pole se používají v sekcích `workbook_header`, `form`, `closure_form`, podsekci `form` uvnitř `section_group` a ve výsledkovém bloku `result` uvnitř `checklist`.

```json
{
  "key": "reporter_name",
  "label": "Jméno oznamovatele",
  "type": "text",
  "editable": true,
  "value": null
}
```

### Klíče pole

| Klíč | Typ | Popis |
|---|---|---|
| `key` | string | Unikátní klíč v rámci sekce |
| `label` | string | Popisek zobrazený v UI |
| `type` | string | Typ vstupního prvku (viz níže) |
| `editable` | bool | `true` = analytik může editovat, `false` = read-only |
| `value` | any | Výchozí hodnota (nebo `null`) |
| `hint` | string | Nápověda zobrazená pod polem |
| `is_example` | bool | Pokud `true`, hodnota se při klonování přesune do `example` (placeholder) |
| `auto_value` | string | Automaticky vyplněno systémem při vytvoření incidentu (viz tabulka níže) |

### Typy polí (`type`)

| `type` | Popis |
|---|---|
| `text` | Jednořádkový textový vstup |
| `textarea` | Víceřádkový textový vstup |
| `datetime` | Datum a čas (`<input type="datetime-local">`) |
| `select` | Výběr z předem definovaných možností |

**Pole typu `select` – rozšíření:**
```json
{
  "key": "severity",
  "label": "Závažnost",
  "type": "select",
  "editable": true,
  "value": null,
  "options": ["critical", "high", "medium", "low"],
  "option_hints": {
    "critical": "Okamžité ohrožení provozu",
    "high": "Závažný incident s potvrzeným dopadem"
  }
}
```

---

## `is_example` – příkladové hodnoty

Pole nebo kroky označené `"is_example": true` slouží jako ukázka vyplnění.
Při vytvoření nového incidentu se hodnota automaticky přesune do klíče `example` a použije jako placeholder – analytik ji přepíše vlastní hodnotou.

```json
{
  "key": "description",
  "label": "Popis události",
  "type": "textarea",
  "editable": true,
  "is_example": true,
  "value": "Uživatel obdržel podezřelý e-mail s přílohou."
}
```

---

## Typ `workbook_header`

Speciální sekce zobrazená na začátku každého incidentu.
Editovatelná pole (zejména `case_title`) vyplňuje analytik; read-only pole zobrazují metadata workbooku v kompaktní mřížce.

```json
{
  "id": "header",
  "type": "workbook_header",
  "title": "Hlavička",
  "fields": [
    {
      "key": "case_title",
      "label": "Stručný popis události",
      "type": "text",
      "editable": true,
      "is_example": true,
      "value": "Příklad vyplnění",
      "hint": "Výstižný popis pro odlišení od ostatních případů"
    },
    {
      "key": "ticket_id",
      "label": "Ticket ID",
      "type": "text",
      "editable": false,
      "value": null,
      "auto_value": "case_id"
    },
    {
      "key": "version",
      "label": "Verze",
      "type": "text",
      "editable": false,
      "value": "2.0"
    }
  ]
}
```

---

## Typ `contact_table`

Tabulka kontaktů pro investigaci a eskalaci. Analytik může editovat vybrané sloupce a přidávat nové řádky.

```json
{
  "id": "contacts",
  "type": "contact_table",
  "title": "Kontaktní matice",
  "description": "Volitelný popis zobrazený v záhlaví",
  "columns": ["system_role", "name", "email", "phone", "when_to_contact"],
  "column_labels": {
    "system_role": "Systém / role",
    "name": "Jméno",
    "email": "E-mail",
    "phone": "Telefon",
    "when_to_contact": "Kdy kontaktovat"
  },
  "editable_columns": ["name", "email", "phone"],
  "allow_append": true,
  "append_row_template": {
    "system_role": null, "name": null, "email": null,
    "phone": null, "when_to_contact": null
  },
  "rows": [
    {
      "system_role": "CISO",
      "name": "Ing. Jan Novák",
      "email": "ciso@firma.cz",
      "phone": "+420 123 456 789",
      "when_to_contact": "Severity High / Critical",
      "is_example": true
    }
  ]
}
```

### Klíče `contact_table`

| Klíč | Popis |
|---|---|
| `columns` | Pořadí sloupců v tabulce |
| `column_labels` | Zobrazované názvy sloupců |
| `editable_columns` | Sloupce, které může analytik editovat inline |
| `allow_append` | `true` = analytik může přidat nový řádek tlačítkem `+` |
| `append_row_template` | Struktura prázdného nového řádku |
| `rows[].is_example` | Hodnoty se při klonování přesunou do `_example` klíčů (placeholder) |

---

## Typ `section_group`

Kontejner sdružující více podsekce do jednoho bloku (zobrazeny jako accordion). Podporované typy podsekce: `form`, `closure_form`, `assets_table`, `checklist` a všechny typy tabulek (`contact_table`, `action_table`, `notification_table`, `raci_table`).

```json
{
  "id": "incident_context",
  "type": "section_group",
  "title": "Kontext UIB",
  "subsections": [
    {
      "id": "common_data",
      "type": "form",
      "title": "Společné údaje",
      "note": "Vyplní SOC Analytik",
      "always_expanded": true,
      "fields": []
    },
    {
      "id": "optional_section",
      "type": "form",
      "title": "Podmíněná sekce",
      "condition": "source_type == 'automated'",
      "fields": []
    }
  ]
}
```

### Klíče podsekce

| Klíč | Popis |
|---|---|
| `always_expanded` | `true` = podsekce se nezbaluje (vždy viditelná) |
| `note` | Poznámka pro analytika zobrazená v záhlaví accordion |
| `condition` | Informativní textový popis podmínky zobrazení (zatím nevynucuje logiku) |

---

## Typ `assets_table`

Tabulka dotčených aktiv s dynamickým přidáváním a mazáním řádků. Používá se jako podsekce uvnitř `section_group` nebo jako samostatná sekce.

```json
{
  "id": "affected_assets",
  "type": "assets_table",
  "title": "Dotčená aktiva",
  "note": "Doplňuj průběžně při každém rozšíření scope",
  "hint": "Pokud je aktivum součástí kritické infrastruktury → ihned informuj CISO.",
  "always_expanded": true,
  "columns": ["asset_name", "asset_ip", "asset_type", "critical_infrastructure", "contact_owner", "guarantor", "email", "phone"],
  "column_labels": {
    "asset_name":              "Název aktiva (hostname, mailbox, IS)",
    "asset_ip":                "IP adresa",
    "asset_type":              "Typ aktiva",
    "critical_infrastructure": "Kritická infrastruktura",
    "contact_owner":           "Kontakt vlastníka",
    "guarantor":               "Garant",
    "email":                   "E-mail",
    "phone":                   "Telefon"
  },
  "column_options": {
    "asset_type": ["Endpoint", "Server", "Mailbox", "Informační systém", "Síťový prvek", "Sdílené úložiště", "Jiné"],
    "critical_infrastructure": ["Ano", "Ne"]
  },
  "editable": true,
  "rows": []
}
```

### Klíče `assets_table`

| Klíč | Popis |
|---|---|
| `columns` | Pořadí sloupců |
| `column_labels` | Zobrazované názvy sloupců |
| `column_options` | Pro zadaný sloupec se místo textového pole zobrazí `<select>` s danými možnostmi |
| `hint` | Text zobrazen jako varování (oranžový alert) nad tabulkou |
| `editable` | `true` = všechny buňky jsou editovatelné, automaticky povoleno přidávání a mazání řádků |
| `rows` | Předvyplněné řádky (obvykle prázdné pole `[]`) |

> **Doporučená struktura sloupců (v2):** `asset_name`, `asset_ip`, `asset_type`, `critical_infrastructure`, `contact_owner`, `guarantor`, `email`, `phone`

---

## Typ `checklist`

Kontrolní seznam kroků. Analytik označuje kroky jako splněné (checkbox) a zapisuje vlastní poznámky. Kroky jsou organizovány do skupin (`step_groups`).

```json
{
  "id": "triage_investigation",
  "type": "checklist",
  "title": "Triage & Investigace",
  "description": "Popis účelu bloku – zobrazí se v záhlaví.",
  "step_groups": [
    {
      "id": "email_analysis",
      "title": "Analýza e-mailu",
      "note": "Přeskoč pokud není relevantní",
      "condition": "has_attachment == true",
      "hints": [
        "Pokud byla příloha otevřena nebo nalezena na více zařízeních → rozšiř scope."
      ],
      "classification_hints": [
        "Hash detekován na TI a příloha otevřena → True Positive, High",
        "Hash na TI nedetekován → zvaž False Positive"
      ],
      "steps": [
        {
          "id": "ea_01",
          "action": "Ověř záhlaví e-mailu (SPF, DKIM, DMARC)",
          "analyst_note": null,
          "done": false
        },
        {
          "id": "ea_02",
          "action": "Zjisti hash přílohy",
          "analyst_note": "SHA256: příklad…",
          "is_example": true,
          "done": false
        }
      ]
    }
  ]
}
```

### Klíče `step_group`

| Klíč | Typ | Popis |
|---|---|---|
| `id` | string | Unikátní identifikátor skupiny |
| `title` | string | Název skupiny kroků |
| `note` | string | Poznámka zobrazená za názvem (např. „Přeskoč pokud …") |
| `condition` | string | Informativní podmínka zobrazení (nevynucuje logiku) |
| `steps` | array | Seznam kroků (viz níže) |
| `hints` | array of strings | Operační nápovědy zobrazené nad kroky (šedý styl) |
| `classification_hints` | array of strings | Klasifikační vodítka (True/False Positive, Severity) – zobrazena s pastelově žlutým pozadím a oranžovým okrajem |

### Klíče kroků (`steps`)

| Klíč | Typ | Popis |
|---|---|---|
| `id` | string | Unikátní identifikátor kroku |
| `action` | string | Text instrukce |
| `analyst_note` | string \| null | Předvyplněná poznámka (nebo `null`) |
| `is_example` | bool | `true` = `analyst_note` je příklad, přesune se do `example` při klonování |
| `done` | bool | Výchozí stav checkboxu – vždy `false` |

### `classification_hints` – vizuální odlišení klasifikačních vodítek

Skupiny kroků mohou obsahovat dva typy nápověd:
- **`hints`** – operační poznámky (šedý styl, ikona ℹ)
- **`classification_hints`** – vodítka pro klasifikaci výsledku (True / False Positive, Severity) – zobrazena s **pastelově žlutým pozadím** a oranžovým levým okrajem (ikona ⬧)

```json
{
  "id": "attachment_analysis",
  "title": "E-mail obsahuje přílohu",
  "hints": [
    "Pokud byla příloha otevřena nebo nalezena na více zařízeních → rozšiř scope."
  ],
  "classification_hints": [
    "Hash detekován na TI a příloha otevřena → True Positive, High · Hash na TI, příloha neotvřena → True Positive, Medium · Hash na TI nedetekován → zvaž False Positive"
  ],
  "steps": [...]
}
```

### Volitelný blok `result`

Na konci checklistu lze přidat výsledkový formulář s `fields` (stejná struktura jako `form`) a `notifications` (seznam notifikačních pravidel). V šabloně phishing_v2 je `result` odstraněn – finální klasifikace se zaznamenává pouze v bloku Uzavření incidentu.

```json
"result": {
  "id": "result_id",
  "title": "Výsledek",
  "fields": [
    {
      "key": "classification",
      "label": "Klasifikace",
      "type": "select",
      "editable": true,
      "value": null,
      "options": ["True Positive", "False Positive", "Benign True Positive"]
    }
  ],
  "notifications": [
    {
      "condition": "True Positive, Critical",
      "actions": ["informuj CISO a Management", "zvaž notifikaci CERT / NÚKIB"]
    }
  ]
}
```

---

## Typ `action_table`

Tabulka akcí containment a remediation. Analytik označuje stav každé akce z předdefinovaného seznamu. Lze přidávat a mazat řádky.

```json
{
  "id": "containment_remediation",
  "type": "action_table",
  "title": "Containment & Remediation",
  "description": "U každé akce zaznamenej stav. Pokud akce není relevantní, napiš N/A.",
  "columns": ["action", "responsible_role", "cooperation", "status"],
  "column_labels": {
    "action": "Akce",
    "responsible_role": "Zodpovědná role",
    "cooperation": "Součinnost",
    "status": "Stav"
  },
  "status_options": ["Provedeno", "Probíhá", "Čeká", "N/A", "Není nutné provést"],
  "editable_columns": ["status"],
  "allow_append": true,
  "allow_delete": true,
  "append_row_template": {
    "action": null, "responsible_role": null, "cooperation": null, "status": null
  },
  "rows": [
    {
      "action": "Počítač izolován od sítě",
      "responsible_role": "SOC Analytický tým",
      "cooperation": "Správce AV/EDR · IT Helpdesk",
      "status": null
    }
  ]
}
```

### Klíče `action_table`

| Klíč | Popis |
|---|---|
| `status_options` | Seznam možností pro sloupec Stav; aktuální hodnoty: `Provedeno`, `Probíhá`, `Čeká`, `N/A`, `Není nutné provést` |
| `editable_columns` | Sloupce editovatelné analytikem (typicky jen `status`) |
| `allow_append` | `true` = analytik může přidat vlastní akci |
| `allow_delete` | `true` = analytik může smazat libovolný řádek |
| `append_row_template` | Struktura prázdného nového řádku |

> **Konvence formulace akcí:** akce jsou formulovány jako **oznamovací tvrzení** popisující co bylo provedeno (např. „Blokována doména odesílatele na mail serveru"), nikoli jako imperatív.

---

## Typ `notification_table`

Tabulka komunikace a notifikací. Shodná struktura s `action_table` – analytik doplňuje poznámky ke každému příjemci.

```json
{
  "id": "communication",
  "type": "notification_table",
  "title": "Komunikace a notifikace",
  "columns": ["recipient", "communication_method", "sla", "note"],
  "column_labels": {
    "recipient": "Příjemce",
    "communication_method": "Způsob komunikace",
    "sla": "SLA pro notifikaci",
    "note": "Poznámka / stav"
  },
  "editable_columns": ["note"],
  "hints": [
    "Oznamovatele informuj vždy – bez ohledu na výsledek klasifikace."
  ],
  "rows": [
    {"recipient": "Vlastník dotčeného aktiva", "communication_method": "E-mail / telefon", "sla": "Do 30 min od Triage", "note": null},
    {"recipient": "CISO / Management",         "communication_method": "E-mail / telefon", "sla": "Do 1 h (High / Critical)", "note": null},
    {"recipient": "CERT / NÚKIB",              "communication_method": "Datová schránka",  "sla": "Dle regulatorní povinnosti", "note": null}
  ]
}
```

> `hints` v `notification_table` se zobrazí jako šedé informační texty pod tabulkou (stejný styl jako `action_table`).

---

## Typ `raci_table`

Read-only RACI matice. Buňky obsahující `R` jsou zvýrazněny tučně červeně.

```json
{
  "id": "raci",
  "type": "raci_table",
  "title": "RACI matice",
  "legend": "R = Responsible · A = Accountable · C = Consulted · I = Informed",
  "columns": ["activity", "soc_team", "system_owners", "asset_owner", "ciso_management", "nukib"],
  "column_labels": {
    "activity":         "Aktivita",
    "soc_team":         "SOC Analytický tým",
    "system_owners":    "Správci systémů / zdrojů dat",
    "asset_owner":      "Vlastník dotčeného aktiva",
    "ciso_management":  "CISO / Management",
    "nukib":            "NÚKIB"
  },
  "rows": [
    {"activity": "Triage & Investigace",    "soc_team": "R, A", "system_owners": "C", "asset_owner": "C",    "ciso_management": "–",               "nukib": "–"},
    {"activity": "Notifikace CERT / NÚKIB", "soc_team": "R",    "system_owners": "–", "asset_owner": "–",    "ciso_management": "A",               "nukib": "I (Critical)"},
    {"activity": "Uzavření incidentu",      "soc_team": "R, A", "system_owners": "–", "asset_owner": "I",    "ciso_management": "I (High/Critical)", "nukib": "–"}
  ]
}
```

### Konvence RACI

| Hodnota | Popis |
|---|---|
| `R` | Responsible – provádí aktivitu |
| `A` | Accountable – zodpovídá za výsledek |
| `C` | Consulted – poskytuje součinnost |
| `I` | Informed – je informován o výsledku |
| `I (Critical)` | Informován pouze při Severity Critical |
| `I (High/Critical)` | Informován při Severity High nebo Critical |
| `–` | Není zapojen |

---

## Typ `closure_form` – uzavření incidentu

Sekce uzavření incidentu. Shodná struktura renderování s `form`, ale sémanticky odlišena jako finální krok workbooku.

### Standardní struktura polí

Všechny workbooky by měly obsahovat closure sekci s níže uvedenými poli **v tomto pořadí**. Šablony specifické pro daný typ útoku mohou vložit vlastní pole (např. `attack_type_final`, `vpn_outage_duration`) **za pole `nukib_notification_required`** a **před `root_cause`**.

| `key` | `label` | `type` | Popis |
|---|---|---|---|
| `final_classification` | Klasifikace výsledku | `select` | True Positive / False Positive / Benign True Positive |
| `impact_ki` | Dotčena KI / KII | `select` | Dopad na kritickou infrastrukturu dle ZOKB č. 181/2014 Sb. |
| `impact_primary_service` | Dostupnost primárních služeb organizace | `select` | Dostupnost (CIA: A) klíčových služeb pro klienty / interní provoz |
| `impact_scope` | Rozsah zasažených uživatelů / systémů | `select` | Celoplošný / Významný / Omezený / Individuální |
| `impact_duration` | Doba výpadku / narušení **(dostupnost)** | `select` | Délka narušení dostupnosti (CIA: Availability) |
| `impact_data` | Dopad na data (důvěrnost / integrita) | `select` | Exfiltrace, neoprávněný přístup, narušení integrity (CIA: C, I) |
| `zavaznost` | Závažnost incidentu | `select` | Kritická / Vysoká / Střední / Nízká – dle ZOKB a NIS2 |
| `nukib_notification_required` | Povinnost hlášení NÚKIB | `select` | Povinná / Zvážit / Není vyžadována (ZOKB §8, vyhl. 82/2018 Sb.) |
| *(volitelná šablon. pole)* | | | Pole specifická pro daný typ incidentu |
| `root_cause` | Root Cause | `textarea` | Kořenová příčina incidentu |
| `actions_taken` | Popis přijatých opatření | `textarea` | Souhrn provedených containment a remediation kroků |
| `recommendations` | Doporučení pro zlepšení | `textarea` | Doporučení pro snížení rizika opakování |
| `lessons_learned` | Lessons Learned | `textarea` | Poznatky pro zlepšení detekce, response nebo procesů |
| `related_service_requests` | Související servisní požadavky | `textarea` | Čísla/odkazy na servisní požadavky z průběhu řešení |
| `reporter_notified` | Oznamovatel informován | `select` | Ano / Ne |
| `closed_at` | Datum uzavření | `datetime` | Datum a čas uzavření |
| `closed_by` | Uzavřel | `text` | Jméno analytika, který incident uzavřel |

### CIA anotace v popisech polí

Pole hodnotící specifický aspekt bezpečnostní triády CIA jsou v `label` označena závorkou:
- `(dostupnost)` – vztahuje se k CIA pilíři **Availability** (dostupnost)
- `(důvěrnost / integrita)` – vztahuje se k CIA pilíři **Confidentiality** a **Integrity**

Ostatní pole (rozsah, KI/KII, klasifikace) CIA pilíř explicitně neuvádějí, protože jejich název sám o sobě dostatečně určuje kontext.

### Závažnost – škála a podmínky notifikace NÚKIB

| Závažnost | Typický scénář | Povinnost hlášení |
|---|---|---|
| **Kritická** | KI/KII přímo zasažena + výpadek primárních služeb, NEBO celoplošný výpadek > 4 hod, NEBO exfiltrace dat s KI kontextem | Povinná (ZOKB §8) |
| **Vysoká** | Primární služby narušeny (bez KI dopadu), NEBO výpadek 1–4 hod pro > 30 % uživatelů, NEBO neoprávněný přístup k datům | Zvážit |
| **Střední** | Sekundární systémy zasaženy, omezený rozsah nebo krátký výpadek (15 min – 1 hod) | Není vyžadována |
| **Nízká** | Minimální nebo žádný provozní dopad. Typicky False Positive nebo Benign True Positive | Není vyžadována |

Lhůty hlášení NÚKIB dle vyhlášky č. 82/2018 Sb.: **do 24 h** (první hlášení) · **do 72 h** (detailní hlášení) · **do 30 dní** (závěrečná zpráva).

### Příklad minimální closure sekce

```json
{
  "id": "closure",
  "title": "Uzavření incidentu",
  "type": "closure_form",
  "description": "Uzavření provádí SOC Analytický tým po dokončení Containment & Remediation, nebo ihned po Triage u False Positive / Benign True Positive.",
  "hint": "Před uzavřením ověř, že oznamovatel byl informován o výsledku šetření.",
  "fields": [
    {"key": "final_classification", "label": "Klasifikace výsledku", "type": "select", "editable": true,
      "is_example": true, "value": "True Positive",
      "options": ["True Positive", "False Positive", "Benign True Positive"]},
    {"key": "impact_ki", "label": "Dotčena KI / KII", "type": "select", "editable": true, "value": null,
      "options": ["Ano – KI/KII přímo zasažena", "Nepřímo – systémy nebo služby navazující na KI/KII", "Ne", "Nelze určit"],
      "hint": "Ověř v interním registru aktiv. KI/KII dle zákona č. 181/2014 Sb. (ZOKB) a prováděcí vyhlášky č. 82/2018 Sb."},
    {"key": "impact_primary_service", "label": "Dostupnost primárních služeb organizace", "type": "select", "editable": true, "value": null,
      "options": ["Zcela nedostupné", "Částečně nedostupné / degradované", "Dostupné bez omezení", "Netýká se"],
      "hint": "Primární = služby poskytované organizací klientům / uživatelům nebo klíčové interní provozní procesy organizace."},
    {"key": "impact_scope", "label": "Rozsah zasažených uživatelů / systémů", "type": "select", "editable": true, "value": null,
      "options": ["Celoplošný (> 50 % uživatelů nebo klíčových systémů)", "Významný (10–50 %)", "Omezený (< 10 %)", "Individuální (1 uživatel / 1 systém)"]},
    {"key": "impact_duration", "label": "Doba výpadku / narušení (dostupnost)", "type": "select", "editable": true, "value": null,
      "options": ["> 4 hodiny", "1–4 hodiny", "15 min – 1 hodina", "< 15 min", "Žádný výpadek / narušení"]},
    {"key": "impact_data", "label": "Dopad na data (důvěrnost / integrita)", "type": "select", "editable": true, "value": null,
      "options": ["Exfiltrace dat potvrzena", "Neoprávněný přístup k datům potvrzen", "Integrita dat narušena", "Žádný dopad na data", "Nelze určit"]},
    {"key": "zavaznost", "label": "Závažnost incidentu", "type": "select", "editable": true, "is_example": true, "value": "Vysoká",
      "options": ["Kritická", "Vysoká", "Střední", "Nízká"],
      "option_hints": {
        "Kritická": "KI/KII přímo zasažena + výpadek primárních služeb, NEBO celoplošný výpadek > 4 hod, NEBO exfiltrace dat s KI kontextem – povinná notifikace NÚKIB (ZOKB §8).",
        "Vysoká":   "Primární služby organizace narušeny (bez KI dopadu), NEBO výpadek 1–4 hod pro > 30 % uživatelů, NEBO neoprávněný přístup k datům.",
        "Střední":  "Sekundární systémy zasaženy, omezený rozsah nebo krátký výpadek (15 min – 1 hod), bez dopadu na primární služby a zákazníky.",
        "Nízká":    "Minimální nebo žádný provozní dopad. Typicky False Positive nebo Benign True Positive."
      },
      "hint": "Závažnost urči dle impact faktorů výše. U KI/KII nebo VIS zakládá závažnost Kritická a Vysoká povinnost hlásit incident NÚKIB dle ZOKB (zák. č. 181/2014 Sb., vyhl. č. 82/2018 Sb.) a NIS2."},
    {"key": "nukib_notification_required", "label": "Povinnost hlášení NÚKIB", "type": "select", "editable": true, "value": null,
      "options": ["Povinná – KI/KII nebo VIS + Kritická/Vysoká závažnost (ZOKB §8, vyhl. 82/2018 Sb.)", "Zvážit – hraniční případ", "Není vyžadována"],
      "hint": "Správci KII a VIS jsou povinni hlásit kybernetické bezpečnostní incidenty NÚKIB. Lhůty: do 24 h (první hlášení) · do 72 h (detailní hlášení) · do 30 dní (závěrečná zpráva) – dle vyhlášky č. 82/2018 Sb."},
    {"key": "root_cause",           "label": "Root Cause",                     "type": "textarea", "editable": true, "value": null},
    {"key": "actions_taken",        "label": "Popis přijatých opatření",       "type": "textarea", "editable": true, "value": null},
    {"key": "recommendations",      "label": "Doporučení pro zlepšení",        "type": "textarea", "editable": true, "value": null},
    {"key": "lessons_learned",      "label": "Lessons Learned",                "type": "textarea", "editable": true, "value": null},
    {"key": "related_service_requests", "label": "Související servisní požadavky", "type": "textarea", "editable": true, "value": null,
      "hint": "Čísla nebo odkazy na servisní požadavky vytvořené v průběhu řešení."},
    {"key": "reporter_notified",    "label": "Oznamovatel informován",         "type": "select",   "editable": true, "value": null, "options": ["Ano", "Ne"]},
    {"key": "closed_at",            "label": "Datum uzavření",                 "type": "datetime", "editable": true, "value": null},
    {"key": "closed_by",            "label": "Uzavřel",                        "type": "text",     "editable": true, "value": null}
  ]
}
```

---

## Souhrn speciálních klíčů

| Klíč | Umístění | Popis |
|---|---|---|
| `is_example: true` | pole, kroky, řádky tabulek | Hodnota = ukázka, při klonování se stane placeholderem |
| `auto_value` | pole | Automaticky vyplněno při vytvoření incidentu. Podporované hodnoty: `"case_id"` · `"template_name"` · `"template_version"` · `"template_status"` · `"template_mitre_tactic"` · `"template_mitre_technique"` · `"template_data_sources"` |
| `always_expanded: true` | podsekce v `section_group` | Podsekce se nezbaluje |
| `allow_append: true` | tabulky | Analytik může přidat řádek tlačítkem `+` |
| `allow_delete: true` | tabulky | Analytik může smazat libovolný řádek |
| `append_row_template` | tabulky | Struktura prázdného přidávaného řádku |
| `editable_columns` | tabulky | Sloupce editovatelné analytikem |
| `column_options` | `assets_table` | Sloupce renderované jako `<select>` místo textového pole |
| `status_options` | `action_table` | Seznam hodnot dostupných v dropdownu Stav |
| `classification_hints` | `step_group` | Klasifikační vodítka s pastelově žlutým pozadím (True/False Positive, Severity) |
| `condition` | podsekce, `step_group` | Informativní podmínka zobrazení (nevynucuje logiku) |
| `note` | podsekce, `step_group` | Poznámka analytika zobrazená v záhlaví |
