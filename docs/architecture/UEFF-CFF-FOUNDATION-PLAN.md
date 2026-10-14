# UEFF — Unified Execution & Fulfillment Fabric
## Az új CFA3 Foundation integrált CFF- és tartós végrehajtási célarchitektúrája

**Tervezési dátum:** 2026-10-14  
**Jóváhagyás alapja:** a tulajdonos jóváhagyta a UEFF koncepcionális architektúráját, kérte a kétoldalú felelősség-, kötelezettség- és garanciakezelés kiegészítését, valamint a kiegészített terv beillesztését **az új CFA3** tervébe.  
**Repository:** `ubuntuokos/CFA3-CinenemFoundArchitecture3`.  
**Státusz:** `APPROVED_TARGET_DESIGN / NOT_IMPLEMENTED / NO_RUNTIME_PASS`.  
**Határ:** tervdokumentáció, nem implementációs terv engedélyezése; nincs donor-adoption, engine selection, install, runtime-admission, GUI, Current Host PASS vagy automatikus scope-bővítés.

### 1. Hol helyezkedik el?

Az UEFF (Unified Execution & Fulfillment Fabric) **egy közös Foundation-képesség**, amelyet több CFA3 alkalmazás a saját projekt- és UI-kontextusából érhet el. Nem külön kreatív alkalmazás, nem második hardware broker, nem Model Router és nem új, különálló CFF telepítés.

Az **CFF (Capability & Fulfillment Fabric) az UEFF integrált, belső képesség-, igény-, tervezési és teljesítési doménje**.

```text
CFA3 alkalmazások / Production / Creative / támogatott külső integrációk
                         |
                         v
UEFF – közös Foundation szolgáltatási képesség
  ├─ CFF: igény, cél, alternatíva, életciklus, minőség
  ├─ CFF: kompetencia, eszköz, anyag, időablak, megvalósíthatóság
  ├─ CFF: kétoldalú vállalás, felelősség, átadás, jótállás/szavatosság
  ├─ tervezési jóváhagyás és változáskövetés
  ├─ motorfüggetlen tartós workflow- és feladatkoordinációs szerződés
  └─ minőség, események és bizonyítékokra hivatkozó tanulási visszacsatolás
                         |
       [külön jogosultsági és hatósági ellenőrzések]
                         |
Model Router · HRB · Workload Mode · Security/Identity ·
kijelölt action/tool határok · projektadat- és asset tulajdonosok ·
hiteles Evidence / Current Host minősítési rendszer
```

A komponenshatárok **logikaiak**, nem írnak elő mikroszolgáltatásokat vagy önálló külön tárolókat. Az alkalmazás projektadatai és a kreatív tartalom szerkeszthető forrásállománya az illetékes alkalmazás/tulajdonos hatáskörében marad; UEFF a feladattervvel, vállalással, hozzáféréssel és bizonyítékhivatkozásokkal dolgozik.

### 2. Az új CFA3 invariánsai

1. A jelen projekt **200 egyeztetendő célképességet** ír elő, nem kész és hitelesített 200-as jegyzéket. A régi repository 175-ös baseline-ja nem kerül át.
2. A Foundation és az új UEFF **még nem implementált és nem minősített**. A régi repository runtime-, Current Host-, donor- vagy CI-állapota nem bizonyíték az új CFA3-ra.
3. **CPU-only alapútvonal, local-first, self-hosted, felhő nélküli alapszolgáltatások**. Accelerátor csak az észlelt, engedélyezett eszközön; sem hardver-, sem modell-/providerjogosultság nem keletkezik UEFF-tervből.
4. A Model Router marad a tervezett AI-modell/provider kiválasztási határ, a HRB a fizikai erőforrás-elhelyezés és lease birtokosa, a Workload Mode a módkezelési határ. A UEFF emberi, pénzügyi vagy szerződéses kapacitásfoglalása **nem HRB hardverlease**.
5. Már meglévő vagy a Foundationban később kanonizált Work Management, Security, Evidence és Rights tulajdonosi határokhoz kell kötni a UEFF-et; nem szabad párhuzamos alapigazságot létrehozni.
6. Külső donor-, workflow-runtime- és license-források csak az új repository saját source-lifecycle, jogi, biztonsági és jóváhagyási lépései után használhatók. A régi repóban lévő PR nem kanonikus UEFF-terv.
7. Kérésre nem keletkezhet automatikus új projekt, utódfeladat, szerződésmódosítás, külső vásárlás vagy szolgáltatásígéret.

### 3. Teljes igény–teljesítés életciklus

`REQUEST_CAPTURE → NEED_AND_OUTCOME_ASSESSMENT → PURPOSE_LIFESPAN_QUALITY → OPTION_COMPARISON → MUTUAL_OBLIGATION_DRAFT → CUSTOMER_CONSULTATION → APPROVED_BASELINE → ELIGIBILITY → RESOURCE_AND_COST_PLAN → COMMITMENT_APPROVAL → CAPACITY_CHECK → DURABLE_EXECUTION → INSPECTION_AND_ACCEPTANCE → WARRANTY_AND_REMEDY_FOLLOWUP → EVIDENCE_FEEDBACK`.

- **Eredeti kérés sértetlenül megmarad:** külön a ténylegesen azonosított céltól, elvárt működéstől és mérhető sikerfeltételektől.
- **Alternatívák:** eredeti, kisebb/nagyobb, eltérő megoldás; tényleges használati idő, tartósság, biztonság és teljes életciklus-költség alapján.
- **Kompetencia:** feladatspecifikus készség, konkrét eszközzel igazolt jártasság, engedély, környezeti feltétel és aktuális rendelkezésre állás. Az ismeretlen nem azonos a bizonyítottan alkalmatlannal.
- **Kapacitás:** folyamatos, időszakos, előre ütemezett, feltételes és sürgősségi igények; eszköz/ember csak a szükséges időablakra. A külső partner „kérhető” kapacitása nem lesz automatikusan „lefoglalt” kapacitás.
- **Vállalás:** a megrendelő által jóváhagyott scope, minőség, ár/keret, határidő, felek kötelezettségei, bizonyíték és jogi feltétel együtt képez vállalási baseline-t. A kockázatos vagy bizonyítatlan vállalást a rendszer nem teheti érvényessé magától.
- **Esemény:** váratlan hiba csak az érintett munkát blokkolhatja és szükség esetén indokolhat biztonságos veszélyelhárítást; bővített helyreállítás külön, jogosult jóváhagyáshoz kötött.

### 4. Responsibility, Commitment & Warranty — kötelező belső domén

A CFF teljesítés- és szerződéstervezési részének kötelező része. **A képesség, a feladat felelőse, a vállalt kötelezettség, a hiányzó előfeltétel, az eredmény ellenőrizhetősége és a jogi felelősség külön fogalmak.**

#### 4.1 Kölcsönös kötelezettségi szerződés

Minden vállalásban legyen külön nyilvántartva:

- `party` és képviseleti jogosultság; `obligor` (kötelezett), `beneficiary` (jogosult), közreműködő, ellenőrzésre jogosult;
- vállalt termék/eredmény/szolgáltatás, mérhető minőség, anyag és kritikus alkatrész, határidő, teljesítés helye és környezete;
- **megrendelői és kivitelezői előfeltételek**: áram, helyszín, hozzáférés, dokumentum, jogosultság, referenciaanyag, anyag, karbantartási információ;
- előfeltétel biztosításának felelőse és bizonyítéka; a feltétel hiányának várakozási, értesítési, költség- és ütemezési következménye;
- elfogadási vizsgálat, vizsgálatot végző fél, elfogadási döntési jogosultság, eltérés dokumentálása;
- garancia/jótállás/szavatosság fennmaradó időbeli kötelezettségei és a jogorvoslat folyamata.

Az elfogadott terjedelem-/szerződésverzió és minden módosítás nyomon követhető. Automatikus elfogadás vagy kötelezettségelengedés tilos.

#### 4.2 Hűtőszekrény — kötelezettségi és oksági teszt

| Tény | Szerződés szerinti tipikus felelős | Helyes következtetés |
|---|---|---|
| A kivitelező kihagyja a vállalt kompresszort | Kivitelező | Dokumentált hiányos teljesítés; az áramellátás hiánya ezt önmagában nem menti |
| A megrendelő nem biztosítja a vállalt elektromos csatlakozást | Megrendelő | Hiányzik egy üzembe helyezési/mérési előfeltétel; a termék teljes működése ettől nem igazolt, de nem is cáfolt |
| A kompresszor is hiányzik, és az áramellátás sem biztosított | Külön felek és külön kötelezettségek | Két önálló hiba/hiány; külön bizonyíték, határidő, okság és jogkövetkezmény |
| Az áramellátás biztosított és a készülék működési teszten megbukik | Vizsgálat szükséges | Nem automatikus végső jogi felelősség: műszaki ok, szerződés és joghatóság vizsgálandó |

A működés állapota lehet `VERIFIED`, `DEFECTIVE`, `NOT_VERIFIABLE`, `DISPUTED`. A **`NOT_VERIFIABLE` nem `PASS` és nem `FAIL`**. Minden összetett esetnél a tényleges okot és vállalt előfeltételeket kell vizsgálni, nem egyetlen automatikus „hibás fél” címkét alkalmazni.

#### 4.3 Garancia, jogszabályi jótállás és szavatosság

- `warranty_issuer`, `covered_object`, `coverage_scope`, `coverage_start_trigger`, `coverage_period`, `legal_jurisdiction`, `statutory_or_voluntary_basis`, `conditions`, `exclusions`, `claim_process`, `repair_or_remedy`, `evidence_requirements`;
- a termék átadása, üzembe helyezése, műszaki próba és átvétele **nem automatikusan ugyanaz az esemény**; garanciakezdetre az alkalmazandó jog és az érvényes vállalás irányadó;
- külön követni kell az ügyfél panaszbejelentését, visszaigazolását, kivizsgálását, intézkedését, javítását/cseréjét, értesítési és reakcióidőit, a vállalt határidőket és lezárását;
- a felhasználói karbantartási, üzemeltetési vagy energiaellátási kötelezettség elmulasztása **nem törölheti automatikusan a jogszabály szerinti szavatossági/jótállási igényeket**;
- a jogi kizárhatóság, az okozati összefüggés, az érvényes feltétel és a bizonyítási teher ország-/szerződésspecifikus; vita esetén jogosult emberi, szakértői vagy jogi döntést kell kérni;
- a korábban fennálló, átadás utáni kötelezettségek fennmaradnak a fő workflow lezárását követően is, ameddig a megfelelő feltételek fennállnak.

#### 4.4 Kötelezettség- és ellenőrzési állapotok

- `DRAFT → PROPOSED → ACCEPTED → ACTIVE → FULFILLED / BREACHED / CANCELLED / DISPUTED`.
- `SUBMITTED → UNDER_REVIEW → VERIFIED / DEFECTIVE / NOT_VERIFIABLE / DISPUTED`.
- `REPORTED → ACKNOWLEDGED → INVESTIGATING → DECIDED → REMEDY_IN_PROGRESS → RESOLVED / DISPUTED`.

A státuszok **tervezett logikai szerződések**, nem implementált állapotgépek. A kötelezettségszegés vagy jogi felelősség végső minősítéséhez a szükséges bizonyíték és illetékes döntéshozó szükséges. A változat-/határidőnapló, hibajegyzék és vitatott állapot nem írható felül észrevétlenül.

#### 4.5 Logikai adatok és interoperabilitás

Tervezett entitások: `original_request`, `outcome`, `quality_lifecycle_profile`, `solution_option`, `capability_evidence`, `resource_requirement`, `conditional_resource`, `plan`, `capacity_reservation`, `party`, `agreement`, `agreement_version`, `obligation`, `precondition`, `responsibility_assignment`, `acceptance_criterion`, `delivery_record`, `inspection`, `defect`, `cause_assessment`, `warranty_policy`, `warranty_claim`, `remedy`, `dispute`, `approval`, `evidence_reference`.

Közös azonosító, provenance, egyedi idempotenciakulcs, jogosultsági kontextus, megerősített időbélyeg, állapotverzió és audit szükséges. **A fizikai adatbázis, PostgreSQL-séma és migráció NINCS kijelölve**. PostgreSQL helyi, relációs/transactional jelöltként vizsgálandó, nem automatikus függőség.

### 5. Tartós végrehajtás — kiválasztás NYITOTT

A UEFF célarchitektúrája a jóváhagyott terv szerint durable workflow-kontraktust tartalmaz; **nem határoz meg kötelező Temporal, Restate, DBOS, Dapr vagy teljesen saját runtime-választást**. Az új CFA3-ban nincs örökölt, igazoltan működő Temporal-bevezetés; a régi repository Temporal-előírása és bizonyítékai itt nem hatóságok.

Elvárt logikai szerződés:

- verziózott workflow- és feladatdefiníció; `TASK`, `DECISION`, `FORK/JOIN`, `EVENT_WAIT`, `TIMER`, `APPROVAL`, `QUALITY_GATE`, `SUBWORKFLOW`, `COMPENSATION`, `TERMINAL`;
- tartós feladatállapot, visszaállítás, timeout, retry, cancellation, crash recovery, esemény- és bemeneti deduplikáció;
- lease, fencing, idempotens tevékenység, outbox/inbox; külső mellékhatásra általános `exactly-once` állítás tilos;
- változatkövető workflow-folytatás és ellenőrzött migráció; jogosultság/kapacitás/előfeltétel szükség szerinti újraellenőrzése;
- a rendszer nem írhatja felül az elfogadott ügyfélcélt, minőséget, szerződést vagy kötelezettségeket „automatikus helyreállítás” ürügyén.

**Motorválasztási döntési kapu:** konkrét funkcionális garanciák → önhostolt/offline/CPU-only alkalmasság → jogosultság és licenc → fizikai host és üzemeltetési kockázatok → reproducible failure/retry/restart prototípus → külön owner approval és admission. Több runtime egy folyamat authoritative állapotát nem birtokolhatja párhuzamosan.

### 6. Váratlan esemény és kölcsönös felelősség

Festés közben felfedezett csőtörés: érintett munka megállítása és jogosult veszélyelhárítás; tény, ok, kötelezett és megrendelői előfeltétel elkülönítése; minimális javítási terv; költség/idő/jogkövetkezmény becslése; **külön jóváhagyás** a bővített kötelezettséghez; végrehajtás és ellenőrzés; visszatérés az eredeti scope-hoz. A bontóvéső feltételes, nem állandó eszközigény.

### 7. Integrációs / felelősségi mátrix

| Tervezett rendszerhatár | UEFF feladata | Kifejezett korlát |
|---|---|---|
| CFA3 alkalmazások | Igény és jóváhagyott feladat átadása / státusz visszajelzése | Nincs közvetlen másik app üzleti adatainak birtokbavétele |
| HRB és Hardware Safety | Eszköz- és számításikapacitás-igény átadása | Nincs UEFF GPU/CPU/NPU placement vagy hardverlease |
| Model Router | AI feladat leírása jogosult döntéshez | Nincs UEFF által végzett önálló model selection |
| Workload Mode | Alkalmazandó működési profil figyelembevétele | Nincs rejtett mód/fallback |
| Security / action és tool boundary | Jóváhagyott cselekmény végrehajtási kérelme | Nincs policy- vagy MCP-bypass |
| Foundation Work/Project | Munkatétel-, scope- és státuszhivatkozás | Nincs párhuzamos work-identity authority |
| Evidence / Rights | Bizonyítékhivatkozás, jogcím, átvételi státusz | Nem saját végső hitelesítési, jogi vagy licenchatóság |
| Tartós runtime (későbbi döntés) | Egységes UEFF workflow-kontraktus | Nyitott termék- és engine-választás; nincs örökölt PASS |

### 8. Elfogadási esetek és döntési kapuk

1. Rövid életű díszlet és tartós épület eltérő minőség-/TCO-ajánlatot eredményez.
2. Az alkalmas szakember konkrét eszközismerete bizonyítékkal van alátámasztva; ismeretlen tudás nem lesz automatikusan pozitív vagy negatív.
3. A teherautó csak rakodáskor foglalt; a feltételes véső csőhiba előtt nem automatikusan megvásárolt.
4. Az áramhiány `NOT_VERIFIABLE`, a hiányzó vállalt kompresszor `DEFECTIVE`, mindkettő együtt külön kötelezettségi nyilvántartást hoz.
5. Átadás után is nyitva maradhat jótállási/szavatossági kötelezettség; jogtalan automatikus igényvesztés tilos.
6. A későn válaszoló worker nem érvényesíthet régi lease-t; crash/retry/idempotencia helyes, de nem ígér hamis exactly-once külső hatást.
7. A folyamat nem bővít scope-ot, nem fizet, nem vállal szerződéses kötelezettséget és nem foglal helyette érvényes host-erőforrást önkényesen.
8. CPU-only offline referenciaútvonal, valódi jogosultsági/evidence- és Current Host-tesztek későbbi, külön engedélyezett szakaszban.

**Beépítés elfogadásának jelenlegi tárgya:** dokumentált Foundation-célarchitektúra, az UEFF–CFF kapcsolat, a kölcsönös felelősség- és garanciakövetelmények, valamint a nyitott workflow-engine státusz. **Nem tárgya:** implementáció, konkrét motor-adoption, migráció, donor intake, runtime/host minősítés vagy release.
