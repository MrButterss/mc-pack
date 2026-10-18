import argparse
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip())
VAULT = COMMON.parents[3]
PY = sys.executable
CHECK = [PY, "tools/check.py", "--no-index"]
CHECK_CI = [PY, "tools/check.py", "--ci"]
IDS = [PY, "tools/check_ids.py"]
BOOT = [PY, "tools/boot_test.py", "--server-dir", str(ROOT.parent / ".tmp" / "boot-server")]
DEPS = ["node", str(VAULT / "dist/projects/mc-pack/tools/check_deps.js")]

CASES = [
    ("TOML syntax", "mods/appleskin.pw.toml", None, "\nbad = = toml\n", False, [CHECK]),
    ("JSON syntax", "config/xaero/minimap/default_radar_categories_client.json", None, "\n{,\n", False, [CHECK]),
    ("SNBT unbalanced", "config/ftbquests/quests/chapters/welcome.snbt", None, "\n{\n", False, [CHECK]),
    ("KubeJS syntax", "kubejs/server_scripts/bulk_recipes.js", None, "\nfunction (\n", False, [CHECK]),
    ("resource pack side both", "resourcepacks/fancy-crops.pw.toml", ('side = "client"', 'side = "both"'), None,
     True, [CHECK]),
    ("mod side typo", "mods/appleskin.pw.toml", ('side = "', 'side = "x'), None, True, [CHECK]),
    ("stale index", "kubejs/server_scripts/bulk_recipes.js", None, "\n// stale\n", False, [CHECK_CI]),
    ("fake KubeJS id", "kubejs/server_scripts/bulk_recipes.js", ("minecraft:stick", "minecraft:fake_stick"), None,
     True, [IDS]),
    ("fake quest id", "config/ftbquests/quests/chapters/aeronautics.snbt",
     ("aeronautics:andesite_propeller", "aeronautics:fake_propeller"), None, True, [IDS]),
    ("sodium-extra side both", "mods/sodium-extra.pw.toml", ('side = "client"', 'side = "both"'), None, True,
     [BOOT], "boot"),
    ("fake id in shaped recipe", "kubejs/server_scripts/bulk_recipes.js", ("minecraft:stick", "minecraft:fake_stick"),
     None, True, [BOOT], "boot"),
    ("architectury jar removed", None, None, None, False, [DEPS], "boot"),
]


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def mods_without(tmp, filename):
    src = Path(subprocess.run([PY, "-c", "import sys; sys.path.insert(0, 'tools'); import boot_test as b; "
                               "print(b.INSTANCE / 'minecraft' / 'mods')"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip())
    dst = tmp / "mods"
    dst.mkdir()
    for jar in src.glob("*.jar"):
        if jar.name != filename:
            shutil.copy2(jar, dst / jar.name)
    return dst


def run_case(case, tmp):
    name, rel, swap, append, refresh, cmds = case[:6]
    wt = tmp / "wt"
    r = git("worktree", "add", "--detach", str(wt), "HEAD")
    if r.returncode:
        raise SystemExit(r.stderr)
    try:
        extra = []
        if rel:
            p = wt / rel
            text = p.read_text(encoding="utf-8")
            if swap:
                assert swap[0] in text, f"{name}: {swap[0]!r} not in {rel}"
                text = text.replace(swap[0], swap[1], 1)
            p.write_text(text + (append or ""), encoding="utf-8")
        else:
            arch = tomllib.loads((wt / "mods/architectury-api.pw.toml").read_text(encoding="utf-8"))["filename"]
            extra = ["--mods", str(mods_without(tmp, arch))]
        if refresh:
            subprocess.run(["packwiz", "refresh"], cwd=wt, capture_output=True)
        results = []
        for cmd in cmds:
            r = subprocess.run(cmd + extra, cwd=VAULT if cmd is DEPS else wt, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            results.append(r.returncode != 0)
        return results
    finally:
        git("worktree", "remove", "--force", str(wt))
        git("worktree", "prune")


def main():
    ap = argparse.ArgumentParser(description="Inject known faults and confirm each check catches them.")
    ap.add_argument("--boot", action="store_true", help="also run boot_test / check_deps cases (slow)")
    args = ap.parse_args()
    if git("status", "--porcelain").stdout.strip():
        print("note: uncommitted changes are not tested; cases run against HEAD")
    missed = 0
    print(f"{'case':<28} {'check':<16} result")
    for case in CASES:
        if len(case) > 6 and not args.boot:
            continue
        with tempfile.TemporaryDirectory() as t:
            results = run_case(case, Path(t))
        for cmd, caught in zip(case[5], results):
            missed += not caught
            print(f"{case[0]:<28} {Path(cmd[1]).stem:<16} {'CAUGHT' if caught else 'MISSED'}")
    print(f"{'FAILED' if missed else 'OK'}: {missed} missed")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
