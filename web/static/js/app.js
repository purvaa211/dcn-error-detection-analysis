/**
 * Frontend Application Controller for DCN Error Detection System
 * Interacts with the Flask integration layer directly.
 */

let currentSessionData = "1011011011001100";
let activeAlgoTab = "all";
let allMetricsRecords = [];

// ======================================================================
// INITIALIZATION
// ======================================================================

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    fetchSessionData();
    initExperimentsTab();
});

function initTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add("active");

            // Lazy tab load
            if (targetId === "tab-algorithm") {
                loadAlgorithmTrace(activeAlgoTab);
            } else if (targetId === "tab-experiments") {
                checkExperimentStatus();
                loadMetricsTable();
            } else if (targetId === "tab-compare") {
                updateCompareDataPreview();
            }
        });
    });
}

// ======================================================================
// SESSION DATA MANAGEMENT
// ======================================================================

async function fetchSessionData() {
    try {
        const res = await fetch("/api/session");
        const data = await res.json();
        if (data.success) {
            updateSessionDisplay(data.data);
        }
    } catch (err) {
        console.error("Failed to fetch session data:", err);
    }
}

function updateSessionDisplay(dataStr) {
    currentSessionData = dataStr;
    const disp = document.getElementById("global-data-display");
    const len = document.getElementById("global-data-length");
    const simInput = document.getElementById("sim-data");
    const compPreview = document.getElementById("comp-data-preview");

    if (disp) disp.textContent = dataStr;
    if (len) len.textContent = `(${dataStr.length} bits)`;
    if (simInput) simInput.value = dataStr;
    if (compPreview) compPreview.textContent = `${dataStr} (${dataStr.length} bits)`;
}

function updateCompareDataPreview() {
    const compPreview = document.getElementById("comp-data-preview");
    if (compPreview) compPreview.textContent = `${currentSessionData} (${currentSessionData.length} bits)`;
}

async function setSessionData(newRaw) {
    try {
        const res = await fetch("/api/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: newRaw })
        });
        const result = await res.json();
        if (result.success) {
            updateSessionDisplay(result.data);
            return result;
        } else {
            alert(result.error || "Failed to update session data.");
        }
    } catch (err) {
        console.error("Error setting session data:", err);
        alert("Network error updating session data.");
    }
    return null;
}

// Modal actions
function openDataModal() {
    const modal = document.getElementById("data-modal");
    const input = document.getElementById("modal-data-input");
    const fb = document.getElementById("modal-feedback");
    if (input) input.value = currentSessionData;
    if (fb) fb.style.display = "none";
    if (modal) modal.classList.add("active");
}

function closeDataModal() {
    const modal = document.getElementById("data-modal");
    if (modal) modal.classList.remove("active");
}

async function submitDataModal() {
    const input = document.getElementById("modal-data-input");
    if (!input) return;
    const val = input.value.trim();
    const res = await setSessionData(val);
    if (res && res.success) {
        closeDataModal();
    }
}

function setModalRandom() {
    let bits = "";
    for (let i = 0; i < 16; i++) bits += Math.random() < 0.5 ? "0" : "1";
    const input = document.getElementById("modal-data-input");
    if (input) input.value = bits;
}

function setModalSample(bits) {
    const input = document.getElementById("modal-data-input");
    if (!input) return;
    if (bits === "8") input.value = "10110011";
    else if (bits === "16") input.value = "1011011011001100";
    else if (bits === "32") input.value = "11001010111100001010010111110000";
}

async function generateRandomData() {
    await setSessionData("r");
}

async function quickTextPrompt() {
    const text = prompt("Enter plain ASCII text to convert to binary bits (e.g. 'DCN'):");
    if (text !== null && text.trim() !== "") {
        await setSessionData(text.trim());
    }
}


// ======================================================================
// TAB 1: SIMULATOR CONTROLLER
// ======================================================================

function toggleSimTechniqueOptions() {
    const tech = document.getElementById("sim-technique").value;
    const crcOpts = document.getElementById("sim-crc-options");
    const chkOpts = document.getElementById("sim-checksum-options");

    if (crcOpts) crcOpts.style.display = tech === "CRC" ? "block" : "none";
    if (chkOpts) chkOpts.style.display = tech === "Checksum" ? "block" : "none";
}

function toggleSimErrorInputs() {
    const errType = document.getElementById("sim-error-type").value;
    const multi = document.getElementById("err-param-multi");
    const burst = document.getElementById("err-param-burst");
    const manual = document.getElementById("err-param-manual");

    if (multi) multi.style.display = errType === "multiple" ? "block" : "none";
    if (burst) burst.style.display = errType === "burst" ? "block" : "none";
    if (manual) manual.style.display = errType === "manual" ? "block" : "none";
}

async function handleSimulate(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-run-sim");
    btn.disabled = true;
    btn.textContent = "Simulating...";

    const data = document.getElementById("sim-data").value.trim();
    const technique = document.getElementById("sim-technique").value;
    const errorType = document.getElementById("sim-error-type").value;
    const crcPoly = document.getElementById("sim-crc-poly").value;
    const chkSize = document.getElementById("sim-chk-size").value;

    let errorAmount = 1;
    let positions = null;

    if (errorType === "multiple") {
        errorAmount = parseInt(document.getElementById("sim-multi-count").value, 10) || 2;
    } else if (errorType === "burst") {
        errorAmount = parseInt(document.getElementById("sim-burst-len").value, 10) || 4;
    } else if (errorType === "manual") {
        const rawPos = document.getElementById("sim-manual-indices").value;
        positions = rawPos.split(",").map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
        errorAmount = positions;
    }

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data,
                technique,
                error_type: errorType,
                error_amount: errorAmount,
                crc_generator: crcPoly,
                checksum_word_size: chkSize,
                positions
            })
        });

        const dataRes = await res.json();
        if (dataRes.success) {
            renderSimulationResult(dataRes.result);
        } else {
            alert(dataRes.error || "Simulation failed.");
        }
    } catch (err) {
        console.error("Simulation request error:", err);
        alert("Failed to communicate with simulation backend.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Simulate Transmission Pipeline";
    }
}

function renderSimulationResult(sim) {
    document.getElementById("sim-empty-state").style.display = "none";
    const container = document.getElementById("sim-results-container");
    container.style.display = "block";

    // Verdict Badge
    const badge = document.getElementById("sim-verdict-badge");
    if (sim.error_type === "clean") {
        badge.className = "badge badge-success";
        badge.textContent = "CLEAN TRANSMISSION (VALID)";
    } else if (sim.error_detected) {
        badge.className = "badge badge-success";
        badge.textContent = "ERROR DETECTED (PASSED)";
    } else {
        badge.className = "badge badge-danger";
        badge.textContent = "ERROR MISSED (UNDETECTED)";
    }

    // Stage 1
    document.getElementById("sim-stage1-meta").textContent =
        `Overhead: +${sim.overhead_bits} bits (${sim.overhead_percentage.toFixed(1)}%)`;
    renderBitStream("sim-out-payload", sim.original_data);
    renderBitStream("sim-out-protected", sim.protected_frame);

    // Stage 2
    document.getElementById("sim-stage2-meta").textContent =
        `Errors Injected: ${sim.errors_injected} bit(s)`;
    renderCorruptedBitStream("sim-out-corrupted", sim.protected_frame, sim.corrupted_frame, sim.flipped_indices);

    const indDiv = document.getElementById("sim-out-indices");
    if (sim.flipped_indices && sim.flipped_indices.length > 0) {
        indDiv.textContent = `Corrupted Bit Positions: [${sim.flipped_indices.join(", ")}]`;
    } else {
        indDiv.textContent = "Corrupted Bit Positions: None (Clean Frame)";
    }

    // Stage 3
    const mpValid = document.getElementById("sim-mp-valid");
    mpValid.textContent = sim.is_valid ? "Valid (Passed)" : "Corrupted (Failed)";
    mpValid.style.color = sim.is_valid ? "#166534" : "#991b1b";

    const mpDetected = document.getElementById("sim-mp-detected");
    if (sim.error_type === "clean") {
        mpDetected.textContent = "N/A (Clean)";
        mpDetected.style.color = "#475569";
    } else {
        mpDetected.textContent = sim.error_detected ? "Detected (Yes)" : "Missed (No)";
        mpDetected.style.color = sim.error_detected ? "#166534" : "#991b1b";
    }

    document.getElementById("sim-mp-overhead").textContent =
        `+${sim.overhead_bits} bits (${sim.overhead_percentage.toFixed(1)}%)`;

    const latUs = (sim.processing_time * 1e6).toFixed(2);
    document.getElementById("sim-mp-latency").textContent = `${latUs} µs`;

    // Stage 4
    document.getElementById("sim-out-explanation").textContent = sim.explanation;
}

function renderBitStream(elementId, bitStr) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = "";
    for (let i = 0; i < bitStr.length; i++) {
        const span = document.createElement("span");
        span.className = "bit-cell";
        span.textContent = bitStr[i];
        el.appendChild(span);
    }
}

function renderCorruptedBitStream(elementId, origStr, corrStr, flippedIndices) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = "";
    const flipSet = new Set(flippedIndices || []);
    for (let i = 0; i < corrStr.length; i++) {
        const span = document.createElement("span");
        span.className = flipSet.has(i) ? "bit-cell flipped" : "bit-cell";
        span.textContent = corrStr[i];
        span.title = `Bit #${i}${flipSet.has(i) ? ' (FLIPPED)' : ''}`;
        el.appendChild(span);
    }
}


// ======================================================================
// TAB 2: COMPARE TECHNIQUES CONTROLLER
// ======================================================================

function toggleCompErrorInputs() {
    const errType = document.getElementById("comp-error-type").value;
    const amountCol = document.getElementById("comp-amount-col");
    const manualCol = document.getElementById("comp-manual-col");
    const label = document.getElementById("comp-amount-label");

    if (errType === "clean") {
        amountCol.style.display = "none";
        manualCol.style.display = "none";
    } else if (errType === "single") {
        amountCol.style.display = "none";
        manualCol.style.display = "none";
    } else if (errType === "multiple") {
        amountCol.style.display = "block";
        manualCol.style.display = "none";
        label.textContent = "Error Bit Count:";
    } else if (errType === "burst") {
        amountCol.style.display = "block";
        manualCol.style.display = "none";
        label.textContent = "Burst Span (bits):";
    } else if (errType === "manual") {
        amountCol.style.display = "none";
        manualCol.style.display = "block";
    }
}

async function handleRunComparison() {
    const errType = document.getElementById("comp-error-type").value;
    let errorAmount = 1;

    if (errType === "multiple" || errType === "burst") {
        errorAmount = parseInt(document.getElementById("comp-error-amount").value, 10) || 2;
    } else if (errType === "manual") {
        errorAmount = document.getElementById("comp-manual-positions").value.trim() || "0";
    }

    try {
        const res = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data: currentSessionData,
                error_type: errType,
                error_amount: errorAmount
            })
        });

        const data = await res.json();
        if (data.success) {
            renderComparisonResults(data.results);
        } else {
            alert(data.error || "Comparison failed.");
        }
    } catch (err) {
        console.error("Comparison error:", err);
        alert("Failed to communicate with comparison backend.");
    }
}

function renderComparisonResults(results) {
    document.getElementById("comp-empty").style.display = "none";
    document.getElementById("comp-table-wrapper").style.display = "block";

    const tbody = document.getElementById("comp-table-body");
    const cardsGrid = document.getElementById("comp-explanations-grid");
    tbody.innerHTML = "";
    cardsGrid.innerHTML = "";

    results.forEach(res => {
        // Table row
        const tr = document.createElement("tr");

        const tdTech = document.createElement("td");
        tdTech.innerHTML = `<strong>${res.technique}</strong>`;

        const tdOverhead = document.createElement("td");
        tdOverhead.textContent = `+${res.overhead_bits} bits (${res.overhead_percentage.toFixed(1)}%)`;

        const tdTime = document.createElement("td");
        const timeUs = (res.processing_time * 1e6).toFixed(2);
        tdTime.textContent = `${timeUs} µs`;

        const tdPositions = document.createElement("td");
        tdPositions.textContent = (res.flipped_indices && res.flipped_indices.length > 0)
            ? `[${res.flipped_indices.join(", ")}]`
            : "None";

        const tdStatus = document.createElement("td");
        if (res.error_type === "clean") {
            tdStatus.innerHTML = '<span class="badge badge-neutral">Clean Frame</span>';
        } else if (res.error_detected) {
            tdStatus.innerHTML = '<span class="badge badge-success">Detected</span>';
        } else {
            tdStatus.innerHTML = '<span class="badge badge-danger">Missed</span>';
        }

        const tdVerdict = document.createElement("td");
        if (res.error_type === "clean") {
            tdVerdict.innerHTML = '<span style="color:#166534;font-weight:600;">[VALID]</span>';
        } else if (res.error_detected) {
            tdVerdict.innerHTML = '<span style="color:#166534;font-weight:600;">[DETECTED]</span>';
        } else {
            tdVerdict.innerHTML = '<span style="color:#991b1b;font-weight:600;">[MISSED]</span>';
        }

        tr.appendChild(tdTech);
        tr.appendChild(tdOverhead);
        tr.appendChild(tdTime);
        tr.appendChild(tdPositions);
        tr.appendChild(tdStatus);
        tr.appendChild(tdVerdict);
        tbody.appendChild(tr);

        // Explanation Card
        const card = document.createElement("div");
        card.className = "comp-card";
        card.innerHTML = `
            <div class="comp-card-title">
                <span>${res.technique}</span>
                <span class="badge ${res.error_detected ? 'badge-success' : (res.error_type === 'clean' ? 'badge-neutral' : 'badge-danger')}">
                    ${res.error_type === 'clean' ? 'Clean' : (res.error_detected ? 'Detected' : 'Missed')}
                </span>
            </div>
            <div class="comp-card-body">
                <p>${res.explanation}</p>
            </div>
        `;
        cardsGrid.appendChild(card);
    });
}


// ======================================================================
// TAB 3: ALGORITHM WORKING CONTROLLER
// ======================================================================

async function loadAlgorithmTrace(tech, btnEl) {
    activeAlgoTab = tech;
    if (btnEl) {
        document.querySelectorAll(".algo-nav-btns .btn").forEach(b => b.classList.remove("active"));
        btnEl.classList.add("active");
    }

    const container = document.getElementById("algo-traces-container");
    container.innerHTML = '<div class="loading-state"><div class="spinner"></div> Generating algorithm traces from backend...</div>';

    const crcPoly = document.getElementById("algo-crc-gen").value;
    const chkSize = document.getElementById("algo-chk-size").value;

    try {
        const url = `/api/algorithm-working?data=${encodeURIComponent(currentSessionData)}&technique=${tech}&crc_generator=${crcPoly}&checksum_word_size=${chkSize}`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.success) {
            renderAlgorithmTraces(data.traces);
        } else {
            container.innerHTML = `<div class="alert alert-warning">${data.error || 'Failed to generate calculations.'}</div>`;
        }
    } catch (err) {
        console.error("Algorithm working fetch error:", err);
        container.innerHTML = '<div class="alert alert-warning">Network error communicating with backend calculation engine.</div>';
    }
}

function refreshAlgorithmTrace() {
    loadAlgorithmTrace(activeAlgoTab);
}

function renderAlgorithmTraces(traces) {
    const container = document.getElementById("algo-traces-container");
    container.innerHTML = "";

    const keys = Object.keys(traces);
    if (keys.length === 0) {
        container.innerHTML = '<div class="empty-state">No algorithm traces available.</div>';
        return;
    }

    keys.forEach(k => {
        const trace = traces[k];
        const box = document.createElement("div");
        box.className = "trace-box";
        box.innerHTML = `
            <div class="trace-header">
                <span class="trace-title">${trace.name}</span>
                <span class="badge badge-accent">Native Backend Calculation</span>
            </div>
            <div class="trace-content">${escapeHtml(trace.raw_text)}</div>
        `;
        container.appendChild(box);
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}


// ======================================================================
// TAB 4: EXPERIMENTS & ANALYTICAL GRAPHS CONTROLLER
// ======================================================================

function initExperimentsTab() {
    // Initial status check
    checkExperimentStatus();
}

async function checkExperimentStatus() {
    try {
        const res = await fetch("/api/experiments/status");
        const data = await res.json();
        if (data.success) {
            updateBaselineUI(data.baseline);
            updateStagingBanner(data.has_staged_run, data.staged_run);
        }
    } catch (err) {
        console.error("Status check error:", err);
    }
}

function updateBaselineUI(baseline) {
    const badge = document.getElementById("baseline-status-badge");
    const lastMod = document.getElementById("baseline-last-mod");

    if (baseline.baseline_ready) {
        badge.className = "badge badge-success";
        badge.textContent = "Baseline Available";
    } else {
        badge.className = "badge badge-warning";
        badge.textContent = "Benchmark Not Run Yet";
    }

    if (lastMod) {
        lastMod.textContent = baseline.last_modified || "Never";
    }
}

function updateStagingBanner(hasStaged, stagedRun) {
    const banner = document.getElementById("staging-banner");
    const msg = document.getElementById("staging-msg");

    if (hasStaged && stagedRun) {
        banner.style.display = "flex";
        msg.textContent = `New experiment results generated (${stagedRun.total_trials} trials in ${stagedRun.elapsed_seconds}s).`;
        // Refresh charts to show newly staged plots
        refreshCharts("staged");
    } else {
        banner.style.display = "none";
    }
}

async function handleRunExperiments(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-run-exp");
    const progress = document.getElementById("exp-progress");
    const progressText = document.getElementById("exp-progress-text");

    btn.disabled = true;
    progress.style.display = "block";
    progressText.textContent = "Executing benchmark experiments across all 4 techniques... Please wait.";

    const sizes = document.getElementById("exp-sizes").value;
    const mags = document.getElementById("exp-mags").value;
    const bursts = document.getElementById("exp-bursts").value;
    const trials = parseInt(document.getElementById("exp-trials").value, 10) || 50;

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

        const data = await res.json();
        if (data.success) {
            progress.style.display = "none";
            updateStagingBanner(true, data);
            loadMetricsTable("staged");
        } else {
            alert(data.error || "Benchmark run failed.");
            progress.style.display = "none";
        }
    } catch (err) {
        console.error("Experiment run error:", err);
        alert("Failed to execute benchmark run.");
        progress.style.display = "none";
    } finally {
        btn.disabled = false;
    }
}

async function applyStagedExperiments() {
    try {
        const res = await fetch("/api/experiments/apply", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            alert("Results and analytical graphs have been successfully applied to the project baseline!");
            checkExperimentStatus();
            refreshCharts("baseline");
            loadMetricsTable("baseline");
        } else {
            alert(data.error || "Failed to apply results.");
        }
    } catch (err) {
        console.error("Apply experiments error:", err);
        alert("Failed to apply staged results.");
    }
}

async function discardStagedExperiments() {
    try {
        const res = await fetch("/api/experiments/discard", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            alert("Newly generated results discarded. Previous baseline results and graphs preserved.");
            checkExperimentStatus();
            refreshCharts("baseline");
            loadMetricsTable("baseline");
        } else {
            alert(data.error || "Failed to discard results.");
        }
    } catch (err) {
        console.error("Discard experiments error:", err);
        alert("Failed to discard staged results.");
    }
}

function refreshCharts(source = "auto") {
    const timestamp = Date.now();
    const charts = [
        { id: "img-chart1", file: "detection_rate_by_error_type.png" },
        { id: "img-chart2", file: "detection_rate_vs_error_magnitude.png" },
        { id: "img-chart3", file: "processing_time_vs_data_size.png" },
        { id: "img-chart4", file: "overhead_vs_data_size.png" }
    ];

    charts.forEach(c => {
        const img = document.getElementById(c.id);
        if (img) {
            img.src = `/api/graphs/${c.file}?source=${source}&t=${timestamp}`;
        }
    });
}

function handleChartError(imgEl) {
    imgEl.alt = "Chart not generated yet. Please run experiments.";
    imgEl.style.opacity = "0.5";
}

async function loadMetricsTable(source = "auto") {
    try {
        const res = await fetch(`/api/metrics?source=${source}`);
        const data = await res.json();
        if (data.success) {
            allMetricsRecords = data.records;
            renderMetricsTable(allMetricsRecords);
        } else {
            const tbody = document.getElementById("metrics-table-body");
            if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center">${data.error}</td></tr>`;
        }
    } catch (err) {
        console.error("Metrics load error:", err);
    }
}

function renderMetricsTable(records) {
    const tbody = document.getElementById("metrics-table-body");
    const countEl = document.getElementById("metrics-row-count");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (countEl) countEl.textContent = `Showing ${records.length} configuration rows`;

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No matching metrics.</td></tr>';
        return;
    }

    records.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${r.technique}</strong></td>
            <td>${r.error_type}</td>
            <td>${r.data_size} bits</td>
            <td>${r.error_amount}</td>
            <td>${r.trials}</td>
            <td><strong>${r.detection_rate}%</strong></td>
            <td>${r.latency_us} µs</td>
            <td>${r.overhead_pct}%</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterMetricsTable() {
    const query = document.getElementById("metrics-search").value.toLowerCase().trim();
    if (!query) {
        renderMetricsTable(allMetricsRecords);
        return;
    }
    const filtered = allMetricsRecords.filter(r =>
        (r.technique && r.technique.toLowerCase().includes(query)) ||
        (r.error_type && r.error_type.toLowerCase().includes(query))
    );
    renderMetricsTable(filtered);
}

// Graph Modal Zoom
function openGraphModal(filename) {
    const modal = document.getElementById("graph-modal");
    const img = document.getElementById("modal-graph-img");
    const title = document.getElementById("modal-graph-title");
    if (!modal || !img) return;

    img.src = `/api/graphs/${filename}?t=${Date.now()}`;
    if (title) title.textContent = filename.replace(".png", "").replace(/_/g, " ").toUpperCase();
    modal.classList.add("active");
}

function closeGraphModal() {
    const modal = document.getElementById("graph-modal");
    if (modal) modal.classList.remove("active");
}
