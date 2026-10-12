# CFA3-POLICY-SEQUENTIAL-EXECUTION-RESULT-INTEGRITY-001

**Megnevezés:** Kötelező szekvenciális feladatvégrehajtás, tényleges eredményközlés és ellenőrzési ciklusok megelőzése

**Verzió:** 1.0  
**Státusz:** JÓVÁHAGYÁSRA VÁR  
**Hatály:** CFA3 teljes fejlesztési rendszere, kiemelten a donoradatbázis feldolgozása

---

## 1. § Alapelv

A CFA3 fejlesztő AI köteles a felhasználó által meghatározott munkafolyamatot a megadott sorrendben végrehajtani.

Az AI nem helyettesítheti a tényleges munkavégzést ismétlődő ellenőrzésekkel, előkészítésekkel, bizonyítékgyártással, elemzésekkel vagy kapcsolódó mellékfeladatokkal.

**A munkafolyamat célja a kért eredmény befejezése, nem az ellenőrzési tevékenységek számának növelése.**

## 2. § Egy feldolgozási egység – teljes lezárás

A donoradatbázis feldolgozásánál a kötelező munkavégzési egység egy kijelölt forrásfájl.

Az AI köteles:

1. Az aktuális forrásfájlt megnyitni.
2. Az összes feldolgozandó rekordot azonosítani.
3. Minden rekord szükséges feldolgozását végrehajtani.
4. A duplikációkat és a korábbi döntéseket kezelni.
5. A fájlhoz tartozó eredményt lezárni.
6. A szükséges ellenőrzéseket elvégezni.
7. Az eredményt az engedélyezett GitHub-folyamatban közzétenni.
8. A tényleges publikált állapotot igazolni.
9. A következő forrásfájlra áttérni.

A következő forrásfájl feldolgozása nem kezdhető meg az előző szabályos lezárása előtt.

A méretkorlát miatt létrehozott több kimeneti fájl nem számít új feldolgozási egységnek.

## 3. § Ismétlődő ellenőrzések tilalma

Tilos ugyanazon változatlan adatokon azonos célú ellenőrzést ismételten végrehajtani, ha annak eredménye már bizonyított.

Újraellenőrzés kizárólag akkor megengedett, ha:

- a releváns adat vagy rendszerállapot ténylegesen megváltozott;
- konkrét hiba kijavítása után szükséges;
- kötelező CI-, publikációs vagy GitHub-kapu megköveteli;
- korábbi bizonyíték érvénytelenné vált.

Az ellenőrzést az érintett változásra kell korlátozni, amennyiben a kötelező rendszerkapuk ezt megengedik.

Az AI nem hozhat létre önfenntartó ellenőrzési ciklust.

## 4. § A tényleges előrehaladás elsőbbsége

A fejlesztő köteles megkülönböztetni:

- a rekordok nyilvántartásba vételét;
- az indexelést és kereshetővé tételt;
- a rekordok tényleges feldolgozását;
- az egyedi donorok elfogadását;
- a GitHubon történő publikációt.

Ezek nem tekinthetők azonos eredménynek.

Előkészített vagy kereshető rekord önmagában nem jelent új, elérhető donort.

A végrehajtás értékelésekor a valóban lezárt és publikált feldolgozási egységek számát is kötelező figyelembe venni.

## 5. § A donorszám növekedésének ellenőrizhetősége

Minden lezárt donorforrásfájl után kötelező meghatározni:

- a feldolgozott rekordok számát;
- az új, egyedi és elfogadott donorazonosítók számát;
- a már ismert donorok számát;
- az elutasított vagy nem jogosult rekordok számát;
- a publikáció előtti és utáni tényleges elérhető donorszámot;
- a donorszám változásának okát.

Az elérhető donorszámot kizárólag a kanonikus, publikált nyilvántartás megfelelő életciklus-státuszú, egyedi donorazonosítói alapján szabad megállapítani.

A „donornak” vagy azzal egyenértékű kifejezett felhasználói jóváhagyás nélküli forrás nem vehető fel automatikusan jóváhagyott donorként.

A donorszám növekedése nem garantálható: ha valamennyi feldolgozott rekord korábban ismert, a növekmény jogosan nulla lehet.

**Tilos azonban a nulla növekményt a feldolgozás elmaradásának, befejezetlenségének vagy hibájának eltitkolására felhasználni.**

## 6. § Kötelező haladási mechanizmus

Minden feldolgozási egységnek meghatározott állapotban kell lennie:

- `PENDING` – feldolgozásra vár.
- `IN_PROGRESS` – tényleges feldolgozás folyik.
- `VALIDATING` – feldolgozás kész, kötelező ellenőrzés folyik.
- `PUBLISHING` – jóváhagyott publikáció folyik.
- `PUBLISHED` – közzététel bizonyított.
- `BLOCKED` – igazolt akadály miatt nem fejezhető be.

A `PUBLISHED` státusz kizárólag a kötelező publikációs bizonyítékok teljesülése után adható meg.

Az AI nem tarthat egy fájlt határozatlan ideig `IN_PROGRESS` vagy `VALIDATING` állapotban úgy, hogy kizárólag ismétlődő tevékenységeket végez.

Az AI köteles felismerni és jelezni, ha egy ismétlődő művelet nem eredményez tényleges haladást.

## 7. § Végtelen és eredménytelen ciklusok megszakítása

Ha ugyanazon célra, változatlan bemenettel ismételt művelet nem eredményez új információt vagy előrehaladást, az AI köteles megszakítani az ismétlést.

Ezt követően:

1. Megállapítja a sikertelenség konkrét okát.
2. Megkülönbözteti a saját végrehajtási hibáját a valódi külső akadálytól.
3. Saját, engedélyezetten javítható technikai hibáját kijavítja.
4. Az eredeti feladat végrehajtását folytatja.
5. Valódi blokkolás esetén a megőrzött feldolgozási állapotot és az akadályt jelenti.

Nem indíthat újabb ellenőrzési sorozatot kizárólag azért, mert a korábbi ismétlések nem hoztak eredményt.

Az önjavítás nem jogosít fel jogosultsági, biztonsági vagy jóváhagyási kapuk megkerülésére.

## 8. § Kötelező donoradatfájl-méretkorlát

Minden új vagy módosított donoradatbázis-fájl felső mérethatára:

**0,95 MiB = legfeljebb 996 147 bájt.**

Ha az eredmény meghaladná a megengedett méretet, az adatokat veszteségmentesen több fájlra kell osztani.

Az átszervezés során kötelező megtartani:

- minden korábban jóváhagyott donoradatot;
- az életciklus-információkat;
- a korábbi döntéseket és történeti kapcsolatokat;
- az egyedi azonosítókat;
- a központi kereshetőséget.

A méretkorlát ellenőrzése kötelező, de nem válhat önálló, végtelenül ismétlődő feldolgozási feladattá.

## 9. § Fájl lezárása és továbblépés

Egy forrásfájl akkor tekinthető lezártnak, ha:

1. Valamennyi rekordját feldolgozták vagy igazolt, végleges eljárási eredménnyel látták el.
2. A duplikációkat és a korábbi állapotokat szabályosan kezelték.
3. A szükséges fájlok és indexek konzisztensek.
4. A méretkorlát teljesül.
5. A kötelező ellenőrzések sikeresek.
6. A publikáció engedélyezetten megtörtént.
7. A publikált GitHub-állapot ellenőrzéssel igazolt.
8. Az eredményről végleges beszámoló készült.

A lezárást követően az AI köteles továbblépni a következő kijelölt fájlra, amennyiben az eredeti felhasználói engedély erre kiterjed.

Korábbi lezárt fájl ismételt feldolgozása csak tényleges változás, igazolt hiba vagy kifejezett felhasználói utasítás alapján engedélyezett.

## 10. § Eredményközlés és válaszok megőrzése

A fejlesztő AI köteles elkülöníteni az ideiglenes munkaközi tájékoztatást a végleges eredményközléstől.

A felhasználó számára fontos alábbi információkat végleges, visszakereshető beszélgetési válaszban kell közölni:

- bizonyított feldolgozási eredmények;
- végleges donorszámok és változások;
- GitHub PR- és merge-azonosítók;
- ellenőrzési eredmények;
- blokkolások;
- befejezett feladatok státusza.

Az ideiglenes üzenet nem helyettesítheti a végleges eredményközlést.

Ha az alkalmazás felülete a munkaközi üzenetet automatikusan elrejti vagy összecsukja, az AI-nak a lényeges eredményt a végleges válaszban is szerepeltetnie kell.

Az AI nem állíthatja, hogy a felület minden üzenetet változatlanul megőriz, ha ennek biztosítására nincs technikai jogosultsága.

A már közölt eredményt későbbi válaszban csak új, igazolt bizonyíték alapján szabad módosítani, a korrekció tényét egyértelműen jelezve.

## 11. § Valós eredmények kötelező jelentése

A fejlesztő nem jelenthet be befejezett munkát kizárólag azért, mert:

- létrejött egy commit;
- elkészült egy index;
- elindult vagy sikeresen lefutott egy CI-folyamat;
- megnyílt egy PR;
- készült egy bizonyítékfájl;
- feldolgozási terv vagy részleges eredmény született.

A befejezést az eredetileg kért eredmény és annak teljesülési feltételei alapján kell megítélni.

A jelentésben világosan el kell különíteni:

**VERIFIED:** ténylegesen bizonyított eredmény.

**PENDING:** még nem véglegesített eredmény.

**BLOCKED:** igazolt, meg nem oldott akadály.

A sikeres PR-összevonás önmagában nem helyettesíti a kötelező main-állapotellenőrzést.

## 12. § Felelősség és eltérések kezelése

Ha az AI azért nem halad, mert eltér a kijelölt munkafolyamattól, ezt saját végrehajtási hibájaként köteles felismerni és jelenteni.

Nem hivatkozhat külső blokkolásra, ha a problémát saját szükségtelen műveletei, hibás sorrendje vagy ismétlődő ellenőrzései okozzák.

Az önjavítás során kizárólag az eredeti feladat teljesítéséhez közvetlenül szükséges módosítások végezhetők.

Önállóan nem kezdeményezhető új projekt, mellékfeladat, audit, szabályalkotás, refaktorálás vagy más alkalmazás fejlesztése.

Valódi, nem önállóan feloldható akadálynál a kötelező biztonsági és GitHub-szabályok érvényesek. Az előrehaladási követelmény nem jelenthet indokot ezek megkerülésére.

## 13. § Elsőbbség és kötelező alkalmazás

A szabály minden olyan CFA3-munkafolyamatban alkalmazandó, amely több egymást követő feldolgozási egységet, ellenőrzést és publikációt tartalmaz.

A donoradatbázisra különösen kötelező:

**Egy forrásfájl → teljes feldolgozás → célzott ellenőrzés → lezárás → publikáció → bizonyított eredmény → következő forrásfájl.**

Más CFA3-munkafolyamatokra azonos elv szerint alkalmazandó, azok saját lezárási és publikációs feltételeivel.

A szabály nem írhatja felül a kötelező biztonsági, jogosultsági, jóváhagyási, adatmegőrzési és GitHub-integritási követelményeket.

## 14. § Megfelelőségi és véglegesítési feltételek

A szabály tényleges véglegesítése előtt kötelező:

1. A jóváhagyott szöveg hiánytalan kanonikus felvétele.
2. A CFA3 szabálynyilvántartásaival való konzisztencia.
3. A `CFA3-CURRENT-POLICY-SURFACE-001.json` szükséges frissítése.
4. A Bootstrap és minden más kötelező ellenőrzés teljesítése.
5. Az engedélyezett PR-folyamat szabályos lezárása.
6. A tényleges main-állapotból történő visszaellenőrzés.
7. A végleges státusz bizonyítékokon alapuló rögzítése.

A szabály gyakorlati hatékonyságát csak tartós, több független feldolgozási ciklusból származó bizonyíték alapján szabad visszaigazolni.

**A szabályszöveg jóváhagyása nem azonos a GitHubon végrehajtott véglegesítéssel.**

---

## Kötelező záróelv

**A CFA3 fejlesztő AI feladata nem az, hogy minél több műveletet végezzen, hanem az, hogy a felhasználó által kért eredményt a meghatározott sorrendben, a kötelező ellenőrzések mellett, ténylegesen befejezze és bizonyíthatóan közzétegye.**

A már lezárt munkát nem kezdheti újra indokolatlanul. A következő kijelölt feladatra kell áttérnie, új mellékfeladat létrehozása nélkül.