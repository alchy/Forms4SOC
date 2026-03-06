# Tvorba SOC Workbooků – Průvodce pro SOC Analytiky

Tento dokument vysvětluje, jak si vytvořit vlastní SOC workbook šablonu pro opakující se typy incidentů.
Neočekává se znalost programování – pracuješ jen s textovým souborem ve formátu JSON.

Technická reference (pro pokročilé): [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)

---

## Co je SOC Workbook a proč ho vytvářet?

SOC Workbook je strukturovaný postup práce pro konkrétní typ bezpečnostního incidentu.
Při zakládání nového incidentu v systému si vybereš šablonu workbooku a systém předvyplní formulář – sekce, kroky, kontakty, RACI matici.

**Přínosy vlastní šablony:**
- Nezačínáš od nuly – každý incident stejného typu má stejný základ
- Méně chyb a zapomenutých kroků
- Nový kolega vidí, co se u tohoto typu incidentu dělá
- Audit trail: každý krok je zdokumentován

---

## Jak začít – 3 kroky

### 1. Zkopíruj Vanilla šablonu

Soubor `data/workbooks/vanilla_v1.json` je připravená kostra. Zkopíruj ho a přejmenuj:

```
vanilla_v1.json  →  ransomware_v1.json
```

Konvence názvu souboru: `typ_incidentu_v{číslo}.json`, malá písmena, podtržítka.

### 2. Uprav soubor v textovém editoru

Otevři soubor v libovolném textovém editoru (VS Code, Notepad++, ...) a uprav:
- Metadata šablony (viz sekce níže)
- Kroky vyšetřování (checklist)
- Specifická pole v sekci Uzavření incidentu

### 3. Vlož soubor do systému a otestuj

Zkopíruj soubor do adresáře `data/workbooks/` (nebo jiného adresáře nakonfigurovaného v Nastavení).
V aplikaci přejdi do **Šablony** – nová šablona se objeví v seznamu se stavem `draft`.
Vytvoř zkušební incident, projdi všechny sekce a zkontroluj, zda vše vypadá správně.
Až jsi spokojený, změň `status` na `active`.

---

## Struktura souboru

### Metadata šablony (začátek souboru)

```json
{
  "template_id": "ransomware-v1",
  "name": "Ransomware – šifrování dat",
  "version": "1.0",
  "category": "Malware",
  "status": "draft",
  "description": "Postup pro řešení ransomware útoku ...",
  "mitre_tactic": "Impact",
  "mitre_technique": "T1486",
  "mitre_subtechnique": "",
  "data_sources": ["EDR", "SIEM", "Backup systém"]
}
```

| Pole | Co vyplnit |
|---|---|
| `template_id` | Unikátní ID, formát `typ-v1` (malá písmena, pomlčky) |
| `name` | Zobrazovaný název v aplikaci |
| `category` | Typ incidentu: Phishing, Malware, DDoS, Ransomware, Insider Threat... |
| `status` | Vždy začínej jako `draft`, po ověření změň na `active` |
| `description` | 1–2 věty – pro koho a na co je šablona |
| `mitre_*` | MITRE ATT&CK taktika a technika (viz attack.mitre.org), nebo prázdný řetězec |
| `data_sources` | Systémy, které analytik při investigaci použije |

### Komentáře `_doc` – pro tvůrce šablony

Klíče začínající `_doc` jsou autorské komentáře – **v aplikaci se nezobrazují**. Vanilla šablona je jimi hustě okomentovaná. Po dokončení šablony je můžeš ponechat nebo smazat.

```json
{
  "_doc": "Tento text vidí jen autor šablony v textovém editoru.",
  "id": "triage",
  "title": "Triage"
}
```

---

## Sekce workbooku

Workbook se skládá ze sekcí. Každá sekce má `type`, který určuje, jak se zobrazí.

### Přehled typů sekcí

| Typ | Kdy použít |
|---|---|
| `workbook_header` | Povinná hlavička – vždy jako první sekce |
| `classification` | Povinná – MITRE ATT&CK klasifikace |
| `contact_table` | Kontakty pro investigaci a eskalaci |
| `section_group` | Skupinový kontejner pro více podsekce (accordion) |
| `form` | Volný formulář s libovolnými poli |
| `checklist` | Kontrolní seznam kroků – jádro workbooku |
| `assets_table` | Tabulka dotčených aktiv |
| `action_table` | Tabulka containment / remediation akcí |
| `notification_table` | Tabulka komunikace a notifikací |
| `closure_form` | Uzavření incidentu – vždy jako předposlední sekce |
| `raci_table` | RACI matice – vždy jako poslední sekce |

### Doporučené pořadí sekcí

```
workbook_header → classification → contacts → [kontext / aktiva] →
triage_investigation (checklist) → containment_remediation → [communication] →
closure → raci
```

---

## Jak upravit checklist (Triage & Investigace)

Checklist je nejdůležitější část workbooku. Kroky jsou organizovány do skupin (`step_groups`).

### Přidání nové skupiny kroků

```json
{
  "id": "lateral_movement",
  "title": "Analýza lateral movement",
  "steps": [
    {
      "id": "lm_01",
      "action": "Ověř přihlášení ze zasaženého účtu na jiné systémy (AD event 4624).",
      "analyst_note": null,
      "done": false
    }
  ]
}
```

### Přidání nápovědy a klasifikačních vodítek

```json
{
  "hints": [
    "Pokud jsou zasaženy více než 3 systémy → rozšiř scope a informuj CISO."
  ],
  "classification_hints": [
    "Šifrování potvrzeno na > 10 systémech → Kritická | < 10 systémů, zálohy OK → Vysoká"
  ]
}
```

- **`hints`** (šedé) – operační poznámky, varování, podmínky
- **`classification_hints`** (žluté) – vodítka pro True/False Positive a Závažnost

### Pravidla pro kroky

- `id` musí být unikátní v celém souboru (doporučený formát: `skupina_číslo`, např. `lm_01`)
- `action` – formuluj jako instrukci pro analytika, co má udělat
- `analyst_note` – vždy začínej jako `null`; přidej `"is_example": true` pokud chceš ukázat příklad vyplnění
- `done` – vždy `false`

---

## Jak přidat pole `is_example`

Pole nebo kroky s `"is_example": true` slouží jako **ukázka vyplnění**. Při vytvoření nového incidentu se hodnota stane placeholderem a analytik ji přepíše vlastní hodnotou.

```json
{
  "key": "root_cause",
  "label": "Root Cause",
  "type": "textarea",
  "editable": true,
  "is_example": true,
  "value": "Uživatel otevřel přílohu phishingového e-mailu → spuštění dropperu → šifrování disku"
}
```

Dobré pro: `root_cause`, `actions_taken`, kroky checklistu – všude, kde chceš ukázat, jak by správně vyplněné pole vypadalo.

---

## Sekce Uzavření incidentu – co neměnit

Sekce `closure_form` obsahuje **standardní pole**, která jsou shodná ve všech workboocích. Tato pole **neměň** (klíče, options, hinty) – zajišťují konzistenci a regulatorní soulad:

- `impact_ki`, `impact_primary_service`, `impact_scope`, `impact_duration`, `impact_data`
- `zavaznost`, `nukib_notification_required`
- `root_cause`, `actions_taken`, `recommendations`, `lessons_learned`
- `related_service_requests`, `reporter_notified`, `closed_at`, `closed_by`

**Šablonově specifická pole** (např. `attack_type_final`, `affected_service`, `vpn_outage_duration`) přidej **za** `nukib_notification_required` a **před** `root_cause`.

---

## Checklist před aktivací šablony

Před změnou `status` z `draft` na `active` ověř:

- [ ] `template_id` je unikátní (zkontroluj ostatní soubory v `data/workbooks/`)
- [ ] `name`, `category`, `description` jsou srozumitelně vyplněny
- [ ] MITRE taktika a technika odpovídají typu incidentu
- [ ] Všechna `id` sekcí a kroků jsou unikátní v rámci souboru
- [ ] Kroky checklistu dávají smysl v logickém pořadí
- [ ] Pole v closure sekci obsahují všechna standardní pole
- [ ] Testovací incident byl vytvořen a všechny sekce se správně zobrazily
- [ ] Tisk incidentu (`Tisk / Uložit PDF`) byl ověřen

---

## Časté chyby a tipy

**JSON je citlivý na formátování.** Chybějící čárka nebo závorka způsobí, že soubor nelze načíst.
Použij validátor: vložení souboru na [jsonlint.com](https://jsonlint.com) okamžitě ukáže chybu.

**Unikátnost ID.** Každé `id` (sekce, krok) musí být unikátní v celém souboru. Doporučená konvence: `prefix_číslo` (např. `t_01`, `i_03`, `lm_01`).

**Verzování.** Pokud výrazně měníš existující šablonu, vytvoř novou verzi souboru (`ransomware_v2.json`) a starý soubor označ jako `deprecated`. Existující incidenty zůstanou funkční.

**Testovací incident nevyplňuj doopravdy.** Zkušební incident po ověření smaž (funkce dostupná pro admina).
