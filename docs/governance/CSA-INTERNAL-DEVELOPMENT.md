# CSA – Internal development infrastructure

CSA-PLAN-001 v1.3 governs this tool. It is **not** part of the deliverable
CFA3 application, Rust crates, installer, or release artifacts. The
suggestion database contains potentially sensitive conversation text; **never
commit live records to this public application repository or any of its
branches**. A branch name containing "internal" does not make it private.

## Boundaries

- Development code: scripts/csa.py, with tests/test_csa.py.
- Canonical rules: canonical/policies/CFA3-POLICY-CSA-INFRASTRUCTURE-ISOLATION-001.md and companion JSON.
- Data: a separately selected storage location outside the application
  checkout; it must not be shipped with the finished product.
- To call the GitHub store canonical, independently confirm a suitably
  access-controlled remote, branch, commit, file readback and permissions.
- Local CLI PASS is not proof of GitHub archiving, automated ChatGPT history
  access, verified implementation status or conversation-native downloads.
- ChatGPT cannot retrieve deleted conversations unless previously preserved.
- No donor migration or donor database changes are authorized by this tool.

## Minimal offline operations

    python3 scripts/csa.py --root /private/csa-archive init
    python3 scripts/csa.py --root /private/csa-archive add --project CFA3 --title "Példa" --suggestion-file /path/to/text.md --source chat:identifier
    python3 scripts/csa.py --root /private/csa-archive find "Példa"
    python3 scripts/csa.py --root /private/csa-archive verify
    python3 scripts/csa.py --root /private/csa-archive export --project CFA3 --output /path/to/export.zip

The user provides the relevant original suggestion as a file; no automatic
access to other conversations is implied. A native ChatGPT attachment must be
created by the active conversation runtime after materializing the real export.

## Remaining qualification

Full historical ingestion, donor-compatible cross-reference graph with
bounded traversal, authoritative repository implementation-state verification,
canonical GitHub synchronization and user-facing native ChatGPT integration
require independent proof. Do not mark those capabilities IMPLEMENTED until
real tests have passed. The parallel donor workflow is unaffected.

## Baseline-kötött rekordok (1.1-es tervezési infrastruktúra)

A v2 rekordok csak megadott, hiteles, 200 elemű CFA3 baseline-névjegyzék mellett vehetők fel. A 176–200 közötti `RESERVED_NUMBER_ONLY` névhelyekre nem lehet ajánlást végleges baseline-hozzárendeléssel felvenni. Az új névhely kiosztása külön jóváhagyási folyamat.

A `--kind` megkülönbözteti az ajánlást, előzetes tervet és egyéb tervezési rekordot. A `--purpose`, `--baseline-id` és `--baseline-roster` kötelező. Az opcionális `--relation` CSA-rekordazonosítókkal kétirányúan indexelt kapcsolatot ad; `--applies-to` és `--excludes` a megengedett és kizárt baseline-felhasználást rögzíti. Az opcionális `--donor-id` hivatkozás olvasási célú `--donor-registry` használatát és kanonikus donorellenőrzést igényel. Donoradat nem másolódik át.

A `verify` a már létrehozott v2 rekordokhoz ugyanazt a hiteles baseline-névjegyzéket kérheti a `--baseline-roster` kapcsolóval. A v1, baseline nélküli rekordok nem minősülnek automatikusan 1.1-kompatibilis rekordokká.

A `CSA-RELATIONS.md` index a közvetlen és fordított hivatkozásokat tartalmazza. A státusz bizonyítékkal változtatható, de ajánlás/előzetes terv jóváhagyása önmagában nem véglegesíti az alkalmazástervet.

## Ellenőrzött, olvasási célú tervezési kontextus

A `context` művelet kizárólag egy `--record-id` **vagy** egy `--baseline-id` megadása után fut. A megadott `--baseline-roster` névjegyzéket, a rekordokat, az indexeket és szükség esetén a `--donor-registry` hivatkozásokat az olvasás előtt ellenőrzi. A kimenet JSON: forrás/proveniencia, eredeti Markdown-szöveg, rekordtípus, jóváhagyási és implementációs állapot, előre és visszafelé mutató kapcsolatok. Kereséskor a `PRIMARY_BASELINE` és `APPLICABLE_BASELINE` szerep külön látható.

Példa: `python3 scripts/csa.py --root /elkülönített/csa-adatok context --baseline-id CAP-001 --baseline-roster /hiteles/CFA3-CAPABILITY-NAMES-200-001.json`

Az eszköz **nem** fér hozzá automatikusan ChatGPT-beszélgetésekhez, nem küld adatokat GitHubra, és a rekordok lekérdezése nem véglegesíti az előzetes terveket. Az `add` művelethez forrás-hivatkozás (`--source`) kötelező; a fájl önmagában tárolt forrásmezője nem bizonyít külső hozzáférést. A JSON-kimenetet csak a jogosult tervezési munkamenet kezelheti.

## Írási integritás – negyedik szakasz

A rekord és az összes érintett index írása ugyanazon tranzakciós műveletben történik. Az előzetes szerkezeti ellenőrzés **a módosítás előtt** fut; a módosítandó rekordot és a várható indexeket a rendszer előre összeállítja. A módosítás alatt `.CSA-WRITE-IN-PROGRESS` jelző blokkolja az egyidejű írást és az olvasást. Szokásos fájlrendszerhiba esetén a folyamat megkísérli a már átírt fájlok visszaállítását; megszakítás vagy sikertelen visszaállítás esetén a jelző a helyén marad, és a nyilvántartás **STOP/BLOCKER** állapotba kerül az ellenőrzött helyreállításig.

Fontos: több fájl egyidejű cseréje nem fizikai, összeomlásbiztos ACID-tranzakció. A megoldás rendes hibákra visszaállítást és megszakításnál blokkoló jelzést biztosít, nem állít automatikus katasztrófa-helyreállítást. A `status` parancs immár kötelezően megköveteli a `--baseline-roster` argumentumot, és az egész helyi nyilvántartást ellenőrzi, mielőtt jóváhagyási státuszt vagy implementációs állapotot módosítana. A végleges alkalmazásterv jóváhagyási határa ezzel sem léphető át automatikusan.
