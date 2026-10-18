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


def consecutive_burst_error(
    frame: str,
    burst_length: int,
    start_position: Union[int, None] = None,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Introduce consecutive burst corruption (dense burst where 100% of bits in span are inverted).

    Args:
        frame: Binary frame string.
        burst_length: Number of consecutive bits to invert.
        start_position: Optional explicit start index. If None or invalid, chosen randomly.
        return_indices: If True, returns (corrupted_frame, flipped_indices).
    """
    if not frame:
        return ("", []) if return_indices else ""

    span = max(1, min(int(burst_length), len(frame)))
    max_start = len(frame) - span

    if start_position is not None and 0 <= int(start_position) <= max_start:
        start = int(start_position)
    else:
        start = random.randint(0, max_start)

    corrupted = list(frame)
    flipped_indices = []

    for pos in range(start, start + span):
        corrupted[pos] = _flip_char(corrupted[pos])
        flipped_indices.append(pos)

    result_str = "".join(corrupted)
    if return_indices:
        return result_str, flipped_indices
    return result_str


def multiple_burst_error(
    frame: str,
    num_bursts: int = 2,
    burst_length: int = 3,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Introduce multiple separated burst episodes across the frame.

    Simulates recurring interference bursts (e.g. periodic impulse spikes or multi-path
    fading) separated by clean bit intervals.

    Args:
        frame: Binary frame string.
        num_bursts: Number of distinct burst episodes (default: 2).
        burst_length: Length of each burst episode in bits (default: 3).
        return_indices: If True, returns (corrupted_frame, flipped_indices).
    """
    if not frame:
        return ("", []) if return_indices else ""

    frame_len = len(frame)
    num_b = max(2, int(num_bursts))
    b_len = max(1, int(burst_length))

    # Ensure bursts fit into the frame with at least 1 clean bit between them if possible
    while num_b * b_len + (num_b - 1) > frame_len and b_len > 1:
        b_len -= 1

    if num_b * b_len > frame_len:
        num_b = max(1, frame_len // max(1, b_len))

    # Divide frame into num_b partitions and place one burst within each partition
    partition_size = frame_len // num_b
    corrupted = list(frame)
    flipped_indices: List[int] = []

    for b_idx in range(num_b):
        part_start = b_idx * partition_size
        part_end = (b_idx + 1) * partition_size if b_idx < num_b - 1 else frame_len
        avail_span = part_end - part_start

        actual_len = min(b_len, avail_span)
        if actual_len < 1:
            continue

        max_offset = avail_span - actual_len
        start_pos = part_start + (random.randint(0, max_offset) if max_offset > 0 else 0)
        end_pos = start_pos + actual_len - 1

        if actual_len <= 2:
            for p in range(start_pos, start_pos + actual_len):
                corrupted[p] = _flip_char(corrupted[p])
                flipped_indices.append(p)
        else:
            # First bit flipped
            corrupted[start_pos] = _flip_char(corrupted[start_pos])
            flipped_indices.append(start_pos)

            # Intermediate bits flipped with 50% probability
            for p in range(start_pos + 1, end_pos):
                if random.random() < 0.5:
                    corrupted[p] = _flip_char(corrupted[p])
                    flipped_indices.append(p)

            # Last bit flipped
            corrupted[end_pos] = _flip_char(corrupted[end_pos])
            flipped_indices.append(end_pos)

    result_str = "".join(corrupted)
    if return_indices:
        return result_str, sorted(list(set(flipped_indices)))
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