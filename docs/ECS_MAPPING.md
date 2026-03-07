# ECS Mapping – Forms4SOC → Elastic Common Schema

Tento dokument mapuje klíče polí používané v šablonách Forms4SOC na odpovídající pole
[Elastic Common Schema (ECS)](https://www.elastic.co/guide/en/ecs/current/index.html).

**Účel:** Podklad pro implementaci Elasticsearch field aliases nebo ingest pipeline,
která umožní dotazovat exportované incidenty přes standardní ECS jména polí
(pro SIEM korelaci, Kibana dashboardy, alerting) bez nutnosti jakýchkoli změn v aplikaci.

**Přístup:** Pole `ecs_field` bude volitelným metadatovým klíčem v definici pole šablony.
Při exportu/importu do Elasticsearch jej čte transformační vrstva.
Pole bez `ecs_field` jsou Forms4SOC-specifická a nemají ECS ekvivalent.

---

## Legenda shody

| Značka | Význam |
|--------|--------|
| `+++` | Přímá shoda – sémantika i datový typ odpovídají |
| `++`  | Dobrá shoda – sémantika sedí, drobné rozdíly v typu nebo granularitě |
| `+`   | Částečná shoda – překryv sémantiky, ECS pole se obvykle používá v jiném kontextu |
| `–`   | Bez ECS ekvivalentu – SOC/Forms4SOC specifické pole |

---

## Klasifikace (`classification`)

Pole sekce `classification` mají nejsilnější a nejpřímější ECS mapování.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `mitre_tactic` | `threat.tactic.name` | `+++` | Přímý ekvivalent |
| `mitre_technique` | `threat.technique.name` | `+++` | Přímý ekvivalent; ECS také `threat.technique.id` pro kód T15xx |
| `mitre_subtechnique` | `threat.technique.subtechnique.name` | `+++` | Přímý ekvivalent; hodnota obsahuje ID i název (např. `T1566.001 – Spearphishing Attachment`) |
| `data_sources` | – | `–` | MITRE data sources nemají ECS ekvivalent |

---

## Dotčená aktiva (`assets_table`)

Pole v tabulce dotčených aktiv mapují na ECS `host.*`.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `asset_name` | `host.name` | `+++` | Hostname nebo název systému |
| `asset_ip` | `host.ip` | `+++` | IP adresa; u DDoS šablony může být CIDR blok – ECS předpokládá konkrétní IP |
| `asset_type` | `host.type` | `++` | Typ hosta; ECS hodnoty nejsou normalizovány, naše hodnoty (Endpoint, Server, VPN brána…) jsou přijatelné |
| `critical_infrastructure` | – | `–` | SOC/regulatorní klasifikace bez ECS ekvivalentu |
| `contact_owner` | – | `–` | Organizační pole |
| `guarantor` | – | `–` | Organizační pole |
| `email` (vlastníka) | – | `–` | Email vlastníka aktiva, nikoli technická identita |
| `phone` (vlastníka) | – | `–` | Telefon vlastníka aktiva |

---

## Kontaktní matice (`contact_table`)

Kontakty jsou osoby/role, nikoli technické účty. Shoda je částečná – ECS `user.*`
byl navržen pro technické identity (AD/LDAP účty), nikoli pro organizační kontakty.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `name` | `user.full_name` | `+` | Sémanticky správné, jiný kontext použití |
| `email` | `user.email` | `++` | Přímý ekvivalent, kontext mírně odlišný |
| `phone` | `user.phone` | `++` | ECS `user.phone` existuje, méně běžné |
| `system_role` | – | `–` | Organizační role, nikoli systémová |
| `when_to_contact` | – | `–` | Procesní pole bez ECS ekvivalentu |

---

## Automatizovaná detekce (sekce `automated_detection`)

Pole popisující SIEM alert / automatizovanou detekci.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `alert_timestamp` | `event.created` | `++` | Čas vzniku alertu; ECS rozlišuje `event.created` (záznam) vs `event.start` (začátek události) |
| `alert_id` | `event.id` | `+++` | ID alertu nebo pravidla |
| `detection_tool` | `observer.product` | `++` | ECS `observer.*` popisuje detekční nástroj/sensor; `observer.name` pro jméno, `observer.product` pro produkt |
| `affected_asset_auto` | `host.name` | `+` | Volný text – může obsahovat hostname i IP dohromady; v ECS by bylo odděleno |
| `alert_description` | `event.reason` | `+` | ECS `event.reason` pro strojový popis; `message` pro human-readable |

---

## Hlášení osobou (sekce `reported_by_person`)

Pole oznamovatele incidentu. ECS nemá přímý namespace pro „reportéra" – nejbližší je `user.*`,
ale v jiném kontextu.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `reported_at` | `event.created` | `++` | Čas přijetí hlášení |
| `reporter_name` | `user.full_name` | `+` | Oznamovatel není technický user; kontext odlišný |
| `reporter_contact` | `user.email` | `+` | Kombinace e-mail + telefon v jednom poli; nelze přímo mapovat |
| `reporter_department` | – | `–` | Organizační jednotka bez ECS ekvivalentu |
| `affected_user` | `user.target.full_name` | `+` | ECS `user.target.*` pro postižený účet; zde je to jen jméno osoby |
| `affected_asset` | `host.name` | `+` | Volný text, může obsahovat hostname i mailbox |
| `target_type` | – | `–` | SOC klasifikace cíle útoku |
| `description_by_reporter` | `event.reason` | `+` | Popis incident vlastními slovy oznamovatele |

---

## Phishing – specifická pole

### E-mailová analýza (checklist kroky, `analyst_note`)

Kroky checklistu jsou procesní záznamy analytika – `analyst_note` je volný text
bez smysluplného ECS mapování. Níže jsou extrahované **datové artefakty**,
které by při strukturovaném uložení mapovaly na ECS:

| Datový artefakt | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| E-mailová adresa odesílatele | `email.from.address` | `+++` | Přímý ekvivalent |
| E-mailová adresa příjemce | `email.to.address` | `+++` | Přímý ekvivalent |
| Předmět e-mailu | `email.subject` | `+++` | Přímý ekvivalent |
| Tělo e-mailu | `email.body.content` | `+++` | Přímý ekvivalent |
| Název přílohy | `email.attachments.file.name` | `+++` | Přímý ekvivalent |
| Hash přílohy (SHA256) | `email.attachments.file.hash.sha256` | `+++` | Přímý ekvivalent |
| Hash přílohy (MD5) | `email.attachments.file.hash.md5` | `+++` | Přímý ekvivalent |
| URL z e-mailu | `url.full` | `+++` | Přímý ekvivalent |
| Doména z URL | `url.domain` | `+++` | Přímý ekvivalent |
| SPF výsledek | – | `–` | ECS nemá standardní pole pro SPF/DKIM/DMARC výsledky |
| DKIM výsledek | – | `–` | Viz výše |
| DMARC výsledek | – | `–` | Viz výše |

> **Poznámka:** Tato pole jsou v aktuálních šablonách zaznamenávána jako volný text
> v `analyst_note` kroků checklistu. Pro ECS mapování by musela být strukturována
> jako samostatná datová pole (v nové sekci nebo rozšíření šablony).

---

## DDoS – specifická pole

### Síťové artefakty útoku (z checklistu `analyst_note`)

Analogicky k phishingu – datové artefakty extrahované ze struktury útoku:

| Datový artefakt | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| Zdrojová IP/CIDR | `source.ip` | `++` | ECS předpokládá konkrétní IP; CIDR blok nemá přímý ekvivalent |
| Cílová IP (VPN GW) | `destination.ip` | `+++` | Přímý ekvivalent |
| Cílový port | `destination.port` | `+++` | Přímý ekvivalent |
| Protokol (TCP/UDP/ICMP) | `network.protocol` nebo `network.transport` | `++` | ECS rozlišuje application protocol (`network.protocol`) a transport (`network.transport`) |
| Objem útoku (bytes) | `network.bytes` | `+` | ECS `network.bytes` je pro jedno spojení, nikoli aggregate objem |
| ASN zdrojového bloku | `source.as.number` | `+++` | Přímý ekvivalent |
| Geolokace zdrojů | `source.geo.country_iso_code` | `+++` | Přímý ekvivalent |

### Uzavírací pole DDoS-specifická (sekce `closure`)

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `attack_type_final` | `threat.technique.subtechnique.name` | `++` | Duplicita s `classification.mitre_subtechnique`; v ECS by bylo jedno pole |
| `attack_volume` | – | `–` | Volný text (Gbps/Mpps); ECS nemá aggregate attack volume |
| `attack_duration` | – | `–` | Volný text; lze odvodit z `event.start` / `event.end` |
| `vpn_outage_duration` | – | `–` | SOC-specifické |
| `vpn_availability_confirmed` | – | `–` | SOC-specifické |

---

## Uzavření incidentu – společná pole (`closure`)

Pole sekce uzavření jsou převážně SOC-specifická a nemají přímý ECS ekvivalent.

| Forms4SOC `key` | ECS pole | Shoda | Poznámka |
|-----------------|----------|:-----:|----------|
| `closed_at` | `event.end` | `++` | Čas ukončení události |
| `final_classification` | – | `–` | True/False Positive je SOC-specifická klasifikace |
| `impact_level` | – | `–` | SOC závažnostní škála (Nízká/Střední/Vysoká/Kritická) |
| `impact_scope` | – | `–` | Rozsah zasažených uživatelů/systémů |
| `impact_duration` | – | `–` | Doba výpadku |
| `impact_data` | – | `–` | Dopad na data (důvěrnost/integrita) |
| `impact_primary_service` | – | `–` | Dostupnost primárních služeb |
| `nukib_notification_required` | – | `–` | Regulatorní povinnost hlášení (CZ-specifické) |
| `ucl_notification_required` | – | `–` | Regulatorní povinnost hlášení (CZ-specifické) |
| `root_cause` | – | `–` | Volný text; ECS nemá standardní pole pro root cause |
| `actions_taken` | – | `–` | Volný text; procesní pole |
| `recommendations` | – | `–` | Volný text; procesní pole |
| `related_service_requests` | – | `–` | ITSM reference; SOC-specifické |
| `reporter_notified` | – | `–` | Procesní pole |

---

## Metadata šablony (top-level JSON klíče)

Metadata celého workbooku (mimo sekce) – platí pro celý incident dokument.

| Forms4SOC klíč | ECS pole | Shoda | Poznámka |
|----------------|----------|:-----:|----------|
| `template_id` | – | `–` | Interní identifikátor šablony |
| `mitre_tactic` (template metadata) | `threat.tactic.name` | `+++` | Stejné jako v sekci `classification` |
| `mitre_technique` (template metadata) | `threat.technique.name` | `+++` | Stejné jako v sekci `classification` |
| `mitre_subtechnique` (template metadata) | `threat.technique.subtechnique.name` | `+++` | Hodnota šablony před výběrem analytikem |
| `category` | `event.category` | `+` | ECS `event.category` má normalizované hodnoty (malware, intrusion_detection…); naše hodnoty (Phishing, DDoS) jsou jinak pojmenované |

---

## Souhrn – přehled ECS namespaců a jejich využití

| ECS namespace | Počet přímých mapování | Sekce / kontext |
|---------------|----------------------:|-----------------|
| `threat.*` | 3 | `classification`, template metadata |
| `host.*` | 2–3 | `assets_table`, detekce |
| `email.*` | 7 | phishing checklist artefakty |
| `user.*` | 2–3 | `contact_table`, reporter |
| `event.*` | 3 | detekce, uzavření |
| `observer.*` | 1 | automatizovaná detekce (`detection_tool`) |
| `url.*` | 2 | phishing artefakty |
| `source.*`, `destination.*` | 4 | DDoS artefakty |
| `network.*` | 2 | DDoS artefakty |

---

## Co toto mapování neřeší

**Vnořené pole (nested arrays):** Pole v `rows[]` tabulek (assets, contacts) jsou uvnitř
nested Elasticsearch objektů. Field alias v Elasticsearch nemůže ukazovat na pole uvnitř
nested array – pro tato pole by byl potřeba ingest pipeline nebo runtime field.

**Strukturovaná pole z checklistu:** Datové artefakty phishingu a DDoS
(emailové hlavičky, hash přílohy, zdrojové CIDR bloky) jsou aktuálně uloženy
jako volný text v `analyst_note`. Pro ECS mapování by musela být strukturována
jako samostatná pole – to by znamenalo rozšíření šablon.

**Přímé top-level mapování:** Pole ve `section_group` subsections a uvnitř `step_groups`
jsou hluboko vnořena v JSON struktuře. Elasticsearch field alias funguje dobře
pro top-level nebo mírně vnořená pole; pro hluboce vnořené struktury
je ingest pipeline spolehlivější.
