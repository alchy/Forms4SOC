# SOC Playbook



###### Hlavička:



|Název playbooku|Podezřelý e-mail|
|-|-|
|Playbook ID|2026-001|
|Verze|1.0|
|Datum poslední aktualizace|4.03.2026|
|Autor / vlastník|SOC Analytický tým|
|Status|Draft|



\*Status: `Draft` – pracovní verze, `Active` – používaná verze, `Deprecated` - stažena z provozu



###### 

###### Klasifikace:



|Kategorie incidentu|Phishing|
|-|-|
|MITRE Tactic|Initial Access|
|MITRE Technique|T1566 – Phishing|
|MITRE Sub-technique|T1566.001 – Spearphishing Attachment|
|Zdroje dat pro investigaci|Inbound SMTP Mail Gateway, Proxy, Antivirus, Umbrella, SIEM|



\*Kategorie incidentu je např. `Phishing`, `DDoS`, `Malware`, `Ransomware`, `Unauthorized Access`, `Insider Threat`, `Data Exfiltration`, `Web Attack`



###### 

###### Správci zdrojů dat & eskalace (kontakty pro investigaci):



|Systém / role|Jméno|E-mail|Telefon|Kdy kontaktovat|
|-|-|-|-|-|
|Správce Exchange / Mail GW|Pavel Knedík|knedlikp@ans.cz|+420 111 222 333|Získání e-mailových logů, blokace odesílatele|
|Správce Proxy|Tomáš Knedlík|knedlikt@ans.cz|+420 111 222 444|Proxy logy, blokace URL / domény|
|Správce AV / EDR|Jakub Knedlík|knedlikj@ans.cz|+420 111 222 555|Hash vyhledání, AV scan, izolace endpointu|
|SOC Analytický tým|SOC tým|soc@ans.cz|+420 111 222 100|Interní koordinace|
|CISO|Menší Šéf|sefm@ans.cz|+420 111 222 600|Severity High / Critical|
|ISO|Velký Šéf|sefv@ans.cz|+420 111 222 700|Severity Critical / dle interní politiky|
|CERT / NÚKIB|NÚKIB|podatelna@nukib.cz|+420 222 362 888|Dle regulatorní povinnosti (NIS2 apod.)|

## 



## Informace o kontextu bezpečnostní události:



###### Společné údaje (vyplní SOC Analytik):



|Ticket ID|*2026-0001*|
|-|-|



---

###### Hlášeno osobou (vyplní SOC Analytik — přeskoč pokud jde o automatizovanou detekci):



|Datum a čas nahlášení|*2025-03-15 09:42 CET*|
|-|-|
|Jméno oznamovatele|*Jan Novák*|
|Oddělení / organizační jednotka|*Účetní oddělení*|
|Kontakt (e-mail / telefon)|*novakj@ans.cz / +420 123 456 789*|
|Postižený uživatel (pokud jiný než oznamovatel)|*(oznamovatel = postižený)*|
|Postižený asset|*PC-NOVAK-01 · mailbox: novakj@ans.cz*|
|Cíl události|*Uživatel*|
|Popis události slovy oznamovatele|*„Přišel podezřelý e-mail s přílohou od neznámého odesílatele."*|



\*Cíl události: `Uživatel` – útok cílí na konkrétního uživatele nebo skupinu · `Informační systém` – cílem je konkrétní IS nebo infrastruktura · `Kombinace`

\*Postižený asset – uveď hostname počítače, IP adresu, název systému nebo mailbox, resp. jakého aktiva se incident týká.



---

###### Automatizovaná detekce (vyplní SOC Analytik — přeskoč pokud hlásila osoba):



|Datum a čas alertu||
|-|-|
|Identifikace detekčního nástroje||
|ID alertu / Identifikace pravidla||
|Postižený asset (hostname, IP, IS)||
|Cíl události||
|Popis alertu||



\*Cíl události: `Uživatel` · `Informační systém` · `Kombinace`



---

###### Dotčené assety (vyplní SOC Analytik):



\*Vyplň při příjmu události podle hlášení. Doplňuj průběžně během Triage a Investigace při každém rozšíření scope. Pokud je některý asset součástí kritické infrastruktury → ihned informuj CISO a postupuj dle regulatorních povinností.



|Asset (hostname, IP, mailbox, IS)|Typ assetu|Kritická infrastruktura|Vlastník / odpovědná osoba|E-mail|Telefon|Zjištěno při|
|-|-|-|-|-|-|-|
|*PC-NOVAK-01 · mailbox: novakj@ans.cz*|*Endpoint / Mailbox*|*Ne*|*Jan Novák*|*novakj@ans.cz*|*+420 123 456 789*|*Hlášení*|
|*PC-SVOBODA-02*|*Endpoint*|*Ne*|*IT Helpdesk*|*helpdesk@ans.cz*|*+420 111 222 200*|*Triage – AV scan*|
|*PC-KRAL-05*|*Endpoint*|*Ne*|*IT Helpdesk*|*helpdesk@ans.cz*|*+420 111 222 200*|*Triage – AV scan*|
|*Doplň při rozšíření scope*|||||||



\*Typ assetu: `Endpoint` · `Server` · `Mailbox` · `Informační systém` · `Síťový prvek` · `Sdílené úložiště` · `Jiné`

\*Kritická infrastruktura: `Ano` · `Ne`

\*Zjištěno při: `Hlášení` · `Triage` · `Investigace`

## 



## Triage:



##### Postup a vyhodnocení:



|Ověření kontextu a artefaktů|Postup|Poznámka SOC Analytika|
|-|-|-|
||Vyžádej si podezřelý e-mail ve formátu `.eml` nebo jako forward na dedikovanou SOC schránku|*E-mail přijat jako .eml*|
||Zaznamenej odesílatele, předmět a časové razítko e-mailu|*Od: invoice@podezrely-domena.com · Předmět: „Faktura #2025-112" · Přijato: 2025-03-15 09:31*|



|Analýza obsahu e-mailu|Postup|Poznámka SOC Analytika|
|-|-|-|
||Zkontroluj obsah e-mailu — identifikuj přítomnost přílohy, hyperlinku nebo pouze textu|*Příloha: faktura_2025.xlsx · Hyperlink přítomen v těle e-mailu*|
||Ověř záhlaví e-mailu (SPF, DKIM, DMARC)|*SPF: fail · DKIM: none · Doména spoofována*|



|E-mail obsahuje přílohu (přeskoč pokud příloha není přítomna)|Postup|Poznámka SOC Analytika|
|-|-|-|
||Zjisti hash přílohy (MD5 / SHA256) — přílohu přímo neotvírej|*SHA256: 3a1f2b…*|
||Ověř hash na VirusTotal nebo interním Threat Intelligence zdroji|*VT: 12/72 detekcí – malicious*|
||Zjisti z AV / EDR, zda byla příloha otevřena, kým a kdy|*Příloha otevřena uživatelem PC-NOVAK-01 ve 09:38*|
||Vyhledej stejný hash na ostatních endpointech přes AV / EDR — kontaktuj Správce AV/EDR (viz Kontaktní matice)|*Hash nalezen na PC-SVOBODA-02 a PC-KRAL-05*|

\*Pokud byla příloha otevřena nebo nalezena na více zařízeních → zaznamenej všechna zasažená zařízení a rozšiř scope.

\*Doporučení ke klasifikaci: hash detekován na TI a příloha byla otevřena → `True Positive`, `High` · hash detekován na TI, příloha nebyla otevřena → `True Positive`, `Medium` · hash na TI nedetekován a příloha nebyla otevřena → zvaž `False Positive`, ověř dalšími kroky



|E-mail obsahuje URL odkaz (přeskoč pokud URL není přítomna)|Postup|Poznámka SOC Analytika|
|-|-|-|
||Extrahuj URL z e-mailu — neotevírej odkaz přímo, použij defangovaný formát (např. `hxxps://`)|*hxxps://podezrely-domena[.]com/faktura*|
||Ověř URL na VirusTotal / URLScan.io nebo interním TI zdroji|*Kategorizováno jako phishing*|
||Zkontroluj proxy logy — byl odkaz prokliknut? Kým? Kdy? Kontaktuj Správce Proxy (viz Kontaktní matice)|*Prokliknutí zaznamenáno 09:39 · uživatel: novakj · PC-NOVAK-01*|

\*Pokud bylo prokliknutí potvrzeno → rozšiř scope. Rozsah kampaně na úrovni mail serveru prověř v Investigaci.

\*Doporučení ke klasifikaci: URL kategorizována jako phishing a prokliknutí potvrzeno → `True Positive`, `High` · URL kategorizována jako phishing, prokliknutí nepotvrzeno → `True Positive`, `Medium` · URL na TI nedetekována, prokliknutí nepotvrzeno → zvaž `False Positive`, ověř dalšími kroky



|Pouze textový e-mail – BEC / Social Engineering (přeskoč pokud příloha nebo URL jsou přítomny)|Postup|Poznámka SOC Analytika|
|-|-|-|
||Zhodnoť povahu žádosti — o co odesílatel žádá. Zkontaktuj postiženého uživatele — byla žádost splněna? Pokud byla žádost splněna → zjisti rozsah (výše transakce, sdílené údaje, …)|*Žádost o převod platby na „nový účet dodavatele". Uživatel žádost nesplnil, nahlásil ihned.*|

\*Pokud uživatel žádost splnil kontaktuj CISO (viz Kontaktní matice).

\*Doporučení ke klasifikaci: žádost splněna (transakce provedena, údaje sdíleny) → `True Positive`, `High` / `Critical` · žádost nesplněna, doména spoofována nebo SPF fail → `True Positive`, `Low` / `Medium` · odesílatel legitimní, žádná anomálie v záhlaví → zvaž `False Positive` nebo `Benign True Positive`



##### Výsledek Triage:



|Pole|Hodnota|
|-|-|
|Klasifikace události|*True Positive*|
|Závažnost (Severity)|*High*|
|Odůvodnění|*Škodlivá příloha otevřena jedním uživatelem, hash nalezen na 2 dalších zařízeních*|
|Rozhodnutí|*Zahájit Investigaci.*|



\*Klasifikace: `True Positive` – potvrzený bezpečnostní incident, pokračuj Investigací · `False Positive` – legitimní aktivita chybně vyhodnocena jako incident, přejdi na Uzavření incidentu · `Benign True Positive` – aktivita odpovídá detekci, ale není škodlivá (např. interní pentest), přejdi na Uzavření incidentu

\*Severity: `Critical` – okamžité ohrožení provozu nebo kritické infrastruktury · `High` – závažný incident s potvrzeným dopadem · `Medium` – incident s omezeným nebo neprokázaným dopadem · `Low` – nízké riziko, žádný aktuální dopad

\*Notifikace po Triage:
- `True Positive` Severity `High` → informuj CISO do 1 hodiny · informuj Vlastníka dotčeného systému do 30 minut (viz Kontaktní matice)
- `True Positive` Severity `Critical` → informuj CISO a Management ihned · zvaž notifikaci CERT / NÚKIB dle regulatorních povinností
- `False Positive` / `Benign True Positive` → informuj oznamovatele o výsledku šetření · přejdi na Uzavření incidentu

## 



## Investigace:



\*Cíl: Potvrdit rozsah kompromitace, korelovat události napříč zdroji, připravit podklady pro Containment. Pro přístup k datům kontaktuj příslušné správce uvedené v Kontaktní matici.



|Závažnost|Akce prováděj dle závažnosti události|Poznámka SOC Analytika|
|-|-|-|
|`High`|Koreluj události napříč dostupnými zdroji (proxy, EDR, mail gateway, SIEM)|*Korelace potvrdila aktivitu na 3 zařízeních, 1 s potvrzeným spuštěním přílohy*|
|`High`|Sestav timeline události — od doručení e-mailu po aktuální stav|*Timeline přiložena k ticketu INC-2025-0042*|
|`High`|Identifikuj scope — počet postižených uživatelů, zařízení, systémů, dat|*3 PC · 18 mailboxů · 1 sdílený síťový disk*|
|`High`|Na inbound mail gateway ověř, kolik příjemců e-mail obdrželo — kontaktuj Správce Exchange (viz Kontaktní matice)|*E-mail doručen 18 uživatelům ve 3 odděleních*|
|`High`|Zhodnoť, zda jde o cílenou nebo plošnou kampaň, zaznamenej seznam postižených mailboxů a přilož k ticketu|*Plošná kampaň – seznam příjemců přiložen k INC-2025-0042*|
|`High`|Ověř, zda došlo k laterálnímu pohybu nebo exfiltraci dat|*Laterální pohyb nezaznamenán · exfiltrace dat nezjištěna*|
|`High`|Proveď nucenou AV kontrolu postižených zařízení — kontaktuj Správce AV/EDR (viz Kontaktní matice)|*AV kontrola spuštěna na PC-NOVAK-01, PC-SVOBODA-02, PC-KRAL-05*|
|`High`|Zajisti důkazy (evidence collection) — logy, .eml soubor, hash, screenshoty|*Uloženo: /evidence/INC-2025-0042/*|

\*Pokud počet příjemců přesáhne 5 nebo jde o plošnou kampaň → zvaž rozeslání bezpečnostního upozornění všem uživatelům (akce v Containment).



### Výsledek Investigace:



|Pole|Hodnota|
|-|-|
|Finální klasifikace|*True Positive*|
|Finální Severity|*High*|
|Potvrzený rozsah|*3 zařízení · škodlivá soubor spuštěn na PC-NOVAK-01 · 18 příjemců phishingové kampaně*|



\*Notifikace po Investigaci:
- Severity `High` → potvrď notifikaci CISO · informuj Vlastníka dotčeného systému o výsledcích (viz Kontaktní matice)
- Severity `Critical` → zvaž notifikaci CERT / NÚKIB · připrav hlášení pro Management

## 



## Containment & Remediation:



\*Zaznamenej u každé akce zodpovědnou roli a aktuální stav. Pokud akce není pro daný incident relevantní, napiš N/A.



|Akce|Zodpovědná role|Součinnost|Stav|
|-|-|-|-|
|Izolace postižených zařízení od sítě|SOC Analytický tým|Správce AV/EDR · IT Helpdesk|*Provedeno*|
|Blokace domény odesílatele na mail serveru|SOC Analytický tým|Správce Exchange|*Provedeno*|
|Blokace URL / domény na proxy / firewallu|SOC Analytický tým|Správce Proxy|*Provedeno*|
|Blokace hash přílohy v AV / EDR|SOC Analytický tým|Správce AV/EDR|*Provedeno*|
|Vyhledání hashe na ostatních zařízeních přes AV / EDR scan|SOC Analytický tým|Správce AV/EDR|*Probíhá*|
|Reset přihlašovacích údajů postižených uživatelů|IT Helpdesk|SOC Analytický tým|*Čeká*|
|Patch / update zranitelného softwaru|Vlastník systému / IT|SOC Analytický tým|*Čeká*|
|Rozeslání bezpečnostního upozornění uživatelům|SOC Analytický tým|–|*Provedeno*|
|Jiné||||

\*Stav: `Provedeno` · `Probíhá` · `Čeká` · `N/A`

## 



## Komunikace a notifikace:



|Příjemce|Způsob komunikace|SLA pro notifikaci|Poznámka / stav|
|-|-|-|-|
|Vlastník dotčeného systému / IS|E-mail / telefon|Do 30 min od Triage|*Notifikován v 10:05*|
|CISO / Management|E-mail / telefon|Do 1 h (High / Critical)|*Notifikován v 10:30*|
|Postižení uživatelé|Hromadný e-mail|Do 2 h|*Upozornění rozesláno v 10:15*|
|Oznamovatel události|E-mail / telefon|Po uzavření incidentu|*Informován o výsledku šetření v 14:35*|
|CERT / NÚKIB|Datová schránka|Dle regulatorní povinnosti|*Neuplatní se – není kritická infrastruktura*|

\*SLA pro notifikaci je orientační. Vždy ověř aktuální požadavky dle platné legislativy (NIS2, GDPR) a interních předpisů organizace.

\*Oznamovatele informuj vždy — bez ohledu na výsledek klasifikace (True Positive i False Positive). Zpětná vazba podporuje kulturu hlášení bezpečnostních událostí.

## 



## Uzavření incidentu:



\*Uzavření provádí SOC Analytický tým po dokončení Containment & Remediation, nebo ihned po Triage pokud byl incident klasifikován jako False Positive či Benign True Positive.

\*Před uzavřením ověř, že oznamovatel byl informován o výsledku šetření.



|Pole|Hodnota|
|-|-|
|Klasifikace výsledku|*True Positive*|
|Finální Severity|*High*|
|Root Cause|*Škodlivá příloha distribuována plošnou phishingovou kampaní, otevřena jedním uživatelem*|
|Popis přijatých opatření|*Izolace 3 zařízení, blokace domény na mail serveru, AV scan*|
|Doporučení pro zlepšení|*Zvážit implementaci sandboxingu příloh na inbound mail gateway*|
|Lessons Learned|*5 uživatelů prokliklo URL před blokací – zvážit proaktivní blokaci na úrovni DNS*|
|Oznamovatel informován|*Ano – novakj@ans.cz, 2025-03-15 14:35*|
|Odkaz na incident ticket|*[INC-2025-0042]()*|
|Datum uzavření|*2025-03-15 14:30 CET*|
|Uzavřel|*SOC Analytický tým*|



\*Klasifikace výsledku: `True Positive` – potvrzený incident · `False Positive` – legitimní aktivita chybně vyhodnocena · `Benign True Positive` – aktivita technicky odpovídá detekci, ale není škodlivá

## 



## Příloha – RACI matice:



|Aktivita|SOC Analytický tým|Správci systémů / zdrojů dat|Vlastník dotčeného IS|CISO / Management|Externí subjekt|
|-|-|-|-|-|-|
|Příjem a zaevidování události|R, A|–|I|–|–|
|Triage|R, A|C (dle potřeby)|–|–|–|
|Investigace|R, A|C|C|–|–|
|Containment & Remediation|R, A|C|C|I (High/Critical)|–|
|Notifikace uživatelů / organizace|R, A|–|I|I|–|
|Eskalace na CISO / Management|R|–|–|A|–|
|Notifikace CERT / NÚKIB|R|–|–|A|I|
|Uzavření incidentu|R, A|–|I|I (High/Critical)|–|

\*Jak číst: R = Responsible (provádí) · A = Accountable (zodpovídá za výsledek) · C = Consulted (poskytuje součinnost) · I = Informed (je informován o výsledku)
