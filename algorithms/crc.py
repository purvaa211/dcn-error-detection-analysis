"""Cyclic Redundancy Check (CRC) Algorithm.

Implements polynomial modulo-2 arithmetic (GF(2) polynomial division using bitwise XOR).
CRC is widely used in data-link and physical layer protocols (Ethernet, Wi-Fi, USB, HDLC, Bluetooth).

Key Standard Polynomials:
- CRC-8:        x^8 + x^2 + x + 1                 (100000111)       [ATM, SMBus]
- CRC-16-CCITT: x^16 + x^12 + x^5 + 1             (10001000000100001)[HDLC, Bluetooth]
- CRC-16-ANSI:  x^16 + x^15 + x^2 + 1             (11000000000000101)[USB, Modbus]
- CRC-32:       IEEE 802.3 Ethernet polynomial

DCN Mathematical Capabilities:
- Detects 100% of single-bit errors (if G(x) has >= 2 terms).
- Detects 100% of two isolated single-bit errors (if G(x) does not divide x^k + 1).
- Detects 100% of odd numbers of bit errors (if G(x) contains (x + 1) factor).
- Detects 100% of burst errors of length L <= r (where r = degree of G(x)).
- Detects 1 - (1/2)^(r-1) of burst errors of length L = r + 1 (99.2% for CRC-8, 99.997% for CRC-16).
- Detects 1 - (1/2)^r of burst errors of length L > r + 1.
"""

from typing import Tuple, Dict, Any, List, Optional

CRC_POLYNOMIALS = {
    "CRC-8": {
        "generator": "100000111",
        "polynomial": "x^8 + x^2 + x + 1",
        "standard": "ATM / SMBus"
    },
    "CRC-16-CCITT": {
        "generator": "10001000000100001",
        "polynomial": "x^16 + x^12 + x^5 + 1",
        "standard": "HDLC, X.25, Bluetooth"
    },
    "CRC-16-ANSI": {
        "generator": "11000000000000101",
        "polynomial": "x^16 + x^15 + x^2 + 1",
        "standard": "USB, Modbus"
    },
    "CRC-32": {
        "generator": "100000100110000010001110110110111",
        "polynomial": "x^32 + x^26 + x^23 + ... + 1",
        "standard": "IEEE 802.3 Ethernet, ZIP"
    },
    "CRC-4-ITU": {
        "generator": "10011",
        "polynomial": "x^4 + x + 1",
        "standard": "ITU-T G.704"
    }
}


def resolve_generator(gen_or_name: str) -> str:
    """Resolve a generator name (e.g. 'CRC-8') or return binary generator string."""
    gen_upper = gen_or_name.upper()
    if gen_upper in CRC_POLYNOMIALS:
        return CRC_POLYNOMIALS[gen_upper]["generator"]
    for key, val in CRC_POLYNOMIALS.items():
        if key.replace("-", "").upper() == gen_upper.replace("-", ""):
            return val["generator"]
    if all(c in "01" for c in gen_or_name) and len(gen_or_name) >= 2:
        return gen_or_name
    raise ValueError(f"Invalid CRC generator: '{gen_or_name}'. Use standard name (CRC-8, CRC-16-CCITT) or binary string.")


def modulo2_divide(
    dividend: str,
    generator: str,
    track_steps: bool = False
) -> Tuple[str, str, List[Dict[str, str]]]:
    """Perform Modulo-2 binary division (GF(2) XOR arithmetic).

    Args:
        dividend: Binary string to divide.
        generator: Divisor binary polynomial.
        track_steps: Whether to record step-by-step XOR divisions.

    Returns:
        tuple (quotient, remainder, step_records)
    """
    g_len = len(generator)
    degree = g_len - 1
    working = list(dividend)
    quotient_bits = []
    steps = []

    # Number of division steps
    steps_count = len(dividend) - degree

    for i in range(steps_count):
        if working[i] == "1":
            quotient_bits.append("1")
            prev_chunk = "".join(working[i:i + g_len])
            for j in range(g_len):
                working[i + j] = str(int(working[i + j]) ^ int(generator[j]))
            if track_steps:
                steps.append({
                    "index": i,
                    "quotient_bit": "1",
                    "before_xor": prev_chunk,
                    "generator": generator,
                    "after_xor": "".join(working[i:i + g_len])
                })
        else:
            quotient_bits.append("0")
            if track_steps:
                steps.append({
                    "index": i,
                    "quotient_bit": "0",
                    "before_xor": "".join(working[i:i + g_len]),
                    "generator": "0" * g_len,
                    "after_xor": "".join(working[i:i + g_len])
                })

    quotient = "".join(quotient_bits)
    remainder = "".join(working[-degree:]) if degree > 0 else ""
    return quotient, remainder, steps


def crc_encode(
    data: str,
    generator: str = "100000111"
) -> str:
    """Encode binary data using CRC modulo-2 division.

    Args:
        data: Binary payload string.
        generator: Binary generator string or preset name (default: '100000111' / CRC-8).

    Returns:
        Transmitted frame (data + remainder).
    """
    gen = resolve_generator(generator)
    degree = len(gen) - 1
    padded_data = data + ("0" * degree)

    _, remainder, _ = modulo2_divide(padded_data, gen, track_steps=False)
    return data + remainder


def crc_check(
    frame: str,
    generator: str = "100000111"
) -> bool:
    """Verify frame integrity using CRC check (backward compatible).

    Returns:
        True if remainder is all zeros (no error detected), False otherwise.
    """
    gen = resolve_generator(generator)
    degree = len(gen) - 1
    if len(frame) < len(gen):
        return False

    _, remainder, _ = modulo2_divide(frame, gen, track_steps=False)
    zero_syndrome = "0" * degree
    return remainder == zero_syndrome


def crc_check_detailed(
    frame: str,
    generator: str = "100000111",
    include_steps: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """Detailed CRC verification with diagnostics for presentation.

    Args:
        frame: Received frame string.
        generator: Generator polynomial.
        include_steps: Whether to compute division trace.

    Returns:
        tuple (is_valid, details_dict)
    """
    gen = resolve_generator(generator)
    degree = len(gen) - 1
    if len(frame) < len(gen):
        return False, {
            "is_valid": False,
            "error": "Frame shorter than generator polynomial."
        }

    quotient, remainder, steps = modulo2_divide(frame, gen, track_steps=include_steps)
    zero_syndrome = "0" * degree
    is_valid = (remainder == zero_syndrome)

    data_payload = frame[:-degree] if degree > 0 else frame
    received_crc = frame[-degree:] if degree > 0 else ""

    details = {
        "generator": gen,
        "degree": degree,
        "received_data": data_payload,
        "received_crc": received_crc,
        "syndrome_remainder": remainder,
        "is_valid": is_valid,
        "quotient": quotient,
        "division_steps": steps if include_steps else []
    }

    return is_valid, details


def format_crc_working(data: str, generator: str = "100000111") -> str:
    """Format step-by-step CRC Modulo-2 polynomial division for educational display."""
    gen = resolve_generator(generator)
    degree = len(gen) - 1
    padded_data = data + ("0" * degree)
    quotient, remainder, steps = modulo2_divide(padded_data, gen, track_steps=True)

    lines = [
        "=" * 60,
        " CYCLIC REDUNDANCY CHECK (CRC) STEP-BY-STEP CALCULATION",
        "=" * 60,
        f" Original Data Bits   : {data} ({len(data)} bits)",
        f" Generator Polynomial : {gen} (Degree = {degree})",
        f" Padded Dividend (D+0): {padded_data} (Appended {degree} zeros)",
        "-" * 60,
        " Modulo-2 Division (XOR arithmetic):"
    ]

    for s in steps:
        idx = s["index"] + 1
        q_bit = s["quotient_bit"]
        b_xor = s["before_xor"]
        g_val = s["generator"]
        a_xor = s["after_xor"]
        lines.append(f"  Step {idx:<2}: Dividend chunk = {b_xor} | Quotient bit = {q_bit}")
        lines.append(f"           XOR with Divisor = {g_val} -> Remainder chunk = {a_xor}")

    lines.append("-" * 60)
    lines.append(f" Complete Quotient   : {quotient}")
    lines.append(f" Final Remainder/FCS : {remainder} ({len(remainder)} bits)")
    lines.append(f" Transmitted Frame   : {data} [FCS: {remainder}] -> {data + remainder}")
    lines.append("=" * 60)

    return "\n".join(lines)