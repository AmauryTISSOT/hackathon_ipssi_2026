import os
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

PYTHON     = sys.executable
DATA_DIR   = Path(__file__).parent
SCRIPTS    = DATA_DIR / "src" / "generate_file"
SAMPLE_DIR = DATA_DIR / "fake_data" / "sample" / datetime.now().strftime("%Y%m%d_%H%M%S")
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

import argparse

_env = os.environ.copy()
_env["PYTHONPATH"] = str(DATA_DIR) + os.pathsep + _env.get("PYTHONPATH", "")

parser = argparse.ArgumentParser()
parser.add_argument("--random", action="store_true", help="Données faker (kbis/rib/urssaf aléatoires, facture/devis sans MongoDB)")
args = parser.parse_args()

facture_script = "facture.py"      if args.random else "sirene_facture.py"
devis_script   = "devis.py"        if args.random else "sirene_devis.py"
rand_arg       = ["--random"]      if args.random else []

SCRIPTS_LIST = [
    (facture_script,         "facture.pdf",          []),
    (devis_script,           "devis.pdf",            []),
    ("kbis.py",              "kbis.pdf",             rand_arg),
    ("RIB.py",               "rib.pdf",              rand_arg),
    ("urssaf_vigilance.py",  "urssaf_vigilance.pdf", rand_arg),
]


def run(cmd: list) -> bool:
    return subprocess.run(cmd, cwd=str(DATA_DIR), env=_env).returncode == 0


def latest_pdf(folder: Path) -> Path | None:
    pdfs = sorted(folder.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True)
    return pdfs[0] if pdfs else None


for script, dest, extra_args in SCRIPTS_LIST:
    print(f"  {script} ...", end=" ", flush=True)
    tmp = SAMPLE_DIR / "_tmp"
    tmp.mkdir(exist_ok=True)
    ok = run([PYTHON, str(SCRIPTS / script), "--count", "1", "--output-dir", str(tmp)] + extra_args)
    src = latest_pdf(tmp) if ok else None
    if src:
        shutil.copy2(src, SAMPLE_DIR / dest)
        print(f"-> {dest}")
    else:
        print("ECHEC")
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\nFichiers dans {SAMPLE_DIR} :")
for f in sorted(SAMPLE_DIR.glob("*.pdf")):
    print(f"  • {f.name}")