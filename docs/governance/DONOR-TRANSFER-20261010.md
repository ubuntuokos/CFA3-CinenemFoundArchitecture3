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

Ez a **rögzített repository-állomány átvitelének** lezárása. A kizárólag korábbi
beszélgetésekben lévő, még vissza nem nyert beküldések teljes lefedettsége, az
eredeti B bizonyítása, a végleges L1 besorolás és az L2–L5 új forráskutatás
továbbra sem tekinthető teljesítettnek. Ezeket nem oldja fel egy állapotjelző
átírása; külön bizonyíték kell hozzájuk.

## Párhuzamos munka védelme

A donorátvitel a meglévő #7 implementációs PR-ben marad. A #8 dokumentációs PR
README- és képfájljait nem módosítja. Az új CFA3 termékkoncepciója, a közös
Foundation, a 200 képesség célja és az L1–L5 szabályai változatlanok.
