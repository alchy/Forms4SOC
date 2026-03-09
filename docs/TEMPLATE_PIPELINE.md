# Konverze šablony YAML → JSON incident

Tento dokument popisuje pipeline, která transformuje YAML soubor šablony workbooku
do JSON dokumentu incidentu připraveného k vyplnění analytikem.

Určeno pro: vývojáře rozšiřující backend, autory šablon, kteří potřebují pochopit,
co systém dělá s jejich YAML souborem.

---

## Co to je a k čemu slouží?

YAML šablony jsou autorsky přívětivý formát pro popis struktury workbooku – zkrácený zápis,
komentáře, předdefinované příkladové hodnoty. Aplikace je ale interně nepředává frontendu
v surovém stavu. Místo toho každý YAML soubor projde třístupňovou pipeline:

1. **Parsování** – `yaml.safe_load()` převede YAML na Python slovník.
2. **Normalizace** – doplní výchozí hodnoty, vygeneruje chybějící ID, rozbalí zkrácené
   zápisy kroků. Výsledkem je úplná, konzistentní datová struktura.
3. **Klonování** – při zakládání incidentu se šablona hluboce zkopíruje, příkladové hodnoty
   se přesunou do placeholderů a `auto_value` pole se vyplní runtime hodnotami (case_id,
   metadata šablony). Výsledek se serializuje jako JSON a uloží do `data/incidents/`.

---

## Jak to funguje?

```
data/workbooks/phishing_v2.yaml
    │   (yaml.safe_load)
    ▼
Python dict – surová data šablony
    │   (_normalize_template)
    ▼
Normalizovaná struktura – úplná ID, výchozí hodnoty, kroky jako dict
    │   (SOCTemplate Pydantic model)
    ▼
GET /api/v1/templates/{id}  →  JSON response pro frontend / editor šablon
    │
    │   POST /api/v1/cases/ {template_id: "phishing-v2"}
    ▼
_clone_template_sections + _fill_auto_values + _strip_examples
    │
    ▼
IncidentCase.data  →  JSON soubor data/incidents/UIB-09032026-1045-3712.json
```

Šablona samotná není nikdy modifikována. Každý incident dostane vlastní hlubokou kopii
sekcí, izolovanou od ostatních incidentů i od šablony.

---

## Rychlý start – co se stane po `POST /api/v1/cases/`

Zavolej:

```bash
curl -X POST http://localhost:8080/api/v1/cases/ \
     -H "Content-Type: application/json" \
     -d '{"template_id": "phishing-v2"}'
```

Systém:
1. Načte `data/workbooks/phishing_v2.yaml`, spustí normalizaci.
2. Vygeneruje `case_id` ve formátu `UIB-DDMMYYYY-HHMM-RRRR` (např. `UIB-09032026-1045-3712`).
3. Hluboce zkopíruje `sections` ze šablony.
4. `example:` zkratku rozbalí na `is_example: true` + `value`/`analyst_note`, pak přesune do placeholderů.
5. `auto_value` pole (ticket_id, workbook_name, …) vyplní runtime hodnotami.
6. Uloží `UIB-09032026-1045-3712.json` do `data/incidents/`.
7. Vrátí `IncidentCase` jako JSON s HTTP 201.

---

## Krok za krokem – co dělá každá fáze

### 1. Parsování

`TemplateService.list_templates()` a `get_template()` čtou soubory z adresáře
nakonfigurovaného v SQLite (`templates_dir`). Výchozí hodnota je `data/workbooks/`.

```python
data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
```

Souborový systém je jedinou závislostí. Chybně naformátovaný YAML způsobí `WARNING`
v logu a soubor je přeskočen – ostatní šablony se načtou normálně.

---

### 2. Normalizace (`_normalize_template`)

Normalizace umožňuje psát šablony ve zkráceném formátu bez opakujícího se boilerplate.
Spouští se ihned po parsování, ještě před validací Pydantic modelem.

Platí pravidlo: **existující hodnoty se nikdy nepřepisují** – normalizace používá výhradně
`setdefault()`. Plný formát šablon je beze změny zpětně kompatibilní.

Normalizace probíhá rekurzivně přes všechny sekce včetně `subsections`.

#### Doplnění výchozích hodnot polí (`_norm_field`)

Každé pole formuláře (`fields[]`) dostane chybějící klíče:

| Klíč | Výchozí hodnota |
|------|-----------------|
| `type` | `"text"` |
| `editable` | `true` |
| `value` | `null` |

Příklad – ve zkráceném YAML zápisu:
```yaml
- key: reporter_name
  label: Jméno oznamovatele
```
Po normalizaci je ekvivalentní:
```yaml
- key: reporter_name
  label: Jméno oznamovatele
  type: text
  editable: true
  value: null
```

#### Rozbalení zkrácených kroků checklistu (`_norm_step`)

Krok zapsaný jako prostý řetězec se rozbalí na plný slovník:

```yaml
# zkrácený zápis v YAML šabloně
steps:
  - Ověř záhlaví e-mailu (SPF, DKIM, DMARC).
```

Po normalizaci:
```json
{
  "id": "triage_investigation_email_analysis_01",
  "action": "Ověř záhlaví e-mailu (SPF, DKIM, DMARC).",
  "analyst_note": null,
  "done": false
}
```

#### Generování ID (`_slugify`)

Sekce, skupiny kroků a kroky bez explicitního `id` dostanou automaticky vygenerované ID
ze svého `title` přes `_slugify()`:

```
"Analýza obsahu e-mailu"  →  "analyza_obsahu_e_mailu"
```

`_slugify` provede Unicode NFD normalizaci, odstraní diakritiku, převede na malá písmena
a nahradí mezery a pomlčky podtržítky.

ID kroku má formát `{section_id}_{group_id}_{pořadí:02d}`, například:
`triage_investigation_email_analysis_01`.

> **Poznámka:** Ruční `id` v YAML šabloně má vždy přednost. Explicitní ID použij všude,
> kde chceš stabilní referenci (např. pro logování nebo budoucí migraci dat).

---

### 3. Klonování šablony do incidentu (`case_service`)

Klonování spouští `POST /api/v1/cases/`. Šablona musí být normalizována – proto se volá
přes `TemplateService.get_template()`, nikoli přímým čtením souboru.

#### Hluboká kopie sekcí

```python
cloned = copy.deepcopy(sections)
```

Hluboká kopie zajišťuje, že úpravy v incidentu nikdy neovlivní šablonu ani jiné incidenty.

#### Zpracování příkladových hodnot (`_strip_examples`)

Pole a kroky se zkratkou `example:` v YAML šabloně slouží jako ukázky správného vyplnění.
Normalizátor zkratku rozbalí na `is_example: true` + `value` resp. `analyst_note`.
Při klonování pak `_strip_examples` přesune hodnotu do klíče `example` v JSON incidentu,
kde ji frontend zobrazí jako šedý placeholder, a `value`/`analyst_note` nastaví na `null`.

Chování závisí na typu záznamu:

**Formulářové pole:**
```yaml
# v šabloně (YAML zkratka)
- key: root_cause
  label: Root Cause
  type: textarea
  example: Uživatel otevřel přílohu phishingového e-mailu
```
```json
// v novém incidentu (po normalizaci + klonování)
{
  "key": "root_cause",
  "label": "Root Cause",
  "type": "textarea",
  "is_example": true,
  "value": null,
  "example": "Uživatel otevřel přílohu phishingového e-mailu"
}
```

**Krok checklistu:**
```yaml
# v šabloně (YAML zkratka)
- action: Ověř záhlaví e-mailu (SPF, DKIM, DMARC)
  example: 'SPF: fail · DKIM: none · Doména spoofována'
```
```json
// v novém incidentu (po normalizaci + klonování)
{
  "action": "Ověř záhlaví e-mailu (SPF, DKIM, DMARC)",
  "analyst_note": null,
  "example": "SPF: fail · DKIM: none · Doména spoofována",
  "is_example": true,
  "done": false
}
```

> **Pozor:** `example:` v řádcích `contact_table` nemá efekt – kontaktní tabulky
> jsou vždy editovatelné přímo a příkladový mechanismus se na ně nevztahuje.

#### Vyplnění automatických hodnot (`_fill_auto_values`)

Pole s klíčem `auto_value` dostanou hodnotu nastavenou při vytvoření incidentu. Nahrazení
probíhá rekurzivně přes celou strukturu sekcí.

| `auto_value` | Vyplněná hodnota |
|---|---|
| `case_id` | Vygenerované ID incidentu, např. `UIB-09032026-1045-3712` |
| `template_name` | `template.name` |
| `template_version` | `template.version` |
| `template_status` | `template.status` |
| `template_mitre_tactic` | `template.mitre_tactic` |
| `template_mitre_technique` | `template.mitre_technique` |
| `template_data_sources` | Zdroje dat jako čárkou oddělený řetězec |

Pole s `auto_value` mají v šabloně typicky `editable: false` – analytik je nemůže změnit.

---

## Přehled API

| Metoda | Endpoint | Přístup | Popis |
|--------|----------|---------|-------|
| `GET` | `/api/v1/templates/` | auth | Seznam všech šablon (normalizované, jako JSON) |
| `GET` | `/api/v1/templates/{id}` | auth | Detail šablony |
| `GET` | `/api/v1/templates/{id}/source` | admin | Zdrojový YAML soubor (pro editor) |
| `PUT` | `/api/v1/templates/{id}` | admin | Uložení upraveného YAML |
| `POST` | `/api/v1/templates/` | admin | Vytvoření nového souboru šablony |
| `DELETE` | `/api/v1/templates/{id}` | admin | Smazání souboru šablony |
| `POST` | `/api/v1/cases/` | auth | Vytvoření incidentu ze šablony |

---

## Přehled funkcí a tříd

| Identifikátor | Soubor | Popis |
|---|---|---|
| `_slugify(text)` | `template_service.py` | Převede název na ASCII slug s podtržítky |
| `_norm_field(field)` | `template_service.py` | Doplní `type`, `editable`, `value` |
| `_norm_step(step, idx, prefix)` | `template_service.py` | Rozbalí string krok, doplní `id`, `done`, `analyst_note` |
| `_norm_group(group, idx, section_id)` | `template_service.py` | Doplní ID skupiny, normalizuje kroky |
| `_norm_section(section, idx)` | `template_service.py` | Doplní ID sekce, rekurzivně normalizuje pole, kroky a subsekce |
| `_normalize_template(data)` | `template_service.py` | Vstupní bod normalizace – projde všechny sekce |
| `TemplateService` | `template_service.py` | CRUD pro YAML soubory šablon |
| `get_template_service(db)` | `template_service.py` | FastAPI dependency – vrátí `TemplateService` s cestou z DB |
| `generate_case_id(username)` | `case_service.py` | Vygeneruje `UIB-DDMMYYYY-HHMM-RRRR` |
| `_strip_examples(obj)` | `case_service.py` | Přesune hodnoty označené `is_example: true` do `example` placeholderů |
| `_fill_auto_values(obj, auto_values)` | `case_service.py` | Vyplní `auto_value` pole runtime hodnotami |
| `_clone_template_sections(sections)` | `case_service.py` | Hluboká kopie + strip examples |
| `create_case(storage, template, username)` | `case_service.py` | Kompletní pipeline: klon → auto_values → uložení |
