import argparse
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRISM = Path(os.environ.get("APPDATA", "")) / "PrismLauncher"
DEFAULT_MODS = PRISM / "instances" / "Create Colony Lean" / "minecraft" / "mods"
VANILLA = PRISM / "libraries" / "com" / "mojang" / "minecraft" / "1.21.1" / "minecraft-1.21.1-client.jar"

ASSET = re.compile(r"assets/([a-z0-9_.-]+)/(?:models/item|models/block|blockstates)/([a-z0-9_/.-]+)\.json$")
DATA = re.compile(r"data/([a-z0-9_.-]+)/loot_tables?/blocks/([a-z0-9_/.-]+)\.json$")
LANG = re.compile(r"assets/[a-z0-9_.-]+/lang/en_us\.json$")
LANG_KEY = re.compile(r"^(?:item|block|fluid)\.([a-z0-9_.-]+?)\.([a-z0-9_/.-]+)$")
JS_ID = re.compile(r"""['"`]([a-z0-9_.-]+):([a-z0-9_/.-]+)['"`]""")
SNBT_ID = re.compile(r"""\b(?:item|id|icon)\s*:\s*"([a-z0-9_.-]+):([a-z0-9_/.-]+)\"""")
SKIP_NS = {"ftbquests", "kubejs", "c", "neoforge", "forge"}


def scan_jar(data, ids, namespaces):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.endswith(".jar"):
                scan_jar(z.read(name), ids, namespaces)
                continue
            m = ASSET.search(name) or DATA.search(name)
            if m:
                ids.add(f"{m[1]}:{m[2]}")
                namespaces.add(m[1])
            elif LANG.search(name):
                try:
                    keys = json.loads(z.read(name).decode("utf-8-sig"))
                except ValueError:
                    continue
                for k in keys:
                    km = LANG_KEY.match(k)
                    if km:
                        ids.add(f"{km[1]}:{km[2].replace('.', '/')}")
                        ids.add(f"{km[1]}:{km[2]}")


def known_ids(mods_dir):
    ids, namespaces = set(), set()
    for jar in [*Path(mods_dir).glob("*.jar"), VANILLA]:
        if jar.exists():
            scan_jar(jar.read_bytes(), ids, namespaces)
    return ids, namespaces


def referenced_ids():
    refs = []
    for p in ROOT.glob("kubejs/**/*.js"):
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            line = re.sub(r"\.id\([^)]*\)|\btype\s*:\s*['\"][^'\"]*['\"]", "", line)
            for m in JS_ID.finditer(line):
                refs.append((p, n, f"{m[1]}:{m[2]}"))
    for p in ROOT.glob("config/ftbquests/**/*.snbt"):
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for m in SNBT_ID.finditer(line):
                refs.append((p, n, f"{m[1]}:{m[2]}"))
    return refs


def unknown(refs, ids, namespaces):
    bad = []
    for p, n, rid in refs:
        ns = rid.split(":", 1)[0]
        if ns in SKIP_NS or ns not in namespaces | {"minecraft"}:
            continue
        if rid not in ids:
            bad.append((p, n, rid))
    return bad


def main():
    ap = argparse.ArgumentParser(description="Fail on item/block ids in kubejs/ and quests that no jar provides.")
    ap.add_argument("--mods", default=DEFAULT_MODS)
    args = ap.parse_args()
    if not Path(args.mods).is_dir():
        print(f"FAIL mods folder not found: {args.mods}")
        return 1
    ids, namespaces = known_ids(args.mods)
    refs = referenced_ids()
    foreign = sorted({r.split(":")[0] for _, _, r in refs} - namespaces - SKIP_NS - {"minecraft"})
    bad = unknown(refs, ids, namespaces)
    for p, n, rid in bad:
        print(f"FAIL {p.relative_to(ROOT)}:{n}: unknown id {rid}")
    if foreign:
        print(f"note: namespaces with no jar assets (not checked): {', '.join(foreign)}")
    print(f"{'FAILED' if bad else 'OK'}: {len(refs)} ids checked against {len(ids)} known, {len(bad)} unknown")
    return 1 if bad else 0


def demo():
    ids, ns = {"create:cogwheel"}, {"create"}
    refs = [(ROOT, 1, "create:cogwheel"), (ROOT, 2, "create:nope"), (ROOT, 3, "kubejs:x"), (ROOT, 4, "zzz:y")]
    assert [r[2] for r in unknown(refs, ids, ns)] == ["create:nope"]


if __name__ == "__main__":
    demo()
    sys.exit(main())
