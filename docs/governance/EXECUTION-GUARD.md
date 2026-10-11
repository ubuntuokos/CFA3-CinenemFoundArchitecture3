# CFA3 Execution Guard – tulajdonos által jóváhagyott aktív szabályok

## Kötelező szabályjegyzék (2026-10-11)

Az eredeti **24 DEV/AI-szabály változatlan azonosítóval és kóddal** megmaradt. A tulajdonos ellenőrzés után újra beküldött **78** korábbi szabályának mindegyike az aktív Execution Guard hatáskörébe tartozik. A 22 történeti DEV/AI-szabály az eredeti 24 megfelelő azonosítójába van beolvasztva; ezeknek nincs új, versengő sorszáma. A **29 minőségi** (`Q-...`) és **27 feladatvezérlési** szabály saját történeti azonosítóval, egyenként szerepel az aktív készletben. **Összesen 80 külön azonosító és 78/78 feldolgozott beküldött rendelkezés.** Jelenleg nem azonosítottunk a 24 eredeti szabállyal összeegyeztethetetlen új rendelkezést; a konfliktus miatt kizártak száma 0.

Kanonikus aktuális szövegek: `canonical/registries/CFA3-EXECUTION-GUARD-OWNER-RULE-SPEC-001.json`. Forrás- és egyeztetési hivatkozások: `docs/governance/exports/CFA3-EXECUTION-GUARD-RULES-AND-CANDIDATES-20261011.json` és `canonical/registries/CFA3-LEGACY-RULE-RECONCILIATION-001.json`. A teljes 3159 történeti fájl külön felülvizsgálata nem előfeltétele a tulajdonos által már kifejezetten jóváhagyott 78 szabály érvényének.

## Ütközések és pontosítások

Az aktuális 24 szabály elsőbbséget élvez valódi szemantikai ellentmondás esetén; a 22 közös azonosítójú történeti szabály kiegészítő tartalma megőrzendő. A donor- és SDK-PR-ek puszta párhuzamos jelenléte nem blokkol, tényleges fájl-, kapu- vagy kizárólagos erőforrásütközés viszont igen. Az azonos akadály legfeljebb három próbálkozására vonatkozó történeti korlát **nem** ad automatikus újrapróbálkozási jogosultságot: a STOP és a kifejezett tulajdonosi engedély elsőbbséget élvez. A tulajdonos `Folytasd`, `Jóváhagyom`, `Készítsd el` parancsa kizárólag az azonos főfeladatra terjed ki. A második egymást követő saját AI-hiba javításához kifejezett jóváhagyás szükséges.

## Ellenőrzések és valódi események

A bootstrap nem igényli váratlan AI-ügynöki hibák, eltérő main, ütköző PR vagy jogosultságsértés éles környezetben történő előidézését. A tesztek kontrollált pozitív és negatív helyzetekkel vizsgálják a szabályazonosítókat, forrásokat, ütközésfelismerést és elutasítási mechanizmusokat. A 80 aktív szabályhoz tartozó strukturális ellenőrzés és a feltételes, feladatonkénti biztonsági kapu különválik.

A referenciaimplementáció önmagában nem avatkozik be minden natív ChatGPT-eszközhívásba. A műveletek éles végrehajtásához továbbra is hiteles tulajdonosi engedély, pontos friss állapot, védett bizonyítékszolgáltató, elkülönített kulcsok és tartós naplózás szükséges. A **80 szabály aktiválása nem hamis futásidejű PASS**; amíg a külön megbízható végrehajtási szolgáltatások nincsenek igazolva, a tényleges kapu fail-closed marad.

## Elhatárolás

A feladat kizárólag a korábbi 78 szabály jóváhagyott reintegrálása a meglévő Execution Guardba, a 24 jelenlegi DEV/AI-szabály megőrzésével. A donor-PR, SDK-PR, más alkalmazás, történeti 3159-fájlos feldolgozás és fizikai Current Host nem része a feladatnak. A `main` védelme és a kötelező `bootstrap` / `qt68-linux` check változatlan.
