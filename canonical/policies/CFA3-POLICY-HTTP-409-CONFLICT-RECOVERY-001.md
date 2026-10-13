# CFA3-POLICY-HTTP-409-CONFLICT-RECOVERY-001

**Megnevezés:** HTTP 409 Conflict hibák kötelező felismerése, biztonságos javítása és tényleges rendszerszintű szabályérvényesítése

**Verzió:** 1.1  
**Státusz:** JÓVÁHAGYOTT, HATÁLYOS v1.1 – a tartós működés végleges elfogadása külön tulajdonosi döntés  
**Szabályviszony:** TELJES HELYETTESÍTÉS  
**Helyettesített változat:** v1.0 – HATÁLYON KÍVÜL HELYEZVE; semmilyen normatív rendelkezése nem alkalmazható  
**Hatály:** CFA3 GitHub-műveletek, repository-kezelés, fájlmódosítások, PR- és merge-folyamatok, API-műveletek és az ezekhez kapcsolódó végrehajtási rendszerek.

## 1. § – Alapelv

A HTTP 409 Conflict kezelésére vonatkozó előírásoknak ténylegesen kikényszeríthető végrehajtási szabályként kell működniük.

A szabály Markdown-, JSON- vagy adatbázis-bejegyzésként történő tárolása önmagában nem jelenti a szabály bevezetését.

A CFA3 kizárólag akkor tekintheti a szabályt végrehajtási szinten érvényesnek, ha az előírások megfelelő végrehajtási kapukhoz kapcsolódnak, és működésük ellenőrizhető.

## 2. § – Teljes helyettesítés és hatályon kívül helyezés

A v1.1 a v1.0 teljes helyettesítője, nem kiegészítése.

A v1.0 teljes egészében hatályon kívül van helyezve. A v1.0 egyetlen rendelkezése sem maradhat önállóan vagy párhuzamosan hatályban. A v1.1 az egyetlen hatályos, alkalmazandó szabályváltozat.

A v1.0 nem használható aktív szabályforrásként, végrehajtási jogosultságként, ellenőrzési kapuk normatív alapjaként vagy automatikus döntési feltételként.

A központi szabálynyilvántartásban kizárólag a v1.1 szerepelhet aktuálisan hatályos változatként. A v1.0 korábbi normatív státuszát minden érintett végrehajtási és nyilvántartási felületen meg kell szüntetni.

A v1.0 korábbi GitHub-commitjai és bizonyítékai kizárólag változtathatatlan audit-előzményként maradhatnak meg; ezek nem jelentenek történeti szabályhatályt.

A v1.1 normatív hatálya önmagában nem bizonyítja a teljes körű futásidejű kikényszerítést és a tartós működést; ezeket külön kell igazolni, és a végleges működési elismerés a felhasználó hatásköre. A v1.0 nem aktiválható vissza automatikusan.

A teljes felülírást a v1.1 kanonikus GitHub main állapotának és a kapcsolódó nyilvántartásnak az ellenőrzése igazolja. A futásidejű lefedettség és a tartós működés bizonyítása ettől elkülönülő elfogadási feltétel, nem a v1.0 hatályának fenntartási oka.

## 3. § – Kötelező végrehajtási integráció

A HTTP 409 Conflict szabály végrehajtását a CFA3 meglévő Execution Guard infrastruktúrájához kell kapcsolni.

A rendszernek támogatnia kell:

1. A HTTP 409 esemény felismerését.
2. A hibához kapcsolódó erőforrás azonosítását.
3. Az aktuális rendszerállapot ellenőrzését.
4. A javítás engedélyezhetőségének meghatározását.
5. A jogosulatlan javítás blokkolását.
6. A biztonságos újrapróbálkozás szabályozását.
7. A sikeres helyreállítás bizonyítását.
8. Az eredeti feladathoz való visszatérést.

Az integráció kizárólag a ténylegesen érintett komponensekre terjedhet ki.

## 4. § – Kötelező végrehajtási állapotgép

A HTTP 409 Conflict kezelésének végrehajtási sorrendje:

1. HTTP 409 észlelése.
2. Exact-state ellenőrzés.
3. Scope és jogosultsági kapu.
4. Javítási döntés.
5. Célzott helyreállítás.
6. Eredmény bizonyítása.
7. Visszatérés az eredeti feladathoz.

Az állapotátmenetek csak megfelelő feltételek teljesülése esetén engedélyezhetők.

Valamennyi döntési kapunál a nem biztonságos vagy nem engedélyezett művelet STOP/BLOCKED állapotba kerül.

Tilos a javítási vagy ellenőrzési kapuk megkerülése.

## 5. § – Exact-state kikényszerítése

Javító művelet nem engedélyezhető, amíg a szükséges aktuális erőforrásállapot nem ismert.

GitHub esetében az ellenőrzésnek ki kell terjednie az érintett branchre, HEAD commitra, fájl-SHA-ra, PR-állapotra és egyéb releváns előfeltételekre.

Az elavult vagy bizonytalan állapot alapján végrehajtott írási műveletet meg kell akadályozni.

Az ellenőrzés és a tényleges írás közötti állapotváltozást megfelelő verzió- vagy előfeltétel-ellenőrzéssel kell kezelni.

## 6. § – Scope és jogosultsági kapu

Minden javítási javaslatot a végrehajtás előtt a jóváhagyott feladathoz kell viszonyítani.

A rendszernek meg kell különböztetnie:

- Az eredeti feladaton belüli, biztonságos technikai korrekciót.
- A tartalmi vagy architekturális változtatást.
- A jogosulatlan mellékfeladatot.
- Az új jóváhagyást igénylő műveletet.

Új PR, rebase, merge, force push vagy más érzékeny GitHub-művelet nem válik automatikusan engedélyezetté egy HTTP 409 eseménytől.

## 7. § – Adatmegőrzés és konfliktusbiztonság

A javítás kizárólag akkor hajtható végre, ha nem okoz jogosulatlan adatvesztést vagy változtatás-felülírást.

A rendszernek ellenőriznie kell az elavult verziókat, az ütköző írásokat és az erőforrás aktuális tartalmát.

Nem bizonyítható adatmegőrzés esetén a műveletet blokkolni kell.

## 8. § – Újrapróbálkozási és ciklusvédelem

A rendszer köteles megakadályozni az azonos körülmények közötti ismételt, eredménytelen végrehajtási ciklusokat.

Újrapróbálkozás csak akkor engedélyezhető, ha a konfliktus kiváltó oka és a javítás hatása ellenőrzött.

Az ismétlések számának korlátozottnak kell lennie. Az ismétlődő konfliktust újra kell értékelni, nem lehet változatlanul tovább próbálkozni.

A ciklusvédelem nem szakíthat meg olyan műveletet, amelynek végrehajtása jogszerűen és bizonyíthatóan előrehalad.

## 9. § – Saját technikai hibák kezelése

Az AI saját technikai végrehajtási hibáját a megengedett önkorrekciós körön belül köteles kijavítani.

A korrekció nem változtathatja meg a felhasználói jóváhagyást, a szabályok hatályát vagy az eredeti feladat célját.

A saját hibából eredő ütközés nem minősíthető automatikusan külső blokkolásnak.

## 10. § – Valódi blokkolás és fail-closed működés

A végrehajtást meg kell állítani, ha:

1. A konfliktus nem azonosítható megbízhatóan.
2. Az aktuális rendszerállapot bizonytalan.
3. A javítás tartalmi döntést igényel.
4. Az adatmegőrzés nem biztosítható.
5. A művelethez nincs megfelelő jogosultság.
6. Kötelező biztonsági vagy CI-előfeltétel sérülne.

A blokkolás konkrét okát és bizonyítékát meg kell őrizni.

Tilos a blokkolás automatikus feloldása feltételezéssel, végtelen újrapróbálkozással vagy biztonsági kapu megkerülésével.

## 11. § – Bizonyítékalapú eredményellenőrzés

A helyreállítás csak akkor minősíthető sikeresnek, ha annak tényleges eredménye visszaellenőrizhető.

A bizonyíték szükség szerint tartalmazza az eredeti hibát, az ellenőrzött kiindulási állapotot, az engedélyezett korrekciót és az új állapotot.

Az API sikeres válasza önmagában nem helyettesíti az erőforrás ellenőrzését.

## 12. § – A 16 eredeti paragrafus kötelező leképezése

A v1.1 valamennyi kötelező rendelkezéséhez kötelező hozzárendelni:

- Egyedi, stabil szabályazonosítót.
- A szabály által érintett végrehajtási pontot.
- Az előfeltételt.
- A megengedett és tiltott műveleteket.
- A megsértéskor alkalmazott döntést.
- A tesztelhető elfogadási feltételt.
- A bizonyítás módját.

Nem maradhat olyan kötelező rendelkezés, amelyhez csak leíró szöveg tartozik, anélkül, hogy a végrehajtási státusza egyértelmű lenne.

## 13. § – Kötelező pozitív és negatív tesztek

A megvalósításnak ki kell terjednie a 409-es konfliktusok jellegzetes eseteire, különösen az elavult SHA-ra, párhuzamos írásra, megváltozott branch-állapotra, jogosulatlan műveletre, ismétlődő konfliktusra és bizonytalan erőforrásállapotra.

A teszteknek igazolniuk kell, hogy az engedélyezett helyreállítás végrehajtható, a tiltott műveletek pedig ténylegesen blokkolódnak.

A kizárólag JSON-mezőket vagy dokumentumszöveget ellenőrző teszt nem elegendő a rendszerszintű PASS-hoz.

## 14. § – Bootstrap és Execution Guard szerepe

A Bootstrap feladata a szabályforrás, a szerkezeti integritás és a kapcsolódó ellenőrzések meglétének igazolása.

Az Execution Guard feladata a tényleges végrehajtási döntések kikényszerítése az általa ellenőrzött műveleteknél.

A két ellenőrzés eredménye nem helyettesítheti egymást.

A szabály teljes körű működése csak akkor jelenthető ki, ha a ténylegesen hatálya alá tartozó műveleti útvonalakon érvényesül. A Guard által nem ellenőrzött közvetlen vagy külső műveleti útvonalakra nem állítható kikényszerítettség.

## 15. § – Véglegesítés

A szabály rendszerszintű véglegesítésének feltétele:

1. A jóváhagyott eredeti szöveg és a teljes helyettesítés rendelkezéseinek megőrzése.
2. A teljes rendelkezés–végrehajtás megfeleltetés.
3. Az engedélyezési és tiltási logika megvalósítása.
4. A szükséges Execution Guard integráció.
5. A pozitív és negatív tesztek sikeres eredménye.
6. A kötelező CI-ellenőrzések teljesítése.
7. A jóváhagyott GitHub-egyesítés.
8. A main ág tényleges állapotának bizonyítása.
9. A futásidejű működés bizonyítása az érintett műveleti útvonalakon.

A tárolt szabályszöveg egyezése, a regisztráció és a CI önmagukban nem elegendők.

## 16. § – Korlátozások és feladatlezárás

Jelen szabály végrehajtása kizárólag a HTTP 409 Conflict helyreállításához közvetlenül szükséges munkára adhat alapot.

Nem engedélyez donor-intake-et, más alkalmazás fejlesztését, önálló architekturális átalakítást, vagy más szabály tartalmi megváltoztatását.

A feladat akkor tekinthető késznek, amikor a jóváhagyott 409-es szabály teljes, alkalmazandó rendelkezésállománya ténylegesen kikényszeríthető, a megkövetelt bizonyítékok rendelkezésre állnak, és nincs ismert végrehajtást akadályozó blocker.

Ekkor a végrehajtásnak meg kell állnia.

A tartós, tényleges működés végleges elismerése a felhasználó döntési jogköre; az implementáció fejlesztési lezárása és a tartós működés későbbi elismerése külön döntés.
