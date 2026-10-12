# CFA3-POLICY-MANDATORY-RULE-CREATION-INTEGRITY-001

**Megnevezés:** Megkerülhetetlen szabályalkotási feladatok végrehajtási integritása és kötelező, bizonyított lezárása

**Verzió:** 1.0  
**Státusz:** JÓVÁHAGYVA  
**Hatály:** Minden CFA3-szabályalkotási, szabálymódosítási, szabálybevezetési és szabályvéglegesítési feladat.

## 1. § Alapelv

Amennyiben a felhasználó egy megkerülhetetlen, kötelező vagy kiemelt érvényű szabály elkészítését rendeli el, az AI elsődleges kötelezettsége az adott szabály teljes, pontos és ellenőrizhető elkészítése.

A feladat nem helyettesíthető más szabállyal, kapcsolódó fejlesztéssel, általános elemzéssel vagy technikai mellékfeladattal.

A szabály megkerülhetetlen jellege nem ad felhatalmazást magasabb szintű biztonsági, jogi vagy hozzáférési korlátozások megsértésére.

## 2. § Kötelező feladatrögzítés

A végrehajtás megkezdése előtt egyértelműen rögzíteni kell:

1. A fő feladatot.
2. A pontosan elvárt eredményt.
3. Az engedélyezett műveleti kört.
4. A tiltott és kizárt műveleteket.
5. A kötelező előfeltételeket.
6. A véglegesítés bizonyítási feltételeit.
7. A feladat befejezési feltételét.

A feladat meghatározása a végrehajtás során nem változtatható meg a felhasználó engedélye nélkül.

## 3. § Feladatelterelés tilalma

Az AI nem térhet át másik szabályra, donoradatbázisra, alkalmazásra, PR-re vagy fejlesztési munkára pusztán azért, mert annak elvégzését hasznosnak tartja.

Újonnan észlelt probléma nem válhat automatikusan önálló feladattá.

Az eredeti feladatot mindaddig fenn kell tartani, amíg azt megfelelően nem teljesítették, a felhasználó nem módosította, vagy tényleges akadály nem teszi lehetetlenné.

## 4. § Adat- és nyilvántartási elkülönítés

A szabálynyilvántartás és a Donor & Reference Registry egymástól elkülönített adatkezelési tartomány.

Szabályalkotási feladat során tilos:

- Donorrekordokat a szabálynyilvántartásba áthelyezni.
- Donoradatbázist önállóan módosítani.
- Donorfeldolgozási feladatot kezdeményezni.
- Más nyilvántartás adatait szabályadatként feltüntetni.
- A szabályalkotási feladatot donoradatbázis-rendezéssé alakítani.

Amennyiben a szabály tartalma donorfeldolgozási előírást érint, az kizárólag normatív rendelkezésként szerepelhet a szabályban, nem donorrekordként.

## 5. § Hiánytalan szabályalkotás

A szabálytervezetnek az összes felhasználó által megadott követelményt tartalmaznia kell.

Az AI nem hagyhat el rendelkezést egyszerűsítés, rövidítés vagy saját értelmezése miatt.

A szabály szövegének egyértelműnek, végrehajthatónak, ellenőrizhetőnek és ellentmondásmentesnek kell lennie.

A felhasználó által kifejezetten meghatározott kötelezettségek nem alakíthatók át puszta ajánlásokká.

## 6. § Jóváhagyási integritás

Az elkészített szabályt jóváhagyásra kell bemutatni.

A felhasználó jóváhagyása után:

1. A jóváhagyott szöveg kötelező érvényű végrehajtási alap.
2. A szöveg önkényes megváltoztatása tilos.
3. A jóváhagyás nem helyettesíti a tényleges GitHub-bevezetést.
4. A bevezetés kizárólag az engedélyezett műveleti körben történhet.
5. Minden tartalmi változtatáshoz új jóváhagyás szükséges.

## 7. § Szó szerinti azonosság

A jóváhagyott szabály kanonikus változatának teljes egészében egyeznie kell a felhasználó által jóváhagyott szöveggel.

Kötelező ellenőrzési elemek:

- Szövegazonosság.
- Fejezetek és rendelkezések teljessége.
- Verzióazonosság.
- Életciklus-státusz helyessége.
- Nyilvántartási hivatkozások konzisztenciája.

A szövegazonosság igazolására determinisztikus összehasonlítás és szükség esetén SHA-256 ellenőrzőösszeg alkalmazandó.

## 8. § Végrehajtási felelősség

Az AI köteles a jóváhagyott és engedélyezett műveleteket a feladat tényleges befejezéséig végrehajtani.

Saját mechanikai hibáját az engedélyezett körön belül köteles kijavítani, amennyiben a javítás nem módosítja a szabály tartalmát vagy a felhasználó döntését.

Az önálló hibajavítás nem jogosít fel más feladat elvégzésére.

## 9. § Scope Guard

Minden művelet előtt ellenőrizni kell:

**Közvetlenül szükséges-e ez a művelet az aktuálisan jóváhagyott szabályalkotási feladat teljesítéséhez?**

Ha nem, a művelet tilos.

Valódi technikai akadály esetén kizárólag az akadály feloldásához szükséges minimális művelet végezhető el, a meglévő biztonsági és jóváhagyási korlátok megtartásával.

Az akadály megszüntetése után az eredeti feladathoz kell visszatérni.

## 10. § Az ellenőrzési ciklusok korlátozása

Az AI nem kerülhet ismétlődő, eredménytelen ellenőrzési vagy javítási ciklusba.

Az azonos bemeneti állapoton megismételt, változatlan ellenőrzés nem számíthat új bizonyítéknak.

Ellenőrzést indokolt esetben kell megismételni, például tényleges állapotváltozás vagy javítás után.

Ismétlődő hiba esetén az okot kell feltárni, nem ugyanazt a sikertelen műveletet korlátlanul ismételni.

A végtelen ciklus veszélyét kötelező jelezni.

## 11. § GitHub-bevezetés

Ha a felhasználó a szabály GitHub-bevezetését is engedélyezte, az AI köteles:

1. Ellenőrizni a tényleges repository-állapotot.
2. Azonosítani a megfelelő kanonikus szabályfájlokat.
3. Kizárólag az engedélyezett fájlokat módosítani.
4. Megőrizni a jóváhagyott teljes szabályszöveget.
5. Helyesen beállítani a szabály életciklus-státuszát.
6. Ellenőrizni a szükséges CI-eredményeket.
7. Igazolni a PR tényleges összevonását, amennyiben az engedélyezett végrehajtás része.
8. Az összevonás után ellenőrizni a konkrét main commitot.

Más alkalmazás vagy nyilvántartás módosítása nem megengedett, kivéve a szabály bevezetéséhez közvetlenül kötelező és engedélyezett kapcsolódó módosításokat.

## 12. § Bizonyítási kötelezettség

A véglegesítés nem állítható pusztán az AI beszámolója alapján.

Kötelező bizonyítási feltételek:

| Kapu | Követelmény |
|---|---|
| TEXT | A jóváhagyott szöveg hiánytalan és azonos |
| STRUCTURE | A szabály szerkezete megfelelő |
| REGISTRY | A szabálynyilvántartás konzisztens |
| STATUS | Az életciklus-státusz megfelelő |
| CI | A kötelező ellenőrzések sikeresek |
| MERGE | A szükséges összevonás bizonyított |
| MAIN | A végleges főági tartalom ellenőrzött |
| SCOPE | Nem történt jogosulatlan feladatbővítés |

Az adott feladatra nem alkalmazható kaput **NOT_APPLICABLE** jelöléssel és indoklással kell dokumentálni.

A véglegesítés kizárólag minden alkalmazandó kapu PASS eredménye esetén jelenthető ki.

## 13. § Hamis lezárás tilalma

Tilos a „kész”, „véglegesítve”, „teljesítve” vagy „ellenőrizve” kifejezést olyan állapotra használni, amelynek feltételei nem teljesültek.

Külön kell kezelni:

- Elkészült szabálytervezet.
- Felhasználó által jóváhagyott szabály.
- GitHubba bevezetett szabály.
- Bizonyítottan véglegesített szabály.
- Tartós működésében külön igazolt szabály.

Ezek az állapotok nem tekinthetők egymással egyenértékűnek.

## 14. § Blokkolások kezelése

Az AI csak ténylegesen igazolt akadályt minősíthet blockernek.

Saját szintaktikai hibája, hibás eszközparamétere vagy javítható mechanikai tévedése önmagában nem elegendő a teljes feladat lezárásához vagy elhagyásához.

Jogosultsági, biztonsági, GitHub-állapotbeli vagy más, külön engedélyt igénylő akadály esetén a megengedett műveleti körnél meg kell állni, és pontosan jelenteni kell az akadályt.

Tilos akadályt mesterségesen létrehozni vagy megkerülni.

## 15. § Feladatbefejezési feltétel

A szabályalkotási feladat akkor zárható le, amikor:

1. Az eredetileg kért eredmény hiánytalanul elkészült.
2. A szükséges felhasználói jóváhagyás megtörtént.
3. Az engedélyezett bevezetési műveletek megtörténtek.
4. Minden alkalmazandó ellenőrzés sikeres.
5. Nincs ismert, megoldatlan blocker.
6. A végleges eredmény ellenőrizhető.
7. Más, nem engedélyezett feladat nem történt.

Ha a megbízás kizárólag szabálytervezet készítésére vonatkozott, annak hiánytalan átadása az adott feladat befejezése; a GitHub-bevezetés nem következik belőle automatikusan.

A befejezés után az AI köteles megállni.

## 16. § Kötelező alkalmazás és eltérések

A szabály minden CFA3-szabályalkotási feladatra alkalmazandó.

A szabály nem használható más elfogadott szabály megkerülésére, adatnyilvántartások összekeverésére vagy a felhasználói rendelkezések önkényes átértelmezésére.

Ha két szabály között tényleges ellentmondás áll fenn, azt konkrét rendelkezések alapján kell azonosítani és feloldásra előterjeszteni.

Az AI nem dönthet önállóan a felhasználó által jóváhagyott rendelkezések tartalmi felülírásáról.

**Záró rendelkezés:** A megkerülhetetlen szabályalkotási feladat kizárólag a felhasználó által meghatározott eredmény előállításával és annak megfelelő, ellenőrizhető lezárásával teljesíthető. Más tevékenység nem helyettesítheti a fő feladatot.
