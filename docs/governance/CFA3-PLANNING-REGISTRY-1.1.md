# CFA3 — tervezési nyilvántartás infrastruktúrája (1.1)

**Tulajdonosi jóváhagyás:** 2026-10-14, a CFA3 baseline-alapú tervezési és döntésnyilvántartás 1.1-es terve.
**Végrehajtási állapot:** infrastruktúra-bootstrap / részleges megvalósítás; nem teljes nyilvántartási rendszer.
**Munkahatár:** kizárólag a CFA3 belső tervezési infrastruktúrája; nem a kész CFA3 alkalmazás funkciója.

## A megvalósítás alapja

A korábban kidolgozott CSA 1.3 archívumkódja (scripts/csa.py) és strukturális tesztjei (tests/test_csa.py) szolgálnak a Markdown-alapú tárolás kezdeti infrastruktúrájául. Ez a PR a fejlesztői kódot és dokumentációt helyezi el a CFA3 forrás-repositoryban, **nem hoz létre és nem publikál tényleges beszélgetési rekordokat**.

A CSA rekordok és indexek csak kifejezetten kijelölt, a CFA3 alkalmazás-repositoryn *kívüli* adattárolóban hozhatók létre. A CSA-adatállomány nem csomagolható be sem Rust-alkalmazásba, sem telepítőbe, sem release-artefaktumba. Ennek hiteles kiadásellenőrzése a tényleges release pipeline elkészülésekor kötelező; ez a PR nem tekinthető ilyen bizonyítéknak. A jelenlegi elkülönítési szabály: canonical/policies/CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001.md.

## A jóváhagyott 1.1-es cél és a jelenlegi különbség

- **Baseline:** 200 stabil, sorszámozott névhely, ebből 1–175 meghatározott, 176–200 sorrendben és külön jóváhagyással átnevezhető fenntartott hely. A fejlesztési ágon létező canonical/registries/CFA3-CAPABILITY-NAMES-200-001.json névjegyzék önálló baseline-feladat; a jelen PR nem másolja, nem véglegesíti és nem írja át. Amíg nem áll rendelkezésre hitelesen az aktuális névjegyzék, baseline-hozzárendelés nem igazolható.
- **Donor Registry:** a párhuzamosan épülő donor-nyilvántartás hiteles adatforrás marad. E PR nem módosít donoradatot, donor-intake-et vagy donorállapotot, és nem állítja, hogy a donorintegráció kész.
- **Nyilvántartási tartalom:** a jóváhagyott végcélban minden ajánlás, előzetes terv, döntés és más önálló elem külön Markdown-rekord, explicit baseline-célhellyel, felhasználási rendeltetéssel és hivatkozásokkal. Az itt átvett CSA 1.3 eszköz jelenleg elsősorban a javaslatok helyi archiválását, indexét, keresését és az engedélyezett státuszrögzítést támogatja: **még nem teljesíti a teljes 1.1-es kapcsolati és donor-kompatibilitási követelményeket**.
- **Jóváhagyás:** javaslat és előzetes terv nem válhat automatikusan hivatalos alkalmazástervvé; külön véglegesítési döntés szükséges. A döntés nem jelenti automatikusan a megvalósítást.
- **Kétirányú tervezési integráció:** helyi, explicit adathozzáférés lehetséges; automatikus ChatGPT-beszélgetésfeltárást, élő GitHub-adattár-szinkronizációt és a teljes visszaható kapcsolati gráfot ez a bootstrap nem igazolja.

## Korlátok és következő ellenőrzések

A forráskód beemelése nem jelenti, hogy a helyi tesztek, a külső adatgyökér jogosultságai, a GitHubba történő archiválás, a 200-as baseline-rekordokhoz kapcsolás vagy a donoradatbázis teljes adatai ellenőrzött, éles rendszerként működnek. Ezeket külön, ténylegesen reprodukálható ellenőrzésekkel kell igazolni.

A megvalósítás további lépései csak az érintett jóváhagyott források tényleges rendelkezésre állásával, a meglévő donorstruktúra ellenőrzött megfeleltetésével és a CFA3 Scope Guard előírásaival végezhetők. A donoradatbázis építését nem kell befejezni a tőle független fejlesztési lépésekhez.

## 1.1 második szakasz – strukturális kapcsolatok

A bootstrap bővítése `csa.record.v2` rekordokat támogat kötelező `record_kind`, `purpose` és stabil `baseline_id` adatokkal; a már jóváhagyott 200 elemű névjegyzék külön forrás. A fenntartott baseline-névhelyek használatát a validátor elutasítja. A kapcsolt rekordok fordított mutatói indexben kereshetők, míg a donor-hivatkozások a meglévő read-only donor-feloldón keresztül érvényesíthetők.

Ez a megvalósítás nem jelenti a donoradatbázis lezárását, a teljes kétirányú ChatGPT-integrációt, és nem módosítja az alkalmazás futásidejű kódját. A további specifikációs egyezéshez a donoradatbázis elkészülő, hiteles szerkezetével való ellenőrzés szükséges.

## Célzott kontextusolvasás

A `context` CLI egy meghatározott rekordazonosító vagy baseline-azonosító alapján, a helyi rekordok és indexek teljes szerkezeti ellenőrzése után állítja elő a következő tervezési lépés számára használható JSON-kontextust. A kapcsolatok fordított irányban is megjelennek. A státusz és a rekordtípus külön marad, ezért a találatok **nem** kapnak automatikus véglegesítési vagy megvalósítási minősítést.

Ez helyi, ellenőrzött olvasási interfész. Nem jelenti a ChatGPT natív integrációjának, a teljes donoradatbázisnak vagy a kiadási kizárásoknak az éles bizonyítását.
