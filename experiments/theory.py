"""Theoretical Detection Bounds for DCN Error Detection Schemes.

Provides analytical, closed-form detection probability limits derived from
algebraic coding theory and networking standards (Tanenbaum, Forouzan, RFC 1071).

Techniques covered:
- Parity Check (VRC):
    Single-bit error -> 1.0 (100%)
    Odd numbers of bit flips -> 1.0 (100%)
    Even numbers of bit flips -> 0.0 (0%, parity invariant, d_min = 2)
- Cyclic Redundancy Check (CRC-8, r = 8):
    Generator G(x) = x^8 + x^2 + x + 1 = (x + 1)(x^7 + x^6 + x^5 + x^4 + x^3 + x^2 + 1)
    Single-bit errors -> 1.0 (100%)
    All odd numbers of bit flips -> 1.0 (100%, since (x+1) divides G(x))
    Bursts of length L <= r (<= 8 bits) -> 1.0 (100%)
    Bursts of length L = r + 1 (9 bits) -> 1 - 2^-(r-1) = 1 - 2^-7 = 99.21875%
    Bursts of length L > r + 1 (e.g. 16 bits) -> 1 - 2^-r = 1 - 2^-8 = 99.609375%
- LRC & Checksum:
    Single-bit error -> 1.0 (100%)
    Multi-bit / burst errors -> None (depend on column collisions / compensating carries)
"""

from typing import Dict, Any, Optional, Union


def get_theoretical_detection(
    technique: str,
    error_type: str,
    error_param: Union[int, float, str, Any] = 1,
    crc_degree: int = 8
) -> Dict[str, Any]:
    """Retrieve theoretical detection probability and explanatory textbook rationale.

    Args:
        technique: Name of error detection technique (e.g. 'VRC / Parity', 'CRC', 'LRC', 'Checksum').
        error_type: Error category ('clean', 'single', 'multiple', 'burst', etc.).
        error_param: Numerical parameter (number of bit errors, burst length, etc.).
        crc_degree: Degree of generator polynomial r (default: 8 for CRC-8).

    Returns:
        Dict with keys:
            'value': float detection rate [0.0, 1.0] or None if no closed form exists.
            'note': String explanation of the mathematical derivation or blind spot.
    """
    tech = (technique or "").strip().lower()
    err = (error_type or "").strip().lower()

    # Parse parameter as integer if possible
    param_int: Optional[int] = None
    try:
        if isinstance(error_param, (int, float)):
            param_int = int(error_param)
        elif isinstance(error_param, str) and error_param.strip().isdigit():
            param_int = int(error_param.strip())
    except (ValueError, TypeError):
        param_int = None

    # 1. Clean transmission
    if err in ("clean", "none", "0") or param_int == 0:
        return {
            "value": None,
            "note": "Clean transmission (0 bit errors injected; detection rate not applicable)"
        }

    # 2. VRC / Parity Check
    if "parity" in tech or "vrc" in tech:
        if err == "single":
            return {
                "value": 1.0,
                "note": "All single-bit errors invert parity (100% guaranteed)"
            }
        elif err == "multiple":
            if param_int is not None:
                if param_int % 2 == 1:
                    return {
                        "value": 1.0,
                        "note": f"Odd number of bit flips ({param_int}) always inverts parity (100% guaranteed)"
                    }
                else:
                    return {
                        "value": 0.0,
                        "note": f"Even number of bit flips ({param_int}) leaves parity invariant (0% detected; d_min = 2)"
                    }
            return {
                "value": None,
                "note": "Multi-bit parity detection depends on whether flip count is odd or even"
            }
        elif err == "burst":
            if param_int == 2:
                return {
                    "value": 0.0,
                    "note": "Burst of length 2 flips exactly both endpoints (even count = 2 -> 0% detected)"
                }
            return {
                "value": None,
                "note": "Burst introduces stochastic mixture of odd and even flips (~50%)"
            }
        return {
            "value": None,
            "note": "No closed-form guarantee for general error pattern"
        }

    # 3. Cyclic Redundancy Check (CRC)
    elif "crc" in tech:
        r = crc_degree
        if err == "single":
            return {
                "value": 1.0,
                "note": f"All single-bit errors detected (G(x) has >= 2 non-zero terms)"
            }
        elif err == "multiple":
            if param_int is not None:
                if param_int % 2 == 1:
                    return {
                        "value": 1.0,
                        "note": f"All odd-bit errors ({param_int}) detected ((x + 1) divides G(x))"
                    }
                else:
                    return {
                        "value": None,
                        "note": f"Even errors ({param_int}) depend on polynomial period and bit spacing"
                    }
            return {
                "value": None,
                "note": "Detection depends on whether error polynomial E(x) is a multiple of G(x)"
            }
        elif err in ("burst", "consecutive_burst"):
            if param_int is not None:
                if param_int <= r:
                    return {
                        "value": 1.0,
                        "note": f"All bursts of length <= r ({param_int} <= {r}) guaranteed detected (100%)"
                    }
                elif param_int == r + 1:
                    val = 1.0 - (2.0 ** -(r - 1))
                    return {
                        "value": val,
                        "note": f"Burst length r+1 ({param_int}): detection probability is 1 - 2^-(r-1) ({val*100:.2f}%)"
                    }
                else:
                    val = 1.0 - (2.0 ** -r)
                    return {
                        "value": val,
                        "note": f"Long burst ({param_int} > r+1): detection probability is 1 - 2^-r (approx {val*100:.2f}%)"
                    }
            return {
                "value": None,
                "note": "Burst detection bound requires burst length specification"
            }
        return {
            "value": None,
            "note": "No closed-form guarantee for general error pattern"
        }

    # 4. Longitudinal Redundancy Check (LRC)
    elif "lrc" in tech:
        if err == "single":
            return {
                "value": 1.0,
                "note": "All single-bit errors alter column parity (100% guaranteed)"
            }
        return {
            "value": None,
            "note": "Multi-bit and burst detection depends on column alignment; no general closed form"
        }

    # 5. Internet Checksum
    elif "checksum" in tech:
        if err == "single":
            return {
                "value": 1.0,
                "note": "All single-bit errors alter 1's complement word sum (100% guaranteed)"
            }
        return {
            "value": None,
            "note": "Compensating errors and carry wrapping prevent general closed-form rate"
        }

    # Fallback
    return {
        "value": None,
        "note": "No established theoretical closed form"
    }
