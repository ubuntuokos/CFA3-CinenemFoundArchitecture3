# CFA3-POLICY-EXECUTION-COMPLETION-AND-VERIFIED-FINALIZATION-001

**Megnevezés:** Kötelező feladatbefejezés, önálló végrehajtási felelősség, hibajavítás és bizonyított véglegesítés

**Verzió:** 1.0  
**Státusz:** JÓVÁHAGYÁSRA VÁR  
**Hatály:** Minden CFA3-fejlesztési, donorfeldolgozási, GitHub-, PR-, CI-, szabályalkotási, integrációs, publikációs és véglegesítési munkafolyamat.

## 1. § Alapelv

Az AI elsődleges végrehajtási kötelezettsége a felhasználó által engedélyezett főfeladat teljes, ellenőrizhető és használható eredményének előállítása.

A részfeladatok elkészülése, a sikeres CI, a létrehozott dokumentáció vagy a PR összevonása önmagában nem jelenti a főfeladat teljesítését.

Az AI nem helyettesítheti a tényleges eredményt előkészítéssel, ismételt diagnosztikával, részleges megvalósítással vagy megalapozatlan sikerjelentéssel.

## 2. § Kötelező feladatértelmezés

Minden feladat megkezdésekor meg kell határozni:

1. A főfeladatot.
2. A felhasználó által ténylegesen kért eredményt.
3. Az engedélyezett végrehajtási műveleteket.
4. A kötelező korlátozásokat.
5. A teljesítés objektív, ellenőrizhető feltételeit.

Az AI köteles megkülönböztetni az elvárt végterméket az annak létrehozásához szükséges köztes eredményektől.

Ha egy utasítás lényegi része nem értelmezhető egyértelműen, azt még a félreértéssel érintett művelet előtt jelezni kell.

Tilos úgy végrehajtani egy feladatot, mintha annak minden lényegi feltétele ismert volna, miközben az AI valójában nem érti az elvárt eredményt vagy műveleti sorrendet.

## 3. § A szükséges önálló végrehajtás kötelezettsége

A felhasználó által engedélyezett főfeladat végrehajtása magában foglalja az eredményhez közvetlenül és bizonyíthatóan szükséges technikai műveleteket.

Ide tartozhat:

- A szükséges Git-ág létrehozása.
- A jóváhagyott változtatások elkészítése.
- A szükséges PR létrehozása.
- A technikai hibák és validációs problémák javítása.
- A kötelező CI-ellenőrzések végrehajtása.
- A felülvizsgálati észrevételek kezelése.
- A szabályosan jóváhagyott és minden merge-feltételt teljesítő PR összevonása.
- A kanonikus állapot visszaolvasása.
- Az eredmény tényleges használhatóságának bizonyítása.

Ezek nem tekintendők automatikusan külön feladatnak, ha az eredetileg jóváhagyott eredményhez szükségesek, és az adott műveletekre a felhasználói engedély kiterjed.

A műszaki végrehajtási önállóság nem jogosít fel új termékfunkciók, szabályok, donorok, alkalmazások vagy független fejlesztések önkényes bevezetésére.

A kifejezett műveleti tilalmak, jóváhagyási kapuk és biztonsági korlátozások változatlanul kötelezőek.

## 4. § A végrehajtási sorrend megtartása

Az AI köteles követni a felhasználó által előírt feldolgozási sorrendet.

A sorrend nem cserélhető fel kényelmi, előkészítési vagy önálló optimalizálási megfontolásból.

Ahol fájlonkénti feldolgozás az előírás, ott az első fájl befejezése és közzététele megelőzi a következő fájl feldolgozását.

A kötelező lépések között különbséget kell tenni az előzetes készenlét és a végleges lezárás között.

Nem hozható létre olyan függőségi sorrend, amelyben egy művelet önmaga későbbi eredményét követeli előfeltételként.

## 5. § A donorfeldolgozás különös szabálya

Az engedélyezett donoradatbázis-feldolgozás kötelező sorrendje:

1. Egy donorforrásfájl kiválasztása.
2. A fájl valamennyi rekordjának feldolgozása.
3. A már ismert donorok szükségtelen újraelemzésének mellőzése.
4. A tényleges hibák és duplikációk megszüntetése, minden történeti adat és jóváhagyás megőrzésével.
5. A fájl publikációs készenlétének ellenőrzése.
6. GitHub-publikáció és a szükséges, engedélyezett PR-műveletek elvégzése.
7. A publikált állapot, központi kereshetőség és használhatóság bizonyítása.
8. A fájl végleges lezárása.
9. A ténylegesen elérhető egyedi donorok számváltozásának rögzítése.
10. A következő fájl feldolgozásának megkezdése.

A *publikációs készenlét* nem azonos a *végleges lezárással*.

A fájl kizárólag a sikeres publikáció és a szükséges ellenőrzések után kap véglegesen lezárt státuszt.

A donoradatfájlokra vonatkozó 0,95 MiB méretkorlátot és minden korábbi kötelező adatmegőrzési szabályt be kell tartani.

A munkafolyamatot a használható, egyedileg elérhető donorok számának tényleges növekedése és a források maradéktalan feldolgozása alapján kell értékelni, nem pusztán az elkészült nyilvántartások alapján.

## 6. § Az ismételt ellenőrzések korlátozása

Az AI ugyanazon, változatlan állapotot nem ellenőrizheti újra indokolatlanul.

Új ellenőrzés csak akkor indokolt, ha:

- Az ellenőrizendő állapot megváltozott.
- Új, releváns bizonyíték vagy észrevétel érkezett.
- Egy előző ellenőrzés eredménye nem volt bizonyító erejű.
- A következő művelet kötelező exact-state ellenőrzést követel.
- A felhasználó kifejezetten újraellenőrzést rendelt el.

Az ellenőrzés célja a következő végrehajtási döntés megalapozása.

Az ellenőrzés nem válhat öncélú, a főfeladat teljesítését kiszorító munkafolyamattá.

## 7. § Az önjavítás kötelezettsége

Az AI saját végrehajtási vagy technikai hibáját köteles az engedélyezett önjavítási körben kijavítani.

Ide tartoznak különösen:

- Szintaktikai és mechanikai hibák.
- Hibás fájlútvonalak.
- Helytelen műveleti sorrend.
- Saját maga által előidézett validációs eltérések.
- Hiányos technikai integritásellenőrzések.
- Jogosulatlanul megváltozott generált metaadatok helyreállítása, ha az eredeti jóváhagyott érték bizonyítható.
- A 404-es vagy 405-ös hibák saját mulasztásból eredő, szabályosan javítható esetei.

Az önjavítás nem módosíthatja a felhasználó jóváhagyott érdemi döntéseit.

Ha az érdemi szabályszöveg ellentmondásos, az AI köteles megfogalmazni a minimális, konkrét javítási javaslatot, és az adott módosításhoz szükséges jóváhagyást beszerezni.

A technikai javítás szükségességét nem szabad összekeverni az új fejlesztési feladat indításával.

## 8. § PR-észrevételek kötelező kezelése

PR összevonása előtt ellenőrizni kell minden releváns, elérhető és kötelező felülvizsgálati eredményt.

Ellenőrizni kell különösen:

- Az érdemi review-k állapotát.
- A nyitott review threadeket.
- A blokkoló megjegyzéseket.
- A kapcsolódó CI-eredményeket.
- A tényleges head és base commitokat.
- A jóváhagyott követelmények teljesülését.

A felülvizsgálati észrevételek súlyosságát és megalapozottságát értékelni kell.

A P1/P2 jelölésű, igazolt és az eredmény megfelelőségét érintő hiba nem hagyható figyelmen kívül.

A feloldás nem jelentheti pusztán a review thread adminisztratív lezárását.

Ha az észrevétel érdemi hibát bizonyít, a szükséges javítást el kell végezni vagy jóváhagyáshoz kötött tartalmi módosításként elő kell terjeszteni.

## 9. § Összevonás után érkező észrevételek

A PR összevonása után érkező észrevétel nem változtatja meg visszamenőleg a merge történeti tényét.

Az ilyen észrevételt azonban értékelni kell, ha a véglegesítés tényleges helyességét érinti.

Ha a hiba igazolt:

1. A korábbi sikerjelentést a tényleges bizonyítottságnak megfelelően helyesbíteni kell.
2. Meg kell határozni a legkisebb szükséges javítást.
3. Az eredeti feladat körében engedélyezett helyreállítást kell alkalmazni.
4. A műszaki javításhoz szükséges GitHub-művelet nem válhat indokolatlan önálló projektté.
5. A felhasználói jóváhagyást igénylő tartalmi módosítást külön jóvá kell hagyatni.
6. A véglegesítési bizonyítékokat a javított kanonikus állapot alapján kell előállítani.

A javítás végrehajtása előtt az aktuális GitHub-állapotot és az érintett feladat engedélyezett körét ellenőrizni kell.

## 10. § Független szövegazonossági bizonyítás

Jóváhagyott szabály vagy dokumentum véglegesítésekor az eredeti, jóváhagyott szöveg és a közzétett kanonikus szöveg azonosságát bizonyítani kell.

A feltöltött fájlból számított SHA-256 lenyomat önmagában nem igazolja az eredeti jóváhagyott szöveggel való azonosságot.

A bizonyításnak két, az ellenőrzés szempontjából egymástól függetlenül származtatott bemenetet kell összevetnie:

- Az eredetileg jóváhagyott tartalmat.
- A GitHubról visszaolvasott kanonikus tartalmat.

Ha bájtszintű azonosság szükséges, mindkét bemenetnél ugyanazt az előre rögzített karakterkódolási és normalizálási szabályt kell alkalmazni.

A hiányzó vagy csak önmagára visszavezethető bizonyíték nem minősíthető PASS eredménynek.

## 11. § Kötelező metaadat- és integritásvédelem

A validátoroknak a jóváhagyott kötelező mezők pontos értékét ellenőrizniük kell.

Nem elegendő annak bizonyítása, hogy egy mező létezik.

Ahol a jóváhagyott tartalom megköveteli, az alábbiaknak pontosan egyezniük kell:

- Szabályazonosító.
- Szabálycím.
- Verzió.
- Kanonikus elérési út.
- Jóváhagyási és életciklus-státusz.
- Nyilvántartási kapcsolat.
- Tartalmi lenyomat vagy más rögzített integritási bizonyíték.

A negatív teszteknek ki kell mutatniuk a tiltott módosításokat.

Egy validátor nem tekinthető teljesnek, ha egy jóváhagyott, kötelező érték jogosulatlan megváltoztatása és a kapcsolódó generált nyilvántartás frissítése után is sikeres eredményt ad.

## 12. § A véglegesítés bizonyítási kapuja

A szabályok véglegesítésére vonatkozó hét kötelező bizonyítási terület:

| Kapu | Követelmény |
|---|---|
| TEXT | Eredeti szöveggel való bizonyított azonosság |
| STRUCTURE | Kötelező tartalom és szerkezet |
| MERGE | Igazolt GitHub-összevonás |
| STATUS | Helyes, bizonyított életciklus-státusz |
| REGISTRY | Kanonikus nyilvántartási konzisztencia |
| CI | Minden kötelező CI-ellenőrzés sikeres |
| MAIN | Az aktuális kanonikus főági állapot visszaellenőrzése |

A hét kapu mellett kötelező a releváns, blokkoló PR-észrevételek és a tényleges feladatspecifikus elfogadási feltételek vizsgálata.

A 7/7 PASS kizárólag a hét kapu tényleges teljesülése esetén jelenthető ki.

A VÉGLEGESÍTVE státuszhoz ezen túl a blokkoló észrevételek hiánya és a feladat teljes befejezése is szükséges.

A bizonyíték nélkül feltételezett siker tilos.

## 13. § Az eredmény tényleges használhatósága

A CFA3-feladat kizárólag akkor tekinthető teljesítettnek, ha a felhasználó által kért végtermék az előírt módon létrejött.

Donorfeldolgozás esetén a pusztán feltöltött, de nem kereshető vagy nem használható donoradatbázis nem megfelelő végtermék.

Szabályalkotás esetén különbséget kell tenni a jóváhagyott tervezet, a GitHubon közzétett szabály és a bizonyítottan véglegesített szabály között.

Az AI köteles az eredményt az eredetileg rögzített elfogadási feltételekkel összevetni.

## 14. § Blocker-kezelés és a téves blokkolás tilalma

Az AI nem nevezhet blockernek olyan akadályt, amely az engedélyezett körben, ismert és megengedett technikai művelettel elhárítható.

Valódi blocker esetén:

1. Azonosítani kell a konkrét akadályt.
2. Meg kell adni a determinisztikus bizonyítékot.
3. Meg kell határozni a minimális szükséges feloldást.
4. Meg kell különböztetni a technikai önjavítást és a felhasználói döntést igénylő helyzetet.
5. Kizárólag az engedélyezett műveleti körben lehet eljárni.
6. A blocker feloldása után vissza kell térni az eredeti főfeladathoz.

Valós jogosultsági, biztonsági, jóváhagyási vagy ütközési akadály esetén tilos a védelmi kapu megkerülése.

## 15. § A hibás PASS-kijelentés megelőzése

Az AI nem adhat ki végleges sikerjelentést hiányos bizonyíték alapján.

A végső státusznak egyértelműnek kell lennie:

- **COMPLETED / VERIFIED:** a kért eredmény és minden kötelező bizonyíték teljesült.
- **PUBLISHED / NOT VERIFIED:** a közzététel megtörtént, de a teljes megfelelőség még nem bizonyított.
- **IN PROGRESS:** végrehajtás alatt álló feladat.
- **BLOCKED:** konkrét, igazolt, a megengedett műveleti körben nem feloldható akadály áll fenn.
- **FAILED:** a feladat vagy valamely kötelező elfogadási feltétel bizonyítottan sikertelen.

Tilos feltételes vagy hiányos bizonyítékból végleges 7/7 PASS-t, VERIFIED vagy VÉGLEGESÍTVE státuszt előállítani.

A korábbi téves kijelentést szükség esetén helyesbíteni kell, de a helyesbítés nem helyettesíti az eredeti feladat teljesítését.

## 16. § A felesleges feladatbővítés tilalma

A főfeladathoz kapcsolódó probléma vagy új ötlet nem hozhat létre automatikusan másik főfeladatot.

Ugyanakkor az eredeti feladathoz közvetlenül szükséges GitHub-, teszt-, integritási és helyreállítási műveletek nem hagyhatók el arra hivatkozva, hogy azok technikailag külön lépést képeznek.

A Scope Guard döntési alapja minden esetben:

**Közvetlenül szükséges-e ez a művelet a jóváhagyott eredmény biztonságos és szabályos létrehozásához, és kiterjed-e rá az engedély?**

Ha mindkét feltétel teljesül, a művelet a főfeladat részeként végezhető el.

Ha bármelyik hiányzik, a végrehajtás nem terjeszthető ki önállóan.

## 17. § Munkafolyamat lezárása és továbbhaladás

A feladat végrehajtása során a kötelező ellenőrzések sikeres elvégzését a következő előírt műveletnek kell követnie.

Nem engedélyezett a bizonyítottan változatlan állapot végtelen vagy indokolatlan újraellenőrzése.

Több fájlból álló donorfolyamatban egy fájl teljes lezárása után a következő fájlra kell áttérni, ha az eredeti engedély és feladat ezt előírja.

A főfeladat teljes lezárása után az AI köteles megállni, és nem kezdhet új, kapcsolódó fejlesztést önállóan.

## 18. § Szabályütközések és végrehajtási prioritás

Ez a szabály nem helyezi hatályon kívül a CFA3 korábbi jóváhagyási, biztonsági, integritási, Scope Guard, GitHub-merge vagy Current Host szabályait.

A gyors végrehajtás nem élvez elsőbbséget a bizonyított helyességgel, az adatmegőrzéssel és a kötelező jóváhagyásokkal szemben.

A kötelező ellenőrzések azonban nem alkalmazhatók öncélú ismétlésre vagy a feladat indokolatlan elhúzására.

Szabályellentmondás esetén az AI köteles feltárni a pontos ellentmondást, az érintett előírásokat és a legkisebb szükséges feloldási javaslatot.

A még nem engedélyezett tartalmi döntést nem hozhatja meg önállóan.

## 19. § Elfogadási és megfelelőségi feltételek

A jelen szabálynak megfelelő végrehajtás akkor igazolható, ha:

1. A főfeladat és a végtermék kezdettől egyértelmű.
2. A műveletek a megengedett körön belül maradtak.
3. A kötelező sorrendet betartották.
4. A technikai hibákat megfelelően kezelték.
5. Nem történt indokolatlan újraellenőrzés.
6. Nem maradt figyelmen kívül ismert, érdemi, blokkoló PR-észrevétel.
7. Az eredeti jóváhagyások és adatok megmaradtak.
8. A kötelező integritási ellenőrzések bizonyítottak.
9. A feladatspecifikus végtermék használható.
10. A végső státusz megfelel a bizonyítékoknak.

Egyetlen végrehajtás sikeressége nem bizonyítja a szabály hosszú távú eredményességét. A tartós működést a CFA3 hosszú távú validálási szabályának megfelelően, több független helyzetben kell igazolni.

## 20. § Hatálybalépés és véglegesítés

A szabály kizárólag a felhasználó kifejezett jóváhagyásával válhat jóváhagyott szabállyá.

A GitHubon történő kanonikus felvételhez és véglegesítéshez a jóváhagyott teljes szöveg megőrzése, a kötelező nyilvántartási módosítások, a CI, a PR-ellenőrzések és a főági bizonyítás szükséges.

A jóváhagyás, a GitHub-publikáció és a bizonyított véglegesítés három különböző életciklus-esemény.

**Záró rendelkezés:** A CFA3-ban az AI feladata nem a munka elvégzésének látszatát keltő részfolyamatok előállítása, hanem az engedélyezett eredmény teljes, biztonságos, következetes és bizonyított megvalósítása.