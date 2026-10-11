"""Error Generation Module for Digital Communication Networks (DCN).

Supports exactly five physical layer error models:
1. Clean transmission: Zero bit errors introduced (ideal channel test).
2. Single-bit error: An isolated 1-bit flip caused by impulse noise.
3. Multiple-bit error: User-specified number (k) of random bit flips.
4. Burst error: A contiguous span of corrupted bits where endpoints are inverted.
5. Manual error injection: Deterministic bit flips at exact user-selected positions.
"""

import random
from typing import Tuple, List, Union


def _flip_char(c: str) -> str:
    return "1" if c == "0" else "0"


def clean_transmission(
    frame: str,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Transmit frame without introducing any bit errors (clean channel).

    Args:
        frame: Binary frame string.
        return_indices: If True, returns (frame, []).
    """
    if return_indices:
        return frame, []
    return frame


def single_bit_error(
    frame: str,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Introduce a single-bit error at a random position.

    Args:
        frame: Binary frame string.
        return_indices: If True, returns (corrupted_frame, [flipped_index]).
    """
    if not frame:
        return ("", []) if return_indices else ""

    position = random.randrange(len(frame))
    corrupted = list(frame)
    corrupted[position] = _flip_char(corrupted[position])
    result_str = "".join(corrupted)

    if return_indices:
        return result_str, [position]
    return result_str


def multiple_bit_error(
    frame: str,
    number_of_errors: int,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Introduce multiple random bit errors.

    Args:
        frame: Binary frame string.
        number_of_errors: Number of bits to corrupt.
        return_indices: If True, returns (corrupted_frame, flipped_indices).
    """
    if not frame:
        return ("", []) if return_indices else ""

    count = max(1, min(int(number_of_errors), len(frame)))
    positions = sorted(random.sample(range(len(frame)), count))

    corrupted = list(frame)
    for pos in positions:
        corrupted[pos] = _flip_char(corrupted[pos])
    result_str = "".join(corrupted)

    if return_indices:
        return result_str, positions
    return result_str


def burst_error(
    frame: str,
    burst_length: int,
    mode: str = "textbook",
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Introduce a burst error of specified span.

    In DCN theory (Forouzan/Tanenbaum), a burst error of length L means:
    - The first bit of the burst span is inverted.
    - The last bit of the burst span is inverted.
    - Intermediate bits may or may not be inverted (50% random probability).

    Args:
        frame: Binary frame string.
        burst_length: Length of the burst span in bits.
        mode: 'textbook' (first/last flipped, intermediate random) or 'dense' (all flipped).
        return_indices: If True, returns (corrupted_frame, flipped_indices).
    """
    if not frame:
        return ("", []) if return_indices else ""

    burst_length = max(1, min(int(burst_length), len(frame)))
    max_start = len(frame) - burst_length
    start = random.randint(0, max_start)
    end = start + burst_length - 1

    corrupted = list(frame)
    flipped_indices = []

    if mode == "dense" or burst_length <= 2:
        for pos in range(start, start + burst_length):
            corrupted[pos] = _flip_char(corrupted[pos])
            flipped_indices.append(pos)
    else:
        # First bit flipped
        corrupted[start] = _flip_char(corrupted[start])
        flipped_indices.append(start)

        # Intermediate bits flipped with 50% probability
        for pos in range(start + 1, end):
            if random.random() < 0.5:
                corrupted[pos] = _flip_char(corrupted[pos])
                flipped_indices.append(pos)

        # Last bit flipped
        corrupted[end] = _flip_char(corrupted[end])
        flipped_indices.append(end)

    result_str = "".join(corrupted)

    if return_indices:
        return result_str, sorted(flipped_indices)
    return result_str


def manual_error(
    frame: str,
    positions: List[int],
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Deterministically corrupt specific bit positions chosen by user."""
    corrupted = list(frame)
    valid_positions = []

    for pos in positions:
        if 0 <= pos < len(frame):
            corrupted[pos] = _flip_char(corrupted[pos])
            valid_positions.append(pos)

    result_str = "".join(corrupted)
    if return_indices:
        return result_str, sorted(valid_positions)
    return result_str