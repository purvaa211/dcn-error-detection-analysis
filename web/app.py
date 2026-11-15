"""Flask Web Application for DCN Error Detection and Analysis System.

Provides an elegant, responsive engineering interface communicating with the Python backend
and object-oriented core architecture through the web_integration adapter layer.
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
    text_to_binary,
    validate_binary_string,
    run_simulation,
    run_comparison,
    get_algorithm_working,
    get_available_crc_polynomials,
    get_overview_statistics,
    get_simulation_history
)
from web_integration.experiment_service import experiment_service
from experiments.theory import get_theoretical_detection
from core.traffic_analysis import (
    parse_pcap_file,
    extract_packet_payload_details,
    evaluate_traffic_error_detection,
    compare_all_traffic_techniques,
    generate_sample_pcap
)

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
    """Render main application page with sidebar layout."""
    current_data = session.get("session_data", DEFAULT_DATA)
    return render_template("index.html", default_data=current_data)


# ======================================================================
# OVERVIEW & HISTORY API
# ======================================================================

@app.route("/api/overview-stats", methods=["GET"])
def api_overview_stats():
    """Retrieve actual application stats and recent experiment history for the Overview page."""
    stats = get_overview_statistics()
    return jsonify({
        "success": True,
        **stats
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    """Retrieve list of previous transmission experiments."""
    limit = int(request.args.get("limit", 50))
    records = get_simulation_history(limit=limit)
    return jsonify({
        "success": True,
        "history": records,
        "count": len(records)
    })


# ======================================================================
# SESSION & DATA UTILITY API
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


@app.route("/api/convert-text", methods=["POST"])
def api_convert_text():
    """Convert ASCII text string into 8-bit binary representation."""
    payload = request.get_json() or {}
    text = payload.get("text", "")
    if not text:
        return jsonify({
            "success": False,
            "error": "Text input cannot be empty."
        }), 400

    binary_str = text_to_binary(text)
    return jsonify({
        "success": True,
        "text": text,
        "binary": binary_str,
        "length": len(binary_str),
        "message": f"Successfully converted '{text}' ({len(text)} chars) to {len(binary_str)}-bit binary representation."
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
    try:
        payload = request.get_json(silent=True) or {}

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

        try:
            trials = int(payload.get("trials", 1000))
        except (ValueError, TypeError):
            trials = 1000

        run_res = experiment_service.run_benchmark(
            data_sizes=sizes,
            multi_error_amounts=mags,
            burst_lengths=bursts,
            trials=trials
        )
        return jsonify(run_res)
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal experiment runner error: {str(e)}"}), 500


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


@app.route("/api/theory-compare", methods=["GET"])
def api_theory_compare():
    """Retrieve comparative analysis of theoretical bounds versus measured benchmark results."""
    source = request.args.get("source", "auto")
    only_theory = request.args.get("only_theory", "false").lower() == "true"
    metrics_res = experiment_service.get_metrics_table(source=source)
    if not metrics_res.get("success"):
        return jsonify(metrics_res)

    records = metrics_res.get("records", [])
    seen = set()
    comparison_records = []

    for r in records:
        err_type = str(r.get("error_type", "")).strip().lower()
        if err_type in ("clean", "none", "0"):
            continue

        tech = str(r.get("technique", "")).strip()
        err_amt = r.get("error_amount")
        key = (tech, err_type, str(err_amt))
        if key in seen:
            continue
        seen.add(key)

        theory_res = get_theoretical_detection(
            technique=tech,
            error_type=err_type,
            error_param=err_amt
        )

        theory_val = theory_res.get("value")
        measured_rate = float(r.get("detection_rate", 0.0))

        if theory_val is not None:
            theory_pct = round(theory_val * 100.0, 2)
            diff = round(abs(measured_rate - theory_pct), 2)
        else:
            theory_pct = None
            diff = None

        if only_theory and theory_val is None:
            continue

        # Format parameter for UI display
        if err_type == "burst":
            param_label = f"span={err_amt}"
        elif err_type == "single":
            param_label = "1 bit"
        else:
            param_label = f"{err_amt} bit(s)"

        comparison_records.append({
            "technique": tech,
            "error_type": err_type,
            "error_amount": err_amt,
            "error_param": param_label,
            "measured_pct": round(measured_rate, 2),
            "theoretical_pct": theory_pct,
            "difference": diff,
            "note": theory_res.get("note", "")
        })

    return jsonify({
        "success": True,
        "records": comparison_records,
        "rows": comparison_records,
        "total": len(comparison_records),
        "source": metrics_res.get("source", "baseline")
    })


# ======================================================================
# NETWORK TRAFFIC ERROR DETECTION API
# ======================================================================

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SAMPLE_PCAP_PATH = os.path.join(PROJECT_ROOT, "samples", "sample_capture.pcap")
if not os.path.exists(SAMPLE_PCAP_PATH):
    generate_sample_pcap(SAMPLE_PCAP_PATH)


@app.route("/api/traffic/upload", methods=["POST"])
def api_traffic_upload():
    """Upload a .pcap or .pcapng file and return parsed packet summaries."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in upload request."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file selected for upload."}), 400

    filename = file.filename.lower()
    if not (filename.endswith(".pcap") or filename.endswith(".pcapng") or filename.endswith(".cap")):
        return jsonify({"success": False, "error": "Invalid file format. Please upload a Wireshark .pcap or .pcapng capture file."}), 400

    import time
    safe_name = f"upload_{int(time.time())}_{os.path.basename(file.filename)}"
    safe_path = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(safe_path)
    session["active_pcap_path"] = safe_path

    res = parse_pcap_file(safe_path)
    if not res.get("success"):
        return jsonify(res), 400

    return jsonify({
        "success": True,
        "filename": file.filename,
        "packets": res["packets"],
        "summary": res["summary"]
    })


@app.route("/api/traffic/sample", methods=["POST", "GET"])
def api_traffic_sample():
    """Load the realistic bundled sample PCAP file for instant demonstration."""
    if not os.path.exists(SAMPLE_PCAP_PATH):
        generate_sample_pcap(SAMPLE_PCAP_PATH)

    session["active_pcap_path"] = SAMPLE_PCAP_PATH
    res = parse_pcap_file(SAMPLE_PCAP_PATH)
    if not res.get("success"):
        return jsonify(res), 500

    return jsonify({
        "success": True,
        "filename": "sample_capture.pcap (Bundled Demonstration)",
        "packets": res["packets"],
        "summary": res["summary"],
        "is_sample": True
    })


@app.route("/api/traffic/select", methods=["POST"])
def api_traffic_select():
    """Extract payload and bitstream details from a selected packet."""
    payload = request.get_json() or {}
    packet_index = int(payload.get("packet_index", 0))
    pcap_path = session.get("active_pcap_path", SAMPLE_PCAP_PATH)

    if not os.path.exists(pcap_path):
        if not os.path.exists(SAMPLE_PCAP_PATH):
            generate_sample_pcap(SAMPLE_PCAP_PATH)
        pcap_path = SAMPLE_PCAP_PATH
        session["active_pcap_path"] = pcap_path

    res = extract_packet_payload_details(pcap_path, packet_index)
    return jsonify(res)


@app.route("/api/traffic/detect", methods=["POST"])
def api_traffic_detect():
    """Apply existing error detection technique to captured packet payload (with optional controlled error)."""
    payload = request.get_json() or {}
    packet_index = int(payload.get("packet_index", 0))
    technique = payload.get("technique", "CRC")
    inject_error = bool(payload.get("inject_error", False))
    error_type = payload.get("error_type", "single")
    error_amount = payload.get("error_amount", 1)
    crc_gen = payload.get("crc_generator", "100000111")
    chk_size = int(payload.get("checksum_word_size", 8))
    positions = payload.get("positions")

    pcap_path = session.get("active_pcap_path", SAMPLE_PCAP_PATH)
    if not os.path.exists(pcap_path):
        if not os.path.exists(SAMPLE_PCAP_PATH):
            generate_sample_pcap(SAMPLE_PCAP_PATH)
        pcap_path = SAMPLE_PCAP_PATH

    pkt_details = extract_packet_payload_details(pcap_path, packet_index)
    if not pkt_details.get("success"):
        return jsonify(pkt_details), 400
    if not pkt_details.get("has_payload"):
        return jsonify({
            "success": False,
            "error": pkt_details.get("reason", "Selected packet contains no payload data.")
        }), 400

    bin_data = pkt_details["binary_string"]
    res = evaluate_traffic_error_detection(
        binary_payload=bin_data,
        technique=technique,
        inject_error=inject_error,
        error_type=error_type,
        error_amount=error_amount,
        crc_generator=crc_gen,
        checksum_word_size=chk_size,
        positions=positions
    )

    if res.get("success"):
        res["packet_metadata"] = pkt_details.get("metadata")
        res["original_checksum_audit"] = pkt_details.get("metadata", {}).get("checksum_details")

    return jsonify(res)


@app.route("/api/traffic/compare", methods=["POST"])
def api_traffic_compare():
    """Run synchronized comparison of all canonical techniques on captured packet payload."""
    payload = request.get_json() or {}
    packet_index = int(payload.get("packet_index", 0))
    inject_error = bool(payload.get("inject_error", False))
    error_type = payload.get("error_type", "single")
    error_amount = payload.get("error_amount", 1)
    positions = payload.get("positions")

    pcap_path = session.get("active_pcap_path", SAMPLE_PCAP_PATH)
    if not os.path.exists(pcap_path):
        if not os.path.exists(SAMPLE_PCAP_PATH):
            generate_sample_pcap(SAMPLE_PCAP_PATH)
        pcap_path = SAMPLE_PCAP_PATH

    pkt_details = extract_packet_payload_details(pcap_path, packet_index)
    if not pkt_details.get("success"):
        return jsonify(pkt_details), 400
    if not pkt_details.get("has_payload"):
        return jsonify({
            "success": False,
            "error": pkt_details.get("reason", "Selected packet contains no payload data.")
        }), 400

    bin_data = pkt_details["binary_string"]
    res = compare_all_traffic_techniques(
        binary_payload=bin_data,
        inject_error=inject_error,
        error_type=error_type,
        error_amount=error_amount,
        positions=positions
    )

    if res.get("success"):
        res["packet_metadata"] = pkt_details.get("metadata")
        res["original_checksum_audit"] = pkt_details.get("metadata", {}).get("checksum_details")

    return jsonify(res)


@app.route("/api/traffic/use-payload", methods=["POST"])
def api_traffic_use_payload():
    """Set the selected packet's binary payload as active session data."""
    payload = request.get_json() or {}
    packet_index = int(payload.get("packet_index", 0))
    pcap_path = session.get("active_pcap_path", SAMPLE_PCAP_PATH)

    pkt_details = extract_packet_payload_details(pcap_path, packet_index)
    if not pkt_details.get("success") or not pkt_details.get("has_payload"):
        return jsonify({"success": False, "error": "Cannot use empty payload."}), 400

    bin_data = pkt_details["binary_string"]
    session["session_data"] = bin_data
    return jsonify({
        "success": True,
        "data": bin_data,
        "length": len(bin_data),
        "source_type": "traffic",
        "message": f"Packet #{packet_index + 1} payload ({len(bin_data)} bits) set as active session data."
    })


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
