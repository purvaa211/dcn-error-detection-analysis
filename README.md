# Data Communication & Computer Networks (DCN) Course Project
## Error Generation, Detection, and Comparative Performance Analysis System

**Author:** Purva  
**Subject:** Data Communication and Computer Networks (DCN)  
**IDE:** Visual Studio Code (VS Code)  
**Language:** Python 3.10+ (Libraries: `matplotlib`, `pandas`, `numpy`)

---

## 1. Project Overview

In computer networks, physical transmission media are inherently susceptible to electromagnetic interference, attenuation, and noise. These impairments cause bit inversions during transmission.

This project implements a complete, structured **Data Link Layer Error Control Architecture** featuring:
1. **Interactive Transmitter-Channel-Receiver Pipeline:** Demonstrates end-to-end data framing, redundancy bit computation, channel error injection, and receiver integrity validation.
2. **Four Detection Techniques:**
   - **VRC / Parity (Vertical Redundancy Check):** Appends 1 parity bit per data unit to achieve even parity ($d_{min} = 2$).
   - **LRC (Longitudinal Redundancy Check):** Organizes data into blocks and computes column-by-column parity bits.
   - **Checksum (Internet Checksum RFC 1071):** Computes 8-bit 1's complement sum with end-around carry (used in TCP/IP).
   - **CRC (Cyclic Redundancy Check):** Modulo-2 binary polynomial division ($GF(2)$ XOR arithmetic) using the standard CRC-8 generator polynomial ($x^8 + x^2 + x + 1$).
3. **Five Error Generation Models:**
   - Clean transmission (zero error introduced)
   - Single-bit error (random isolated bit flip)
   - Multiple-bit error (user-specified $k$ bit flips)
   - Burst error (contiguous span of noise with corrupted endpoints)
   - Manual error injection (user selects exact bit positions to flip)
4. **Four Analytical Visualizations:**
   - Detection rate by error type and technique (Grouped bar chart)
   - Detection rate versus error magnitude (Multi-bit curve highlighting parity limitation)
   - Processing time versus data size (Computational latency benchmark in $\mu s$)
   - Transmission overhead versus data size (Redundancy percentage trade-off)

---

## 2. Project Directory Structure

```
error_detection_project/
│
├── algorithms/                    # Error Detection Algorithms
│   ├── parity.py                  # VRC / Parity (Vertical Redundancy Check)
│   ├── lrc.py                     # LRC (Longitudinal Redundancy Check)
│   ├── checksum.py                # Internet Checksum (RFC 1071 1's complement)
│   ├── crc.py                     # Cyclic Redundancy Check (CRC-8, Modulo-2 division)
│   └── two_dim_parity.py          # 2D Matrix Parity helper
│
├── simulation/                    # Transmission & Noise Simulation
│   ├── error_generator.py         # 5 Error models: Clean, Single, Multiple, Burst, Manual
│   └── simulator.py               # End-to-end pipeline & synchronized multi-technique comparison
│
├── experiments/                   # Empirical Benchmarking Suite
│   ├── experiment_runner.py       # Monte Carlo empirical trials
│   └── metrics.py                 # Statistical aggregation (clean separate from corrupted)
│
├── visualization/                 # The 4 Analytical Visualizations
│   ├── plot_results.py            # High-resolution (300 DPI) plotting engine
│   ├── detection_rate_by_error_type.png       # Graph 1: Detection Rate by Error Type & Technique
│   ├── detection_rate_vs_error_magnitude.png  # Graph 2: Detection Rate vs Error Magnitude
│   ├── processing_time_vs_data_size.png       # Graph 3: Processing Time vs Data Size
│   └── overhead_vs_data_size.png              # Graph 4: Transmission Overhead vs Data Size
│
├── experiment_results.csv         # Raw experimental Monte Carlo trials
├── metrics_results.csv            # Aggregated statistical performance indicators
├── main.py                        # Interactive console CLI with exactly 5 main menu options
└── README.md                      # Project manual, architecture & viva guide
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

## 4. Main Menu Overview (`main.py`)

When you run `python main.py`, the menu appears with exactly these five options:

```
========================================================================
     DATA COMMUNICATION AND COMPUTER NETWORKS (DCN) PROJECT
      ERROR GENERATION, DETECTION & ANALYSIS SYSTEM
========================================================================
  Current Session Data : 1011011011001100 (16 bits)
========================================================================
  1. Simulate Transmission
  2. Compare Detection Techniques
  3. View Algorithm Working
  4. Run Experiments and View Graphs
  5. Exit
  [C] Change Session Data
========================================================================
```

### Feature Details:

- **Session Data Reuse:**
  - Input data is configured once at startup (binary, ASCII text, or random bits) and stored in session state.
  - Automatically reused across Options 1, 2, and 3 without asking the user repeatedly.
  - A simple prompt (`Change data? [y/N]`) or pressing `[C]` allows updating session data anytime.

- **1. Simulate Transmission:**
  - Uses current session data.
  - User selects detection technique (**VRC / Parity**, **LRC**, **Checksum**, **CRC**).
  - User selects error model (**Clean**, **Single-bit**, **Multiple-bit**, **Burst**, **Manual**) and only the necessary parameters.
  - Displays the full **Sender** $\to$ **Channel** (with visual `^` pointers at error positions) $\to$ **Receiver** $\to$ **Final Verdict** pipeline.

- **2. Compare Detection Techniques:**
  - Uses current session data.
  - User specifies the error model only once (no preset fixed scenario lists).
  - Automatically evaluates **VRC / Parity**, **LRC**, **Checksum**, and **CRC** on identical payload error positions.
  - Displays a single comparative table showing Overhead (bits and %), Processing Time ($\mu s$), Detection Result, and Final Verdict.

- **3. View Algorithm Working:**
  - Displays step-by-step mathematical traces:
    - **VRC / Parity:** Shows 1s count, parity bit rule, and appended frame.
    - **LRC:** Shows 2D block grid, column-by-column 1s counts, and resulting LRC block check character.
    - **Checksum:** Shows word division, 1's complement summation, end-around carry wrapping, and bitwise NOT.
    - **CRC:** Shows generator polynomial, zero padding, full Modulo-2 XOR division trace, quotient, and FCS remainder.

- **4. Run Experiments and View Graphs:**
  - Allows configuration of payload sizes, error magnitudes, burst lengths, and trial counts.
  - Generates fresh datasets (`experiment_results.csv`, `metrics_results.csv`).
  - Keeps clean transmissions separate from corrupted trials.
  - Generates the 4 required analytical graphs directly from the latest data.

- **5. Exit:**
  - Terminates the application.

---

## 5. Analytical Visualizations Explained

| Chart File | Analytical Purpose | Key DCN Takeaway |
| :--- | :--- | :--- |
| **`detection_rate_by_error_type.png`** | Grouped bar chart comparing the 4 techniques across Single-bit, Multiple-bit, and Burst errors. | Highlights comparative robustness: CRC provides near 100% detection across all error types; VRC drops on multiple errors; LRC provides strong burst protection. |
| **`detection_rate_vs_error_magnitude.png`** | Evaluates detection probability as error count increases from 1 to 8 bits. | **Parity Oscillation:** VRC detects 100% of odd errors (1, 3, 5, 7) and 0% of even errors (2, 4, 6, 8) because $d_{min}=2$. LRC, Checksum, and CRC maintain high detection. |
| **`processing_time_vs_data_size.png`** | Compares execution latency in microseconds ($\mu s$) across payload sizes (32 to 1024 bits). | Demonstrates algorithm efficiency: VRC and Checksum require simple $O(N)$ operations, while CRC polynomial division incurs slightly higher processing time. |
| **`overhead_vs_data_size.png`** | Compares redundancy bit percentage as payload size grows from 32 to 1024 bits. | Demonstrates bandwidth trade-off: Redundancy percentage drops dramatically as payload grows ($O(1)$ redundant bits versus $O(N)$ payload). |

---

## 6. DCN Viva / Jury Question & Answer Guide

### Q1: Why does VRC (Single Parity) fail to detect two-bit errors?
> **Answer:** Parity check has a minimum Hamming distance of $d_{min} = 2$. It can only guarantee detection for $d_{min} - 1 = 1$ bit error. When an even number of bits (such as 2, 4, or 6) are inverted, the parity (evenness or oddness of 1s) remains unchanged, resulting in an undetected error.

### Q2: What is Longitudinal Redundancy Check (LRC) and how does it differ from VRC?
> **Answer:** In LRC, data is organized into blocks (rows), and parity is computed for each column across all rows to form an LRC block check byte. While VRC fails if two bits flip in the same character/row, LRC detects them because they affect different columns. LRC only fails if an even number of bit errors occur in the exact same column position across different rows.

### Q3: What is the weakness of the Internet Checksum?
> **Answer:** The Internet Checksum (RFC 1071) uses 1's complement addition with end-around carry. Its main vulnerability is **compensating errors**—if one bit is flipped from 0 to 1 and another bit in the same column in another word is flipped from 1 to 0, the sum remains identical, and the error goes undetected. It is also insensitive to transposition of whole words.

### Q4: What makes CRC the preferred error detection technique in Data Link protocols?
> **Answer:** CRC is based on polynomial modulo-2 arithmetic. If generator polynomial $G(x)$ of degree $r$ satisfies standard conditions:
> - It detects 100% of single-bit errors (if $G(x)$ has $\ge 2$ terms).
> - It detects 100% of double-bit errors (if $G(x)$ does not divide $x^k + 1$).
> - It detects 100% of odd-bit errors (if $G(x)$ contains $(x+1)$ as a factor).
> - It detects 100% of burst errors of length $L \le r$.
> - It is implemented efficiently in hardware using linear feedback shift registers (LFSRs).
