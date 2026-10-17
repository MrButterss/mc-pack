import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "tools", ".github"}


def files(*patterns):
    for pattern in patterns:
        for p in ROOT.rglob(pattern):
            if not SKIP.intersection(p.relative_to(ROOT).parts):
                yield p


def snbt_balanced(text):
    stack, in_str, esc = [], False, False
    pairs = {"}": "{", "]": "["}
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append((ch, i))
        elif ch in "}]":
            if not stack or stack.pop()[0] != pairs[ch]:
                return f"unmatched '{ch}' at char {i}"
    if in_str:
        return "unterminated string"
    if stack:
        return f"unclosed '{stack[-1][0]}' at char {stack[-1][1]}"
    return None


def main():
    errors = []

    for p in files("*.toml"):
        try:
            tomllib.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{p.relative_to(ROOT)}: TOML {e}")

    for p in files("*.json", "*.mcmeta"):
        try:
            json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            errors.append(f"{p.relative_to(ROOT)}: JSON {e}")

    for p in files("*.snbt"):
        err = snbt_balanced(p.read_text(encoding="utf-8"))
        if err:
            errors.append(f"{p.relative_to(ROOT)}: SNBT {err}")

    node = shutil.which("node")
    for p in files("kubejs/**/*.js"):
        if not node:
            errors.append("node not found; KubeJS scripts not checked")
            break
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"{p.relative_to(ROOT)}: JS {r.stderr.strip().splitlines()[-1]}")

    for p in files("mods/*.pw.toml"):
        side = tomllib.loads(p.read_text(encoding="utf-8")).get("side")
        if side not in ("client", "server", "both"):
            errors.append(f"{p.relative_to(ROOT)}: side is {side!r}")

    for p in files("resourcepacks/*.pw.toml", "shaderpacks/*.pw.toml"):
        side = tomllib.loads(p.read_text(encoding="utf-8")).get("side")
        if side != "client":
            errors.append(f"{p.relative_to(ROOT)}: resource/shader pack must be side = \"client\", is {side!r}")

    if "--no-index" not in sys.argv:
        packwiz = shutil.which("packwiz")
        if not packwiz:
            errors.append("packwiz not found; index not checked")
        else:
            subprocess.run([packwiz, "refresh"], cwd=ROOT, check=True, capture_output=True)
            diff = subprocess.run(["git", "diff", "--name-only", "--", "index.toml", "pack.toml"],
                                  cwd=ROOT, capture_output=True, text=True).stdout.strip()
            if diff and "--ci" in sys.argv:
                errors.append("index.toml is stale: run packwiz refresh and commit it")
            elif diff:
                print("note: index was stale and has been refreshed; commit index.toml")

    for e in errors:
        print("FAIL", e)
    print(f"{'FAILED' if errors else 'OK'}: {len(errors)} problem(s)")
    return 1 if errors else 0


def demo():
    assert snbt_balanced('{a:[1,2],b:"}"}') is None
    assert snbt_balanced("{a:[1}") is not None
    assert snbt_balanced('{a:"x}') == "unterminated string"


if __name__ == "__main__":
    demo()
    sys.exit(main())
