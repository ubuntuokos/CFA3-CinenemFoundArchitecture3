# CFA3 Execution Guard – tulajdonos által jóváhagyott aktív szabályok

## Kötelező szabályjegyzék (2026-10-11)

Az eredeti **24 DEV/AI-szabály változatlan azonosítóval és kóddal** megmaradt. A tulajdonos ellenőrzés után újra beküldött **78** korábbi szabályának mindegyike az aktív Execution Guard hatáskörébe tartozik. A 22 történeti DEV/AI-szabály az eredeti 24 megfelelő azonosítójába van beolvasztva; ezeknek nincs új, versengő sorszáma. A **29 minőségi** (`Q-...`) és **27 feladatvezérlési** szabály saját történeti azonosítóval, egyenként szerepel az aktív készletben. A történeti 80 aktív azonosító mellé a tulajdonos a `RULE-ADMISSION-001` és a `CFA3-SEQUENTIAL-COMMAND-001` szabályokat adta. **Összesen 82 külön aktív azonosító, az eredeti 78/78 történeti beküldés változatlan elszámolásával.** Jelenleg nem azonosítottunk a 24 eredeti szabállyal összeegyeztethetetlen új rendelkezést; a konfliktus miatt kizártak száma 0.

Kanonikus aktuális szövegek: `canonical/registries/CFA3-EXECUTION-GUARD-OWNER-RULE-SPEC-001.json`. Forrás- és egyeztetési hivatkozások: `docs/governance/exports/CFA3-EXECUTION-GUARD-RULES-AND-CANDIDATES-20261011.json` és `canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json`. A teljes 3159 történeti fájl külön felülvizsgálata nem előfeltétele a tulajdonos által már kifejezetten jóváhagyott 78 szabály érvényének.

## Ütközések és pontosítások

Az aktuális 24 szabály elsőbbséget élvez valódi szemantikai ellentmondás esetén; a 22 közös azonosítójú történeti szabály kiegészítő tartalma megőrzendő. A donor- és SDK-PR-ek puszta párhuzamos jelenléte nem blokkol, tényleges fájl-, kapu- vagy kizárólagos erőforrásütközés viszont igen. Az azonos akadály legfeljebb három próbálkozására vonatkozó történeti korlát **nem** ad automatikus újrapróbálkozási jogosultságot: a STOP és a kifejezett tulajdonosi engedély elsőbbséget élvez. A tulajdonos `Folytasd`, `Jóváhagyom`, `Készítsd el` parancsa kizárólag az azonos főfeladatra terjed ki. A második egymást követő saját AI-hiba javításához kifejezett jóváhagyás szükséges.

## Ellenőrzések és valódi események

A bootstrap nem igényli váratlan AI-ügynöki hibák, eltérő main, ütköző PR vagy jogosultságsértés éles környezetben történő előidézését. A tesztek kontrollált pozitív és negatív helyzetekkel vizsgálják a szabályazonosítókat, forrásokat, ütközésfelismerést és elutasítási mechanizmusokat. A 82 aktív szabályhoz tartozó strukturális ellenőrzés és a feltételes, feladatonkénti biztonsági kapu különválik.

A referenciaimplementáció önmagában nem avatkozik be minden natív ChatGPT-eszközhívásba. A műveletek éles végrehajtásához továbbra is hiteles tulajdonosi engedély, pontos friss állapot, védett bizonyítékszolgáltató, elkülönített kulcsok és tartós naplózás szükséges. A **82 szabály aktiválása nem hamis futásidejű PASS**; amíg a külön megbízható végrehajtási szolgáltatások nincsenek igazolva, a tényleges kapu fail-closed marad.

## Elhatárolás

**Történeti feladathatár:** az eredeti szabály-visszaállítási feladat kizárólag a korábbi 78 szabály jóváhagyott reintegrálása volt, a 24 eredeti DEV/AI-szabály megőrzésével. A később, külön tulajdonosi utasítás alapján jóváhagyott `RULE-ADMISSION-001` és `CFA3-SEQUENTIAL-COMMAND-001` bevezetése ettől elkülönülő szabályfelvételi döntés; a közös nyilvántartásban mindkettő saját azonosítóval és forrással szerepel. A donor-PR, SDK-PR, más alkalmazás, történeti 3159-fájlos feldolgozás és fizikai Current Host nem része a feladatnak. A `main` védelme és a kötelező `bootstrap` / `qt68-linux` check változatlan.

## Új szabály felvétele és Bootstrap-elszámoltathatóság

A `RULE-ADMISSION-001` szabály kifejezetten a szabályfelvételre is érvényesíti az egyetlen kijelölt főfeladat korlátját. Az új policy-forrást a `CFA3-CURRENT-POLICY-SURFACE-001.json` jegyzi, és a Bootstrap, a fix tesztszámok, az Execution Guard-szabálylista, a PR fájlkészlete és a hibafelelősség egymással konzisztensen változik. Sikertelen ellenőrzés után az AI asszisztens feladatvezérlési vagy az AI fejlesztő implementációs felelősségét tényszerű, ellenőrzött okkal kell azonosítani; bizonyíték nélkül felelős megjelölése tilos. E rendelkezés nem jelent új futásidejű PASS-t vagy engedélyt másik feladat elindítására.

## Kötelező „Egy parancs – egy válasz” munkamenet

A `CFA3-SEQUENTIAL-COMMAND-001` szabály minden, a felhasználó által több lépésben végrehajtandó parancs- vagy tesztsorozatra kötelező. Az AI egyszerre pontosan egy futtatható parancsot vagy tesztet adhat meg, előre jelzi a várt eredményt, majd megvárja a felhasználó visszaküldött teljes kimenetét. Csak annak elemzése után adhatja ki a következő lépést. Hiba esetén kizárólag a közvetlen következő diagnosztikai vagy javítási lépést adhatja meg. A szabály tulajdonos által jóváhagyott, de önmagában nem bizonyít futásidejű kikényszerítést vagy PASS-t.
