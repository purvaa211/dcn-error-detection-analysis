"""Two-Dimensional Parity Check (LRC - Longitudinal Redundancy Check + VRC).

Organizes data bits into a two-dimensional grid of R rows and C columns.
- For each row, an even parity bit is computed (Row Parity / VRC).
- For each column, an even parity bit is computed (Column Parity / LRC).
- The final frame includes the data rows + row parity bits + column parity block.

DCN Characteristics:
- Detects all 1-bit, 2-bit, and 3-bit errors.
- Detects most burst errors of length <= block width.
- Can locate and correct single-bit errors by taking the intersection of the
  faulty row and faulty column.
- Minimum Hamming distance d_min = 4 (for detection).
"""

from typing import Tuple, Dict, Any, List


def pad_to_block_size(data: str, col_size: int = 8) -> Tuple[str, int]:
    """Pad binary data with leading zeros so length is a multiple of col_size.

    Returns:
        tuple (padded_data, padding_added)
    """
    remainder = len(data) % col_size
    if remainder != 0:
        padding_needed = col_size - remainder
        padded_data = data + ("0" * padding_needed)
        return padded_data, padding_needed
    return data, 0


def encode_2d_parity(data: str, col_size: int = 8) -> Tuple[str, Dict[str, Any]]:
    """Encode binary data using 2D (Row + Column) Parity.

    Args:
        data: Binary string payload.
        col_size: Number of data columns per row (default: 8 bits).

    Returns:
        tuple (protected_frame, matrix_details)
    """
    padded_data, pad_count = pad_to_block_size(data, col_size)
    num_rows = len(padded_data) // col_size

    # Split into rows
    rows: List[str] = [
        padded_data[i * col_size:(i + 1) * col_size]
        for i in range(num_rows)
    ]

    # Calculate row parities (Even Parity for each row)
    row_parities: List[str] = [
        "0" if row.count("1") % 2 == 0 else "1"
        for row in rows
    ]

    # Calculate column parities (Even Parity for each column)
    col_parities: List[str] = []
    for c in range(col_size):
        col_ones = sum(1 for r in range(num_rows) if rows[r][c] == "1")
        col_parities.append("0" if col_ones % 2 == 0 else "1")
    col_parity_block = "".join(col_parities)

    # Parity of the row parities (bottom-right corner bit)
    corner_bit = "0" if row_parities.count("1") % 2 == 0 else "1"

    # Frame structure:
    # Row 0 (col_size bits) + row_parities[0]
    # Row 1 (col_size bits) + row_parities[1] ...
    # Column parity row (col_size bits) + corner_bit
    frame_parts = []
    for r in range(num_rows):
        frame_parts.append(rows[r] + row_parities[r])
    frame_parts.append(col_parity_block + corner_bit)

    protected_frame = "".join(frame_parts)

    details = {
        "col_size": col_size,
        "num_rows": num_rows,
        "pad_count": pad_count,
        "data_rows": rows,
        "row_parities": row_parities,
        "col_parities": col_parities,
        "corner_bit": corner_bit,
        "redundancy_bits": len(protected_frame) - len(data),
        "protected_frame": protected_frame
    }

    return protected_frame, details


def check_2d_parity(
    frame: str,
    col_size: int = 8
) -> Tuple[bool, Dict[str, Any]]:
    """Verify received frame using 2D Parity Check.

    Reconstructs the (num_rows + 1) x (col_size + 1) matrix,
    checks row and column parity, and identifies error positions if possible.

    Args:
        frame: Received bit sequence.
        col_size: Column width of data (default: 8).

    Returns:
        tuple (is_valid, check_details)
    """
    row_width = col_size + 1
    if len(frame) % row_width != 0:
        # Frame length mismatch
        return False, {
            "is_valid": False,
            "error_message": f"Frame length {len(frame)} is not a multiple of row width {row_width}"
        }

    total_matrix_rows = len(frame) // row_width
    num_data_rows = total_matrix_rows - 1

    matrix_rows = [
        frame[i * row_width:(i + 1) * row_width]
        for i in range(total_matrix_rows)
    ]

    # Check row parities
    failed_rows = []
    for r in range(total_matrix_rows):
        row_str = matrix_rows[r]
        if row_str.count("1") % 2 != 0:
            failed_rows.append(r)

    # Check column parities
    failed_cols = []
    for c in range(row_width):
        col_ones = sum(1 for r in range(total_matrix_rows) if matrix_rows[r][c] == "1")
        if col_ones % 2 != 0:
            failed_cols.append(c)

    is_valid = (len(failed_rows) == 0 and len(failed_cols) == 0)

    # Can locate error if exactly 1 row and 1 column failed
    single_error_coord = None
    if len(failed_rows) == 1 and len(failed_cols) == 1:
        single_error_coord = (failed_rows[0], failed_cols[0])

    details = {
        "is_valid": is_valid,
        "col_size": col_size,
        "num_data_rows": num_data_rows,
        "matrix_rows": matrix_rows,
        "failed_rows": failed_rows,
        "failed_cols": failed_cols,
        "single_error_coord": single_error_coord,
        "error_count_estimate": max(len(failed_rows), len(failed_cols))
    }

    return is_valid, details


def format_2d_matrix_display(details: Dict[str, Any]) -> str:
    """Format the 2D parity matrix as an ASCII grid for visual presentation."""
    if "matrix_rows" not in details:
        return "No matrix structure available."

    rows = details["matrix_rows"]
    col_size = details["col_size"]
    failed_rows = set(details.get("failed_rows", []))
    failed_cols = set(details.get("failed_cols", []))

    lines = []
    header = "       " + " ".join(f"C{c}" for c in range(col_size)) + " | RowParity"
    sep = "     +" + "-" * (col_size * 3 + 1) + "+-----------"
    lines.append(header)
    lines.append(sep)

    for r in range(len(rows) - 1):
        row_data = "  ".join(rows[r][:col_size])
        row_par = rows[r][col_size]
        flag = " [FAIL]" if r in failed_rows else " [OK]  "
        lines.append(f"  R{r:<2} | {row_data} |     {row_par}    {flag}")

    lines.append(sep)
    # Bottom column parity row
    lrc_row = rows[-1]
    col_pars = "  ".join(lrc_row[:col_size])
    corner = lrc_row[col_size]
    flag_corner = " [FAIL]" if (len(rows) - 1) in failed_rows else " [OK]  "
    lines.append(f"  LRC | {col_pars} |     {corner}    {flag_corner}")

    # Column flags
    col_status = "       " + " ".join(" X " if c in failed_cols else " . " for c in range(col_size))
    lines.append(col_status)

    return "\n".join(lines)
