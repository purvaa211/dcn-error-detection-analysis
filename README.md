# Network Error Generation and Detection Analysis System
## Data Communication and Networking (DCN) Engineering Simulation & Analysis Suite

**Subject:** Data Communication and Computer Networks (DCN)  
**Implementation:** Python 3.10+ (Flask, NumPy, Pandas, Matplotlib)  
**Visual Identity:** Warm Ivory + Forest Green Engineering Workbench  
**Repository:** [https://github.com/purvaa211/dcn-error-detection-analysis](https://github.com/purvaa211/dcn-error-detection-analysis)

---

## 1. Project Overview & Core Objective

In computer networking, physical transmission media (copper pairs, optical links, wireless RF channels) are subject to thermal noise, electromagnetic interference, crosstalk, and attenuation. These physical channel impairments cause bit inversions during transmission.

The **Network Error Generation and Detection Analysis System** is an interactive engineering simulator and research workbench designed to:
1. **Simulate end-to-end data transmission** across an unreliable communication channel connecting a Sender, Physical Channel, and Receiver.
2. **Model realistic transmission errors** including stochastic thermal noise, burst errors, solid contiguous disturbance, and multi-burst episodes.
3. **Evaluate canonical error detection techniques** across the Data Link and Transport layers (Parity Check / VRC, LRC, 1's Complement Checksum, and CRC).
4. **Conduct rigorous experimental analysis** through Monte Carlo trials, calculating empirical detection rates, Wilson confidence intervals, computational latency, and bandwidth overhead tradeoffs.

---

## 2. System Architecture & Object-Oriented Design (OOP)

The internal software architecture is structured around networking components and software engineering design patterns:

```
dcn-error-detection-analysis/
│
├── core/                               # Object-Oriented Architecture Package
│   ├── detection.py                    # ErrorDetection (ABC), ParityCheck, LRC, Checksum, CRC
│   ├── channel.py                      # TransmissionChannel & noise etiology modeling
│   ├── networking.py                   # Sender, Receiver, and NetworkSimulator orchestrator
│   ├── analysis.py                     # ExperimentConfig, ExperimentResult, ExperimentAnalyzer
│   ├── history.py                      # HistoryManager (JSON-based persistence)
│   └── __init__.py                     # Clean package exports
│
├── algorithms/                         # Core Algorithm Implementations
│   ├── parity.py                       # VRC / Parity (Even Parity - 1 bit, d_min = 2)
│   ├── lrc.py                          # LRC (2D Block Parity - 8-bit Block Check Character)
│   ├── checksum.py                     # 1's Complement Checksum (8-bit default, 16-bit RFC 1071)
│   ├── crc.py                          # CRC Modulo-2 Polynomial Division (CRC-8, CRC-16, CRC-32)
│   └── two_dim_parity.py               # 2D Matrix Parity helper
│
├── simulation/                         # Transmission & Noise Simulation
│   ├── error_generator.py              # 7 Error models (Clean, Single, Multiple, Burst, Consecutive, Multi-burst, Manual)
│   └── simulator.py                    # Backward-compatible bridge delegating to core.NetworkSimulator
│
├── experiments/                        # Empirical Benchmarking Suite
│   ├── experiment_runner.py            # Monte Carlo trials runner (default: 1,000 trials per config)
│   └── metrics.py                      # Statistical aggregation & clean vs corrupted separation
│
├── visualization/                      # Analytical Visualizations
│   ├── plot_results.py                 # High-resolution (300 DPI) plotting suite with Warm Ivory / Forest Green theme
│   ├── detection_rate_by_error_type.png       # Graph 1: Detection Rate by Error Type & Technique
│   ├── detection_rate_vs_error_magnitude.png  # Graph 2: Detection Rate vs Error Magnitude
│   ├── processing_time_vs_data_size.png       # Graph 3: Computational Latency vs Data Size
│   └── overhead_vs_data_size.png              # Graph 4: Transmission Overhead vs Data Size
│
├── web/                                # Web Application Interface
│   ├── app.py                          # Flask application controller & API routes
│   ├── templates/                      # Jinja2 templates (index.html with sidebar layout)
│   └── static/                         # Static assets (css/style.css, js/app.js)
│
├── web_integration/                    # Adapter & Staging Services
│   ├── adapter.py                      # Bridge between Web API and Python core
│   └── experiment_service.py           # Thread-safe experiment staging manager
│
├── simulation_history.json             # Persistent log of user-executed experiments
├── experiment_results.csv              # Raw Monte Carlo trial logs (104,000 trials)
├── metrics_results.csv                 # Aggregated performance metrics
├── main.py                             # Interactive console CLI menu
├── run_web.py                          # Web launcher script
└── README.md                           # Documentation & manual
```

### OOP Principles Demonstrated
- **Abstraction:** The abstract base class `ErrorDetection` defines standard methods (`encode`, `verify`, `get_working_steps`, `get_redundancy_bits`, `get_overhead_percentage`).
- **Inheritance:** Concrete subclasses `ParityCheck`, `LRC`, `Checksum`, and `CRC` inherit from `ErrorDetection`.
- **Encapsulation:** Internal algorithmic state (parity modes, word size, CRC generator polynomials, channel noise causes) are encapsulated within their respective classes.
- **Runtime Polymorphism:** The `Sender`, `Receiver`, and `NetworkSimulator` interact with any `ErrorDetection` instance polymorphically without branching logic.
- **Composition:** `NetworkSimulator` is composed of `Sender`, `TransmissionChannel`, and `Receiver`.
- **Exception Handling & Validation:** Robust validation for binary strings, ASCII text conversion, payload lengths, and channel noise parameters.

---

## 3. Web Application Interface (Warm Ivory + Forest Green)

The interface is styled in a **Warm Ivory + Forest Green** palette (`#F5F3ED` canvas with `#315C49` and `#244638` forest accents) featuring a persistent left sidebar and five dedicated pages:

### 1. Overview Page
- **Hero Introduction:** Highlighting the project identity, DCN scope, and primary action shortcuts.
- **Dynamic Application Statistics:** Live indicators for Total Simulations, Injected Errors, Average Detection Rate, and Evaluated Algorithms extracted directly from `simulation_history.json`.
- **Visual Transmission Pipeline:** Flow diagram showing `SENDER` &rarr; `ENCODER` &rarr; `TRANSMISSION CHANNEL` &rarr; `RECEIVER` &rarr; `ERROR DETECTION`.
- **Recent Experiments Table:** Historical log showing Experiment ID, Selected Technique, Error Model, Injected Errors, Verdict, and Timestamp.

### 2. Transmission Simulator (Core Feature)
- **Step 1: Enter Data:** Binary input mode with validation or ASCII Text input with real-time automatic conversion to 8-bit binary representation, plus a random binary generator (8, 16, 32 bits).
- **Step 2: Select Technique:** Parity Check (VRC), LRC (8-bit), Checksum (8-bit default, 16-bit RFC 1071), or CRC (CRC-8, CRC-16, CRC-32) with concise working descriptions.
- **Step 3: Select Error Pattern:** Clean transmission (0 errors), Single-bit error, Multiple-bit errors, Textbook burst error, Consecutive burst corruption (100% solid contiguous span), Multiple burst episodes, or Manual bit injection.
- **Step 4: Execute Transmission:** Prominent "Start Transmission" CTA triggering the real backend pipeline.
- **Step 5: Step-by-Step Visualization:**
  - **A. ORIGINAL DATA:** Sender payload bits.
  - **B. ENCODED DATA:** Original bits + redundant check bits highlighted in forest green.
  - **C & D. TRANSMISSION CHANNEL:** Frame in transit with exact physical noise cause and injection mechanism. Flipped bits highlighted in muted red.
  - **E. RECEIVER DATA:** Received frame arriving at destination.
  - **F. ERROR DETECTION RESULT:** Verdict banner (`[ERROR DETECTED]`, `[CLEAN TRANSMISSION]`, `[ERROR MISSED]`) with mathematical textbook explanation.
- **Step 6: Transmission Performance Metrics:** Metric cards showing Payload Size, Frame Size, Redundancy Bits, Overhead Percentage, Latency (in $\mu s$), and Verification Verdict.

### 3. Error Detection (Algorithms Guide)
- Educational reference cards for all four techniques outlining detection guarantees, mathematical principles, blind spots, and redundancy overheads.
- **Interactive Working Trace Viewer:** Generates real backend execution traces (e.g. Modulo-2 polynomial division steps, 1's complement addition with end-around carry, LRC matrix layout).

### 4. Algorithm Comparison
- Synchronized evaluation of all four techniques on the exact same payload data and identical physical error conditions.
- Real-time comparison table detailing Algorithm Name, Redundancy Overhead, Latency, Injected Positions, Detection Status, and Final Verdict.
- Comparative insight cards explaining why each technique behaves differently under specific error patterns.

### 5. Experimental Analysis
- Configuration interface for Monte Carlo benchmark sweeps (payload sizes, error quantities, burst spans, trials per configuration).
- **Four Analytical Visualizations (300 DPI):**
  1. *Detection Rate by Error Type and Technique* (Grouped Bar Chart)
  2. *Detection Rate versus Error Magnitude* (Multiple-bit curve demonstrating Parity's 100% odd vs 0% even behavior)
  3. *Processing Time versus Data Size* (Computational latency benchmark)
  4. *Transmission Overhead versus Data Size* (Bandwidth penalty curves)
- Filterable metrics table extracted from `metrics_results.csv`.

---

## 4. How to Run the Project

### Prerequisites
- Python 3.10 or higher
- Required packages: `flask`, `pandas`, `numpy`, `matplotlib`

```bash
pip install -r requirements.txt
```

### Option A: Launch Web Application
Start the Flask web server:
```bash
python run_web.py
```
Or directly using Flask:
```bash
python -m flask --app web.app run
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

### Option B: Run Interactive Console CLI
Launch the terminal-based interactive CLI menu:
```bash
python main.py
```

### Option C: Run Benchmark Suite & Generate Visualizations
To re-run the 104,000 Monte Carlo benchmark trials and generate high-resolution analytical graphs:
```bash
python experiments/experiment_runner.py
python experiments/metrics.py
python visualization/plot_results.py
```

---

## 5. Experimental Verification & Theoretical Alignment

With $N = 1,000$ trials per configuration, experimental results align with networking theory:
- **Odd error counts (1, 3, 5, 7 bits):** CRC-8 achieves **100.0%** detection due to the $(x+1)$ factor in the generator polynomial $G(x) = x^8 + x^2 + x + 1$.
- **Short bursts ($L \le 8$ bits):** CRC-8 achieves deterministic **100.0%** detection ($L \le r = 8$).
- **Long bursts ($L = 12, 16$ bits):** CRC-8 detection rate converges to **99.8%**, matching the theoretical bound $1 - 2^{-r} \approx 99.61\%$.
- **Parity Invariance:** Simple 1D Parity achieves exactly **100.0%** detection for odd errors and **0.0%** detection for even errors ($d_{min} = 2$).
