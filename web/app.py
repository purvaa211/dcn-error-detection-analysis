"""Flask Web Application for DCN Error Detection and Analysis.

Provides a clean browser interface communicating with the Python backend
through the web_integration adapter layer.
"""

import os
import sys
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, send_file, session

# Add root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_integration.adapter import (
    parse_input_data,
    run_simulation,
    run_comparison,
    get_algorithm_working,
    get_available_crc_polynomials
)
from web_integration.experiment_service import experiment_service

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)
app.secret_key = os.urandom(24)

DEFAULT_DATA = "1011011011001100"


# ======================================================================
# PAGE ROUTE
# ======================================================================

@app.route("/")
def index():
    """Render main application page."""
    current_data = session.get("session_data", DEFAULT_DATA)
    return render_template("index.html", default_data=current_data)


# ======================================================================
# SESSION API
# ======================================================================

@app.route("/api/session", methods=["GET"])
def get_session():
    """Retrieve current session data."""
    data = session.get("session_data", DEFAULT_DATA)
    return jsonify({
        "success": True,
        "data": data,
        "length": len(data)
    })


@app.route("/api/session", methods=["POST"])
def update_session():
    """Update current session data with binary, random, or converted ASCII text."""
    payload = request.get_json() or {}
    raw_input = payload.get("data", "")
    parsed = parse_input_data(raw_input, default=DEFAULT_DATA)

    session["session_data"] = parsed["data"]
    return jsonify({
        "success": True,
        "data": parsed["data"],
        "length": parsed["length"],
        "source_type": parsed["source_type"],
        "message": parsed["message"]
    })


# ======================================================================
# SIMULATION API
# ======================================================================

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    """Execute single-technique transmission simulation."""
    payload = request.get_json() or {}
    data = payload.get("data") or session.get("session_data", DEFAULT_DATA)
    technique = payload.get("technique", "CRC")
    error_type = payload.get("error_type", "single")
    error_amount = payload.get("error_amount", 1)
    crc_generator = payload.get("crc_generator", "100000111")
    checksum_word_size = int(payload.get("checksum_word_size", 8))
    positions = payload.get("positions")

    res = run_simulation(
        data=data,
        technique=technique,
        error_type=error_type,
        error_amount=error_amount,
        crc_generator=crc_generator,
        checksum_word_size=checksum_word_size,
        positions=positions
    )
    return jsonify(res)


# ======================================================================
# COMPARISON API
# ======================================================================

@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Execute side-by-side comparison across all 4 techniques."""
    payload = request.get_json() or {}
    data = payload.get("data") or session.get("session_data", DEFAULT_DATA)
    error_type = payload.get("error_type", "single")
    error_amount = payload.get("error_amount", 1)

    res = run_comparison(
        data=data,
        error_type=error_type,
        error_amount=error_amount
    )
    return jsonify(res)


# ======================================================================
# ALGORITHM WORKING API
# ======================================================================

@app.route("/api/algorithm-working", methods=["GET"])
def api_algorithm_working():
    """Retrieve educational step-by-step calculations."""
    data = request.args.get("data") or session.get("session_data", DEFAULT_DATA)
    technique = request.args.get("technique", "all")
    crc_gen = request.args.get("crc_generator", "100000111")
    chk_size = int(request.args.get("checksum_word_size", 8))
    parity_mode = request.args.get("parity_mode", "even")

    res = get_algorithm_working(
        data=data,
        technique=technique,
        crc_generator=crc_gen,
        checksum_word_size=chk_size,
        parity_mode=parity_mode
    )
    return jsonify(res)


@app.route("/api/crc-polynomials", methods=["GET"])
def api_crc_polynomials():
    """Get standard CRC polynomial options."""
    polys = get_available_crc_polynomials()
    return jsonify({
        "success": True,
        "polynomials": polys
    })


# ======================================================================
# EXPERIMENTS & GRAPHS API
# ======================================================================

@app.route("/api/experiments/status", methods=["GET"])
def api_experiments_status():
    """Check status of benchmark results, graphs, and staging."""
    base_status = experiment_service.get_baseline_status()
    staged_run = experiment_service.last_staged_run
    return jsonify({
        "success": True,
        "baseline": base_status,
        "has_staged_run": staged_run is not None,
        "staged_run": staged_run
    })


@app.route("/api/experiments/run", methods=["POST"])
def api_experiments_run():
    """Execute benchmark experiments in staging environment."""
    payload = request.get_json() or {}

    # Parse configurable parameters
    sizes_raw = payload.get("data_sizes")
    if sizes_raw:
        if isinstance(sizes_raw, str):
            sizes = [int(s.strip()) for s in sizes_raw.split(",") if s.strip().isdigit()]
        else:
            sizes = [int(s) for s in sizes_raw]
    else:
        sizes = [32, 64, 128, 256, 512]

    mags_raw = payload.get("multi_error_amounts")
    if mags_raw:
        if isinstance(mags_raw, str):
            mags = [int(m.strip()) for m in mags_raw.split(",") if m.strip().isdigit()]
        else:
            mags = [int(m) for m in mags_raw]
    else:
        mags = [1, 2, 3, 4, 5, 8]

    bursts_raw = payload.get("burst_lengths")
    if bursts_raw:
        if isinstance(bursts_raw, str):
            bursts = [int(b.strip()) for b in bursts_raw.split(",") if b.strip().isdigit()]
        else:
            bursts = [int(b) for b in bursts_raw]
    else:
        bursts = [2, 4, 8, 16]

    trials = int(payload.get("trials", 50))

    run_res = experiment_service.run_benchmark(
        data_sizes=sizes,
        multi_error_amounts=mags,
        burst_lengths=bursts,
        trials=trials
    )
    return jsonify(run_res)


@app.route("/api/experiments/apply", methods=["POST"])
def api_experiments_apply():
    """Apply staged experiment results to project baseline."""
    res = experiment_service.apply_staged_results()
    return jsonify(res)


@app.route("/api/experiments/discard", methods=["POST"])
def api_experiments_discard():
    """Discard staged experiment results."""
    res = experiment_service.discard_staged_results()
    return jsonify(res)


@app.route("/api/graphs/<filename>", methods=["GET"])
def api_get_graph(filename):
    """Serve requested analytical graph image."""
    source = request.args.get("source", "auto")
    file_path = experiment_service.get_graph_file_path(filename, source=source)
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Graph not found"}), 404
    return send_file(file_path, mimetype="image/png")


@app.route("/api/metrics", methods=["GET"])
def api_get_metrics():
    """Serve metrics table records."""
    source = request.args.get("source", "auto")
    res = experiment_service.get_metrics_table(source=source)
    return jsonify(res)


# ======================================================================
# APPLICATION ENTRY
# ======================================================================

def create_app():
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=================================================================")
    print(f" DCN Error Detection System - Web Server Starting")
    print(f" URL: http://127.0.0.1:{port}")
    print(f" Press Ctrl+C in terminal to stop.")
    print(f"=================================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
