"""Backend Adapter for DCN Error Detection System.

Directly invokes the original untouched Python backend functions without modifying
or duplicating any algorithm or simulation logic.
"""

import sys
import os
import random
from typing import Dict, Any, List, Optional, Tuple, Union

# Ensure the root project directory is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithms.parity import (
    add_vrc,
    check_vrc,
    format_vrc_working
)
from algorithms.lrc import (
    add_lrc,
    check_lrc,
    calculate_lrc,
    format_lrc_working
)
from algorithms.checksum import (
    add_checksum,
    verify_checksum_detailed,
    format_checksum_working
)
from algorithms.crc import (
    crc_encode,
    crc_check_detailed,
    format_crc_working,
    CRC_POLYNOMIALS
)
from simulation.simulator import (
    simulate,
    compare_all_techniques
)


def validate_binary_string(data: str) -> Tuple[bool, str]:
    """Validate that the string is a non-empty sequence of binary bits (0 or 1)."""
    cleaned = (data or "").strip()
    if not cleaned:
        return False, "Input data cannot be empty."
    if not all(c in "01" for c in cleaned):
        return False, f"Input must contain only binary digits ('0' and '1'). Got: '{cleaned}'"
    return True, ""


def text_to_binary(text: str) -> str:
    """Convert an ASCII string to an 8-bit binary string representation."""
    return "".join(format(ord(c), "08b") for c in text)


def parse_input_data(user_input: str, default: str = "1011011011001100") -> Dict[str, Any]:
    """Parse raw user input into validated binary string, matching the backend's behavior.
    
    Supports:
    1. Direct binary string (e.g. '1011011011001100')
    2. 'r' or 'random' for a random 16-bit binary payload
    3. Plain text string, converted to 8-bit ASCII binary representation
    """
    raw = (user_input or "").strip()
    if not raw:
        return {
            "data": default,
            "length": len(default),
            "source_type": "default",
            "message": f"Using default payload ({len(default)} bits)."
        }

    # 1. Direct binary
    if all(c in "01" for c in raw):
        return {
            "data": raw,
            "length": len(raw),
            "source_type": "binary",
            "message": f"Valid binary payload ({len(raw)} bits)."
        }

    # 2. Random request
    if raw.lower() in ("r", "random"):
        random_bits = "".join(random.choice("01") for _ in range(16))
        return {
            "data": random_bits,
            "length": len(random_bits),
            "source_type": "random",
            "message": f"Generated random 16-bit payload: {random_bits}"
        }

    # 3. ASCII Text conversion
    converted = text_to_binary(raw)
    return {
        "data": converted,
        "length": len(converted),
        "source_type": "text",
        "original_text": raw,
        "message": f"Converted ASCII text '{raw}' to {len(converted)}-bit binary representation."
    }


def sanitize_for_json(obj: Any) -> Any:
    """Recursively convert NumPy or special types to standard JSON-compatible Python primitives."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(x) for x in obj]
    elif hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    elif isinstance(obj, float):
        if obj != obj:  # NaN
            return None
        return obj
    return obj


def run_simulation(
    data: str,
    technique: str = "CRC",
    error_type: str = "single",
    error_amount: Any = 1,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    positions: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Execute end-to-end transmission simulation via backend simulator."""
    valid, err_msg = validate_binary_string(data)
    if not valid:
        return {"success": False, "error": err_msg}

    # Normalize error type
    error_type = error_type.lower().strip()
    valid_error_types = ["clean", "single", "multiple", "burst", "consecutive_burst", "multiple_burst", "manual"]
    if error_type not in valid_error_types:
        return {
            "success": False,
            "error": f"Invalid error model '{error_type}'. Allowed: {', '.join(valid_error_types)}"
        }

    # Format error_amount based on type
    if error_type == "clean":
        parsed_amount: Any = 0
    elif error_type == "single":
        parsed_amount = 1
    elif error_type == "multiple":
        try:
            parsed_amount = int(error_amount)
            if parsed_amount < 1:
                return {"success": False, "error": "Error bit count must be at least 1."}
        except (ValueError, TypeError):
            parsed_amount = 2
    elif error_type == "burst":
        try:
            parsed_amount = int(error_amount)
            if parsed_amount < 1:
                return {"success": False, "error": "Burst length must be at least 1."}
        except (ValueError, TypeError):
            parsed_amount = 4
    elif error_type in ("consecutive_burst", "consecutive"):
        try:
            parsed_amount = int(error_amount)
            if parsed_amount < 1:
                return {"success": False, "error": "Consecutive burst length must be at least 1."}
        except (ValueError, TypeError):
            parsed_amount = 4
    elif error_type in ("multiple_burst", "multi_burst"):
        if isinstance(error_amount, dict):
            parsed_amount = error_amount
        elif isinstance(error_amount, (list, tuple)):
            parsed_amount = error_amount
        else:
            try:
                parsed_amount = int(error_amount)
                if parsed_amount < 1:
                    parsed_amount = 3
            except (ValueError, TypeError):
                parsed_amount = 3
    elif error_type == "manual":
        if positions is not None:
            parsed_amount = positions
        elif isinstance(error_amount, list):
            parsed_amount = error_amount
        else:
            try:
                parsed_amount = [
                    int(p.strip()) for p in str(error_amount).split(",") if p.strip().isdigit()
                ]
            except Exception:
                parsed_amount = [0]
        if not parsed_amount:
            return {"success": False, "error": "At least one bit position must be specified for manual error."}

    try:
        # Call original untouched backend simulation function
        sim_result = simulate(
            data=data,
            technique=technique,
            error_type=error_type,
            error_amount=parsed_amount,
            crc_generator=crc_generator,
            checksum_word_size=checksum_word_size
        )

        sanitized = sanitize_for_json(sim_result)
        return {
            "success": True,
            "result": sanitized
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Backend simulation error: {str(e)}"
        }


def run_comparison(
    data: str,
    error_type: str = "single",
    error_amount: Any = 1
) -> Dict[str, Any]:
    """Execute side-by-side comparison across all four canonical techniques."""
    valid, err_msg = validate_binary_string(data)
    if not valid:
        return {"success": False, "error": err_msg}

    error_type = error_type.lower().strip()
    valid_error_types = ["clean", "single", "multiple", "burst", "consecutive_burst", "multiple_burst", "manual"]
    if error_type not in valid_error_types:
        return {
            "success": False,
            "error": f"Invalid error model '{error_type}'. Allowed: {', '.join(valid_error_types)}"
        }

    # Format error_amount
    if error_type == "clean":
        parsed_amount: Any = 0
    elif error_type == "single":
        parsed_amount = 1
    elif error_type == "multiple":
        try:
            parsed_amount = int(error_amount)
        except (ValueError, TypeError):
            parsed_amount = 2
    elif error_type == "burst":
        try:
            parsed_amount = int(error_amount)
        except (ValueError, TypeError):
            parsed_amount = 4
    elif error_type in ("consecutive_burst", "consecutive"):
        try:
            parsed_amount = int(error_amount)
        except (ValueError, TypeError):
            parsed_amount = 4
    elif error_type in ("multiple_burst", "multi_burst"):
        if isinstance(error_amount, dict):
            parsed_amount = error_amount
        elif isinstance(error_amount, (list, tuple)):
            parsed_amount = error_amount
        else:
            try:
                parsed_amount = int(error_amount)
            except (ValueError, TypeError):
                parsed_amount = 3
    elif error_type == "manual":
        if isinstance(error_amount, list):
            parsed_amount = error_amount
        else:
            try:
                parsed_amount = [
                    int(p.strip()) for p in str(error_amount).split(",") if p.strip().isdigit()
                ]
            except Exception:
                parsed_amount = [0]
        if not parsed_amount:
            return {"success": False, "error": "At least one bit position must be specified for manual error."}

    try:
        # Call original untouched backend compare_all_techniques function
        comp_results = compare_all_techniques(
            data=data,
            error_type=error_type,
            error_amount=parsed_amount
        )

        sanitized = sanitize_for_json(comp_results)
        return {
            "success": True,
            "results": sanitized,
            "count": len(sanitized)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Backend comparison error: {str(e)}"
        }


def get_algorithm_working(
    data: str,
    technique: str = "all",
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    parity_mode: str = "even"
) -> Dict[str, Any]:
    """Retrieve detailed step-by-step traces for educational demonstration."""
    valid, err_msg = validate_binary_string(data)
    if not valid:
        return {"success": False, "error": err_msg}

    tech_lower = technique.lower().strip()
    traces: Dict[str, Any] = {}

    try:
        if tech_lower in ("vrc", "parity", "vrc / parity", "all"):
            traces["vrc"] = {
                "name": "Vertical Redundancy Check (VRC / Parity)",
                "raw_text": format_vrc_working(data, mode=parity_mode),
                "redundancy_bits": 1,
                "parity_mode": parity_mode
            }

        if tech_lower in ("lrc", "longitudinal redundancy check", "all"):
            traces["lrc"] = {
                "name": "Longitudinal Redundancy Check (LRC)",
                "raw_text": format_lrc_working(data, block_size=8),
                "block_size": 8
            }

        if tech_lower in ("checksum", "internet checksum", "all"):
            traces["checksum"] = {
                "name": f"Internet Checksum ({checksum_word_size}-bit)",
                "raw_text": format_checksum_working(data, word_size=checksum_word_size),
                "word_size": checksum_word_size
            }

        if tech_lower in ("crc", "cyclic redundancy check", "all"):
            traces["crc"] = {
                "name": "Cyclic Redundancy Check (CRC)",
                "raw_text": format_crc_working(data, generator=crc_generator),
                "generator": crc_generator
            }

        return {
            "success": True,
            "data": data,
            "traces": sanitize_for_json(traces)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error formatting algorithm calculations: {str(e)}"
        }


def get_available_crc_polynomials() -> Dict[str, Any]:
    """Return the standard CRC polynomials defined in the backend."""
    return sanitize_for_json(CRC_POLYNOMIALS)
