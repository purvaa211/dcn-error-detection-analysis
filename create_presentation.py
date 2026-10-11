"""Script to generate professional 16:9 PowerPoint Presentation for DCN Project.

Generates: DCN_Error_Detection_Project_Presentation.pptx
Includes:
- Academic Intro, Objectives, Methodology, System Architecture
- Error Models & Mathematical Principles of VRC, LRC, Checksum, CRC
- High-Resolution Embedded Graphs from visualization/
- Comparative Performance Matrix Table
- Conclusions & Application Domain Recommendations
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualization")
OUTPUT_PPTX = os.path.join(PROJECT_ROOT, "DCN_Error_Detection_Project_Presentation.pptx")

# Color Palette
DARK_NAVY = RGBColor(15, 23, 42)       # #0F172A
SLATE_GRAY = RGBColor(51, 65, 85)      # #334155
LIGHT_BG = RGBColor(248, 250, 252)     # #F8FAFC
CARD_BG = RGBColor(255, 255, 255)      # #FFFFFF
ACCENT_BLUE = RGBColor(37, 99, 235)    # #2563EB
EMERALD = RGBColor(22, 163, 74)        # #16A34A
CORAL_RED = RGBColor(225, 29, 72)      # #E11D48
TEXT_MUTED = RGBColor(100, 116, 139)   # #64748B
BORDER_COLOR = RGBColor(226, 232, 240) # #E2E8F0


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_header(slide, title_text, category_text="DCN PROJECT EVALUATION"):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.7))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = DARK_NAVY

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=BORDER_COLOR):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1)
        else:
            shape.line.fill.background()
        return shape

    # ==================================================================
    # SLIDE 1: TITLE SLIDE
    # ==================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = add_card(s1, Inches(0), Inches(0), Inches(13.333), Inches(7.5), bg_color=DARK_NAVY, border_color=None)

    # Accent decorative block
    dec = add_card(s1, Inches(0.8), Inches(1.2), Inches(3.2), Inches(0.36), bg_color=ACCENT_BLUE, border_color=None)
    tf_dec = dec.text_frame
    p_dec = tf_dec.paragraphs[0]
    p_dec.text = "DATA COMMUNICATION & NETWORKS"
    p_dec.font.size = Pt(10)
    p_dec.font.bold = True
    p_dec.font.color.rgb = RGBColor(255, 255, 255)
    p_dec.alignment = PP_ALIGN.CENTER

    tbox1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(11.5), Inches(2.2))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Experimental Analysis of Error Detection\nTechniques in Data Communication"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Comparative Diagnostic & Performance Evaluation of VRC, LRC, Internet Checksum, and CRC"
    p1_sub.font.size = Pt(18)
    p1_sub.font.color.rgb = RGBColor(148, 163, 184)
    p1_sub.space_before = Pt(16)

    # Author details card
    acard = add_card(s1, Inches(0.8), Inches(4.5), Inches(11.7), Inches(2.2), bg_color=SLATE_GRAY, border_color=None)
    atbox = s1.shapes.add_textbox(Inches(1.1), Inches(4.7), Inches(11.2), Inches(1.8))
    atf = atbox.text_frame
    
    pa1 = atf.paragraphs[0]
    pa1.text = "Author / Presenter: Purva Deshmukh"
    pa1.font.size = Pt(18)
    pa1.font.bold = True
    pa1.font.color.rgb = RGBColor(255, 255, 255)

    pa2 = atf.add_paragraph()
    pa2.text = "Project Scope: End-to-End Simulation, Dual Interactive Interfaces (CLI & Web), and Empirical Benchmarking"
    pa2.font.size = Pt(14)
    pa2.font.color.rgb = RGBColor(203, 213, 225)
    pa2.space_before = Pt(8)

    pa3 = atf.add_paragraph()
    pa3.text = "Techniques Analyzed: Vertical Redundancy Check (VRC) | Longitudinal Redundancy Check (LRC) | Internet Checksum | CRC-16 / CRC-32"
    pa3.font.size = Pt(13)
    pa3.font.color.rgb = RGBColor(148, 163, 184)
    pa3.space_before = Pt(6)

    # ==================================================================
    # SLIDE 2: INTRODUCTION & PROBLEM CONTEXT
    # ==================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Introduction: Transmission Impairments & Reliability", "1. PROJECT BACKGROUND")

    c1 = add_card(s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    t1 = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
    tf1 = t1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "Physical Channel Realities"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    points1 = [
        "Noise and Interference: Physical channels (copper, fiber, wireless) are prone to thermal noise, cross-talk, and impulse spikes.",
        "Bit Corruption: Transmitted electrical signals distort, flipping binary 1s to 0s and vice versa.",
        "Error Distribution Patterns: Real physical channels produce single-bit flips, random multi-bit noise, and contiguous burst errors.",
        "Data Link Layer Obligation: Packets cannot be safely delivered to upper protocol layers without rigorous frame integrity verification."
    ]
    for pt in points1:
        p = tf1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    c2 = add_card(s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    t2 = s2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf2 = t2.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "The Engineering Trade-Off Dilemma"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    points2 = [
        "Detection Power vs. Bandwidth: Adding redundancy bits increases channel overhead and reduces effective payload throughput.",
        "Computational Complexity: Simple parity calculation runs in O(1) CPU time, whereas polynomial division incurs significant processing latency.",
        "Algorithmic Blind Spots: Simple algorithms fail on specific multi-bit or burst patterns (e.g. even parity blind spots).",
        "Project Goal: Rigorously evaluate and compare all four canonical error-detection mechanisms across identical payloads and channel conditions."
    ]
    for pt in points2:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 3: OBJECTIVES OF THE SYSTEM
    # ==================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "System Objectives & Engineering Requirements", "2. PROJECT OBJECTIVES")

    obj_cards = [
        ("End-to-End 3-Stage Pipeline", "Model realistic Sender (Transmitter Encoding), Physical Channel (Noise/Corruption), and Receiver (Integrity Verification) without external black-box libraries.", Inches(0.8), Inches(1.6)),
        ("Four Canonical Techniques", "Implement native mathematical logic for VRC (Parity), LRC (2D block matrix), 1's Complement Internet Checksum, and CRC (Modulo-2 polynomial division).", Inches(6.8), Inches(1.6)),
        ("Five Physical Error Models", "Support clean transmission, single-bit flips, independent multiple-bit flips, burst errors, and manual bit-index injection for targeted stress testing.", Inches(0.8), Inches(4.3)),
        ("Dual Interface & Benchmarking", "Provide an interactive CLI and modern browser web interface backed by empirical batch experiments generating 4 publication-quality analytical graphs.", Inches(6.8), Inches(4.3))
    ]

    for title, desc, left, top in obj_cards:
        add_card(s3, left, top, Inches(5.7), Inches(2.5))
        tbox = s3.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), Inches(5.3), Inches(2.1))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(13.5)
        p_desc.font.color.rgb = SLATE_GRAY
        p_desc.space_before = Pt(8)

    # ==================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE
    # ==================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "System Architecture: 3-Tier Layered Design", "3. ARCHITECTURE & WORKFLOW")

    tier_cards = [
        ("Tier 1: Core Mathematical Algorithms", "Location: algorithms/\n• parity.py: VRC (Even/Odd schemes)\n• lrc.py: Block matrix column-wise XOR\n• checksum.py: 1's complement addition with end-around carry\n• crc.py: Modulo-2 polynomial division (CRC-8, CRC-16, CRC-32)\nZero third-party algorithm dependencies.", Inches(0.8), Inches(1.6)),
        ("Tier 2: Physical Channel & Simulation", "Location: simulation/ & experiments/\n• error_generator.py: 5 physical noise injection models\n• simulator.py: End-to-end 3-stage pipeline coordinator\n• experiment_runner.py: Multi-threaded batch benchmarking\n• metrics.py: Data aggregation with clean/corrupted separation", Inches(4.8), Inches(1.6)),
        ("Tier 3: Dual Presentation Layer", "Location: main.py, web/, web_integration/\n• Terminal CLI: Interactive console with session data retention\n• Web Application: Modern Flask + HTML5/CSS3/JS UI\n• web_integration: Adapter layer preserving original backend code intact\n• Staging Manager: Prevents unexpected file overwrite.", Inches(8.8), Inches(1.6))
    ]

    for title, desc, left, top in tier_cards:
        add_card(s4, left, top, Inches(3.7), Inches(5.2))
        tbox = s4.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), Inches(3.3), Inches(4.8))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = DARK_NAVY

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12.5)
        p_desc.font.color.rgb = SLATE_GRAY
        p_desc.space_before = Pt(12)

    # ==================================================================
    # SLIDE 5: 3-STAGE TRANSMISSION PIPELINE
    # ==================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Methodology: End-to-End Transmission Pipeline", "4. METHODOLOGY")

    pipeline_steps = [
        ("Stage 1: Transmitter (Sender)", "Input Payload: Binary bit sequence (e.g. 10110011)\n1. Encode payload using selected technique.\n2. Compute redundancy / check bits (r bits).\n3. Append check bits to generate Protected Frame (n = k + r bits).\n4. Record encoding latency (T_enc).", Inches(0.8)),
        ("Stage 2: Physical Channel", "Channel Noise Simulation:\n1. Apply selected error model (Single, Multiple, Burst, Manual).\n2. Flip binary bits at designated channel indices (0 -> 1, 1 -> 0).\n3. Produce Received / Corrupted Frame.\n4. Track exact corrupted bit indices.", Inches(4.8)),
        ("Stage 3: Receiver Verification", "Integrity Verification:\n1. Extract payload and redundant check bits.\n2. Recompute check sequence on received payload.\n3. Compare received vs expected check sequence.\n4. Emit binary verdict: ERROR DETECTED vs ERROR MISSED.", Inches(8.8))
    ]

    for title, desc, left in pipeline_steps:
        add_card(s5, left, Inches(1.6), Inches(3.7), Inches(5.2))
        tbox = s5.shapes.add_textbox(left + Inches(0.2), Inches(1.8), Inches(3.3), Inches(4.8))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = SLATE_GRAY
        p_desc.space_before = Pt(12)

    # ==================================================================
    # SLIDE 6: ERROR MODELS
    # ==================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Physical Error Models Implemented", "5. ERROR GENERATION LOGIC")

    err_models = [
        ("1. Clean Transmission", "No bits altered (Channel Noise = 0). Validates that legitimate clean frames pass verification without false alarms.", Inches(0.8), Inches(1.6), Inches(5.7)),
        ("2. Single-Bit Error", "Exactly one bit flipped at a random or specified index. Corresponds to isolated white noise or thermal fluctuation in copper wires.", Inches(6.8), Inches(1.6), Inches(5.7)),
        ("3. Multiple-Bit Errors", "m independent bit flips scattered across payload. Crucial for exposing the fundamental limitations of single parity checks.", Inches(0.8), Inches(3.4), Inches(5.7)),
        ("4. Burst Error", "A contiguous sequence of bits of length B, where the first and last bits are guaranteed flipped, and intermediate bits flip with probability p=0.5.", Inches(6.8), Inches(3.4), Inches(5.7)),
        ("5. Manual Error Injection", "User or tester provides exact comma-separated bit indices to flip. Enables reproducible scenario testing (e.g. flipping identical columns in LRC).", Inches(0.8), Inches(5.2), Inches(11.7))
    ]

    for title, desc, left, top, width in err_models:
        add_card(s6, left, top, width, Inches(1.5))
        tbox = s6.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(1.2))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = DARK_NAVY

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = SLATE_GRAY
        p_desc.space_before = Pt(4)

    # ==================================================================
    # SLIDE 7: MATHEMATICAL WORKING OF DETECTION TECHNIQUES
    # ==================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Mathematical Principles of the 4 Detection Techniques", "6. ALGORITHMIC WORKING")

    algo_cards = [
        ("Vertical Redundancy Check (VRC)", "• Mechanism: Appends 1 parity bit to ensure even number of 1s in the frame.\n• Mathematics: P = b_0 ⊕ b_1 ⊕ ... ⊕ b_{k-1}\n• Detection: Catches 100% of odd-count bit errors.\n• Limitation: 0% detection on even errors (d_min = 2).", Inches(0.8), Inches(1.6)),
        ("Longitudinal Redundancy Check (LRC)", "• Mechanism: Organizes payload into 2D matrix of 8-bit blocks; calculates column-wise parity.\n• Mathematics: LRC_j = ⊕_{i=1}^m Block_{i,j}\n• Detection: Catches burst errors across blocks.\n• Limitation: Misses 2-bit flips in the identical column.", Inches(6.8), Inches(1.6)),
        ("Internet Checksum (RFC 1071)", "• Mechanism: Divides payload into 8-bit/16-bit words; sums using 1's complement arithmetic.\n• Mathematics: Checksum = ~(Sum + End-around Carries)\n• Detection: Receiver sum of payload + checksum must equal all 1s (0xFF).\n• Feature: Low CPU overhead, used in TCP/IP/UDP.", Inches(0.8), Inches(4.3)),
        ("Cyclic Redundancy Check (CRC)", "• Mechanism: Modulo-2 binary polynomial division using XOR arithmetic.\n• Mathematics: T(x) = D(x) · x^r + R(x), where R(x) = (D(x) · x^r) mod G(x)\n• Polynomials: CRC-8 (100000111), CRC-16 (IBM/CCITT), CRC-32 (IEEE 802.3).\n• Detection: Mathematically guarantees detection of all burst errors ≤ r bits.", Inches(6.8), Inches(4.3))
    ]

    for title, desc, left, top in algo_cards:
        add_card(s7, left, top, Inches(5.7), Inches(2.5))
        tbox = s7.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), Inches(5.3), Inches(2.1))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12.5)
        p_desc.font.color.rgb = SLATE_GRAY
        p_desc.space_before = Pt(6)

    # ==================================================================
    # SLIDE 8: DUAL INTERFACE IMPLEMENTATION
    # ==================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Implementation: Terminal CLI & Web Interface", "7. IMPLEMENTATION")

    c1 = add_card(s8, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    t1 = s8.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Interactive Terminal CLI (main.py)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    cli_pts = [
        "1. Simulate Data Transmission: Interactive parameter selection with Sender -> Channel -> Receiver breakdown.",
        "2. Compare Error Detection Techniques: Runs VRC, LRC, Checksum, and CRC under synchronized payload error positions.",
        "3. View Algorithm Working: Full step-by-step mathematical trace generation (matrix grids, XOR steps).",
        "4. Run Experiments and View Graphs: Benchmark generator with temporary staging & confirmation workflow.",
        "5. Session Persistence: Data entered once is reused across all menus without repeated prompting."
    ]
    for pt in cli_pts:
        p = tf1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(8)

    c2 = add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    t2 = s8.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Browser Web Application (web/ + web_integration/)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    web_pts = [
        "Zero Backend Modification: Invokes native Python backend directly via typed adapter layer.",
        "Visual Bit Highlighting: Corrupted bits are highlighted in red inline for intuitive visual comparison.",
        "Tabbed Navigation: Four dedicated modules matching the terminal operations.",
        "Staging Protection: Staged runs allow user to preview newly generated graphs before applying to project baseline.",
        "One-Click Launcher: start_website.bat auto-binds to 0.0.0.0 and launches browser to http://127.0.0.1:5000."
    ]
    for pt in web_pts:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(8)

    # ==================================================================
    # SLIDE 9: RESULT 1 - DETECTION RATE BY ERROR TYPE
    # ==================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Analytical Graph 1: Detection Rate by Error Type", "8. RESULTS & PERFORMANCE")

    img_p1 = os.path.join(VIZ_DIR, "detection_rate_by_error_type.png")
    if os.path.exists(img_p1):
        s9.shapes.add_picture(img_p1, Inches(0.8), Inches(1.6), width=Inches(6.2))

    c_r1 = add_card(s9, Inches(7.3), Inches(1.6), Inches(5.2), Inches(5.2))
    t_r1 = s9.shapes.add_textbox(Inches(7.5), Inches(1.8), Inches(4.8), Inches(4.8))
    tf_r1 = t_r1.text_frame
    tf_r1.word_wrap = True
    p = tf_r1.paragraphs[0]
    p.text = "Empirical Insights"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    r1_pts = [
        "Single-Bit Errors: All 4 techniques achieve 100% detection rate. Single-bit errors are completely caught by any standard parity bit or checksum.",
        "Multiple-Bit Errors: VRC detection rate drops drastically (~50%) because any even number of corrupted bits preserves the original parity bit.",
        "Burst Errors: CRC and LRC demonstrate superior resilience, catching 100% of burst spans within their design parameters.",
        "Checksum Behavior: Catches >90% of random multiple-bit errors, but misses compensating errors where carry bits cancel out."
    ]
    for pt in r1_pts:
        p = tf_r1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 10: RESULT 2 - DETECTION RATE VS ERROR MAGNITUDE
    # ==================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Analytical Graph 2: Detection Rate vs. Error Magnitude", "9. RESULTS & PERFORMANCE")

    img_p2 = os.path.join(VIZ_DIR, "detection_rate_vs_error_magnitude.png")
    if os.path.exists(img_p2):
        s10.shapes.add_picture(img_p2, Inches(0.8), Inches(1.6), width=Inches(6.2))

    c_r2 = add_card(s10, Inches(7.3), Inches(1.6), Inches(5.2), Inches(5.2))
    t_r2 = s10.shapes.add_textbox(Inches(7.5), Inches(1.8), Inches(4.8), Inches(4.8))
    tf_r2 = t_r2.text_frame
    tf_r2.word_wrap = True
    p = tf_r2.paragraphs[0]
    p.text = "The Parity Paradox Demonstrated"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    r2_pts = [
        "Oscillating Parity Curve: Graph clearly proves the textbook parity limitation:\n- Odd bit errors (1, 3, 5): 100% Detection\n- Even bit errors (2, 4, 8): Exactly 0% Detection",
        "LRC 2D Robustness: Because bits are distributed across 8 columns, LRC detects even errors provided they do not occur in the exact same column.",
        "CRC Immunity: CRC maintains a flat 100% line across almost all error magnitudes for standard payloads.",
        "Engineering Significance: Proves why simple parity is unsuitable for noisy physical media without higher-order checks."
    ]
    for pt in r2_pts:
        p = tf_r2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 11: RESULT 3 - PROCESSING LATENCY VS DATA SIZE
    # ==================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Analytical Graph 3: Processing Latency vs. Data Size", "10. RESULTS & PERFORMANCE")

    img_p3 = os.path.join(VIZ_DIR, "processing_time_vs_data_size.png")
    if os.path.exists(img_p3):
        s11.shapes.add_picture(img_p3, Inches(0.8), Inches(1.6), width=Inches(6.2))

    c_r3 = add_card(s11, Inches(7.3), Inches(1.6), Inches(5.2), Inches(5.2))
    t_r3 = s11.shapes.add_textbox(Inches(7.5), Inches(1.8), Inches(4.8), Inches(4.8))
    tf_r3 = t_r3.text_frame
    tf_r3.word_wrap = True
    p = tf_r3.paragraphs[0]
    p.text = "Computational Complexity"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    r3_pts = [
        "Linear Growth: All four techniques scale linearly O(N) with payload size, but with substantially different slope coefficients.",
        "VRC Latency: Minimal CPU time (single bitwise count/accumulation), making it ideal for low-power microcontroller links.",
        "Internet Checksum: Highly optimized in software due to native 8/16-bit integer ALU register additions.",
        "CRC Latency: Higher computational overhead due to modulo-2 polynomial division steps; modern NICs offload CRC to dedicated hardware silicon."
    ]
    for pt in r3_pts:
        p = tf_r3.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 12: RESULT 4 - TRANSMISSION OVERHEAD VS DATA SIZE
    # ==================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Analytical Graph 4: Transmission Overhead vs. Data Size", "11. RESULTS & PERFORMANCE")

    img_p4 = os.path.join(VIZ_DIR, "overhead_vs_data_size.png")
    if os.path.exists(img_p4):
        s12.shapes.add_picture(img_p4, Inches(0.8), Inches(1.6), width=Inches(6.2))

    c_r4 = add_card(s12, Inches(7.3), Inches(1.6), Inches(5.2), Inches(5.2))
    t_r4 = s12.shapes.add_textbox(Inches(7.5), Inches(1.8), Inches(4.8), Inches(4.8))
    tf_r4 = t_r4.text_frame
    tf_r4.word_wrap = True
    p = tf_r4.paragraphs[0]
    p.text = "Bandwidth Utilization Penalty"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    r4_pts = [
        "Diminishing Overhead Ratio: Fixed-width check codes (VRC: 1 bit, CRC-16: 16 bits, Checksum: 8 bits) decrease in percentage overhead as payload grows.",
        "Short Frame Penalty: At 32-bit payload, CRC-16 incurs a 50% bandwidth penalty; at 512 bits, overhead drops to just 3.125%.",
        "LRC Block-Scaling: LRC requires an 8-bit check block, maintaining moderate overhead across varying data sizes.",
        "Protocol Design Rule: For tiny payloads (e.g. sensor telemetry), lightweight checksums or VRC save channel airtime; for MTU-sized packets (1500 bytes), CRC overhead is negligible (<0.2%)."
    ]
    for pt in r4_pts:
        p = tf_r4.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 13: COMPARATIVE SUMMARY MATRIX TABLE
    # ==================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Comprehensive Comparative Matrix", "12. COMPARATIVE EVALUATION")

    rows, cols = 5, 7
    table_shape = s13.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    table = table_shape.table

    headers = ["Technique", "Redundancy (Bits)", "CPU Cost", "Single-Bit", "Even-Bit", "Burst Errors", "Primary Real-World Use"]
    data = [
        ["VRC / Parity", "1 bit", "Minimal (O(1))", "100%", "0% (Fails)", "Poor", "Async Serial, ASCII, RAM parity"],
        ["LRC", "8 bits (block)", "Low (O(N))", "100%", "Good*", "Moderate", "Magnetic tape, ISO 7816 Smart Cards"],
        ["Checksum", "8 / 16 bits", "Low (O(N))", "100%", "High (~90%)", "Good", "TCP, UDP, IP headers (Transport Layer)"],
        ["CRC-16 / 32", "16 / 32 bits", "Moderate (Div)", "100%", "100%", "Guaranteed*", "Ethernet, Wi-Fi 802.11, HDLC, SATA"]
    ]

    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER

    for row_idx, row_data in enumerate(data):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(241, 245, 249) if row_idx % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.font.size = Pt(11)
            p.font.color.rgb = DARK_NAVY
            if col_idx in (0, 6):
                p.alignment = PP_ALIGN.LEFT
            else:
                p.alignment = PP_ALIGN.CENTER

    # ==================================================================
    # SLIDE 14: CONCLUSION & RECOMMENDATIONS
    # ==================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Conclusion & Engineering Recommendations", "13. CONCLUSION")

    c1 = add_card(s14, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    t1 = s14.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Key Takeaways"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_NAVY

    conc_pts = [
        "1. No Universal Solution: Error detection selection is an explicit engineering trade-off between channel error characteristics, bandwidth penalty, and computational latency.",
        "2. CRC Dominance at Data Link: CRC-16 and CRC-32 remain the undisputed standard for physical and data link layers due to mathematical guarantees against burst and multi-bit errors.",
        "3. Software Checksum Dominance at Transport: Internet Checksum remains optimal for host software TCP/IP stacks because 1's complement summation executes in ALU integer units without division overhead.",
        "4. Modular Dual-Interface Success: The architecture cleanly decouples the mathematical backend from both the CLI and modern Flask web interface."
    ]
    for pt in conc_pts:
        p = tf1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    c2 = add_card(s14, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    t2 = s14.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Future Scope & Extensions"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    fut_pts = [
        "Error Correction Integration: Extend the simulation pipeline from detection-only to forward error correction (FEC) using Hamming Codes (7,4) and Reed-Solomon.",
        "Hardware Emulation: Implement lookup table (LUT) accelerated CRC algorithms to compare software bit-by-bit vs table-driven division speedups.",
        "Real-World Noise Modeling: Integrate statistical Gilbert-Elliott burst channel Markov models to simulate realistic fading wireless links.",
        "Automated ARQ Simulation: Implement Automatic Repeat reQuest (Stop-and-Wait, Go-Back-N, Selective Repeat) over detected frame corruptions."
    ]
    for pt in fut_pts:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = SLATE_GRAY
        p.space_before = Pt(10)

    # ==================================================================
    # SLIDE 15: Q&A / CLOSING
    # ==================================================================
    s15 = prs.slides.add_slide(blank_layout)
    bg15 = add_card(s15, Inches(0), Inches(0), Inches(13.333), Inches(7.5), bg_color=DARK_NAVY, border_color=None)

    tbox15 = s15.shapes.add_textbox(Inches(1.5), Inches(2.2), Inches(10.3), Inches(3.2))
    tf15 = tbox15.text_frame
    tf15.word_wrap = True
    p15 = tf15.paragraphs[0]
    p15.text = "Thank You!"
    p15.font.size = Pt(46)
    p15.font.bold = True
    p15.font.color.rgb = RGBColor(255, 255, 255)
    p15.alignment = PP_ALIGN.CENTER

    p15_sub = tf15.add_paragraph()
    p15_sub.text = "Questions & Jury Discussion"
    p15_sub.font.size = Pt(22)
    p15_sub.font.color.rgb = ACCENT_BLUE
    p15_sub.alignment = PP_ALIGN.CENTER
    p15_sub.space_before = Pt(14)

    p15_repo = tf15.add_paragraph()
    p15_repo.text = "GitHub Repository: https://github.com/purvaa211/dcn-error-detection-analysis\nProject: DCN Error Generation, Detection & Comparative Analysis"
    p15_repo.font.size = Pt(14)
    p15_repo.font.color.rgb = RGBColor(148, 163, 184)
    p15_repo.alignment = PP_ALIGN.CENTER
    p15_repo.space_before = Pt(20)

    prs.save(OUTPUT_PPTX)
    print(f"Successfully generated PowerPoint presentation with {len(prs.slides)} slides at: {OUTPUT_PPTX}")


if __name__ == "__main__":
    create_deck()
