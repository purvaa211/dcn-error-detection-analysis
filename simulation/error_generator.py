"""Error Generation Module for Digital Communication Networks (DCN).

Models physical layer channel impairments:
1. Single-bit error: An isolated 1-bit flip caused by brief impulse noise.
2. Multiple-bit error: Two or more non-consecutive or random bit flips.
3. Burst error: A contiguous span of bits corrupted where the first and last bits
   in the burst window are flipped, and intermediate bits may be flipped.
4. Manual bit flip: Deterministic error injection at exact user-specified indices
   (essential for jury demonstrations and edge-case testing).
5. Channel Noise (Bit Error Rate - BER): Probabilistic independent bit-flipping model.
"""

import random
from typing import Tuple, List, Union


def _flip_char(c: str) -> str:
    return "1" if c == "0" else "0"


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

    # Clamp to avoid random.sample error
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
    - The first bit of the burst is inverted.
    - The last bit of the burst is inverted.
    - The (L - 2) intermediate bits may or may not be inverted (random probability).

    Args:
        frame: Binary frame string.
        burst_length: Length of the burst span.
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
        # Textbook definition:
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


def ber_channel_error(
    frame: str,
    bit_error_rate: float = 0.05,
    return_indices: bool = False
) -> Union[str, Tuple[str, List[int]]]:
    """Simulate a noisy channel where each bit has probability BER of flipping."""
    corrupted = list(frame)
    flipped = []

    for i in range(len(frame)):
        if random.random() < bit_error_rate:
            corrupted[i] = _flip_char(corrupted[i])
            flipped.append(i)

    # Ensure at least 1 error occurs if BER > 0 and frame is non-empty
    if not flipped and bit_error_rate > 0 and frame:
        forced = random.randrange(len(frame))
        corrupted[forced] = _flip_char(corrupted[forced])
        flipped.append(forced)

    result_str = "".join(corrupted)
    if return_indices:
        return result_str, sorted(flipped)
    return result_str