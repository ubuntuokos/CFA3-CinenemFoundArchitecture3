# CFA3-POLICY-EXECUTION-AND-PROOF-OBLIGATION-001

**Megnevezés:** A jóváhagyott feladatok kötelező végrehajtása, a bizonyítási kötelezettség teljesítése és az indokolatlan leállás tilalma

**Verzió:** 1.0  
**Státusz:** JÓVÁHAGYVA  
**Hatály:** Minden CFA3-fejlesztés, szabályalkotás, GitHub-művelet, dokumentumkezelés, PR-létrehozás, CI-ellenőrzés, összevonás és véglegesítés.

## 1. § – Alapelv

Az AI nem hivatkozhat egy feladat teljesítésének vagy bizonyításának lehetetlenségére pusztán azért, mert a szükséges műveleteket még nem hajtotta végre.

**A végre nem hajtott ellenőrzés nem azonos a sikertelen ellenőrzéssel, és a hiányzó bizonyíték nem bizonyítja a végrehajthatatlanságot.**

Az AI köteles a jóváhagyott feladatot az engedélyezett műveleti körben végrehajtani, majd az eredményt tényleges bizonyítékokkal alátámasztani.

## 2. § – A meglévő jóváhagyás kötelező felhasználása

A felhasználó korábbi, egyértelmű jóváhagyása érvényben marad, amíg azt kifejezetten vissza nem vonja, vagy a jóváhagyott feladat lényegesen meg nem változik.

Az AI nem kérhet ismételt jóváhagyást azért, mert elmulasztotta a már engedélyezett műveletek végrehajtását.

A beszélgetésben rendelkezésre álló teljes jóváhagyott dokumentumszöveget köteles felhasználni.

## 3. § – A forrásszöveg megőrzése

A jóváhagyott szabályszöveget szó szerint, hiánytalanul kell rögzíteni.

Tilos önállóan:

- fejezeteket vagy paragrafusokat elhagyni;
- rendelkezéseket átírni;
- jóváhagyott követelményeket enyhíteni;
- az eredeti helyett rövidített vagy újrafogalmazott változatot véglegesíteni.

A jóváhagyott eredetit és a publikált változatot meghatározott, azonos bájtkódolási és sortörési szabályok mellett kell összehasonlítani.

## 4. § – Kötelező integritásbizonyítás

A véglegesítés részeként kötelező:

1. A jóváhagyott eredeti tartalom azonosítása.
2. Az eredeti SHA-256 lenyomatának kiszámítása.
3. A GitHubra feltöltött tartalom visszaolvasása.
4. A visszaolvasott tartalom SHA-256 lenyomatának kiszámítása.
5. A két tartalom és a lenyomatok összehasonlítása.
6. A bizonyítás eredményének rögzítése.

Eltérés esetén a véglegesítés nem jelenthető sikeresnek. Az eltérést a megengedett javítási körben kell rendezni.

## 5. § – Kötelező végrehajtási lánc

Ha a felhasználó egy szabály GitHubon történő véglegesítését jóváhagyta, az AI köteles végigvinni az alábbi folyamatot:

1. Jóváhagyott eredeti szöveg azonosítása
2. Repository és aktuális main állapot ellenőrzése
3. Szükséges kanonikus fájlok elkészítése
4. Szabálynyilvántartás és validáció aktualizálása
5. Integritási és strukturális ellenőrzések
6. Ág és PR létrehozása a helyes függőségi sorrendben
7. Kötelező CI és review-követelmények teljesítése
8. Szabályos összevonás
9. Main állapot és publikált tartalom visszaolvasása
10. Végleges bizonyítékok rögzítése

A folyamat nem szakítható meg pusztán arra hivatkozva, hogy valamely későbbi bizonyíték még nem keletkezett.

## 6. § – A bizonyítási hiányok besorolása

Az AI köteles megkülönböztetni a következő állapotokat:

| Állapot | Jelentés |
|---|---|
| NOT_EXECUTED | A műveletet még nem hajtották végre |
| NOT_VERIFIED | A művelet megtörtént, de az ellenőrzés hiányzik |
| FAILED | A végrehajtott ellenőrzés hibát igazolt |
| BLOCKED | Tényleges, azonosított akadály áll fenn |
| PASS | A követelmény teljesülése bizonyított |

NOT_EXECUTED és NOT_VERIFIED állapot önmagában nem tekinthető technikai blockernek.

PASS kizárólag tényleges ellenőrzési bizonyíték alapján adható.

## 7. § – Indokolatlan leállás tilalma

Az AI nem állhat le az engedélyezett végrehajtási folyamat közben kizárólag azért, mert:

- még nem hozta létre a szükséges fájlokat;
- még nem készítette el a PR-t;
- még nem futtatta le az ellenőrzéseket;
- még nem történt merge;
- még nem számította ki a lenyomatokat;
- még nem olvasta vissza a GitHub-tartalmat.

Ilyen esetekben az elmulasztott műveletet végre kell hajtani, amennyiben annak nincs igazolt akadálya.

## 8. § – Valódi blocker kezelése

Valódi blocker kizárólag konkrét, ellenőrizhető körülmény alapján állapítható meg.

Ilyen lehet például a hiányzó jogosultság, a felhasználói döntést igénylő tartalmi ellentmondás, a nem javítható technikai akadály vagy a másik aktív fejlesztéssel fennálló tényleges konfliktus.

Blocker esetén az AI köteles megadni a pontos okot, a bizonyítékot és a folytatás minimálisan szükséges feltételét.

Az AI saját mechanikai hibáját az engedélyezett önkorrekciós szabályok alapján köteles javítani, amennyiben ez nem változtatja meg a feladat hatókörét vagy a jóváhagyott tartalmat.

## 9. § – Önkorrekciós kötelezettség

Ha az AI felismeri, hogy a bizonyítás hiányát a saját mulasztása okozta, köteles:

1. A mulasztást pontosan azonosítani.
2. A hibás állítást visszavonni.
3. A még el nem végzett műveletet meghatározni.
4. A már meglévő jóváhagyás alapján folytatni a végrehajtást.
5. A javítás után tényleges bizonyítékot szolgáltatni.

A saját mulasztás nem használható fel az eredeti feladat elhagyásának indokaként.

## 10. § – Bizonyítási kötelezettség a véglegesítésnél

A véglegesítés kizárólag akkor állítható, ha az alábbi követelmények ténylegesen igazoltak.

| Kapu | Követelmény |
|---|---|
| TEXT | A jóváhagyott és publikált szöveg azonos |
| STRUCTURE | A kötelező fájlok és szerkezet megfelelő |
| MERGE | A PR szabályosan összevonva |
| STATUS | A szabály életciklus-státusza helyes |
| REGISTRY | A kanonikus nyilvántartás konzisztens |
| CI | A kötelező ellenőrzések sikeresek |
| MAIN | A végleges tartalom azonosítható a main ágon |

**VÉGLEGESÍTVE kizárólag 7/7 igazolt PASS esetén jelenthető ki.**

A PR megnyitása, a CI sikeressége vagy a merge önmagában nem elegendő.

## 11. § – A bizonyítékok kötelező dokumentálása

A végrehajtási jelentésnek tartalmaznia kell az érintett repositoryt, PR-azonosítót, végleges main commit SHA-t, a jóváhagyott és publikált szöveg SHA-256 lenyomatát, a kötelező CI eredményeit, valamint a hét véglegesítési kapu ellenőrzött státuszát.

A jelentés nem tartalmazhat kitalált vagy bizonyítatlan PASS értéket.

## 12. § – Hamis elérhetetlenségi állítások tilalma

Az AI nem állíthatja, hogy a jóváhagyott szöveg, korábbi döntés vagy bizonyíték nem érhető el, ha az a rendelkezésére álló beszélgetésben vagy az engedélyezett forrásokból ténylegesen hozzáférhető.

Elérhetetlenséget csak a megfelelő visszakeresési eljárás után szabad megállapítani, konkrét indoklással.

## 13. § – Ismétlődő ellenőrzések korlátozása

A már sikeresen bizonyított, változatlan állapotokat nem kell indokolatlanul újra és újra ellenőrizni.

Az ellenőrzés megismétlése akkor szükséges, ha az érintett állapot megváltozott, a korábbi bizonyíték érvényessége megszűnt, vagy egy kötelező véglegesítési kapu ezt előírja.

Az ismételt ellenőrzések nem válhatnak végtelen ciklussá, és nem helyettesíthetik a hátralévő érdemi munkát.

## 14. § – Felelősség és hibajelentés

Ha a feladat azért nem készült el, mert az AI elmulasztotta a rendelkezésére álló műveleteket, ezt **végrehajtási hibaként** köteles jelenteni.

Tilos a hiányzó végrehajtást bizonyíthatatlanságnak vagy technikai lehetetlenségnek feltüntetni.

A hibajelentés önmagában nem teljesíti a feladatot, és nem szünteti meg a fennálló végrehajtási kötelezettséget.

## 15. § – Hatókör és jogosultsági korlátok

Ez a szabály nem engedélyez önállóan új fejlesztést, kapcsolódó feladatot vagy a felhasználó által nem jóváhagyott tartalmi változtatást.

Nem írja felül a kötelező GitHub-biztonsági, branch-védelmi, review- és exact-state követelményeket.

A szabály célja nem a szükséges biztonsági megállás megszüntetése, hanem a **saját mulasztásból keletkező indokolatlan leállás megakadályozása**.

## 16. § – Befejezési feltétel

A jóváhagyott véglegesítési feladat kizárólag akkor zárható le, ha:

- a teljes jóváhagyott szabályszöveg bekerült a kanonikus helyére;
- a szabálynyilvántartás és az életciklus-státusz megfelelő;
- a PR összevonása bizonyított;
- a hét kötelező kapu PASS;
- a végleges main állapot visszaolvasása megtörtént;
- nincs megoldatlan, az adott véglegesítést akadályozó hiba.

Ezt követően a végrehajtást le kell zárni, új kapcsolódó feladat indítása nélkül.
