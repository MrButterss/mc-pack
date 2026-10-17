import argparse
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRISM = Path(os.environ.get("APPDATA", "")) / "PrismLauncher"
INSTANCE = PRISM / "instances" / "Create Colony Lean"
NEOFORGE = tomllib.loads((ROOT / "pack.toml").read_text(encoding="utf-8"))["versions"]["neoforge"]
INSTALLER_URL = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{NEOFORGE}/neoforge-{NEOFORGE}-installer.jar"
COPY_DIRS = ("config", "defaultconfigs", "kubejs")


def java_path():
    cfg = (INSTANCE / "instance.cfg").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^JavaPath=(.+)$", cfg, re.M)
    if m:
        p = Path(m[1].strip().replace("javaw.exe", "java.exe"))
        if p.exists():
            return str(p)
    return shutil.which("java") or sys.exit("FAIL no Java 21 found; set JavaPath in Prism")


def install_server(server, java):
    marker = server / "libraries" / "net" / "neoforged" / "neoforge" / NEOFORGE
    if marker.exists():
        return
    server.mkdir(parents=True, exist_ok=True)
    installer = server / "installer.jar"
    print(f"downloading NeoForge {NEOFORGE} installer")
    urllib.request.urlretrieve(INSTALLER_URL, installer)
    subprocess.run([java, "-jar", str(installer), "--installServer", str(server)], cwd=server, check=True,
                   stdout=subprocess.DEVNULL)
    installer.unlink()


def client_only_files():
    names = set()
    for p in (ROOT / "mods").glob("*.pw.toml"):
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        if data.get("side") == "client":
            names.add(data["filename"])
    return names


def prepare(server, mods_dir, memory):
    for d in ("mods", "world", "crash-reports", "logs", *COPY_DIRS):
        shutil.rmtree(server / d, ignore_errors=True)
    (server / "mods").mkdir()
    skip = client_only_files()
    copied = 0
    for jar in Path(mods_dir).glob("*.jar"):
        if jar.name not in skip:
            shutil.copy2(jar, server / "mods" / jar.name)
            copied += 1
    for d in COPY_DIRS:
        if (ROOT / d).is_dir():
            shutil.copytree(ROOT / d, server / d)
    (server / "eula.txt").write_text("eula=true\n")
    (server / "server.properties").write_text("online-mode=false\nserver-port=25599\nlevel-name=world\n"
                                              "spawn-protection=0\nmax-players=1\n")
    (server / "user_jvm_args.txt").write_text(f"-Xmx{memory}\n-Xms1G\n")
    return copied, len(skip)


def crash_summary(server, log_lines):
    reports = sorted((server / "crash-reports").glob("*.txt"), key=lambda p: p.stat().st_mtime)
    text = reports[-1].read_text(encoding="utf-8", errors="replace").splitlines() if reports else log_lines
    keep = [l for l in text if re.search(r"Caused by:|Suspected Mods?:|Description:|Missing or unsupported|"
                                         r"invalid dist|Mixin apply failed|InvalidInjectionException", l)]
    failed = next((m[1] for l in text for m in [re.search(r"Failure message: .*\(([a-z0-9_]+)\) has failed", l)] if m),
                  None)
    culprit = failed or next((m[1] for l in text for m in [re.search(r"at (?:LAYER \w+/|TRANSFORMER/)([a-z0-9_]+)@", l)]
                              if m and m[1] not in ("minecraft", "neoforge", "fml_loader")), None)
    if culprit:
        print(f"culprit mod (first mod frame in the stack): {culprit}")
    if reports:
        print(f"crash report: {reports[-1]}")
    for l in (keep or text[-40:])[:25]:
        print("  " + l.strip())


def kubejs_errors(server):
    log = server / "logs" / "kubejs" / "server.log"
    if not log.exists():
        return []
    return [l.strip() for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if re.search(r"\[(ERR|ERROR)\b|\bERROR\b", l)]


def run(server, java, timeout):
    args_file = server / "libraries" / "net" / "neoforged" / "neoforge" / NEOFORGE / (
        "win_args.txt" if os.name == "nt" else "unix_args.txt")
    proc = subprocess.Popen([java, "@user_jvm_args.txt", f"@{args_file}", "nogui"], cwd=server,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    lines, done = [], threading.Event()

    def reader():
        for line in proc.stdout:
            lines.append(line.rstrip())
            if "Done (" in line and "For help" in line:
                done.set()
    threading.Thread(target=reader, daemon=True).start()
    start = time.time()
    crashes = server / "crash-reports"
    while not done.is_set() and proc.poll() is None and time.time() - start < timeout:
        if crashes.is_dir() and any(crashes.iterdir()):
            time.sleep(3)
            break
        time.sleep(1)
    elapsed = time.time() - start
    booted = done.is_set()
    if booted:
        proc.stdin.write("stop\n")
        proc.stdin.flush()
    try:
        proc.wait(timeout=120 if booted else 5)
    except subprocess.TimeoutExpired:
        proc.kill()
    (server / "boot_test.log").write_text("\n".join(lines), encoding="utf-8")
    return booted, elapsed, lines


def main():
    ap = argparse.ArgumentParser(description="Boot a NeoForge dedicated server with this pack and report crashes.")
    ap.add_argument("--mods", default=INSTANCE / "minecraft" / "mods", help="jars to test (default: Prism instance)")
    ap.add_argument("--server-dir", default=ROOT.parent / ".tmp" / "boot-server")
    ap.add_argument("--memory", default="4G")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    server, java = Path(args.server_dir), java_path()
    install_server(server, java)
    copied, skipped = prepare(server, args.mods, args.memory)
    print(f"server: {server}\nmods copied: {copied}, client-only skipped: {skipped}")
    booted, elapsed, lines = run(server, java, args.timeout)
    js = kubejs_errors(server)
    if not booted:
        print(f"FAIL server did not reach Done in {elapsed:.0f}s")
        crash_summary(server, lines)
        return 1
    print(f"server booted in {elapsed:.0f}s")
    for l in js[:15]:
        print(f"FAIL kubejs: {l}")
    print(f"{'FAILED' if js else 'OK'}: boot ok, {len(js)} KubeJS error line(s); full log {server / 'boot_test.log'}")
    return 1 if js else 0


if __name__ == "__main__":
    sys.exit(main())
