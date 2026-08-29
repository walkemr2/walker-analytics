from pathlib import Path
import subprocess
import sys
from datetime import datetime

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

SCRIPT_DIR = BASE_DIR / "scripts"

SCRIPTS = [
    "01_WEB_price_data_pipeline.py",
    "02_WEB_asset_snapshot.py",
    "03_WEB_rotation_analytics.py",
    "04_WEB_early_rotation_signals.py",
]

print("=" * 72)
print("WALKER ANALYTICS - MASTER REFRESH")
print("=" * 72)
print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("Python:", sys.executable)
print("Script directory:", SCRIPT_DIR)
print()

for number, script_name in enumerate(SCRIPTS, start=1):
    script_path = SCRIPT_DIR / script_name

    print("=" * 72)
    print(f"STEP {number} OF {len(SCRIPTS)}")
    print(f"Running: {script_name}")
    print("=" * 72)

    if not script_path.exists():
        print(f"ERROR: Script not found:")
        print(script_path)
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR)
    )

    if result.returncode != 0:
        print()
        print("=" * 72)
        print("REFRESH FAILED")
        print("=" * 72)
        print(f"Failed script: {script_name}")
        print(f"Return code: {result.returncode}")
        sys.exit(result.returncode)

    print()
    print(f"SUCCESS: {script_name}")
    print()

print("=" * 72)
print("WALKER ANALYTICS REFRESH COMPLETE")
print("=" * 72)
print("Completed:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()
print("All four pipeline stages completed successfully.")