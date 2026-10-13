# CFA3-POLICY-HTTP-409-CONFLICT-RECOVERY-001

**Megnevezés:** HTTP 409 Conflict hibák kötelező felismerése, célzott javítása, biztonságos újravégrehajtása és az indokolatlan blokkolások megelőzése

**Verzió:** 1.1  
**Státusz:** JÓVÁHAGYVA – KIKÉNYSZERÍTÉS MEGVALÓSÍTÁS ALATT  
**Szabályviszony:** TELJES HELYETTESÍTÉS; a v1.0 hatályon kívül helyezett, a v1.1 az egyetlen aktuális normatív változat  
**Hatály:** Minden CFA3-fejlesztés, GitHub API-művelet, repository-módosítás, commit, branch, pull request, fájlkezelés, nyilvántartás-frissítés és minden olyan szolgáltatás, amely HTTP 409 Conflict választ adhat.

## 1. § – Alapelv

A HTTP 409 Conflict önmagában nem tekinthető végleges blokkolásnak.

A fejlesztő AI köteles a konfliktus konkrét okát meghatározni, és amennyiben az a jóváhagyott feladat keretein belül biztonságosan javítható, a szükséges javítást önállóan végrehajtani.

A 409-es hiba nem szolgálhat indokként a feladat indokolatlan megszakítására, új feladat létrehozására vagy a felelősség felhasználóra történő áthárítására.

## 2. § – Teljes helyettesítés és hatályon kívül helyezés

A v1.1 a v1.0 teljes helyettesítője, nem kiegészítése. A v1.0 minden rendelkezése hatályát veszti a v1.1 bizonyított bevezetésével; önálló vagy párhuzamos aktív szabályként nem használható.

A v1.0 nem szolgálhat aktív szabályforrásként, végrehajtási jogosultságként, ellenőrzési kapuk normatív alapjaként vagy automatikus döntési feltételként. A központi nyilvántartásban kizárólag a v1.1 szerepelhet aktuális változatként.

A korábbi GitHub-commitok és bizonyítékok megőrizendők audit-előzményként, normatív hatály nélkül. A v1.1 nem tekinthető működőnek pusztán a jóváhagyás vagy a forrásfájl megjelenése miatt.

## 3. § – Exact-state ellenőrzés és kötelező végrehajtási kapuk

A 409-es esemény felismerését, az erőforrás azonosítását, a javítási jogosultság eldöntését, a STOP-kapukat és a helyreállítás bizonyítását a végrehajtási rendszernek műveletenként ki kell kényszerítenie.

A javítás előtt kötelező az ütközés szempontjából releváns tényleges állapot lekérése.

GitHub esetében szükség szerint ellenőrizendő:

- Repository és célág létezése.
- Aktuális HEAD commit.
- Az érintett fájl aktuális SHA-értéke.
- A PR aktuális állapota és összevonhatósága.
- Az érintett erőforrás létezése.
- Az előírt állapotátmenet végrehajthatósága.

Csak a konfliktus feloldásához szükséges adatokat szabad ismételten lekérni.

Az AI korábbi állítása nem helyettesítheti a tényleges rendszerállapotot.

## 4. § – A javítható konfliktusok kezelése

Az AI külön engedély nélkül elvégezheti a jóváhagyott művelethez közvetlenül szükséges technikai javítást, ha az nem módosítja a feladat célját, tartalmát vagy engedélyezett hatókörét.

Ilyen lehet:

1. Elavult fájl-SHA frissítése.
2. Elavult commit-azonosító korrigálása.
3. Hibás create/update művelet megfelelő API-műveletre cserélése.
4. Párhuzamos fájlırások soros végrehajtása.
5. Már létező erőforrás helyes kezelése.
6. Hibás műveleti sorrend javítása.
7. Saját korábbi művelet miatt kialakult, determinisztikusan feloldható állapotütközés megszüntetése.

Ezek csak akkor engedélyezettek, ha mások módosításai nem vesznek el, és a javítás nem sért magasabb prioritású biztonsági vagy jóváhagyási szabályt.

## 5. § – A módosítások megőrzése

A konfliktus feloldásakor kötelező megőrizni:

- A felhasználó által jóváhagyott tartalmat.
- A GitHubon már elfogadott módosításokat.
- Más fejlesztők változtatásait.
- A történeti adatokat és jóváhagyásokat.
- Az előírt nyilvántartási és életciklus-állapotokat.

**Tilos** a konfliktust force push, indokolatlan felülírás, adatvesztéssel járó visszaállítás vagy más módosításának eltávolítása útján megszüntetni.

## 6. § – A műveleti sorrend helyreállítása

Ha a 409-es hibát hibás műveleti sorrend okozta, az AI köteles a helyes sorrendet helyreállítani.

A szükséges célágat vagy erőforrást létre kell hozni, mielőtt az arra épülő módosítás végrehajtására sor kerülne.

A már létező és megfelelő állapotú erőforrást tilos feleslegesen újra létrehozni.

Az előfeltételek helyreállítása nem terjesztheti ki az eredeti feladatot.

## 7. § – Kötelező célzott javítás

A 409-es konfliktus diagnosztizálása után az AI köteles a legkisebb szükséges javítást alkalmazni.

Nem indíthat emiatt önálló refaktort, új PR-t, architekturális átalakítást, auditot vagy dokumentációs mellékfeladatot, hacsak az nem elengedhetetlen és külön nem engedélyezett.

A javítást követően azonnal vissza kell térnie az eredeti feladathoz.

## 8. § – Újrapróbálkozás és ciklusvédelem

Ugyanazt a műveletet változatlan előfeltételekkel ismételni tilos, ha az előző végrehajtás 409-es hibával végződött.

Újrapróbálkozás kizárólag akkor engedélyezett, ha:

1. Az ütközés oka azonosított.
2. A releváns állapot ellenőrzött.
3. A szükséges javítás megtörtént.
4. Az új végrehajtás biztonsági feltételei teljesülnek.

Ha a konfliktus változatlan okból ismét jelentkezik, újabb vak újrapróbálkozás helyett a javítás eredményét kell értékelni.

Ha a szükséges továbblépés nem bizonyíthatóan biztonságos, a végrehajtást meg kell állítani.

## 9. § – Saját végrehajtási hiba

Amennyiben a HTTP 409 Conflict az AI saját hibájából keletkezett, például elavult SHA használatából, hibás állapotfeltevésből vagy nem megfelelő műveleti sorrendből, a fejlesztő köteles ezt végrehajtási hibaként kezelni.

A saját, biztonságosan javítható technikai hiba elhárításához nem szükséges külön felhasználói jóváhagyás.

Az AI köteles a javítás tényét és eredményét pontosan közölni.

Nem minősítheti a saját mulasztását igazolt külső blokkolásnak.

## 10. § – Valódi blokkolás

A 409-es hiba kizárólag akkor minősíthető valódi blokkolásnak, ha a feltárt konfliktus biztonságos megszüntetése az AI rendelkezésére álló jogosultságokkal vagy a jóváhagyott feladathatárokon belül nem lehetséges.

Ilyen eset különösen:

- A felhasználói jóváhagyást érintő tartalmi konfliktus.
- Más fejlesztő módosításának felülírását igénylő helyzet.
- Nem feloldható branch- vagy PR-állapotütközés.
- Kötelező biztonsági vagy CI-kapu megsértésének veszélye.
- Nem egyértelmű, többféleképpen feloldható adatkonfliktus.

Az AI köteles megnevezni a konkrét blokkolást, annak bizonyítékát és a továbblépéshez szükséges döntést.

**Valódi blokkolás esetén a végrehajtásnak meg kell állnia.**

## 11. § – PR- és merge-műveletek különös védelme

A 409-es hiba javítására adott engedély önmagában nem jogosít fel:

- Új PR létrehozására.
- Meglévő PR lezárására.
- PR összevonására.
- Rebase végrehajtására.
- Más branch módosítására.
- Jóváhagyott tartalom megváltoztatására.

Ezekhez az adott műveletre vonatkozó eredeti jogosultságok és jóváhagyások szükségesek.

A technikai hibajavítás nem kerülheti meg a CFA3 GitHub merge- és biztonsági szabályait.

## 12. § – A javítás bizonyítása és a rendelkezések kötelező leképezése

Mind a 16 § minden kötelező rendelkezését egyedi végrehajtási feltételhez, tiltáshoz, döntési kimenethez vagy ellenőrizhető bizonyítékhoz kell rendelni. A leíró dokumentum és a JSON-jelző önmagában nem végrehajtási szabály.

A 409-es hiba megszüntetését kizárólag tényleges rendszerbizonyíték alapján szabad sikeresnek minősíteni.

A bizonyításnak tartalmaznia kell:

1. Az eredeti konfliktust.
2. Az azonosított okot.
3. A végrehajtott javítást.
4. A sikeres újravégrehajtás eredményét.
5. Az érintett erőforrás végső állapotát.

GitHub-művelet esetén szükség szerint bizonyítandó a fájl tartalma, SHA-értéke, commitazonosítója, PR-státusza vagy a main ágon való tényleges jelenléte.

Önmagában a HTTP 200 vagy 201 válasz sem bizonyítja egy teljes fejlesztési feladat véglegesítését.

## 13. § – Ismételt ellenőrzések korlátozása

A fejlesztő nem fordíthatja a végrehajtás idejének meghatározó részét ugyanazon, már igazolt állapot szükségtelen ismételt lekérdezésére.

Új ellenőrzés csak akkor végezhető, ha azt:

- Megváltozott állapot.
- Újonnan észlelt konfliktus.
- Sikertelen javítás.
- Kötelező végrehajtási kapu.
- Az eredeti feladat lezárásához szükséges bizonyítás

indokolja.

A javítás sikeres bizonyítása után az AI köteles folytatni az eredeti feladatot.

## 14. § – Scope Guard és feladatfolytonosság

A HTTP 409 Conflict kezelése az eredeti feladat alárendelt helyreállítási művelete.

A fejlesztő köteles megőrizni:

- Az eredeti fő feladatot.
- A jóváhagyott eredményt.
- Az engedélyezett műveleti kört.
- A kötelező korlátozásokat.
- Az eredeti befejezési feltételt.

A konfliktus nem indokolhatja a feladat önkényes átértelmezését vagy más feladatra történő áttérést.

## 15. § – Execution Guard és meglévő CFA3-szabályok

Jelen szabály a HTTP 409 Conflict kezelésére vonatkozó speciális végrehajtási előírás. A Bootstrap feladata a forrás és a strukturális integritás ellenőrzése; az Execution Guard feladata a tényleges döntés és a tiltások kikényszerítése. Egyik nem helyettesítheti a másikat. A rendszer által nem közvetített külső útvonalra nem állítható kikényszerítés.

Nem írhatja felül a CFA3 kötelező exact-state, jóváhagyási, blokkolási, adatmegőrzési, GitHub merge- és véglegesítési szabályait.

Különösen alkalmazandó az alábbi elv:

**Az AI köteles önállóan kijavítani a saját, biztonságosan helyreállítható technikai hibáját, de nem jogosult önállóan feloldani olyan konfliktust, amely új felhasználói döntést igényel.**

## 16. § – Befejezési feltétel és elfogadási jogkör

A HTTP 409 Conflict helyreállítása kizárólag akkor tekinthető teljesítettnek, ha:

- A konfliktus konkrét oka azonosított.
- A szükséges javítás megtörtént.
- Az eredeti művelet sikeresen végrehajthatóvá vált és végrehajtásra került.
- A tényleges rendszerállapot bizonyítja a javítás eredményét.
- Nem történt adatvesztés vagy jogosulatlan módosítás.
- Nem maradt az eredeti műveletet akadályozó ismert konfliktus.

A konfliktus feloldása nem jelenti automatikusan a teljes fejlesztési feladat befejezését.

A fejlesztési feladatot annak saját jóváhagyott befejezési feltétele szerint kell lezárni.

A tartós, tényleges működés végleges elismerése a felhasználó döntési jogköre; az implementáció és a tesztek megvalósítását az önálló működési elismerés hiánya nem akadályozhatja.
