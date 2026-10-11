"""Launcher for DCN Error Detection Web Interface.

Starts the local Flask web server connecting to the untouched backend modules
and automatically opens the default web browser.

Usage:
    python run_web.py
"""

import sys
import os
import time
import socket
import threading
import webbrowser

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import flask
except ImportError:
    print("\n[Error] Flask is not installed.")
    print("Please install Flask by running: pip install flask\n")
    sys.exit(1)

from web.app import app


def get_available_port(preferred: int = 5000) -> int:
    """Check if preferred port is available, or find an alternative."""
    for p in [preferred, 5001, 8080, 5050]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return preferred


def auto_open_browser(url: str):
    """Wait for server to bind, then automatically open browser."""
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    preferred_port = int(os.environ.get("PORT", 5000))
    port = get_available_port(preferred_port)
    url = f"http://127.0.0.1:{port}"

    print("\n" + "=" * 70)
    print("  DATA COMMUNICATION & COMPUTER NETWORKS (DCN) PROJECT")
    print("  ERROR GENERATION, DETECTION & ANALYSIS WEB APPLICATION")
    print("=" * 70)
    print(f"  * Web Server URL   : {url}")
    print(f"  * Localhost URL    : http://localhost:{port}")
    print("  * Original Backend : Untouched & Connected via web_integration")
    print("  * Features Available:")
    print("      1. Transmission Simulator (Sender -> Channel -> Receiver)")
    print("      2. Comparative Analysis (VRC, LRC, Checksum, CRC)")
    print("      3. Step-by-Step Algorithm Working")
    print("      4. Experiments & 4 Analytical Visualizations")
    print("  * Status: Opening in your default browser automatically...")
    print("  * Note  : Keep this terminal window open while using the website.")
    print("  * Exit  : Press Ctrl+C in this terminal to stop the server.")
    print("=" * 70 + "\n")

    # Launch browser in a background thread
    threading.Thread(target=auto_open_browser, args=(url,), daemon=True).start()

    # Listen on 0.0.0.0 so both 127.0.0.1 and localhost work reliably
    app.run(host="0.0.0.0", port=port, debug=False)
