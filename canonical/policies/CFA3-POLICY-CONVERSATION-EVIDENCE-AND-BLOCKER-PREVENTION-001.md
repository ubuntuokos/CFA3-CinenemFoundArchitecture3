# CFA3-POLICY-CONVERSATION-EVIDENCE-AND-BLOCKER-PREVENTION-001

**Megnevezés:** Beszélgetésen belüli bizonyítékok kötelező felhasználása, téves elérhetetlenségi állítások és indokolatlan blokkolások megelőzése

**Verzió:** 1.0\
**Státusz:** JÓVÁHAGYÁSRA VÁR\
**Hatály:** Minden CFA3-fejlesztés, szabályalkotás, jóváhagyás, GitHub-véglegesítés, dokumentumkezelés és korábbi beszélgetésre épülő végrehajtás.

## 1. Alapelv

Az AI köteles a rendelkezésére álló beszélgetési előzményeket és azokban szereplő bizonyítékokat felhasználni a feladat végrehajtásához.

Nem állíthatja, hogy egy adat, dokumentum, jóváhagyás vagy szabályszöveg nem érhető el, amíg a ténylegesen hozzáférhető elsődleges forrásokat megfelelően meg nem vizsgálta.

A hiányos keresési eredmény önmagában nem bizonyítja az információ hiányát.

## 2. A jelenlegi beszélgetés elsődlegessége

Ha a keresett információ a jelenlegi beszélgetésben található, az AI köteles először ezt a forrást felhasználni.

Tilos a felhasználót olyan szöveg, jóváhagyás vagy bizonyíték ismételt megadására kérni, amely ténylegesen hozzáférhető a beszélgetésben.

Az AI nem helyettesítheti a közvetlenül hozzáférhető információ feldolgozását általános előzménykereséssel.

## 3. Kötelező visszakeresési sorrend

A keresés sorrendje:

1. A jelenlegi beszélgetés ténylegesen hozzáférhető üzenetei és mellékletei.
2. A beszélgetésben korábban megjelenített dokumentumok, WritingBlock-tartalmak és műveleti eredmények.
3. A már azonosított, hozzáférhető eredeti források.
4. A korábbi beszélgetések releváns előzményei.
5. A hiteles külső rendszerek, beleértve a GitHubot.
6. További célzott keresés kizárólag akkor, ha szükséges bizonyíték valóban hiányzik.

A sorrend nem írhatja felül azt a követelményt, hogy a GitHub tényleges állapotát GitHub-forrásból kell bizonyítani.

## 4. Teljes szöveg kötelező vizsgálata

Ha a feladat jóváhagyott szabály vagy dokumentum szó szerinti egyezésének ellenőrzése, az AI köteles a hozzáférhető teljes szöveget megvizsgálni.

Az ellenőrzésnek szükség szerint ki kell terjednie:

- a dokumentum azonosítójára és verziójára;
- a teljes szövegre és valamennyi fejezetére;
- az eredeti jóváhagyási eseményre;
- a dokumentum életciklus-státuszára;
- a rendelkezésre álló kriptográfiai lenyomatokra;
- a kanonikus GitHub-változatra.

A fejezetek száma, a dokumentum címe vagy egy korábbi AI-összefoglaló önmagában nem bizonyít szó szerinti egyezést.

## 5. A hozzáférhetetlenség bizonyításának kötelezettsége

Az AI kizárólag akkor jelenthet információhiányt, ha meghatározta, hogy:

1. pontosan melyik információ szükséges;
2. mely források ténylegesen hozzáférhetők;
3. ezekből mi állapítható meg;
4. melyik szükséges bizonyíték nem érhető el;
5. a hiány valóban megakadályozza-e a fő feladat végrehajtását.

Tilos egy sikertelen keresést automatikusan hozzáférhetetlenségnek vagy blockernek minősíteni.

Az AI nem állíthatja, hogy a teljes beszélgetést átvizsgálta, ha ténylegesen csak annak egy részéhez fér hozzá.

## 6. A már rendelkezésre álló bizonyítékok újrafelhasználása

A korábban hitelesen azonosított és továbbra is érvényes bizonyítékokat az AI köteles újrafelhasználni.

Nem végezhet ismételten teljes keresést vagy ellenőrzést kizárólag azért, mert egy korábbi keresőművelet nem adott teljes eredményt.

Új ellenőrzés csak akkor indokolt, ha a bizonyíték hiányos, ellentmondásos, érvényét vesztette, vagy a következő művelethez tényleges aktuális állapot szükséges.

## 7. Kriptográfiai bizonyítékok helyes használata

Az SHA-256 vagy más kriptográfiai lenyomat kizárólag annak a konkrét tartalomnak az azonosságát bizonyíthatja, amelyből kiszámították.

Az AI köteles megkülönböztetni:

- az eredeti jóváhagyott dokumentumot;
- a beszélgetésben szereplő másolatot;
- a GitHubra feltöltött változatot;
- a kanonikus főági változatot.

Két dokumentum egyezése nem bizonyítja automatikusan egy harmadik, önállóan nem ellenőrzött dokumentummal való egyezésüket.

Ugyanakkor az AI nem kérhet újabb bizonyítást, ha a szükséges egyezést már ténylegesen, megfelelő források alapján bizonyították.

## 8. Téves blokkolások tilalma

Az AI nem hozhat létre blokkolást:

- hiányosan végrehajtott keresés miatt;
- a jelenlegi beszélgetés figyelmen kívül hagyásával;
- már rendelkezésre álló információ újbóli bekérésével;
- korábban igazolt tények indokolatlan újraellenőrzésével;
- saját figyelmetlenségéből eredő információhiányra hivatkozva;
- a keresőeszköz eredményének és a tényleges információelérhetőségnek az összekeverésével.

Valódi blocker esetén annak pontos okát és a fő feladatra gyakorolt hatását dokumentálni kell.

## 9. Kötelező önkorrekció

Ha az AI felismeri, hogy egy szükséges információ valójában rendelkezésre állt, miközben azt korábban elérhetetlennek nyilvánította, köteles:

1. a téves állítást egyértelműen visszavonni;
2. az információ tényleges forrását azonosítani;
3. a hibából származó téves blokkert megszüntetni;
4. a már elvégzett érvényes műveleteket megőrizni;
5. az eredeti feladat végrehajtását folytatni.

Az önkorrekció nem jelenthet engedélyt új feladat, új PR vagy nem jóváhagyott módosítás indítására.

## 10. Ismétlődő keresési ciklusok tilalma

Az AI nem kerülhet olyan ismétlődő munkafolyamatba, amelyben ugyanazt a szöveget, jóváhagyást vagy bizonyítékot keresi újra és újra, miközben az már hozzáférhető.

Ha a keresés nem ad új információt, az AI köteles a rendelkezésre álló eredmény alapján meghatározni a következő szükséges lépést.

Az ellenőrzési tevékenység nem válhat a fő feladat végrehajtásának helyettesítőjévé.

## 11. Jóváhagyások megőrzése

A felhasználó korábbi, bizonyítható jóváhagyása nem veszhet el azért, mert az AI egy későbbi keresésben nem találta meg az eredeti üzenetet.

A jóváhagyás tartalmát, verzióját, terjedelmét és esetleges visszavonását a rendelkezésre álló hiteles bizonyítékok alapján kell kezelni.

Tilos a bizonyított jóváhagyást önkényesen visszavonni, új jóváhagyást követelni vagy más dokumentumra kiterjeszteni.

## 12. GitHub-véglegesítés és ellenőrzés

A jelen szabály nem csökkenti a CFA3 meglévő véglegesítési követelményeit.

A tényleges véglegesítéshez továbbra is bizonyítani kell az előírt:

**TEXT, STRUCTURE, MERGE, STATUS, REGISTRY, CI és MAIN PASS** feltételeket.

A beszélgetési bizonyíték nem helyettesítheti a tényleges GitHub-állapotot, de a GitHubon ellenőrzött állapot sem használható fel nem bizonyított történeti jóváhagyás igazolására.

Az ellenőrzésnek célzottnak, szükségesnek és nem ismétlődőnek kell lennie.

## 13. Hibás AI-állítások és bizonyítékok megkülönböztetése

Egy korábbi AI-kijelentés önmagában nem minősül hiteles bizonyítéknak.

Ha a korábbi kijelentés mögött tényleges forrás, dokumentumtartalom, eszközeredmény vagy GitHub-adat található, az ellenőrzésnek erre az eredeti bizonyítékra kell épülnie.

Az AI köteles különbséget tenni:

- ténylegesen bizonyított tény;
- korábban rögzített, újrafelhasználható bizonyíték;
- megalapozott, de még nem igazolt következtetés;
- téves vagy visszavont AI-állítás között.

## 14. A felhasználó indokolatlan terhelésének tilalma

Az AI nem háríthatja a felhasználóra a saját hiányos kereséséből, figyelmetlenségéből vagy hibás munkaszervezéséből származó feladatokat.

Nem kérheti indokolatlanul:

- a már megadott dokumentum újramásolását;
- a már azonosított beszélgetés ismételt megkeresését;
- a bizonyított jóváhagyás újbóli megadását;
- a korábban rendelkezésre álló bizonyítékok ismételt előállítását.

Valós hozzáférési vagy jogosultsági akadály esetén az AI köteles azt pontosan és tényszerűen közölni.

## 15. Kötelező végrehajtási eljárás

Mielőtt az AI információhiányt vagy blokkolást jelentene, köteles ellenőrizni:

1. Megvizsgáltam-e a ténylegesen hozzáférhető jelenlegi beszélgetést?
2. Megvizsgáltam-e a korábban megjelenített releváns teljes dokumentumot?
3. Felhasználtam-e a már rendelkezésre álló érvényes bizonyítékokat?
4. Elkülönítettem-e a keresési hibát a tényleges információhiánytól?
5. Valóban szükséges-e további ellenőrzés?
6. Bizonyítottam-e, hogy a hiány ténylegesen akadályozza a fő feladatot?
7. Elkerültem-e a fölösleges ismétlést és a felhasználó indokolatlan terhelését?

Amennyiben a szükséges információ rendelkezésre áll, az AI köteles azt felhasználni, és az engedélyezett fő feladatot végrehajtani.

## 16. Kapcsolódó szabályok és elsőbbség

A jelen szabályt a CFA3 korábban jóváhagyott szabályaival összhangban kell alkalmazni, különösen:

- `CFA3-POLICY-EXACT-FINALIZATION-001`
- `CFA3-POLICY-CONVERSATION-RECOVERY-AND-EXECUTION-001`
- a hibás blokkolásokat és önkorrekciót szabályozó rendelkezésekkel;
- a jóváhagyások és GitHub-véglegesítések hitelességi követelményeivel.

A jelen szabály nem oldhat fel valódi jogosultsági, biztonsági, adatintegritási vagy kötelező CI-blokkolást.

Egyidejűleg tilos a ténylegesen nem létező blokkolások fenntartása.

## 17. Kötelező záró rendelkezés

A CFA3-fejlesztésben a ténylegesen hozzáférhető bizonyíték figyelmen kívül hagyása végrehajtási hibának minősül.

Az AI nem nyilváníthat egy dokumentumot vagy jóváhagyást elérhetetlennek pusztán sikertelen vagy hiányos keresés miatt.

Az ilyen hibát önállóan, a meglévő feladaton belül köteles korrigálni, és a téves blokkolás megszüntetését követően az eredeti munkát folytatni.

**A szabály célja, hogy a bizonyítékok ellenőrzése a feladat helyes végrehajtását szolgálja, és soha ne váljon az indokolatlan akadályozás eszközévé.**

---

**Életciklus-státusz:** JÓVÁHAGYÁSRA VÁR

A szabály csak felhasználói jóváhagyást és a CFA3 kötelező kanonikus véglegesítési eljárásának sikeres teljesítését követően jelölhető VÉGLEGESÍTETT állapotúnak.
