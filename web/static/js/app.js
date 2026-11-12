/**
 * Network Error Generation and Detection Analysis System
 * Client-Side Application Controller
 * 
 * Features:
 * - Sidebar page routing & view management
 * - Interactive step-by-step transmission simulator
 * - Real-time bitstream color-coded visualization (original, redundancy, flipped)
 * - Text-to-binary ASCII conversion
 * - Educational algorithm working calculations
 * - Synchronized side-by-side algorithm comparison
 * - Benchmark sweep runner & filterable metrics table
 * - High-res analytical chart zoom modal
 */

// Application State
const AppState = {
    currentPage: "overview",
    sessionData: "1011011011001100",
    simInputMode: "binary", // "binary" or "text"
    metricsData: [],
    currentTraceAlgo: "all"
};

// Page Metadata for Top Header Bar
const PAGE_META = {
    overview: {
        title: "Overview",
        desc: "Simulating unreliable communication channels and evaluating error detection techniques."
    },
    simulator: {
        title: "Transmission Simulator",
        desc: "Interactive step-by-step data framing, physical channel noise injection, and receiver error detection."
    },
    detection: {
        title: "Error Detection",
        desc: "Mathematical working principles and pedagogical traces for the four canonical techniques."
    },
    comparison: {
        title: "Algorithm Comparison",
        desc: "Synchronized side-by-side performance comparison on identical payload and channel error conditions."
    },
    experiments: {
        title: "Experimental Analysis",
        desc: "Batch Monte Carlo benchmark evaluation and 300 DPI analytical performance visualizations."
    }
};

// ==========================================================================
// INITIALIZATION & ROUTING
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    loadOverviewStats();
    loadMetricsTable();

    // Check hash for direct deep-linking
    const hash = window.location.hash.replace("#", "");
    if (hash && PAGE_META[hash]) {
        navigateToPage(hash);
    } else {
        navigateToPage("overview");
    }
});



function navigateToPage(pageId) {
    if (!PAGE_META[pageId]) return;
    AppState.currentPage = pageId;

    // Update Sidebar Navigation States
    document.querySelectorAll(".nav-link").forEach(btn => {
        if (btn.getAttribute("data-page") === pageId) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Update Page View Displays
    document.querySelectorAll(".page-view").forEach(view => {
        view.classList.remove("active");
    });
    const targetView = document.getElementById(`view-${pageId}`);
    if (targetView) targetView.classList.add("active");

    // Update Top Header Info
    const meta = PAGE_META[pageId];
    const titleEl = document.getElementById("top-header-title");
    const descEl = document.getElementById("top-header-desc");
    if (titleEl) titleEl.textContent = meta.title;
    if (descEl) descEl.textContent = meta.desc;

    // Update URL Hash without reload
    window.location.hash = pageId;

    // View-specific trigger hooks
    if (pageId === "overview") {
        loadOverviewStats();
    } else if (pageId === "detection") {
        loadTraceForAlgo(AppState.currentTraceAlgo);
    } else if (pageId === "comparison") {
        updateCompPayloadDisplay();
    } else if (pageId === "experiments") {
        loadMetricsTable();
    }
}

// ==========================================================================
// SESSION DATA MANAGEMENT
// ==========================================================================

async function initSession() {
    try {
        const res = await fetch("/api/session");
        const json = await res.json();
        if (json.success && json.data) {
            setGlobalPayload(json.data);
        }
    } catch (e) {
        console.error("Session fetch failed, using default payload", e);
    }
}

function setGlobalPayload(data) {
    AppState.sessionData = data;

    // Update Sidebar Pill
    const sidePill = document.getElementById("sidebar-payload-display");
    if (sidePill) sidePill.textContent = data;

    // Update Simulator input if in binary mode
    const simInput = document.getElementById("sim-data-input");
    if (simInput && AppState.simInputMode === "binary") {
        simInput.value = data;
    }

    // Update Comparison payload input
    updateCompPayloadDisplay();
}

function updateCompPayloadDisplay() {
    const compInput = document.getElementById("comp-payload-val");
    if (compInput) compInput.value = AppState.sessionData;
}

// ==========================================================================
// OVERVIEW PAGE CONTROLLER
// ==========================================================================

async function loadOverviewStats() {
    try {
        const res = await fetch("/api/overview-stats");
        const json = await res.json();
        if (!json.success) return;

        // Populate Summary Cards
        const simsEl = document.getElementById("stat-total-sims");
        const errsEl = document.getElementById("stat-total-errors");
        const detEl = document.getElementById("stat-avg-detection");
        const algoEl = document.getElementById("stat-algo-count");

        if (simsEl) simsEl.textContent = Number(json.total_simulations).toLocaleString();
        if (errsEl) errsEl.textContent = Number(json.total_injected_errors).toLocaleString();
        if (detEl) detEl.textContent = `${json.avg_detection_rate}%`;
        if (algoEl) algoEl.textContent = json.algorithms_count || 4;

        // Populate Recent Experiments Table
        const tbody = document.getElementById("overview-recent-table");
        if (!tbody) return;

        const recent = json.recent_experiments || [];
        if (recent.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color:var(--text-muted); padding:24px;">No simulations recorded yet. Run a transmission test!</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        recent.forEach(exp => {
            const tr = document.createElement("tr");

            let resultBadge = "";
            if (exp.error_type === "clean") {
                resultBadge = `<span class="badge badge-neutral">Clean Frame</span>`;
            } else if (exp.error_detected) {
                resultBadge = `<span class="badge badge-success">Detected</span>`;
            } else {
                resultBadge = `<span class="badge badge-danger">Missed</span>`;
            }

            tr.innerHTML = `
                <td><code>${exp.id}</code></td>
                <td><strong>${escapeHtml(exp.technique)}</strong></td>
                <td>${escapeHtml(formatErrorTypeName(exp.error_type))}</td>
                <td>${exp.errors_injected} bits</td>
                <td>${resultBadge}</td>
                <td><small style="color:var(--text-muted);">${exp.timestamp}</small></td>
            `;
            tbody.appendChild(tr);
        });

    } catch (e) {
        console.error("Failed to load overview stats:", e);
    }
}

function formatErrorTypeName(type) {
    const map = {
        clean: "Clean (0 errors)",
        single: "Single-Bit Error",
        multiple: "Multiple-Bit Errors",
        burst: "Burst Error",
        consecutive_burst: "Consecutive Burst",
        multiple_burst: "Multiple Burst",
        manual: "Manual Injection"
    };
    return map[type] || type;
}

// ==========================================================================
// TRANSMISSION SIMULATOR CONTROLLER
// ==========================================================================

function setSimulatorInputMode(mode) {
    AppState.simInputMode = mode;
    const tabBinary = document.getElementById("tab-btn-binary");
    const tabText = document.getElementById("tab-btn-text");
    const wrapBinary = document.getElementById("sim-mode-binary-wrap");
    const wrapText = document.getElementById("sim-mode-text-wrap");

    if (mode === "binary") {
        if (tabBinary) tabBinary.classList.add("active");
        if (tabText) tabText.classList.remove("active");
        if (wrapBinary) wrapBinary.style.display = "block";
        if (wrapText) wrapText.style.display = "none";
    } else {
        if (tabBinary) tabBinary.classList.remove("active");
        if (tabText) tabText.classList.add("active");
        if (wrapBinary) wrapBinary.style.display = "none";
        if (wrapText) wrapText.style.display = "block";
    }
}

function handleBinaryInputChange() {
    const input = document.getElementById("sim-data-input");
    if (!input) return;
    const val = input.value.trim();
    if (val && /^[01]+$/.test(val)) {
        AppState.sessionData = val;
        setGlobalPayload(val);
    }
}

async function handleTextToBinaryLive() {
    const textInput = document.getElementById("sim-text-input");
    const preview = document.getElementById("sim-text-conversion-preview");
    if (!textInput || !preview) return;

    const text = textInput.value;
    if (!text) {
        preview.textContent = "Enter text to automatically convert to 8-bit ASCII binary.";
        return;
    }

    try {
        const res = await fetch("/api/convert-text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const json = await res.json();
        if (json.success) {
            preview.innerHTML = `<strong>ASCII Binary (${json.length} bits):</strong> <code style="word-break:break-all;">${json.binary}</code>`;
            // Update active session data with converted text
            AppState.sessionData = json.binary;
            const simInput = document.getElementById("sim-data-input");
            if (simInput) simInput.value = json.binary;
            setGlobalPayload(json.binary);
        } else {
            preview.textContent = json.error || "Conversion failed";
        }
    } catch (e) {
        console.error("Text conversion error:", e);
    }
}

function generateSimulatorRandom(bits = 16) {
    let randStr = "";
    for (let i = 0; i < bits; i++) {
        randStr += Math.random() < 0.5 ? "0" : "1";
    }
    const input = document.getElementById("sim-data-input");
    if (input) input.value = randStr;
    setGlobalPayload(randStr);
}

function handleTechSelectionChange() {
    const select = document.getElementById("sim-tech-select");
    const crcOpts = document.getElementById("sim-crc-options");
    const chkOpts = document.getElementById("sim-checksum-options");
    const desc = document.getElementById("sim-tech-short-desc");
    if (!select) return;

    const val = select.value;
    if (crcOpts) crcOpts.style.display = (val === "CRC") ? "block" : "none";
    if (chkOpts) chkOpts.style.display = (val === "Checksum") ? "block" : "none";

    const descMap = {
        "VRC / Parity": "Appends a single bit to enforce an even number of '1's. Catches 100% of single-bit errors; misses all even errors.",
        "LRC": "Divides bitstream into 8-bit blocks and computes column-wise parity check characters.",
        "Checksum": "Accumulates m-bit words using 1's complement addition with end-around carry and bitwise inversion.",
        "CRC": "Treats data as polynomial coefficients over GF(2) and appends remainder from modulo-2 generator division."
    };
    if (desc) desc.textContent = descMap[val] || "";
}

function handleErrorSelectionChange() {
    const select = document.getElementById("sim-error-select");
    if (!select) return;

    const val = select.value;
    const hide = id => { const el = document.getElementById(id); if (el) el.style.display = "none"; };
    const show = id => { const el = document.getElementById(id); if (el) el.style.display = "block"; };

    hide("wrap-multi-count");
    hide("wrap-burst-span");
    hide("wrap-consec-span");
    hide("wrap-multiburst-spec");
    hide("wrap-manual-spec");

    if (val === "multiple") show("wrap-multi-count");
    else if (val === "burst") show("wrap-burst-span");
    else if (val === "consecutive_burst") show("wrap-consec-span");
    else if (val === "multiple_burst") show("wrap-multiburst-spec");
    else if (val === "manual") show("wrap-manual-spec");
}

async function handleSimulatorSubmit(event) {
    if (event) event.preventDefault();

    const dataInput = document.getElementById("sim-data-input");
    const data = (dataInput ? dataInput.value.trim() : "") || AppState.sessionData;

    if (!data || !/^[01]+$/.test(data)) {
        alert("Please enter a valid binary payload string consisting only of '0' and '1'.");
        return;
    }

    const tech = document.getElementById("sim-tech-select").value;
    const errType = document.getElementById("sim-error-select").value;

    let errAmount = 1;
    let positions = null;

    if (errType === "multiple") {
        errAmount = parseInt(document.getElementById("sim-param-multi").value, 10) || 2;
    } else if (errType === "burst") {
        errAmount = parseInt(document.getElementById("sim-param-burst").value, 10) || 4;
    } else if (errType === "consecutive_burst") {
        errAmount = parseInt(document.getElementById("sim-param-consec").value, 10) || 4;
    } else if (errType === "multiple_burst") {
        errAmount = {
            num_bursts: parseInt(document.getElementById("sim-param-mb-count").value, 10) || 2,
            burst_length: parseInt(document.getElementById("sim-param-mb-len").value, 10) || 3
        };
    } else if (errType === "manual") {
        const rawPos = document.getElementById("sim-param-manual").value;
        positions = rawPos.split(",").map(p => parseInt(p.trim(), 10)).filter(n => !isNaN(n));
        errAmount = positions;
    }

    const crcGen = document.getElementById("sim-crc-poly") ? document.getElementById("sim-crc-poly").value : "100000111";
    const chkWordSize = document.getElementById("sim-chk-words") ? parseInt(document.getElementById("sim-chk-words").value, 10) : 8;

    const btn = document.getElementById("btn-start-transmission");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<div class="spinner"></div> Transmitting...`;
    }

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data: data,
                technique: tech,
                error_type: errType,
                error_amount: errAmount,
                crc_generator: crcGen,
                checksum_word_size: chkWordSize,
                positions: positions
            })
        });

        const json = await res.json();
        if (json.success && json.result) {
            renderSimulatorResults(json.result);
            loadOverviewStats(); // Update dashboard count
        } else {
            alert(json.error || "Simulation failed");
        }
    } catch (e) {
        console.error("Simulation request error:", e);
        alert("An error occurred during transmission simulation.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Transmission`;
        }
    }
}

function renderSimulatorResults(sim) {
    const emptyState = document.getElementById("sim-empty-state");
    const activeResults = document.getElementById("sim-active-results");
    if (emptyState) emptyState.style.display = "none";
    if (activeResults) activeResults.style.display = "block";

    // Verdict Badge
    const verdictPill = document.getElementById("sim-verdict-pill");
    if (verdictPill) {
        if (sim.error_type === "clean") {
            verdictPill.className = "badge badge-neutral";
            verdictPill.textContent = "Clean Transmission";
        } else if (sim.error_detected) {
            verdictPill.className = "badge badge-success";
            verdictPill.textContent = "Error Detected";
        } else {
            verdictPill.className = "badge badge-danger";
            verdictPill.textContent = "Error Missed (Undetected)";
        }
    }

    // Stage A: Original Data
    const origBox = document.getElementById("vis-stream-orig");
    if (origBox) {
        origBox.innerHTML = renderBitCells(sim.original_data, [], 0);
    }
    const metaOrig = document.getElementById("vis-meta-orig");
    if (metaOrig) metaOrig.textContent = `Payload: ${sim.payload_length} bits`;

    // Stage B: Encoded Data
    const encBox = document.getElementById("vis-stream-enc");
    if (encBox) {
        encBox.innerHTML = renderBitCells(sim.protected_frame, [], sim.payload_length);
    }
    const metaEnc = document.getElementById("vis-meta-enc");
    if (metaEnc) metaEnc.textContent = `Frame: ${sim.protected_frame.length} bits (+${sim.overhead_bits} check bits)`;

    // Stage C & D: Transmission Channel & Noise
    const chanBox = document.getElementById("vis-stream-chan");
    if (chanBox) {
        chanBox.innerHTML = renderBitCells(sim.corrupted_frame, sim.flipped_indices, sim.payload_length);
    }
    const metaChan = document.getElementById("vis-meta-chan");
    if (metaChan) metaChan.textContent = `${sim.errors_injected} bit(s) flipped at indices: [${sim.flipped_indices.join(", ")}]`;

    const causeEl = document.getElementById("vis-cause-text");
    if (causeEl) causeEl.textContent = sim.error_cause || "None";

    const mechEl = document.getElementById("vis-mechanism-text");
    if (mechEl) mechEl.textContent = sim.error_introduction || "None";

    // Stage E: Receiver Data
    const recvBox = document.getElementById("vis-stream-recv");
    if (recvBox) {
        recvBox.innerHTML = renderBitCells(sim.corrupted_frame, sim.flipped_indices, sim.payload_length);
    }
    const metaRecv = document.getElementById("vis-meta-recv");
    if (metaRecv) metaRecv.textContent = `Received Frame: ${sim.corrupted_frame.length} bits`;

    // Stage F: Verdict & Explanation
    const verdictTitle = document.getElementById("vis-verdict-title");
    const explText = document.getElementById("vis-explanation-text");
    if (verdictTitle) {
        if (sim.error_type === "clean") {
            verdictTitle.innerHTML = `<span style="color:var(--primary);">[INTEGRITY VERIFIED]</span> No channel noise detected.`;
        } else if (sim.error_detected) {
            verdictTitle.innerHTML = `<span style="color:var(--status-success-text);">[ERROR DETECTED]</span> Receiver integrity verification failed as expected.`;
        } else {
            verdictTitle.innerHTML = `<span style="color:var(--status-error-text);">[ERROR MISSED]</span> Transmission was corrupted but escaped receiver detection!`;
        }
    }
    if (explText) explText.textContent = sim.explanation;

    // Results Metrics Grid
    const valPayload = document.getElementById("res-val-payload");
    const valFrame = document.getElementById("res-val-frame");
    const valOverBits = document.getElementById("res-val-overhead-bits");
    const valOverPct = document.getElementById("res-val-overhead-pct");
    const valLatency = document.getElementById("res-val-latency");
    const valStatus = document.getElementById("res-val-status");

    if (valPayload) valPayload.textContent = `${sim.payload_length} bits`;
    if (valFrame) valFrame.textContent = `${sim.protected_frame.length} bits`;
    if (valOverBits) valOverBits.textContent = `+${sim.overhead_bits} bits`;
    if (valOverPct) valOverPct.textContent = `${Number(sim.overhead_percentage).toFixed(1)}%`;
    if (valLatency) valLatency.textContent = `${(sim.processing_time * 1e6).toFixed(2)} µs`;
    if (valStatus) {
        valStatus.textContent = sim.is_valid ? "Valid (Accepted)" : "Corrupted (Rejected)";
        valStatus.style.color = sim.is_valid ? "var(--status-success-text)" : "var(--status-error-text)";
    }
}

function renderBitCells(bitstring, flippedIndices = [], redundancyStartIndex = 0) {
    const flipSet = new Set(flippedIndices);
    let html = "";
    for (let i = 0; i < bitstring.length; i++) {
        const bit = bitstring[i];
        let cls = "bit-cell";
        let title = `Bit index ${i}: ${bit}`;

        if (flipSet.has(i)) {
            cls += " flipped";
            title += " (CORRUPTED IN TRANSMISSION)";
        } else if (redundancyStartIndex > 0 && i >= redundancyStartIndex) {
            cls += " redundancy";
            title += " (REDUNDANT CHECK BIT)";
        } else {
            cls += " original";
        }

        html += `<span class="${cls}" title="${title}">${bit}</span>`;
    }
    return html;
}

function resetSimulatorView() {
    const simInput = document.getElementById("sim-data-input");
    if (simInput) simInput.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==========================================================================
// ERROR DETECTION PAGE CONTROLLER
// ==========================================================================

async function loadTraceForAlgo(tech) {
    AppState.currentTraceAlgo = tech;
    const titleEl = document.getElementById("algo-trace-title");
    const contentEl = document.getElementById("algo-trace-content");
    if (contentEl) contentEl.textContent = "Calculating step-by-step mathematical trace from backend...";

    const titleMap = {
        vrc: "VRC / Parity Check Step-by-Step Calculation",
        lrc: "LRC Matrix Step-by-Step Calculation",
        checksum: "Internet Checksum 1's Complement Step-by-Step Calculation",
        crc: "CRC Modulo-2 Polynomial Division Working",
        all: "All Four Error Detection Techniques Calculations"
    };
    if (titleEl) titleEl.textContent = titleMap[tech] || "Algorithm Working Trace";

    try {
        const res = await fetch(`/api/algorithm-working?technique=${tech}&data=${AppState.sessionData}`);
        const json = await res.json();
        if (json.success && json.traces) {
            let combinedText = "";
            for (const [key, trace] of Object.entries(json.traces)) {
                combinedText += `\n${trace.raw_text}\n\n`;
            }
            if (contentEl) contentEl.textContent = combinedText.trim();
        } else {
            if (contentEl) contentEl.textContent = json.error || "Failed to load algorithm trace.";
        }
    } catch (e) {
        console.error("Trace load error:", e);
        if (contentEl) contentEl.textContent = "Error loading calculation working.";
    }
}

// ==========================================================================
// ALGORITHM COMPARISON CONTROLLER
// ==========================================================================

function handleCompErrorChange() {
    const select = document.getElementById("comp-err-type");
    const amountCol = document.getElementById("comp-amount-col");
    const label = document.getElementById("comp-amount-label");
    if (!select || !amountCol) return;

    const val = select.value;
    if (val === "clean" || val === "single") {
        amountCol.style.display = "none";
    } else {
        amountCol.style.display = "block";
        if (val === "burst" || val === "consecutive_burst") {
            if (label) label.textContent = "Burst Span (bits):";
        } else {
            if (label) label.textContent = "Bit Error Count:";
        }
    }
}

async function executeComparison() {
    const data = AppState.sessionData;
    const errType = document.getElementById("comp-err-type").value;
    const errAmount = parseInt(document.getElementById("comp-err-amount").value, 10) || 2;

    const tbody = document.getElementById("comp-results-tbody");
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center"><div class="spinner"></div> Executing synchronized comparison across 4 techniques...</td></tr>`;
    }

    try {
        const res = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data: data,
                error_type: errType,
                error_amount: errAmount
            })
        });

        const json = await res.json();
        if (json.success && json.results) {
            renderComparisonTable(json.results);
        } else {
            if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color:var(--status-error-text);">${json.error || "Comparison failed"}</td></tr>`;
        }
    } catch (e) {
        console.error("Comparison execution failed:", e);
    }
}

function renderComparisonTable(results) {
    const tbody = document.getElementById("comp-results-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    results.forEach(item => {
        const tr = document.createElement("tr");

        let statusBadge = "";
        if (item.error_type === "clean") {
            statusBadge = `<span class="badge badge-neutral">Clean Frame</span>`;
        } else if (item.error_detected) {
            statusBadge = `<span class="badge badge-success">Detected</span>`;
        } else {
            statusBadge = `<span class="badge badge-danger">Missed</span>`;
        }

        const verdictStr = item.is_valid
            ? `<span style="color:var(--status-success-text); font-weight:700;">[VALID]</span>`
            : `<span style="color:var(--status-error-text); font-weight:700;">[CORRUPTED]</span>`;

        tr.innerHTML = `
            <td><strong>${escapeHtml(item.technique)}</strong></td>
            <td>+${item.overhead_bits} bits (${Number(item.overhead_percentage).toFixed(1)}%)</td>
            <td>${(item.processing_time * 1e6).toFixed(2)} µs</td>
            <td><code>[${(item.flipped_indices || []).join(", ")}]</code></td>
            <td>${statusBadge}</td>
            <td>${verdictStr}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ==========================================================================
// EXPERIMENTAL ANALYSIS CONTROLLER
// ==========================================================================

async function runBenchmarkSweep() {
    const btn = document.getElementById("btn-run-benchmark");
    const progress = document.getElementById("exp-progress-box");
    const progressText = document.getElementById("exp-progress-text");

    const sizes = document.getElementById("exp-sizes").value;
    const mags = document.getElementById("exp-mags").value;
    const bursts = document.getElementById("exp-bursts").value;
    const trials = parseInt(document.getElementById("exp-trials").value, 10) || 1000;

    if (btn) btn.disabled = true;
    if (progress) progress.style.display = "flex";
    if (progressText) progressText.textContent = `Running ${trials} Monte Carlo trials per configuration across all 4 algorithms...`;

    try {
        const res = await fetch("/api/experiments/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data_sizes: sizes,
                multi_error_amounts: mags,
                burst_lengths: bursts,
                trials: trials
            })
        });

        const json = await res.json();
        if (json.success) {
            // Apply staged results directly
            await fetch("/api/experiments/apply", { method: "POST" });
            refreshCharts();
            loadMetricsTable();
            alert("Benchmark experiments successfully completed and analytical graphs updated!");
        } else {
            alert(json.error || "Benchmark sweep failed.");
        }
    } catch (e) {
        console.error("Benchmark sweep failed:", e);
        alert("Failed to execute benchmark sweep.");
    } finally {
        if (btn) btn.disabled = false;
        if (progress) progress.style.display = "none";
    }
}

function refreshCharts() {
    const ts = new Date().getTime();
    for (let i = 1; i <= 4; i++) {
        const img = document.getElementById(`img-chart${i}`);
        if (img) {
            const currentSrc = img.src.split("?")[0];
            img.src = `${currentSrc}?t=${ts}`;
        }
    }
}

async function loadMetricsTable() {
    try {
        const res = await fetch("/api/metrics");
        const json = await res.json();
        const records = json.records || json.rows || [];
        if (json.success && records.length > 0) {
            AppState.metricsData = records;
            renderMetricsTableRows(records);
        } else if (records.length === 0) {
            const tbody = document.getElementById("metrics-table-body");
            if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px; color:var(--text-muted);">No metrics found in metrics_results.csv. Run benchmark experiments to populate.</td></tr>`;
        }
    } catch (e) {
        console.error("Failed to load metrics table:", e);
        const tbody = document.getElementById("metrics-table-body");
        if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px; color:var(--status-error-text);">Failed to load metrics dataset.</td></tr>`;
    }
}

function renderMetricsTableRows(rows) {
    const tbody = document.getElementById("metrics-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!rows || rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:24px; color:var(--text-muted);">No metrics matching your search.</td></tr>`;
        return;
    }

    // Render up to 100 rows
    const displayRows = rows.slice(0, 100);

    displayRows.forEach(r => {
        const tr = document.createElement("tr");
        const trialsVal = r.total_trials || r.trials || 1000;
        const latencyVal = r.latency_us != null ? r.latency_us : (r.average_processing_time_us != null ? r.average_processing_time_us : (r.average_processing_time ? (r.average_processing_time * 1e6).toFixed(2) : 0));
        const overheadVal = r.overhead_pct != null ? r.overhead_pct : (r.average_overhead_percentage != null ? r.average_overhead_percentage : 0);
        const detVal = r.detection_rate != null ? r.detection_rate : 0;

        tr.innerHTML = `
            <td><strong>${escapeHtml(r.technique)}</strong></td>
            <td>${escapeHtml(r.error_type)}</td>
            <td>${r.data_size} bits</td>
            <td>${r.error_amount}</td>
            <td>${trialsVal}</td>
            <td><strong>${detVal}%</strong></td>
            <td>${latencyVal} µs</td>
            <td>${overheadVal}%</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterMetricsTable() {
    const q = (document.getElementById("metrics-search-input").value || "").toLowerCase().trim();
    if (!q) {
        renderMetricsTableRows(AppState.metricsData);
        return;
    }
    const filtered = AppState.metricsData.filter(r => 
        (r.technique || "").toLowerCase().includes(q) ||
        (r.error_type || "").toLowerCase().includes(q) ||
        String(r.data_size).includes(q)
    );
    renderMetricsTableRows(filtered);
}

// ==========================================================================
// MODALS
// ==========================================================================

function openDataModal() {
    const input = document.getElementById("modal-data-input");
    const feedback = document.getElementById("modal-feedback");
    if (input) input.value = AppState.sessionData;
    if (feedback) feedback.style.display = "none";
    document.getElementById("data-modal").classList.add("active");
}

function closeDataModal() {
    document.getElementById("data-modal").classList.remove("active");
}

function setModalRandom(bits = 16) {
    let rand = "";
    for (let i = 0; i < bits; i++) rand += Math.random() < 0.5 ? "0" : "1";
    document.getElementById("modal-data-input").value = rand;
}

function setModalSample(type) {
    document.getElementById("modal-data-input").value = "NET";
}

async function submitDataModal() {
    const input = document.getElementById("modal-data-input");
    const feedback = document.getElementById("modal-feedback");
    const raw = (input ? input.value.trim() : "");

    try {
        const res = await fetch("/api/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: raw })
        });
        const json = await res.json();
        if (json.success) {
            setGlobalPayload(json.data);
            closeDataModal();
        } else {
            if (feedback) {
                feedback.textContent = json.message || "Failed to update payload.";
                feedback.style.color = "var(--status-error-text)";
                feedback.style.display = "block";
            }
        }
    } catch (e) {
        console.error("Payload update error:", e);
    }
}

function openGraphModal(filename, title) {
    const modal = document.getElementById("graph-modal");
    const img = document.getElementById("modal-graph-img");
    const titleEl = document.getElementById("modal-graph-title");
    if (img) img.src = `/api/graphs/${filename}?t=${new Date().getTime()}`;
    if (titleEl) titleEl.textContent = title;
    if (modal) modal.classList.add("active");
}

function closeGraphModal() {
    const modal = document.getElementById("graph-modal");
    if (modal) modal.classList.remove("active");
}

// Helper: Escape HTML
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
