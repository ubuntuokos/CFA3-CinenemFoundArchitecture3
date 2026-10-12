## CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001 — v1.0

**Megnevezés:** CSA fejlesztési infrastruktúra és végtermék kötelező elkülönítése

**1. A CSA rendeltetése**

A CSA a CFA3 fejlesztését támogató belső rendszer. Nem tekinthető a kész CFA3 alkalmazás részének, és javaslatadatbázisa nem válhat végfelhasználói alkalmazáskomponenssé.

**2. Komponensek elhelyezése**

| CSA-komponens | Kötelező elhelyezés |
|---|---|
| Működési képességek | CFA3 fejlesztési infrastruktúra |
| Szabályok | CFA3 központi szabályrendszer |
| Javaslatadatbázis | Elkülönített belső fejlesztési adattároló |
| ChatGPT-hozzáférés | Jogosultságkezelt fejlesztési hozzáférés |
| Kész CFA3 alkalmazás | CSA javaslatadatbázisa nélkül |

**3. GitHub-elkülönítés és hozzáférésvédelem**

A CSA javaslatadatbázisát a CFA3 alkalmazáskódjától elkülönítve, a korábban jóváhagyott CSA-PLAN-001 v1.3 tárolási tervével összhangban, privát GitHub-repository belső ágán kell kezelni.

A külön GitHub-ág nem biztonsági határ. A privát tárolás, az engedélyezett hozzáférések és az adatok alkalmazáskódtól való elkülönítése egymástól független kötelező követelmények.

**4. Kiadási tilalom**

A CSA javaslatadatbázisa nem kerülhet:
- a CFA3 telepítőcsomagjaiba;
- a kiadott release-artefaktumokba;
- a végfelhasználóknak átadott alkalmazásokba;
- az alkalmazással terjesztett adatcsomagokba.

A kiadási folyamatnak ellenőriznie kell a kizárást. Nem elegendő kizárólag a fejlesztői szándék.

**5. Fejlesztési felhasználhatóság**

A ChatGPT a CSA javaslatadatbázisát a CFA3 fejlesztési feladatainak előkészítéséhez, elemzéséhez és tervezéséhez felhasználhatja, amennyiben a hozzáférés engedélyezett.

A javaslatok felhasználása nem jelenti azok automatikus jóváhagyását vagy megvalósítási engedélyét.

**6. Kötelező elkülönítési alapelv**

A CSA fejlesztéstámogató infrastruktúrájának és a CFA3 végtermékének életciklusa, tárolása, hozzáféréskezelése és kiadási folyamata elkülönítendő.

Az elkülönítés nem akadályozhatja a CSA engedélyezett fejlesztéstámogató működését.