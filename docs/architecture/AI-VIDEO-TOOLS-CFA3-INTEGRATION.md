# CFA3 — AI Video Tools: integráció az egységes rendszertervbe

**Állapot:** tulajdonos által elfogadott alkalmazásterv, implementáció nélkül.
**Hatály:** kizárólag az AI Video Tools és annak már meghatározott CFA3 kapcsolódási pontjai.
**Forrás / teljes, kötelező specifikáció:** [CFA3 AI Video Tools v2.0 FINAL](../plans/accepted/CFA3-AI-VIDEO-TOOLS-V2-FINAL.md), 2026-10-15.
**Nyilvántartási hivatkozás:** `canonical/registries/CFA3-ACCEPTED-APPLICATION-PLANS-001.json`, `CFA3-AI-VIDEO-TOOLS-V2-FINAL`.

Ez a dokumentum a teljes, 23 fejezetes elfogadott terv **alkalmazáskatalógus- és architektúra-projekciója**. Nem írja felül a forrást, nem hoz létre új platformszintű felelőst, és nem jelent megvalósítási vagy teszt-PASS bizonyítékot.

## Alkalmazáskatalógus és felelősségi határ

- **Alkalmazás:** AI Video Tools; önálló, gyors, többmotoros helyi/felhő AI-videógenerálási alkalmazás.
- **Elsődleges funkciók:** Text-to-Video, Image-to-Video, Video-to-Video, referencia-vezérelt generálás, állókép-animáció, promptalapú mozgás, generatív variációk, backend által támogatott videó-hosszabbítás.
- **Nem feladata:** teljes timeline-alapú videószerkesztés, kompozitálás, színkorrekció vagy a Video Editor, VFX Studio és Animation Studio szakosított felelősségének átvétele.
- **Fő felület:** közös CFA3 natív Qt 6 GUI; Quick Generate, Generators, Models, Jobs, Outputs, Packages, Settings. A támogatott paramétereket minden generátor-/modellverzióhoz ténylegesen deklarálni kell. Upstream WebUI vagy rendszerböngésző nem használható CFA3 GUI-helyettesítőként.

## Alaptelepítési és csomagkezelési követelmény

| Azonosító | Kötelező alapintegráció | Tervezett vezérlési forma |
| --- | --- | --- |
| AVT-001 | FramePack | Helyi backend |
| AVT-002 | WanGP | Helyi backend |
| AVT-003 | LTX Desktop | Helyi / támogatott szolgáltatói backend |
| AVT-004 | VideoX-Fun | Helyi backend |
| AVT-005 | EasyAnimate | Helyi backend |
| AVT-006 | Runway API | Felhőszolgáltató-adapter |
| AVT-007 | Kling AI API | Felhőszolgáltató-adapter |

Mind a hét a kötelező alapcsomag része; a tényleges futtathatóság és hardverkompatibilitás külön állapot. A két API-szolgáltató **adaptere** kerül helyben telepítésre, nem a távoli AI-modell. A CFA3 alaptelepítője AI-model weights állományokat nem tartalmaz, és nem indít automatikus modellletöltést. Az újabb, jóváhagyott generátorok alapértelmezés szerint opcionális csomagok; telepítésük csak felhasználói döntéssel történhet.

## Kötelező meglévő CFA3-rétegkapcsolatok

| CFA3 felelős / terület | AI Video Tools kapcsolódás |
| --- | --- |
| Teljes alkalmazáskatalógus / AI alkalmazások / Creative Video | Önálló AI Video Tools alkalmazás, nem új Video Editor |
| Shared Plugin & Extension Fabric | Helyi generátormotorok és Runway/Kling felhőadapterek egységes integrációs szerződése |
| CFA3 Model Manager | Kizárólagos helyi modellkeresés, beszerzés, ellenőrzés, deduplikáció, verzióváltás, megőrzés és eltávolítás |
| Model Router | Modell- és futtatási útvonal kiválasztása |
| Temporal / közös workflow-réteg | Tartós generálási feladatok, állapotok, hibák, megszakítás/újraindítás tényleges támogatás szerint |
| Host Resource Broker | Hardver- és erőforrás-jogosultság, foglalás |
| Hardware Policy / Current Host | CPU-only platformalap, kijelző-GPU védelem, fail-closed, fizikai PASS |
| Shared Asset Management | Referenciaanyagok, generált videók és generálási metaadatok központi kezelése |
| Shared Export/Import | Engedélyezett asset- és projekthandoff |
| Shared Security | Jogosultság, hitelesítés, titokkezelés, adatküldési és költség-hozzájárulás |
| Package Management | Kötelező/opcionális csomagok, verzió, licenc, függőségizoláció |
| CFA3 GUI Framework | Natív Qt 6 felület, közös navigáció, témák és státuszok |
| Fejlődéskövetés | Ellenőrzött upstream verzió-, képesség-, licenc- és kompatibilitási adatok |

A Shared komponensek felelőssége **nem változik** az AI Video Tools felvételétől. Az adapter nem hozhat létre saját általános Model Managert, workflow-motort vagy végleges médiatárat; az izolált Python/backend környezetek nem hozhatnak létre külön modellweights-példányokat.

## Generálási életciklus és védelmi előfeltételek

1. CFA3 GUI-ban generátor és igazolt paraméterek kiválasztása.
2. Telepített / futtatható állapot, backend-képességek és esetleges kompatibilitási blokkolók ellenőrzése.
3. Helyi generátornál központi modellfeloldás a Model Managerrel; létező, kompatibilis példány újrafelhasználása, párhuzamos azonos letöltés nélkül.
4. Model Router útvonal-döntés; Host Resource Broker és Hardware Policy jogosultsági ellenőrzés. Hiányzó bizonyítéknál **BLOCKED**, nem szimulált PASS vagy rejtett fallback.
5. Felhőgenerálásnál kifejezett adatküldési és költségfeltételek ellenőrzése; nincs előzetesen nem jóváhagyott fizetős vagy felhős váltás.
6. Közös Temporal/workflow feladat, adapterindítás, ténylegesen támogatott állapot-/előrehaladás-/megszakításkezelés.
7. Kimenet és proveniencia a Shared Asset Managementben; csak jóváhagyott handoff más kreatív alkalmazásnak.

A workflow állapotai a teljes terv 10.2. fejezete szerint: `CREATED`, `VALIDATING`, `MODEL_PREPARATION`, `WAITING_FOR_RESOURCES`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `BLOCKED`.

## Modell-életciklus és kompatibilitás

A CFA3 Model Manager a teljes helyi modellállomány-életciklus kizárólagos felelőse. Azonos, integritással igazolt tartalmú modellt nem szabad ismét letölteni; eltérő verziók/formátumok/kvantálások nem azonosíthatók bizonyíték nélkül. Frissítéskor a kompatibilis alkalmazáshivatkozásokat és a szükséges régi verziókat meg kell őrizni; sikertelen frissítés nem károsíthatja a működő verziót. Megszűnt vagy nem karbantartott modell automatikus törlése tilos; a felhasználó a függőségek ismeretében dönthet.

## Kreatív átadások, feltételes kapcsolatok

A Shared Asset Management és Export/Import útján adhat át generált videót a CFA3 Video Editor, VFX Studio, Animation Studio, Story / Screenplay Studio, Scene / Shot Designer és Production Studio számára, **csak ott, ahol jóváhagyott és ténylegesen szükséges handoff-kontraktus létezik**. Ez nem hoz létre automatikus futásidejű függőséget és nem engedélyezi más alkalmazások fejlesztését.

## Integrációs feladat- és bizonyítási határ

A megvalósítás előfeltétele az adott upstream kiadás, API/CLI/headless vezérlés, licenc, terjeszthetőség, OS/hardver és adatvédelmi/költségkövetelmények hiteles ellenőrzése. Ha a kötelező eszköz integrációját ezek blokkolják, az **blocker**, nem ok a kötelező eszköz csendes kihagyására. A teljes terv 20. fejezete tartalmazza a kötelező elfogadási ellenőrzéseket; egyik sincs e dokumentummal teljesítettnek nyilvánítva.

A hét generátor alapcsomag-tagsága **nem jelent donor-jóváhagyást**. Nincs donor-intake, más alkalmazásfejlesztés, új shared infrastruktúra, automatikus telepítés, PR-mellékfeladat vagy architekturális refaktor. A CFA3 tervezési döntései, biztonsági szabályai és Scope Guard változatlanok.
