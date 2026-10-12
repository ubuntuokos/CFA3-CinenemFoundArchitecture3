# CFA3-POLICY-EXACT-FINALIZATION-001

**Megnevezés:** Szabályok szó szerinti azonosságának, életciklus-státuszának és bizonyított véglegesítésének kötelező ellenőrzése

**Állapot:** JAVASLAT – JÓVÁHAGYÁSRA VÁR

**Hatály:** Minden CFA3-szabály, szabálymódosítás, szabálynyilvántartás és kapcsolódó véglegesítési folyamat.

## 1. Alapelv

CFA3-szabály kizárólag akkor nyilvánítható véglegesítettnek, ha a felhasználó által jóváhagyott teljes szabályszöveg változatlanul bekerült a kanonikus GitHub-tárolóba, a kapcsolódó nyilvántartások helyesek, és az eredmény a tényleges főágállapotból ellenőrizhető.

A sikeres CI, a jóváhagyott PR vagy a PR összevonása önmagában nem bizonyítja a teljes véglegesítést.

## 2. A jóváhagyott szabályszöveg sérthetetlensége

A felhasználó által jóváhagyott szabályszöveg kötelezően megőrzendő.

Tilos önálló jóváhagyás nélkül:

- A szabály rövidítése vagy összefoglalása.
- Fejezetek, bekezdések vagy mondatok elhagyása.
- A rendelkezések átértelmezése, átfogalmazása vagy összevonása.
- A követelmények gyengítése vagy kiegészítése.
- A szabály teljes szövegének kiváltása egy tartalmi kivonattal.

Amennyiben a felhasználó 20 fejezetet hagyott jóvá, mind a 20 fejezetet teljes terjedelemben, az elfogadott sorrendben és tartalommal kell megőrizni.

A jóváhagyott szöveg módosításához új, kifejezett jóváhagyás szükséges.

## 3. Kötelező tartalmi azonossági ellenőrzés

A szabály GitHubra történő felvétele előtt ellenőrizni kell:

1. A jóváhagyott eredeti szöveg rendelkezésre állását.
2. A fejezetek, bekezdések és mellékletek teljességét.
3. A feltöltendő szabályszöveg és a jóváhagyott változat szó szerinti azonosságát.
4. A szabályazonosító és a verzió helyességét.
5. A kapcsolódó JSON- és registry-bejegyzések konzisztenciáját.

Az azonosságot determinisztikus ellenőrzéssel kell bizonyítani, lehetőség szerint azonos karakterkódolású, kanonikus szövegek bájtszintű összehasonlításával és SHA-256 lenyomattal.

Az ellenőrzés nem alapulhat kizárólag AI által készített szöveges összefoglalón.

## 4. Státusz és tényleges életciklus egyezősége

A szabály státuszának minden esetben a ténylegesen bizonyított életciklusállapotot kell tükröznie.

Például a `OWNER_APPROVED_PENDING_PR_REVIEW_AND_MERGE` státusz nem maradhat a végleges kanonikus állapotban, ha a PR már összevonásra került, és az adott életciklus-séma szerint a státuszfrissítés esedékes.

Az összevonás azonban nem jogosít automatikusan végleges státusz beállítására, ha a tartalmi vagy nyilvántartási ellenőrzés hiányos.

A státuszok megállapításakor kizárólag a tényleges GitHub-állapot, a jóváhagyási bizonyítékok és a kanonikus státuszséma használható.

## 5. Kötelező nyilvántartási konzisztencia

Új szabály vagy szabálymódosítás esetén a `CFA3-CURRENT-POLICY-SURFACE-001.json` és minden közvetlenül érintett kanonikus nyilvántartás megfelelő bejegyzését ellenőrizni kell.

Követelmény:

- A szabályazonosítók egyezzenek.
- A verziók és hivatkozások helyesek legyenek.
- A szabály státusza ne mondjon ellent a bizonyított GitHub-állapotnak.
- A nyilvántartások ne hivatkozzanak hiányos szabályváltozatra.
- Az alkalmazott ellenőrzések ne tartalmazzanak a valóságtól eltérő, fixen beírt elvárt állapotokat.

## 6. Kötelező összevonás utáni ellenőrzés

A PR sikeres összevonását követően a fejlesztő köteles a tényleges főágállapotból ellenőrizni:

1. A szabály teljes szövegének jelenlétét és szó szerinti azonosságát.
2. A végleges fájlok és nyilvántartások meglétét.
3. A szabály aktuális életciklus-státuszát.
4. A szabályazonosítók, verziók és hivatkozások konzisztenciáját.
5. Az előírt ellenőrzőkapuk eredményeit.
6. A vizsgált főág-commit pontos SHA-azonosítóját.

A korábban megvizsgált PR-ág állapota nem helyettesítheti az összevonás utáni főágállapot vizsgálatát.

## 7. A véglegesítés kötelező feltételei

A szabály akkor és csak akkor tekinthető teljesen véglegesítettnek, ha az alábbi feltételek mind teljesülnek:

- **TEXT PASS:** a teljes szabályszöveg azonos a jóváhagyott változattal.
- **STRUCTURE PASS:** minden jóváhagyott fejezet és melléklet hiánytalan.
- **MERGE PASS:** a megfelelő változat ténylegesen bekerült a főágba.
- **STATUS PASS:** a nyilvántartott státusz megfelel a valós életciklusnak.
- **REGISTRY PASS:** a kapcsolódó nyilvántartások konzisztensek.
- **CI PASS:** minden kötelező ellenőrzőkapu sikeres.
- **MAIN PASS:** az eredmény a kanonikus főág konkrét commitjából bizonyított.

Egyetlen hiányzó vagy sikertelen feltétel esetén sem adható teljes véglegesítési PASS.

## 8. Téves véglegesítési kijelentések tilalma

Az AI és a fejlesztő nem jelentheti ki, hogy egy szabály teljesen véglegesített, amíg az előző fejezet valamennyi feltétele bizonyítottan nem teljesült.

Kifejezetten tilos a véglegesítést kizárólag az alábbiakkal igazolni:

- Sikeres CI.
- PR összevonása.
- Sikeres GitHub API-válasz.
- Korábbi AI-visszaigazolás.
- Hiányos fájl- vagy státuszellenőrzés.

Ha csak a PR összevonása bizonyított, kizárólag ez az eredmény jelenthető ki.

## 9. Eltérések és hibák kezelése

Bármely tartalmi, státuszbeli vagy nyilvántartási eltérés észlelésekor:

1. Az eltérést pontosan azonosítani kell.
2. A teljes véglegesítési kijelentést meg kell tagadni, illetve a korábban tévesen kiadott kijelentést helyesbíteni kell.
3. Meg kell állapítani, hogy a hiányosságot az AI asszisztens, az AI fejlesztő vagy igazolt külső körülmény okozta-e.
4. A saját, engedélyezett körben javítható mechanikai hibát a CFA3 önkorrekciós szabályai szerint kell kezelni.
5. Új PR-t, jogosultságváltoztatást vagy külön jóváhagyást igénylő módosítást nem szabad önállóan indítani.
6. A javítás után az összes érintett véglegesítési feltételt ismét ellenőrizni kell.

A hiányosság eltitkolása vagy sikeresként feltüntetése tilos.

## 10. A szabály életciklusának lezárása

A szabály véglegesítésének lezárásakor kötelező bizonyítékokat rögzíteni:

- Szabályazonosító és verzió.
- A jóváhagyott szöveg azonosságának eredménye.
- A kanonikus GitHub-commit SHA-ja.
- A vonatkozó PR azonosítója.
- Az aktuális, ellenőrzött státusz.
- A kötelező ellenőrzőkapuk eredményei.
- Az ellenőrzés időpontja.

A bizonyítékok hiányában a véglegesítés nem igazolt.

## 11. Visszamenőleges alkalmazás

Ha korábban véglegesítettnek nevezett CFA3-szabálynál később tartalmi hiányosság vagy hibás státusz derül ki, a szabály véglegesítettségét újra kell értékelni.

A történeti GitHub- és jóváhagyási bizonyítékok nem írhatók felül és nem hamisíthatók meg.

A javítás nem változtathatja meg önállóan a felhasználó által eredetileg jóváhagyott szabályt.

Ez a rendelkezés nem engedélyez önálló, általános visszamenőleges auditot vagy más szabályokra kiterjedő fejlesztést.

## 12. Elsőbbségi és hatásköri korlátozás

A jelen szabály a tartalmi azonosság és a véglegesítés igazolásának kötelező követelményeit határozza meg.

Nem írja felül a CFA3 meglévő jóváhagyási, GitHub-módosítási, biztonsági, Scope Guard és blockerkezelési előírásait.

A jelen szabály nem használható fel más feladat automatikus indítására, további PR létrehozására vagy a kijelölt feladatkör bővítésére.

## 13. Kötelező záró rendelkezés

**A CFA3-ban a jóváhagyott szabályszöveg teljes és változatlan kanonikus jelenléte, a helyes életciklus-státusz, valamint az összevonás utáni tényleges főágellenőrzés együttesen szükséges a véglegesítés kimondásához.**

A GitHub által elfogadott változtatás nem tekinthető automatikusan a felhasználó által jóváhagyott tartalom teljesítésének.

**Véglegesítési alapelv: APPROVED TEXT = CANONICAL TEXT + VERIFIED LIFECYCLE + VERIFIED MAIN STATE.**

Mindhárom összetevő bizonyítása kötelező.