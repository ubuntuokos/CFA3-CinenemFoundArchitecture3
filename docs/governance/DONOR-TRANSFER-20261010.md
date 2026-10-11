# Régi CFA3 → új CFA3: donoradatok átvitele

## Kiadott feladat és átadott eredmény

A tulajdonos 2026. október 10-i kérése: végezzük el a donorátvitelt a régi
CFA3-ból az új CFA3-ba. Az eredmény a rögzített régi repository donorállományának
és a korábban visszanyert további forrásoknak az aktív, kereshető új referencia-
nyilvántartása. A régi repository változatlan marad.

Forrás: `ubuntuokos/Final-Architecture-v3.0`,
`a9c724da62bf49f3353c694990fc51443e634b4a`.
A forrás donorjegyzékének Git blobja:
`062b7b27aeeaf74819ac315f30c5cbde4ed2c95b`.

| Átvitt állomány | Darab |
| --- | ---: |
| Régi főág összes donor-/forrásrekordja | 1919 |
| Korábban visszanyert további forrás | 62 |
| Összes kereshető forrásazonosító | 1981 |
| Jóváhagyott donorreferencia | 884 |
| Megőrzött jelölt | 962 |
| Korábban elemzett forrás | 130 |
| Leváltott referencia, megőrzött történettel | 1 |
| Jóvá nem hagyott forrás | 4 |
| Eredeti locator-/aliaskapcsolat | 3946 |
| Hiányzó régi főági rekord | 0 |
| Módosult történeti rekord | 0 |
| Külön megőrzött elutasított forrás | 1 |

A 19–26. források már regisztrált 81 donorának és 83 eredeti URL-jének lekérdezési
eredménye változatlan. A több történeti azonosítóhoz kapcsolódó URL-eknél az
eredeti elsődleges feloldás és minden kapcsolódó azonosító megmarad.

## Aktív nyilvántartás és használat

Az aktív átvitt referenciaállomány:
`canonical/registries/CFA3-DONOR-TRANSFER-SNAPSHOT-001.json`.
A korábbi `CFA3-DONOR-REFERENCE-REGISTRY-001.json` a már jóváhagyott 19–26.
részhalmaz változatlan bizonyítéka; nem az összes átvitt forrás számlálója.
A történeti `STAGED` dokumentumok korábbi állapotfelvételek, nem új hatóságok.

```bash
python3 scripts/donor_reference_lookup.py --id FA3-DONOR-OPENCUT-001
python3 scripts/donor_reference_lookup.py --url https://github.com/OpenCut-app/OpenCut
python3 scripts/source_lifecycle.py https://github.com/OpenCut-app/OpenCut
```

Az első két parancs a megőrzött referenciaadatot adja vissza. Az életciklus-
ellenőrzés a korábbi döntést ismeri, de friss upstream-ellenőrzés nélkül nem
állít változatlanságot vagy új verzióra szóló engedélyt.

Újragenerálás és ellenőrzés:

```bash
python3 scripts/transfer_donors.py
python3 scripts/build_source_lifecycle_index.py
python3 scripts/transfer_donors.py --check
python3 scripts/build_source_lifecycle_index.py --check
python3 -m unittest discover -s tests -v
```

Az átvitel előbb ideiglenes állományon ellenőrzi a forrásokat, majd atomi
fájlcserét használ; a Git commit az együtt tartozó adatokat és keresőkódot egy
verzióba köti. Sikertelen felépítéskor a korábbi snapshot megmarad. A PR főágba
kerülését és a főági verzió visszaolvasását külön kell ellenőrizni; a puszta
fájlgenerálás nem jelenti az összevonás megtörténtét.

## Mit igazol a lezárás?

A rögzített régi főág 1919 rekordját közvetlenül a régi Git-objektumból olvastuk
vissza, és mezőnként összehasonlítottuk az új snapshot `historical_record`
adataival. Nincs elveszett azonosító és nincs átírt történeti mező. Az összes
1981 azonosító és 3946 locator visszakeresési tesztet kapott.

Az átvitel nem módosít donorengedélyt licenc-, SDK-, modell-, provider- vagy
runtime-engedéllyé. A jelölt és elemzett státusz nem lesz automatikusan
jóváhagyott donor. A régi #545 PR 17 nem befogadott javaslata és 3 még nem
alkalmazott kulcscseréje külön megőrzött függő tétel, nem eltüntetett adat.

A régi repository 1499 kanonikus JSON-fájljának ellenőrzése egy további, a fő
donorjegyzékből már eltávolított rekordot talált: DonutBrowser, `REJECTED`.
Az eredeti elutasítási napló változatlanul archivált, a kereső az elutasítást
visszaadja azonosító vagy történeti locator alapján; a forrás nem kerül vissza
az aktív donorállományba. Az eredeti napló blobja:
`1bb853ef2dc9a15231ab4acda136ee5c02c9e2c8`.

Ez a **rögzített repository-állomány átvitelének** lezárása. A kizárólag korábbi
beszélgetésekben lévő, még vissza nem nyert beküldések teljes lefedettsége, az
eredeti B bizonyítása, a végleges L1 besorolás és az L2–L5 új forráskutatás
továbbra sem tekinthető teljesítettnek. Ezeket nem oldja fel egy állapotjelző
átírása; külön bizonyíték kell hozzájuk.

## Párhuzamos munka védelme

A donorátvitel első állománya a #7 PR-rel került főágra. A tulajdonos 2026. október
11-i utasítása alapján az összevonás után jelzett öt keresési/lifecycle-hibát
ugyanennek a feladatnak a célzott javítása kezeli, védett főág esetén javító PR-ben.
A #8 dokumentációs PR
README- és képfájljait nem módosítja. Az új CFA3 termékkoncepciója, a közös
Foundation, a 200 képesség célja és az L1–L5 szabályai változatlanok.

## Összevonás utáni keresési és lifecycle-javítás

- Az eredeti transfer snapshot változatlan: Git blob
  `c863fe31d2c300bf15c9996432f86a70f9a18d74`, 1981 megőrzött identitás.
- A lifecycle-projekció az eredeti 3946 útvonal mellé 33 további egyedi,
  kifejezetten megőrzött történeti aliast rendel: összesen 3979 tárolt útvonal.
  A 574 történeti delta-alias feloldása is megmarad; ezek nem mind különböznek
  a tárolt útvonalaktól, ezért a számlálók nem adhatók egyszerűen össze.
- A történeti notes mező visszaolvasható. Egyértelmű, teljes upstream commit
  hiányzó strukturált verzió esetén összehasonlítható; PR-proveniencia,
  rövidített hash vagy többértelmű megfigyelés nem ad változatlansági igazolást.
- A kapu újraszámolja a történeti rekordok és rekordhalmaz ellenőrzőösszegét,
  majd ellenőrzi a lifecycle-indexhez kötött transfer-fájl SHA-256 értékét.
- Mind az 56 jelenlegi tulajdonosi megerősítés konkrét rekordja szerepel a
  korábbi döntésben. A megerősítési fájl ellenőrzőösszege a projekció része;
  törlés, eltérő kötés és megváltozott állomány blokkolja a lifecycle-lekérdezést.
- Létező locator hiányzó célazonosítóval integritási hibát ad, nem egyszerű
  „nem található” eredményt.

## Friss ellenőrzési bizonyíték a #11 javításhoz (2026-10-11)

A korábbi 111 tesztes bejegyzés történeti, nem tekinthető a javított kódállapot
végső bizonyítékának. Az ellenőrzött, `main`-nel szinkronizált kódcommit:
`8f024c7b0d04e86e7a24473c2ecc555991f3817c` (a főági szülő
`bd26ce9f24eb31a5e4c810a3c97c79c23ed21521`).

- GitHub Actions `CFA3 bootstrap reference checks`:
  https://github.com/ubuntuokos/CFA3-CinenemFoundArchitecture3/actions/runs/38148020871
  — `success`; a **teljes Python unittest-discovery 128 tesztet futtatott**,
  `Ran 128 tests in 114.601s`, `OK`.
- Az új `test_tuple_container_cannot_bypass_validated_snapshot_deep_freeze`
  negatív regresszió ezen a pontos commiton `ok`. A GitHub CI
  Rust-first workspace-ellenőrzése is `success`.
- GitHub Actions `CFA3 Qt 6.8 Linux environment`:
  https://github.com/ubuntuokos/CFA3-CinenemFoundArchitecture3/actions/runs/38148020917
  — `success`.
- A korábban javított integritási-, jóváhagyási-, locator- és lifecycle-hibák
  tesztjei ugyanezen teljes tesztfutás részei. A teljes snapshot, az elutasítási
  napló és a tulajdonosi bizonyítékok hitelesítését a regressziók is ellenőrzik.

Ez a bizonyíték **csak a megjelölt kódcommitra** vonatkozik. A dokumentációs
commitra és a végleges PR HEAD-re a GitHub kötelező ellenőrzéseit külön, friss
állapotból kell visszaigazolni, a független code review-val együtt. A szintetikus
CI soha nem fizikai Current Host PASS, és nem igazolja az eredeti B, a teljes
történeti beküldéskészlet vagy az L1–L5 lezárását.

A #11 első független review-jának négy kiegészítő észrevétele is regressziós
tesztet kapott. A referencia-kereső a teljes snapshotot és mindkét lookup-indexet
ellenőrzi, így másik donor sérülése sem marad észrevétlen. A lifecycle-index
minden döntési, proveniencia- és útvonalmezőjének egyeznie kell a megőrzött
bemenetekből előállított projekcióval. A tulajdonosi megerősítés dokumentumazonosítója,
forráscommitja és cél-snapshotja is kötött. A belső gyorsítótár teljes, típushelyes
adatérték alapján működik; változott adat nem használhat korábbi sikeres ellenőrzést.
