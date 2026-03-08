# Tvorba SOC Workbooků – Průvodce pro SOC Analytiky

Tento dokument vysvětluje, jak vytvořit vlastní SOC workbook šablonu pro opakující se typy incidentů.
Nepředpokládá se znalost programování – pracuješ jen s textovým souborem ve formátu YAML.

Technická reference (pro pokročilé): [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)

---

## Co je SOC Workbook a proč ho vytvářet?

SOC Workbook je strukturovaný postup práce pro konkrétní typ bezpečnostního incidentu.
Při zakládání nového incidentu v systému vybereš šablonu workbooku – systém předvyplní formulář s příslušnými sekcemi, kroky a kontakty.

```
Šablona workbooku (YAML soubor)
    │
    ▼
Analytik zakládá incident → systém vytvoří dokument podle šablony
    │
    ▼
Analytik vyplní formulář → uloží → incident je zdokumentován
```

**Přínosy vlastní šablony:**
- Nezačínáš od nuly – každý incident stejného typu má stejný základ
- Méně chyb a vynechaných kroků
- Nový kolega vidí přesně, co se u tohoto typu incidentu dělá
- Audit trail: každý krok je zdokumentován

---

## Jak začít – 3 kroky

### 1. Zkopíruj Vanilla šablonu

Soubor `data/workbooks/vanilla_v1.yaml` je připravená kostra. Zkopíruj ho a přejmenuj:

```
vanilla_v1.yaml  →  ransomware_v1.yaml
```

Konvence názvu souboru: `typ_incidentu_v{číslo}.yaml` (malá písmena, podtržítka).

### 2. Uprav soubor v editoru šablon nebo textovém editoru

Nejpohodlnější způsob je otevřít šablonu přímo v aplikaci – sekce **Šablony → Klonovat**.
Alternativně uprav soubor v libovolném textovém editoru (VS Code, Notepad++, ...) a vlož ho do adresáře `data/workbooks/`.

Uprav:
- Metadata šablony (viz sekce níže)
- Kroky vyšetřování (checklist)
- Pole specifická pro daný typ incidentu v sekci Klasifikace a uzavření

### 3. Otestuj šablonu

V aplikaci přejdi do **Šablony** – nová šablona se objeví se stavem `draft`.
Vytvoř zkušební incident, projdi všechny sekce a zkontroluj, zda vše vypadá správně.
Až jsi spokojený, změň `status` na `active`.

---

## Metadata šablony (začátek souboru)

```yaml
template_id: ransomware-v1
name: Ransomware – šifrování dat
version: '1.0'
category: Malware
status: draft
description: Postup pro řešení ransomware útoku ...
mitre_tactic: Impact
mitre_technique: T1486
mitre_subtechnique: ''
data_sources:
  - EDR
  - SIEM
  - Backup systém
```

| Pole | Co vyplnit |
|------|------------|
| `template_id` | Unikátní ID ve formátu `typ-v1` (malá písmena, pomlčky) |
| `name` | Zobrazovaný název v aplikaci |
| `category` | Typ incidentu: Phishing, Malware, DDoS, Ransomware, Insider Threat... |
| `status` | Vždy začínej jako `draft`, po ověření změň na `active` |
| `description` | 1–2 věty – pro koho a na co je šablona |
| `mitre_tactic` | MITRE ATT&CK taktika (viz attack.mitre.org), nebo prázdný řetězec |
| `mitre_technique` | MITRE ATT&CK technika (např. `T1486`), nebo prázdný řetězec |
| `data_sources` | Systémy, které analytik při investigaci použije |

### Komentáře v YAML souboru

YAML podporuje komentáře nativně pomocí znaku `#`. Používej je pro poznámky sobě nebo kolegům – v aplikaci se nezobrazují.

```yaml
# Uprav kroky dle svého prostředí.
- title: Posouzení – ověření alertu
  steps:
    # Tento krok odstraň pokud alert pochází z automatizace.
    - Ověř, zda je alert validní.
```

---

## Sekce workbooku

Workbook se skládá ze sekcí. Každá sekce má `type`, který určuje způsob zobrazení.

### Přehled typů sekcí

| Typ | Kdy použít |
|-----|------------|
| `workbook_header` | Povinná hlavička – vždy jako první sekce |
| `classification` | Povinná – MITRE ATT&CK klasifikace a zdroje dat |
| `contact_table` | Kontakty pro investigaci a eskalaci |
| `section_group` | Skupinový kontejner pro více podsekce (accordion) |
| `form` | Volný formulář s libovolnými poli; nepovinný `hint` zobrazí modrý box nad formulářem |
| `checklist` | Kontrolní seznam kroků – jádro workbooku |
| `assets_table` | Tabulka dotčených aktiv |
| `action_table` | Tabulka akcí Odezva nebo komunikační matice |
| `raci_table` | RACI matice – vždy jako poslední sekce |

### Doporučené pořadí sekcí

```
workbook_header → classification → contact_table → [section_group s kontextem / aktiva]
→ checklist (posouzení, třídění) → action_table (odezva) → action_table (komunikace)
→ form (klasifikace a uzavření) → raci_table
```

---

## Jak upravit checklist (Posouzení, třídění a rozhodování)

Checklist je nejdůležitější část workbooku. Kroky jsou organizovány do skupin (`step_groups`).

### Zkrácený a plný zápis kroků

Jednoduchý krok (bez nápovědy nebo ukázky) zapíšeš jednou řádkou:

```yaml
steps:
  - Ověř záhlaví e-mailu (SPF, DKIM, DMARC).
  - Prověř hash přílohy na VirusTotal.
  - Zhodnoť rozsah kompromitace.
```

Plný zápis použij pro kroky s nápovědou nebo ukázkou vyplnění (`is_example`):

```yaml
steps:
  - action: Zjisti hash přílohy (MD5 / SHA256) – přílohu přímo neotvírej.
    analyst_note: 'SHA256: 3a1f2b…'
    is_example: true
```

### Přidání nové skupiny kroků

```yaml
- title: Analýza lateral movement
  steps:
    - Ověř přihlášení ze zasaženého účtu na jiné systémy (AD event 4624).
    - Zkontroluj RDP / SSH připojení v SIEM za posledních 7 dní.
```

### Přidání nápovědy a klasifikačních vodítek

```yaml
- title: Analýza přílohy
  steps:
    - Prověř hash na VirusTotal.
  hints:
    - Pokud je příloha otevřena na více zařízeních → rozšiř scope.
  classification_hints:
    - 'Hash detekován na TI + příloha otevřena → True Positive, High'
```

- **`hints`** (šedé) – operační poznámky, varování, podmínky pro rozšíření scope
- **`classification_hints`** (žluté) – vodítka pro True/False Positive a Závažnost

### Pravidla pro kroky

- **`id` kroků i skupin nemusíš uvádět** – systém je vygeneruje automaticky z názvu skupiny.
  Pokud chceš mít kontrolu nad ID (např. pro referenci v jiném dokumentu), zadej `id` ručně.
- `action` – instrukce pro analytika formulovaná jako „co má udělat"
- `analyst_note` – pokud necháš prázdné, aplikace doplní automaticky `null`; přidej `is_example: true` pro ukázku vyplnění

---

## Pole `is_example` – ukázky vyplnění

Pole nebo kroky s `is_example: true` slouží jako **ukázka vyplnění**. Při vytvoření nového incidentu se hodnota stane placeholderem a analytik ji přepíše vlastní hodnotou.

```yaml
- key: root_cause
  label: Root Cause
  type: textarea
  is_example: true
  value: Uživatel otevřel přílohu phishingového e-mailu → spuštění dropperu → šifrování disku
```

Dobré pro: `root_cause`, `actions_taken`, kroky checklistu – všude, kde chceš ukázat, jak správně vyplněné pole vypadá.

> **`is_example` v kontaktní tabulce nepoužívej.** Řádky `contact_table` jsou předvyplněné jako běžný editovatelný text; `is_example: true` v jejich řádcích nemá efekt.

---

## Sekce Klasifikace a uzavření – co neměnit

Sekce uzavření incidentu (type `form` s klíčem `hint`) obsahuje **standardní pole shodná ve všech workboocích**.
Tato pole **neměň** – zajišťují konzistenci a regulatorní soulad:

- `impact_level`, `impact_primary_service`, `impact_scope`, `impact_duration`, `impact_data`
- `nukib_notification_required`, `ucl_notification_required`
- `root_cause`, `actions_taken`, `recommendations`
- `related_service_requests`, `reporter_notified`, `closed_at`

**Šablonově specifická pole** (např. `attack_type_final`, `vpn_outage_duration`) přidej **za** `ucl_notification_required` a **před** `root_cause`.

---

## Checklist před aktivací šablony

Před změnou `status` z `draft` na `active` ověř:

- [ ] `template_id` je unikátní – zkontroluj ostatní soubory v `data/workbooks/`
- [ ] `name`, `category`, `description` jsou srozumitelně vyplněny
- [ ] MITRE taktika a technika odpovídají typu incidentu
- [ ] Kroky checklistu dávají smysl v logickém pořadí
- [ ] Sekce Klasifikace a uzavření obsahuje všechna standardní pole
- [ ] Testovací incident byl vytvořen a všechny sekce se správně zobrazily
- [ ] Tisk incidentu (`Tisk / Uložit PDF`) byl ověřen

---

## Časté chyby a tipy

**YAML je citlivý na odsazení.** Každá úroveň se odsazuje o 2 mezery. Nikdy nesměšuj mezery a tabulátory.
V editoru šablon (v aplikaci) máš zvýraznění syntaxe a validaci přímo v reálném čase.

**Speciální znaky v hodnotách.** Pokud hodnota obsahuje dvojtečku, uvozovky nebo začíná zvláštním znakem, ohraň ji apostrofy nebo uvozovkami:
```yaml
hint: 'Lhůty: do 24 h · do 72 h · do 30 dní'
value: "Faktura #2025-112"
```

**Verzování.** Pokud výrazně měníš existující šablonu, vytvoř novou verzi souboru (`ransomware_v2.yaml`) a starý soubor označ jako `deprecated`. Existující incidenty zůstanou funkční.

**Testovací incident nevyplňuj doopravdy.** Zkušební incident po ověření smaž – funkce dostupná pro admina.
