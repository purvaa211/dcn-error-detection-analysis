# Data Communication & Computer Networks (DCN) Course Project
## Error Generation, Detection, and Comparative Performance Analysis System

**Author:** Purva  
**Subject:** Data Communication and Computer Networks (DCN)  
**IDE:** Visual Studio Code (VS Code)  
**Language:** Python 3.10+ (Libraries: `matplotlib`, `pandas`, `numpy`)

---

## 1. Project Overview

In computer networks, physical transmission media are inherently susceptible to electromagnetic interference, thermal noise, and attenuation. These impairments corrupt transmitted bits, manifesting as **single-bit**, **multiple-bit**, or **burst errors**.

This project implements a complete, structured **Data Link Layer Error Control Architecture** featuring:
1. **Interactive Transmitter-Channel-Receiver Pipeline:** Demonstrates end-to-end data framing, redundancy bit computation, channel error injection, and receiver integrity validation.
2. **Proper Error Detection Techniques:**
   - **Vertical Redundancy Check (1D Parity):** Even and Odd Parity schemes.
   - **Two-Dimensional Parity Matrix (2D Parity / LRC + VRC):** Detects 1, 2, and 3-bit errors; pinpoints coordinates to correct single-bit errors.
   - **Internet Checksum (RFC 1071):** 8-bit and 16-bit 1's complement arithmetic with end-around carry (used in TCP/IP).
   - **Cyclic Redundancy Check (CRC):** Modulo-2 binary polynomial division ($GF(2)$ XOR arithmetic) supporting CRC-8 (ATM), CRC-16-CCITT (Bluetooth/HDLC), CRC-32 (Ethernet), and custom polynomials.
   - **Hamming Code (7,4):** Forward Error Detection and Correction.
3. **Channel Impairment & Error Generation Models:**
   - Single-bit impulse noise
   - Multiple random bit errors
   - Textbook burst errors (first & last bit corrupted, intermediate random)
   - Deterministic manual bit flips (for interactive jury testing)
   - Probabilistic Bit Error Rate (BER) channel noise
4. **Focused DCN Analytical Visualizations:** Generates only the 4 essential comparative charts + 1 Master 2x2 Presentation Dashboard. No repetitive or redundant graphs!

---

## 2. Project Directory Structure

```
error_detection_project/
│
├── algorithms/                    # Error Detection & Correction Algorithms
│   ├── parity.py                  # 1D Parity (Even & Odd VRC)
│   ├── two_dim_parity.py          # 2D Matrix Parity (LRC + VRC) with visual grid
│   ├── checksum.py                # Internet Checksum (RFC 1071 1's complement)
│   ├── crc.py                     # Cyclic Redundancy Check (CRC-8, CRC-16, CRC-32)
│   └── hamming.py                 # Hamming Code (7,4) (Detection & Correction)
│
├── simulation/                    # Transmission & Noise Simulation
│   ├── error_generator.py         # Channel noise models (Single, Multi, Burst, Manual, BER)
│   └── simulator.py               # End-to-end transmitter -> channel -> receiver pipeline
│
├── experiments/                   # Empirical Benchmarking Suite
│   ├── experiment_runner.py       # Monte Carlo empirical trials
│   └── metrics.py                 # Statistical aggregation (Detection %, Latency, Overhead)
│
├── visualization/                 # Publication-Ready Analytical Visualizations
│   ├── plot_results.py            # High-resolution (300 DPI) plotting engine
│   ├── detection_rate_by_error_count.png  # Chart 1: Multi-Bit Detection Curve
│   ├── burst_error_detection_rate.png     # Chart 2: Burst Noise Immunity Curve
│   ├── transmission_overhead.png          # Chart 3: Bandwidth Overhead Tradeoff
│   ├── processing_time.png                # Chart 4: Execution Latency (us)
│   └── dcn_performance_dashboard.png     # Master 2x2 Presentation Dashboard
│
├── experiment_results.csv         # Raw experimental Monte Carlo trials
├── metrics_results.csv            # Aggregated statistical performance indicators
├── main.py                        # Interactive menu-driven console CLI for jury presentation
└── README.md                      # Project manual, viva preparation guide & documentation
```

---

## 3. How to Run in Visual Studio Code

1. Open the project folder in **Visual Studio Code**:
   ```
   File -> Open Folder -> c:\Users\Purva\OneDrive\Desktop\error_detection_project
   ```
2. Open the built-in terminal (`Ctrl + ~` or `Terminal -> New Terminal`).
3. Run the interactive console application:
   ```bash
   python main.py
   ```
4. To run individual modules directly:
   - Run Benchmark: `python experiments/experiment_runner.py`
   - Recompute Metrics: `python experiments/metrics.py`
   - Generate Graphs: `python visualization/plot_results.py`

---

## 4. Interactive Menu Overview (`main.py`)

When you run `python main.py`, an interactive menu appears:

```
========================================================================
     DATA COMMUNICATION AND COMPUTER NETWORKS (DCN) PROJECT
      ERROR GENERATION, DETECTION & ANALYSIS SYSTEM
========================================================================
  [1] Interactive Transmission Walkthrough (Sender -> Channel -> Receiver)
  [2] Multi-Technique Comparison on Same Input (Side-by-Side Live Demo)
  [3] Step-by-Step CRC Modulo-2 Division Trace
  [4] 2D Parity Matrix Grid Visualizer (Row + Column Check)
  [5] Generate Essential Analytical Visualizations & Dashboard
  [6] Run Statistical Benchmark Suite (Regenerate CSV Datasets)
  [7] DCN Theoretical Quick Reference & Jury Viva Guide
  [8] Exit
========================================================================
```

### Highlights for Your Presentation:
- **Option 1 (Interactive Walkthrough):** Allows you or the jury to enter custom binary strings (e.g., `11010011`) or regular text strings (e.g., `DCN`), select any error detection technique, and inject errors. The console displays the transmission stage by stage, highlighting corrupted bits with index pointers (`^`), receiver syndromes, and theoretical explanations.
- **Option 2 (Side-by-Side Comparison):** Runs Parity, 2D-Parity, Checksum, CRC-8, and CRC-16 against the **exact same corrupted frame**. Shows live how Even Parity misses 2 bit errors while 2D-Parity and CRC detect them!
- **Option 3 (CRC Modulo-2 Division Trace):** Displays the exact quotient, XOR operations, and remainder calculation step-by-step. Perfect for answering: *"Show me the modulo-2 division math."*
- **Option 4 (2D Parity Matrix Visualizer):** Prints an ASCII grid showing data rows, row parities, and column parity (LRC). If 1 bit is flipped, it highlights the intersection `(Row r, Column c)` and shows how it can be corrected.
- **Option 5 (Visualization Suite):** Generates only the 4 essential analytical graphs and the Master 2x2 Dashboard without blocking popups.

---

## 5. Analytical Visualizations Explained

Only the 4 essential analytical charts required for DCN analysis are generated:

| Chart File | Analytical Purpose | Key DCN Takeaway |
| :--- | :--- | :--- |
| **`detection_rate_by_error_count.png`** | Evaluates detection probability as error count increases from 1 to 8 bits. | **Parity Oscillation:** Parity detects 100% of odd errors (1, 3, 5, 7) and 0% of even errors (2, 4, 6, 8) because $d_{min}=2$. **2D Parity & CRC** detect ~100% across all error amounts. |
| **`burst_error_detection_rate.png`** | Measures resilience against contiguous impulse noise across spans of 2 to 16 bits. | **CRC Mathematical Guarantee:** CRC-8 guarantees 100% detection for burst lengths $L \le 8$. Single parity averages only ~50% detection for burst errors. |
| **`transmission_overhead.png`** | Compares redundancy bit percentage as payload size grows from 32 to 1024 bits. | Shows bandwidth tradeoff: Parity adds only 1 bit ($O(1)$), CRC adds degree $r$ bits (overhead drops below 1% for larger frames), 2D parity has higher overhead on small frames. |
| **`processing_time.png`** | Compares execution latency (encoding + checking time in microseconds $\mu s$). | Parity and Checksum require simple addition/XOR ($O(N)$), while CRC polynomial division takes slightly higher computational time. |
| **`dcn_performance_dashboard.png`** | **Master 2x2 Dashboard** combining all 4 charts into one figure. | Ideal for inserting as a single slide into your PowerPoint presentation! |

---

## 6. DCN Viva / Jury Question & Answer Guide

### Q1: Why does Single Parity Check fail to detect two-bit errors?
> **Answer:** Parity check has a minimum Hamming distance of $d_{min} = 2$. It can only detect errors up to $d_{min} - 1 = 1$. When an even number of bits (such as 2, 4, or 6) are inverted, the parity (evenness or oddness of 1s) remains unchanged, resulting in an undetected error.

### Q2: How does Two-Dimensional (2D) Parity improve upon 1D Parity?
> **Answer:** 2D Parity arranges data bits into an $R \times C$ matrix, calculating row parity (VRC) and column parity (LRC). Its minimum Hamming distance is $d_{min} = 4$. It detects all 1-bit, 2-bit, and 3-bit errors. Furthermore, for a single-bit error, the intersection of the corrupted row and corrupted column pinpoints the exact bit coordinate, enabling forward error correction (FEC).

### Q3: What is the weakness of the Internet Checksum?
> **Answer:** The Internet Checksum (RFC 1071) uses 1's complement addition. Its main vulnerability is **compensating errors**—if one bit is flipped from 0 to 1 and another bit in the same column in another word is flipped from 1 to 0, the sum remains identical, and the error goes undetected. It is also insensitive to transposition of whole words.

### Q4: What makes CRC the preferred error detection technique in Data Link protocols?
> **Answer:** CRC is based on polynomial modulo-2 arithmetic. If generator polynomial $G(x)$ of degree $r$ satisfies standard conditions:
> - It detects 100% of single-bit errors (if $G(x)$ has $\ge 2$ terms).
> - It detects 100% of double-bit errors (if $G(x)$ does not divide $x^k + 1$).
> - It detects 100% of odd-bit errors (if $G(x)$ contains $(x+1)$ as a factor).
> - It detects 100% of burst errors of length $L \le r$.
> - It detects $1 - (1/2)^{r-1}$ of burst errors of length $L = r+1$ (99.2% for CRC-8; 99.997% for CRC-16).
> - It is implemented efficiently in hardware using simple linear feedback shift registers (LFSRs).
