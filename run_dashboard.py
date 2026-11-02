"""
One-command launcher for the Founder Morning Dashboard.
Run: python run_dashboard.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    dashboard_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    print("=" * 60)
    print("🚀 Launching COD Guardian Founder Dashboard...")
    print(f"📍 Script: {dashboard_path}")
    print("=" * 60)
    cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port=8501", "--server.headless=false"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped.")

if __name__ == "__main__":
    main()
