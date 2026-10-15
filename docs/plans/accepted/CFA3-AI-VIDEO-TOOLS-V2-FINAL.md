# CFA3 — AI VIDEO TOOLS
## Teljes, elfogadott funkcionális és architekturális rendszerterv

**Kategória:** Elfogadott tervek  
**Alkalmazásterület:** AI / Video Generation / Creative Tools  
**Dokumentumverzió:** 2.0 FINAL  
**Döntési állapot:** Felhasználó által elfogadott  
**Implementációs állapot:** Tervezett, még nem megvalósított  
**Dátum:** 2026. október 15.  
**Platform:** CFA3 — Cinema Fund Architectura 3

---

# 1. Az alkalmazás rendeltetése

Az AI Video Tools a CFA3 kreatív platform önálló AI-videógeneráló alkalmazása.

Feladata a gyors, egyszerűen használható AI-videógeneráló rendszerek egyetlen CFA3-alkalmazásba szervezése.

Az alkalmazás a Stability Matrix által képviselt eszközgyűjtemény-modellt követi, de annak funkcionális megközelítését a CFA3 saját, egységes platformarchitektúrájához igazítja.

## 1.1. Elsődleges célok

- Egyszerű és gyors AI-videógenerálás.
- Több különböző AI-videógeneráló motor közös felületen történő használata.
- Helyben futtatható és felhőalapú generálórendszerek támogatása.
- A CFA3 meglévő kreatív alkalmazásaiban nem szereplő generátorok megőrzése.
- A hasznos generálási technológiák fejlődésének követése.
- Új eszközök későbbi integrálásának biztosítása.
- Közös AI-modellhasználat és modellkezelés.
- A felesleges alkalmazás-, modell- és infrastruktúra-duplikáció megszüntetése.

## 1.2. Funkcionális határok

Az AI Video Tools nem teljes értékű, timeline-alapú videószerkesztő alkalmazás.

Nem helyettesíti a CFA3 Video Editor, VFX Studio, Animation Studio vagy más szakosított kreatív alkalmazásokat.

Feladata elsősorban a generálás, a gyors előállítás, a generátorok vezérlése és az eredmények továbbadása.

A videószerkesztési, kompozitálási, színkorrekciós és összetett produkciós funkciók a megfelelő CFA3-alkalmazások felelősségi körében maradnak.

---

# 2. Kötelező AI Video Tools alapcsomag

A CFA3 telepítésekor hét előre meghatározott generálórendszernek vagy szolgáltatóadapternek kell felkerülnie a számítógépre.

Ezek az AI Video Tools alapcsomagjának kötelező részei.

| Azonosító | Eszköz | Elsődleges szerep | Integráció |
|---|---|---|---|
| AVT-001 | FramePack | Képből videó generálása, képkockák fokozatos előállítása | Helyi backend |
| AVT-002 | WanGP | Több modellcsaládot támogató AI-videógenerálás | Helyi backend |
| AVT-003 | LTX Desktop | Gyors AI-videógenerálás, helyi és támogatott távoli útvonalakkal | Helyi / szolgáltatói backend |
| AVT-004 | VideoX-Fun | Szöveg-, kép- és videóvezérelt generálás | Helyi backend |
| AVT-005 | EasyAnimate | AI-videógenerálás és animációs képességek | Helyi backend |
| AVT-006 | Runway API | Felhőalapú AI-videógenerálás | Cloud adapter |
| AVT-007 | Kling AI API | Felhőalapú AI-videógenerálás | Cloud adapter |

## 2.1. Az alapcsomag kötelező szabályai

1. Mind a hét eszköznek szerepelnie kell a CFA3 alaptelepítési tervében.
2. Egyik sem válhat automatikusan opcionális eszközzé.
3. A felhasználónak nem kell külön kiválasztania a hét alapeszközt.
4. A rendszer minden telepített eszközt a közös AI Video Tools katalógusában tart nyilván.
5. Az alkalmazások használata a CFA3 saját GUI-ján keresztül történik.
6. Az AI-modellfájlok nem részei az alaptelepítőnek.
7. A generátorok futtathatósága a hardveres és technikai követelményektől függ.
8. A telepített és az aktuálisan futtatható állapotot külön kell kezelni.

## 2.2. Az alapcsomag technikai tartalma

A helyi eszközöknél telepítendő:

- a szükséges generálómotor;
- a megfelelő futtatási komponensek;
- az alkalmazásspecifikus függőségek;
- a CFA3-integrációs adapter;
- a konfiguráció és képességdefiníció;
- a verzió- és kompatibilitási metaadatok.

A Runway és Kling esetében:

- a CFA3 szolgáltatóadapter;
- API-kapcsolati és feladatkezelési integráció;
- közös hitelesítéskezelési kapcsolat;
- a támogatott szolgáltatási képességek nyilvántartása.

A felhőszolgáltatások távoli modelljei nem települnek helyi AI-modellfájlként.

## 2.3. Upstream források

- FramePack: https://github.com/lllyasviel/FramePack
- WanGP: https://github.com/deepbeepmeep/WanGP
- LTX Desktop: https://github.com/Lightricks/LTX-Desktop
- VideoX-Fun: https://github.com/aigc-apps/VideoX-Fun
- EasyAnimate: https://github.com/aigc-apps/EasyAnimate
- Runway API: https://docs.dev.runwayml.com/api/
- Kling AI API: https://kling.ai/document-api/apiReference/model/textToVideo

A konkrét kiadásokat, licenceket, támogatott platformokat és vezérlőinterfészeket az implementáció előtt hitelesen ellenőrizni kell.

---

# 3. Opcionálisan telepíthető generátorok

A hét kötelező alapeszközön túl később bármennyi megfelelő és jóváhagyott AI-videógenerátor felvehető az AI Video Tools katalógusába.

Az újonnan hozzáadott generátorok nem részei automatikusan a CFA3 alaptelepítésének.

## 3.1. Opcionális csomagok működése

A katalógusban szereplő opcionális generátor:

- megtekinthető;
- képességei összehasonlíthatók;
- rendszerkövetelményei ellenőrizhetők;
- telepítése külön indítható;
- a telepített példánya frissíthető;
- felhasználói döntéssel eltávolítható.

A később megjelenő generátor telepítését a CFA3 nem kezdeményezheti önállóan.

## 3.2. Kötelező telepítési besorolás

| Besorolás | Telepítési szabály |
|---|---|
| CORE_REQUIRED | CFA3 alaptelepítéssel kötelező |
| OPTIONAL_AVAILABLE | Katalógusban elérhető, nincs telepítve |
| OPTIONAL_INSTALLED | Felhasználó által telepített |
| INCOMPATIBLE | Az adott célrendszeren nem támogatott |
| INSTALL_BLOCKED | A telepítés technikai, jogi vagy biztonsági akadályba ütközik |

Az alapcsomag frissítése nem módosíthatja automatikusan az opcionális csomagok telepítési besorolását.

---

# 4. CFA3 natív grafikus felület

## 4.1. Kötelező GUI-elv

Az AI Video Tools valamennyi generátora kizárólag a CFA3 saját grafikus felhasználói felületén keresztül használható.

A rendszer alapértelmezett böngészője nem szolgálhat az eszközök grafikus felületeként.

Nem engedélyezett az a megoldás, amelyben az AI Video Tools csak elindítja a FramePack, WanGP vagy más upstream alkalmazás eredeti WebUI-ját.

Az upstream alkalmazások generálómotorját és támogatott funkcióit kell a CFA3 felületével összekapcsolni.

## 4.2. GUI-technológia

A CFA3 saját natív GUI-előírásának megfelelő Qt 6 alapú felhasználói felület szükséges.

A felületnek illeszkednie kell:

- a CFA3 közös navigációjához;
- az egységes vizuális megjelenéshez;
- a közös témakezeléshez;
- a CFA3 felhasználói és munkaterület-kezeléséhez;
- az egységes hibajelzési és visszajelzési rendszerhez;
- a platform közös konfigurációs felületéhez.

## 4.3. Fő GUI-területek

### Quick Generate

Egyszerű generálási felület a legfontosabb funkciókkal:

- generátorválasztás;
- szöveges prompt;
- referencia-kép vagy videó;
- modellválasztás;
- képarány;
- felbontás;
- generálási időtartam;
- támogatott minőségi beállítások;
- generálási művelet indítása.

Csak az adott generátor által ténylegesen támogatott paraméterek jelenhetnek meg.

### Generators

A hét kötelező és a további telepített generátor kezelőfelülete.

Megjeleníti:

- a generátor nevét;
- telepített verzióját;
- elérhetőségét;
- futtatási állapotát;
- támogatott modelleit;
- fő képességeit;
- szükséges hardvert;
- esetleges konfigurációs hiányosságait.

### Models

A közös CFA3 Model Manager funkcióinak integrált megjelenítése.

Az AI Video Tools nem készít saját modellkezelő rendszert.

### Jobs

A generálási feladatok közös állapotkövetési felülete.

Megjeleníthető:

- várakozó feladat;
- előkészítés;
- modell rendelkezésre bocsátása;
- folyamatban lévő generálás;
- támogatott előrehaladási adatok;
- befejezett feladat;
- sikertelen vagy megszakított folyamat.

### Outputs

Generált videók megtekintése és kezelése.

A kész videók a CFA3 közös médiakezelési rendszerében kerülnek nyilvántartásba.

### Packages

Kötelező alapeszközök és opcionális csomagok kezelése.

### Settings

Alkalmazásspecifikus beállítások, hitelesítés, adapterállapot és engedélyezett futtatási lehetőségek.

---

# 5. Generálómotorok integrációja

Az AI Video Tools nem az upstream alkalmazások grafikus felületét, hanem azok vezérelhető generálási képességeit integrálja.

Minden motor a Shared Plugin & Extension Fabric infrastruktúrához kapcsolódik.

## 5.1. Adapterfelelősségek

Egy generátoradapter kezeli:

1. A generálómotor felismerését.
2. A támogatott képességek deklarálását.
3. A szükséges konfiguráció továbbítását.
4. A modellkövetelmények közlését a CFA3 Model Managerrel.
5. A generálási paraméterek átalakítását.
6. A generálási feladat indítását.
7. A feladatállapot továbbítását.
8. A támogatott megszakítási műveleteket.
9. A hibák strukturált továbbítását.
10. Az elkészült videó átadását a CFA3 médiakezelésének.

## 5.2. Lehetséges backendkapcsolatok

- Támogatott API.
- Parancssori interfész.
- Python backendkapcsolat.
- Natív programozott interfész.
- Biztonságosan vezérelhető háttérszolgáltatás.
- Külső felhőszolgáltató API-ja.

A megfelelő integrációs módszert eszközönként, a tényleges upstream támogatás alapján kell meghatározni.

## 5.3. Integrációs tiltások

Az adapter nem hozhat létre:

- külön AI Model Managert;
- saját tartós modellletöltési nyilvántartást;
- külön általános workflow-motort;
- párhuzamos médiatárolási rendszert;
- a CFA3 hardvervédelmét megkerülő futtatási útvonalat.

Ha valamely eszköz nem vezérelhető megfelelő interfészen keresztül, az integrációt blokkoltnak kell minősíteni, nem pedig külső böngészővel helyettesíteni.

---

# 6. CFA3 Model Manager — kizárólagos modellkezelés

## 6.1. Központi felelősség

A CFA3 Model Manager a teljes platform közös AI-modellkezelő komponense.

Az AI Video Tools minden helyi AI-modellműveletet rajta keresztül végez.

Felelősségei:

- modellazonosítás;
- modellkeresés;
- modellletöltés;
- integritásellenőrzés;
- közös modellnyilvántartás;
- közös modellállományok kezelése;
- deduplikáció;
- modellverzió-kezelés;
- frissítési folyamatok;
- kompatibilitás-nyilvántartás;
- megszűnt modellek életciklus-kezelése;
- modellmegőrzés és eltávolítás.

A Model Manager saját, már jóváhagyott működési elvei elsődlegesek.

## 6.2. Modell nélküli CFA3-telepítés

A CFA3 telepítője nem tartalmaz AI-modellfájlokat.

Az AI Video Tools telepítésekor csak az alkalmazások, backendek, adapterek és szükséges futtatási komponensek kerülnek telepítésre.

Az AI-modellek az adott alkalmazás elindítása után, tényleges igény alapján válhatnak szükségessé.

## 6.3. Modelllekérés

Amikor a felhasználó elindít egy generátort:

1. A generátoradapter meghatározza a szükséges AI-modellt.
2. A CFA3 Model Manager ellenőrzi a közös modelltárat.
3. Ellenőrzi a modellazonosítót, verziót és kompatibilitást.
4. Ha a modell már rendelkezésre áll, a meglévő példányt biztosítja.
5. Ha a modell hiányzik, a Model Manager kezeli a beszerzését.
6. A letöltött modell a közös modelltárban kerül nyilvántartásba.
7. A kompatibilis CFA3-alkalmazások ugyanazt a példányt használhatják.

## 6.4. Kötelező deduplikáció

**Ha egy modell megfelelő példánya már le van töltve, ugyanannak a modellállománynak az ismételt letöltése tilos.**

Ez a szabály a teljes CFA3-platformra érvényes.

Nem számít, hogy a modellt először melyik alkalmazás töltötte le.

Példa:

Ha a WanGP által használt modell már szerepel a CFA3 közös modelltárában, és a VideoX-Fun vagy másik CFA3-alkalmazás ugyanazt a kompatibilis modellállományt igényli, a meglévő példányt kell felhasználni.

Új letöltés nem indítható.

## 6.5. Párhuzamos letöltések megakadályozása

Ha több alkalmazás egyszerre kér egy hiányzó modellt, a CFA3 Model Manager egyetlen közös letöltési műveletet kezel.

A többi modellkérés ehhez a folyamatban lévő feladathoz kapcsolódik.

Nem indulhat egymással párhuzamosan több azonos letöltés.

## 6.6. Modellverziók

Eltérő modellverziók, kvantálások, finomhangolt változatok és fájlformátumok csak akkor tekinthetők ugyanannak az állománynak, ha tényleges tartalmuk megegyezik.

A közös modellkezelőnek a következőket kell nyilvántartania:

- modellazonosító;
- verzió;
- változat;
- fájlformátum;
- integritási azonosító;
- forrás;
- licenc;
- kompatibilis alkalmazások;
- használati függőségek.

A különböző, ténylegesen szükséges és kompatibilitási okból megtartandó változatok központilag, ellenőrzött módon kezelhetők.

---

# 7. Modellfrissítések

Ha egy már letöltött modellhez új verzió jelenik meg, a frissítést a CFA3 Model Manager végzi.

## 7.1. Kötelező frissítési folyamat

1. A Model Manager ellenőrzi a modell hiteles forrását.
2. Meghatározza az elérhető új verziót.
3. Ellenőrzi az új verzió integritását és licencfeltételeit.
4. Ellenőrzi, mely CFA3-alkalmazások használják a modellt.
5. Megállapítja az új verzió kompatibilitását.
6. Központilag letölti a szükséges új változatot.
7. Regisztrálja az új verziót a közös modelltárban.
8. Biztonságosan átállítja a kompatibilis alkalmazások hivatkozásait.
9. A korábbi verziókat csak akkor távolítja el, ha azok megőrzésére már nincs szükség.

## 7.2. Kompatibilitásvédelem

Az új modellverzió bevezetése nem teheti működésképtelenné egy másik CFA3-alkalmazás korábbi, kompatibilis modellhasználatát.

Ha az új verzió nem kompatibilis valamelyik érintett alkalmazással, a működő verziót meg kell őrizni.

A frissítés nem írhat felül visszaállíthatatlanul egy használatban lévő modellállományt.

## 7.3. Sikertelen frissítés

A modellfrissítés sikertelensége esetén a meglévő, működő és engedélyezett verzió nem sérülhet.

Az érvénytelen vagy sérült új változat nem válhat aktív modellé.

A CFA3 Model Manager a saját helyreállítási és hibakezelési előírásai szerint jár el.

---

# 8. Megszűnt és nem karbantartott AI-modellek

Ha egy modell eredeti forrása megszűnik, vagy a modell fejlesztését hivatalosan befejezik, annak meglévő helyi példányát a CFA3 nem törölheti automatikusan.

A felhasználó dönthet a további kezeléséről.

## 8.1. Első lehetőség — megtartás

A felhasználó megtarthatja a modellt.

Ebben az esetben:

- a modell továbbra is a közös modelltárban marad;
- nem szükséges újra letölteni;
- a kompatibilis alkalmazások továbbra is használhatják;
- nem kerül automatikusan törlésre;
- a CFA3 nyilvántartja a megszűnt támogatási állapotot.

A modell addig használható, amíg az alkalmazásokkal kompatibilis, és a CFA3 kötelező biztonsági előírásai a futtatását engedélyezik.

## 8.2. Második lehetőség — eltávolítás

A felhasználó kérheti a modell eltávolítását.

A Model Manager először ellenőrzi:

- mely alkalmazások használják;
- mely alkalmazások függnek a modelltől;
- az eltávolítás milyen funkciókat érint;
- a modellnek vannak-e más alkalmazások számára szükséges változatai.

A rendszer a következmények bemutatása után, kifejezett felhasználói megerősítéssel hajthatja végre az eltávolítást.

## 8.3. Megszűnt forrás felismerése

A forrás átmeneti elérhetetlensége nem jelenti automatikusan a fejlesztés megszűnését.

A CFA3-nak külön kell kezelnie:

- átmeneti forráshibát;
- tartós elérhetetlenséget;
- hivatalosan megszűnt támogatást;
- archivált modellt;
- eltávolított vagy visszavont modellkiadást.

A felhasználói döntést ténylegesen ellenőrzött információkra kell alapozni.

---

# 9. Generálási képességek

Az AI Video Tools a rendelkezésre álló generálómotorok támogatásától függően többféle videógenerálási módszert biztosít.

## 9.1. Tervezett képességcsoportok

| Képesség | Leírás |
|---|---|
| Text-to-Video | Videó generálása szöveges leírásból |
| Image-to-Video | Állókép animálása, videó készítése |
| Video-to-Video | Meglévő videó generatív átalakítása |
| Reference-guided Generation | Referenciák alapján irányított generálás |
| Image Animation | Állóképek mozgásának létrehozása |
| Prompt-based Motion | Mozgás leírásalapú vezérlése |
| Generative Variation | Támogatott változatok és alternatív eredmények készítése |
| Video Extension | Videó továbbgenerálása, ahol a backend támogatja |

Nem minden generátor támogat minden funkciót.

A CFA3-nak generátoronként és modellverziónként kell nyilvántartania a tényleges képességeket.

## 9.2. Generálási paraméterek

A közös GUI a támogatott paraméterek alapján kezelheti:

- prompt;
- negatív prompt;
- referenciaanyag;
- képarány;
- felbontás;
- időtartam;
- képkockasebesség;
- modellválasztás;
- véletlen seed;
- minőségi profil;
- generálási lépések;
- generálás-specifikus beállítások.

A GUI kizárólag a kiválasztott backend által igazolt paramétereket jelenítheti meg.

## 9.3. Generálási eredmények

Az elkészült videókhoz rendelkezésre álló generálási metaadatokat rögzíteni kell.

Ilyenek lehetnek:

- használt generátor;
- modellazonosító;
- modellverzió;
- generálási paraméterek;
- futtatási környezet;
- eredeti referenciaanyagok;
- létrehozási idő;
- feladat azonosítója;
- kimeneti formátum.

A metaadatkezelés a CFA3 közös médiarendszeréhez kapcsolódik.

---

# 10. Generálási feladatok végrehajtása

A feladatok a CFA3 meglévő közös workflow-architektúráját használják.

A korábban elfogadott célarchitektúra szerint a tartós feladatok központi motorja a Temporal.

## 10.1. Végrehajtási sorrend

1. A felhasználó megnyitja az AI Video Tools alkalmazást.
2. Kiválasztja a használni kívánt generátort.
3. Megadja a generálási paramétereket.
4. A rendszer ellenőrzi a generátor rendelkezésre állását.
5. A helyi generátor a CFA3 Model Manageren keresztül igényli a modellt.
6. A Model Router meghatározza a megfelelő futtatási útvonalat.
7. A hardverbiztonsági szolgáltatások ellenőrzik a végrehajtási jogosultságokat.
8. Felhőgenerátor esetén az adatküldési és költségfeltételeket ellenőrizni kell.
9. A közös workflow-motor létrehozza és vezérli a generálási feladatot.
10. Az adapter elindítja a generálómotort.
11. A CFA3 GUI megjeleníti a támogatott állapot- és előrehaladási információkat.
12. A befejezett videó a közös médiakezelőbe kerül.
13. A felhasználó megtekintheti vagy továbbadhatja az eredményt.

## 10.2. Feladatállapotok

A generálási feladatok logikai állapotai:

- CREATED
- VALIDATING
- MODEL_PREPARATION
- WAITING_FOR_RESOURCES
- QUEUED
- RUNNING
- COMPLETED
- FAILED
- CANCELLED
- BLOCKED

Az állapotokat a közös workflow-infrastruktúra vezérli; az AI Video Tools GUI csak megjeleníti és a jogosult műveleteken keresztül kezeli őket.

## 10.3. Megszakítás és helyreállítás

A generátoradapternek jeleznie kell, hogy támogatja-e:

- a feladat megszakítását;
- az előrehaladás lekérdezését;
- az előnézetet;
- a folyamat újraindítását;
- a megszakadt feladat folytatását.

A CFA3 nem állíthat támogatást olyan funkcióhoz, amelyet a tényleges backend nem biztosít.

---

# 11. Közös CFA3 infrastruktúra

Az AI Video Tools a platform meglévő közös rétegeit használja.

| Shared komponens | Felelősség |
|---|---|
| Shared Plugin & Extension Fabric | Generátorok integrációja |
| CFA3 Model Manager | Teljes AI-modell-életciklus |
| Model Router | Modell- és futtatási útvonal kiválasztása |
| Temporal / közös workflow-réteg | Tartós generálási folyamatok |
| Shared Asset Management | Referenciaanyagok, videók és metaadatok |
| Shared Export/Import | Kimenetek és projektadatok átadása |
| Shared Security | Hozzáférések, jogosultságok, titkok |
| Host Resource Broker | Erőforrások engedélyezése és kiosztása |
| Hardware Policy | Hardveres biztonsági követelmények |
| CFA3 GUI Framework | Közös grafikus megjelenítés |
| Package Management | Kötelező és opcionális eszközök kezelése |

## 11.1. Felelősségi elkülönítés

A CFA3 Model Manager kezeli a modellállományokat.

A Model Router dönt a modell és a futtatási útvonal kiválasztásáról.

A Host Resource Broker kezeli a tényleges erőforrásjogosultságokat és erőforrásfoglalásokat.

A közös workflow-réteg kezeli a tartós folyamatokat.

Az AI Video Tools a generátorokhoz kapcsolódó alkalmazásspecifikus funkciókért felel.

## 11.2. Infrastrukturális duplikáció tilalma

Az AI Video Tools nem hozhat létre párhuzamosan olyan általános szolgáltatást, amelynek már létezik meghatározott CFA3-felelőse.

Az integrációk a megfelelő shared kontraktusokon keresztül történnek.

---

# 12. CFA3 hardverbiztonság

Az AI Video Tools minden AI-futtatása a CFA3 egységes hardvervédelmi szabályait követi.

## 12.1. CPU-only alapútvonal

A CFA3 CPU-only platformalapja kötelező.

Az AI Video Tools vezérlési, katalógus-, modelllekérési és alapvető felhasználói funkciói nem tehetik kötelezővé külön AI-gyorsító jelenlétét.

A GPU-t igénylő generálómotorok tényleges generálási képessége csak támogatott és engedélyezett hardveren működhet.

## 12.2. GPU-használat

- Az elérhető gyorsítókat a CFA3 közös infrastruktúrája kezeli.
- A kijelző GPU-ja alapértelmezés szerint nem használható AI-feladatokra.
- Kivétel kizárólag a korábban meghatározott szabályok szerint engedélyezhető.
- A hardverhasználat nem kerülheti meg a Model Router és az erőforrás-kezelő felelősségét.
- Nem történhet rejtett GPU- vagy felhőszolgáltató-váltás.

## 12.3. Fail-closed működés

Ha a kötelező erőforrás-, jogosultsági vagy hardverellenőrzés nem sikerül, a generálás nem indulhat el.

A hiányzó Current Host bizonyíték nem helyettesíthető szimulált eredménnyel.

A fizikai PASS kizárólag ténylegesen igazolt hardveres ellenőrzésből származhat.

---

# 13. Helyi futtatókörnyezetek izolálása

A FramePack, WanGP, LTX Desktop, VideoX-Fun és EasyAnimate eltérő futtatási és szoftverfüggőségekkel rendelkezhetnek.

A CFA3-nak meg kell akadályoznia, hogy az egyik generátor függőségeinek telepítése tönkretegye a másik generátor működését.

## 13.1. Kötelező követelmények

- Az egymással ütköző Python- és egyéb függőségeket izolálni kell.
- A függőségek nem módosíthatják ellenőrizetlenül a CFA3 közös futtatási környezetét.
- Az alkalmazásspecifikus futtatókörnyezetek a közös Model Managerhez kapcsolódnak.
- A modellweights fájlok nem duplikálódhatnak az izolált környezetekben.
- Egy generátor frissítése nem módosíthatja észrevétlenül másik generátor környezetét.

A futtatókörnyezetek izolálása nem jelenthet párhuzamos AI-modelltárolást.

---

# 14. Felhőszolgáltatások integrációja

A Runway és a Kling az alapcsomag kötelező felhőszolgáltató-adapterei.

## 14.1. Felhőadapterek feladata

- támogatott modell- és képességlista;
- API-kapcsolat kezelése;
- hitelesítési adatok felhasználása;
- generálási feladat indítása;
- távoli feladatállapot lekérdezése;
- eredmény elérése és átvétele;
- felhőszolgáltatói hibák kezelése;
- a generált videó CFA3 médiakezelésbe történő továbbítása.

## 14.2. Felhasználói kontroll

A felhőgenerálás nem járhat automatikus, előzetesen nem engedélyezett adatküldéssel vagy költséggel.

A CFA3-nak a megfelelő shared infrastruktúrán keresztül kell kezelnie:

- a hitelesítést;
- a szükséges felhasználói engedélyt;
- a lehetséges költséginformációkat;
- a szolgáltatói korlátozásokat;
- a feladatok státuszát.

A felhőszolgáltatás átmeneti elérhetetlensége nem eredményezhet automatikus helyi vagy másik felhőszolgáltatóra történő átállást, ha azt a CFA3 szabályai nem engedélyezik.

---

# 15. Médiakezelés és kreatív alkalmazások közötti átadás

A generált videók a CFA3 közös Asset Management rendszerébe kerülnek.

Az AI Video Tools nem alakít ki saját, a platform többi részétől elszigetelt végleges médiatárolót.

## 15.1. Kimenetek kezelése

A rendszernek biztosítania kell:

- az elkészült videók nyilvántartását;
- a generálási metaadatok megőrzését;
- a referenciaanyagokkal való kapcsolatok rögzítését;
- a támogatott videóformátumok kezelését;
- az eredmények továbbadását más CFA3-alkalmazásokhoz.

## 15.2. Kapcsolódó CFA3-alkalmazások

| Célalkalmazás | Kapcsolat |
|---|---|
| CFA3 Video Editor | Generált videók átvétele szerkesztéshez |
| VFX Studio | Generált videók felhasználása effektekhez és kompozitáláshoz |
| Animation Studio | Animált és generált szekvenciák felhasználása |
| Story / Screenplay Studio | Jelenet- és történetkoncepciók videós megjelenítése, ahol jóváhagyott kapcsolat létezik |
| Scene / Shot Designer | Generált vizuális referenciaanyagok átvétele |
| Production Studio | Produkciós assetek és kapcsolódó eredmények kezelése |

Ezek logikai integrációs célok, nem automatikusan létrejövő futásidejű függőségek.

Csak a ténylegesen szükséges, jóváhagyott CFA3 handoff-kapcsolatokat szabad megvalósítani.

---

# 16. Fejlődéskövetés és technológiai megőrzés

Az AI Video Tools egyik alapvető rendeltetése a gyors AI-videógeneráló technológiák fejlődésének követése.

Az alapcsomag és az opcionális csomagok nyilvántartása tartalmazhatja:

- az upstream projektet;
- a hivatalos forrásokat;
- az aktuálisan ellenőrzött verziót;
- a kiadások változásait;
- az új generálási képességeket;
- a modelltámogatás változásait;
- a futtatási követelmények változásait;
- a kompatibilitási problémákat;
- a licencfeltételeket;
- a projekt támogatási és karbantartási állapotát.

## 16.1. Fejlődéskövetési cél

A nyilvántartás alapján eldönthető legyen, hogy:

- a generátor továbbra is hasznos-e;
- új képességei megjeleníthetők-e a CFA3 GUI-jában;
- változott-e az adapter interfésze;
- szükséges-e integrációs frissítés;
- a generátor támogatása folytatódik-e.

A fejlődéskövetés nem jelenthet automatikus donor-felvételt vagy új fejlesztési feladatot.

## 16.2. Donor Registry határ

A generátorok alapcsomag-tagsága önmagában nem jelenti azok jóváhagyását donorként.

A CFA3 Donor & Reference Registry szabályai változatlanul érvényesek.

Donor-felvétel kizárólag a külön meghatározott jóváhagyási eljárással történhet.

---

# 17. Csomagfrissítés és életciklus-kezelés

A generátorok programcsomagjainak frissítése külön kezelendő az AI-modellfájlok frissítésétől.

A generátorcsomagokhoz tartozó műveletek a CFA3 közös csomagkezelő infrastruktúráján keresztül történnek.

A modellek frissítése kizárólag a CFA3 Model Manager felelőssége.

## 17.1. Csomagállapotok

- INSTALLED_READY
- INSTALLED_SETUP_REQUIRED
- INSTALLED_HARDWARE_BLOCKED
- INSTALL_BLOCKED
- INSTALL_FAILED
- UPDATE_AVAILABLE
- INCOMPATIBLE
- UPSTREAM_DISCONTINUED

## 17.2. Frissítési ellenőrzés

Az alkalmazásfrissítések során ellenőrizni kell:

1. az upstream csomag integritását;
2. a megváltozott függőségeket;
3. a CFA3-adapter kompatibilitását;
4. a GUI-ban megjelenített képességeket;
5. a Model Managerhez kapcsolódó követelményeket;
6. a hardverkövetelmények változásait.

Az egyik alkalmazás frissítése nem módosíthatja automatikusan másik alkalmazás működését.

---

# 18. Licenc- és terjesztési ellenőrzések

Az AI Video Tools hét kötelező alapeszköze terméktervezési döntés.

A tényleges integráció és terjesztés azonban csak a jogszerűen engedélyezett felhasználási módokkal történhet.

Minden eszköznél ellenőrizni kell:

- az alkalmazáskód licencét;
- a terjesztési jogosultságokat;
- a kereskedelmi beágyazás feltételeit;
- az upstream komponensek módosítási feltételeit;
- a headless vagy programozott használat megengedettségét;
- az esetleges attribúciós követelményeket;
- az AI-modellek külön licencfeltételeit;
- a felhőszolgáltatások használati feltételeit.

Egy licencakadály nem jogosítja fel a rendszert a kötelező eszköz észrevétlen kihagyására.

Az ilyen akadályt tényleges blockerként kell nyilvántartani.

---

# 19. Megvalósítási fázisok

## I. Exact-state ellenőrzés

A tényleges CFA3 repository, alkalmazáskatalógus és shared infrastruktúra állapotának hiteles ellenőrzése.

**Eredmény:** ellenőrzött műszaki kiinduló állapot.

## II. Upstream integrációs ellenőrzés

A hét generátor programozott vezérlési lehetőségeinek, futtatási követelményeinek és licenceinek vizsgálata.

**Eredmény:** eszközönként hiteles integrációs specifikáció.

## III. GUI- és adaptertervezés

A CFA3 natív GUI, a közös adapterkontraktusok és a szükséges shared kapcsolatok részletes kidolgozása.

**Eredmény:** implementációra alkalmas végrehajtási terv.

## IV. Alapcsomag megvalósítása

A hét kötelező generátor integrálása a CFA3 meglévő infrastruktúrájával.

**Eredmény:** telepíthető, integrált AI Video Tools.

## V. Integrációs és biztonsági ellenőrzések

A telepítés, modellkezelés, GUI, generálás, hardvervédelem és közös szolgáltatások célzott ellenőrzése.

**Eredmény:** igazolt követelményteljesítés.

A fázisok között a CFA3 jóváhagyási és Scope Guard szabályai érvényesek.

---

# 20. Kötelező elfogadási tesztek

## 20.1. Telepítés

- [ ] Mind a hét alapeszköz telepítése ellenőrzött.
- [ ] Nincs AI-modellweights a CFA3 telepítőjében.
- [ ] A telepítés nem indít AI-modellletöltést.
- [ ] A kötelező telepítés hibája nem jelenhet meg teljes sikernek.
- [ ] Opcionális generátor nem települ felhasználói döntés nélkül.

## 20.2. GUI

- [ ] Mind a hét generátor a CFA3 saját felületén használható.
- [ ] Generátorhasználathoz nem nyílik rendszerböngésző.
- [ ] Az eredeti upstream GUI nem szükséges a közös munkafolyamathoz.
- [ ] A paraméterek az adott backend tényleges képességei szerint jelennek meg.
- [ ] A generálás és a feladatállapot megjelenítése a CFA3-ban történik.
- [ ] A GUI az alkalmazandó Qt 6 követelményeket teljesíti.

## 20.3. Model Manager

- [ ] A helyi modellletöltéseket kizárólag a közös Model Manager végzi.
- [ ] Meglévő azonos modellállomány esetén nem indul új letöltés.
- [ ] Több alkalmazás azonos modellkérését egy központi letöltési folyamat szolgálja ki.
- [ ] Egyetlen kompatibilis közös modellpéldány több alkalmazás számára elérhető.
- [ ] Új modellverzió esetén működik a központi frissítés.
- [ ] Inkompatibilis frissítés nem semmisíti meg a korábbi használható változatot.
- [ ] Megszűnt modellnél a felhasználó választhat a megtartás és eltávolítás között.
- [ ] Modell törlése előtt minden érintett alkalmazásfüggőséget ellenőrizni kell.

## 20.4. Shared integráció

- [ ] Minden generátor a Shared Plugin & Extension Fabric segítségével kapcsolódik.
- [ ] A Model Router a futtatási útvonal döntési pontja.
- [ ] Az erőforrások a megfelelő központi jogosultsági szolgáltatáson keresztül érhetők el.
- [ ] A tartós workflow-feladatok a közös architektúrát használják.
- [ ] A generált videók a közös CFA3 médiakezelésbe kerülnek.
- [ ] Nem jön létre párhuzamos Model Manager, általános workflow-rendszer vagy médiatár.

## 20.5. Hardverbiztonság

- [ ] Működik a CPU-only vezérlési útvonal.
- [ ] A kijelző GPU-ja védett.
- [ ] A hardveres ellenőrzések a tényleges állapoton alapulnak.
- [ ] Hiányzó jogosultság vagy bizonyíték esetén a rendszer fail-closed működik.
- [ ] Nincs rejtett hardveres vagy felhőalapú végrehajtási útvonalváltás.

## 20.6. Csomagkezelés

- [ ] A kötelező és opcionális csomagok külön nyilvántartottak.
- [ ] Új opcionális csomag csak felhasználói művelettel telepíthető.
- [ ] A csomagfrissítések nem sértik más generátorok függőségeit.
- [ ] Az opcionális csomag eltávolítása nem töröl más alkalmazások számára szükséges AI-modelleket.

---

# 21. Scope Guard

A megvalósítás során kizárólag az AI Video Tools elfogadott céljaihoz közvetlenül szükséges munkák végezhetők el.

Nem indítható automatikusan:

- más CFA3-alkalmazás fejlesztése;
- általános architekturális refaktor;
- új shared infrastruktúra létrehozása;
- donor-intake;
- új, önálló PR vagy párhuzamos fejlesztési feladat;
- kapcsolódó, de nem szükséges tesztprogram;
- új szabályalkotási mellékfeladat.

Valódi blocker esetén csak a feloldásához közvetlenül szükséges művelet engedélyezett.

A végrehajtás az elfogadási feltételek teljesülése után megáll.

---

# 22. Beépítés a CFA3 teljes rendszertervébe

Az AI Video Tools nem különálló, a teljes CFA3-tervtől független elképzelés.

A CFA3 egységes rendszertervének az alábbi kapcsolódási pontokon kell tartalmaznia az elfogadott alkalmazást.

| CFA3 terület | Kötelező beépítendő elem |
|---|---|
| Teljes alkalmazáskatalógus | AI Video Tools mint önálló alkalmazás |
| AI-alkalmazások | Gyors AI-videógenerálás |
| Video / Creative réteg | Generált videók átadása a szerkesztési és produkciós rendszereknek |
| Telepítési architektúra | Hét kötelező alapeszköz |
| Csomagkezelés | Opcionális későbbi generátorok |
| GUI-rendszer | CFA3 natív, Qt 6 alapú felület |
| Shared Plugin & Extension Fabric | Helyi és felhőgenerátorok adapterei |
| CFA3 Model Manager | Közös modellek, deduplikáció, frissítések |
| Model Router | AI-modellek és futtatási útvonalak kiválasztása |
| Workflow-infrastruktúra | Tartós generálási feladatok |
| Shared Asset Management | Referenciák és generált videók |
| Shared Export/Import | Kreatív alkalmazások közötti átadás |
| Host Resource Broker | Erőforrások és futtatási jogosultságok |
| Security | Licenc, hozzáférés, hitelesítés és biztonság |
| Hardvervédelem | CPU-only alap, GPU-védelem, fail-closed |
| Fejlődéskövetés | Generátorok verzió- és képességváltozásainak követése |

A CFA3 teljes terve nem csupán az AI Video Tools nevét veszi át, hanem a jelen dokumentumban meghatározott követelményeket is.

A kapcsolódó shared komponensek meglévő felelőssége nem módosul pusztán az AI Video Tools felvétele miatt.

---

# 23. Végleges döntés

Az AI Video Tools a CFA3 elfogadott alkalmazásainak egyike.

A hét kötelező alapcsomag:

1. FramePack
2. WanGP
3. LTX Desktop
4. VideoX-Fun
5. EasyAnimate
6. Runway API
7. Kling AI API

Az alkalmazás a CFA3 saját natív GUI-ján keresztül használható.

A telepítő AI-modellfájlokat nem tartalmaz.

A modellállományok teljes életciklusa a közös CFA3 Model Manager felelőssége.

Azonos, kompatibilis modellállományt tilos ismételten letölteni.

Új verzió megjelenésekor központi, kompatibilitást megőrző frissítés szükséges.

A megszűnt támogatású vagy forrású modellek meglévő példányának további sorsáról a felhasználó dönt.

A helyi és felhőalapú generálórendszerek a Shared Plugin & Extension Fabric infrastruktúrán keresztül kapcsolódnak a CFA3-hoz.

A Model Router, a közös workflow-réteg, a médiakezelés, a biztonsági és hardvervédelmi rendszerek változatlan platformszintű felelősségekkel működnek.

A később felvett AI-videógenerátorok alapértelmezés szerint opcionális csomagok.

**Az AI Video Tools teljes elfogadott terve a CFA3 egységes rendszertervéhez tartozik, és annak további tervezésében kötelezően figyelembe veendő alkalmazásspecifikáció.**

**Dokumentum vége — CFA3 AI Video Tools v2.0 FINAL**