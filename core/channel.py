"""Transmission Channel Component for DCN Simulation System.

Encapsulates physical medium noise simulation and error injection models.
Demonstrates:
- Separation of concerns: Channel noise is isolated from Sender and Receiver.
- State encapsulation: Transmission artifacts, noise causes, and mechanisms.
"""

from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass

from simulation.error_generator import (
    clean_transmission,
    single_bit_error,
    multiple_bit_error,
    burst_error,
    consecutive_burst_error,
    multiple_burst_error,
    manual_error
)


@dataclass
class ChannelTransmissionResult:
    """Encapsulates the state of a frame after traversing the physical channel."""
    original_frame: str
    corrupted_frame: str
    flipped_indices: List[int]
    errors_injected: int
    error_type: str
    error_cause: str
    error_mechanism: str


class TransmissionChannel:
    """Simulates an unreliable physical communications link subject to noise."""

    def __init__(self, name: str = "Unreliable Physical Channel"):
        self.name = name

    def transmit(
        self,
        frame: str,
        error_type: str = "single",
        error_amount: Union[int, float, List[int], Dict[str, Any]] = 1,
        forced_indices: Optional[List[int]] = None
    ) -> ChannelTransmissionResult:
        """Transmit a frame through the noisy channel.
        
        Args:
            frame: Protected frame bitstring from the Sender.
            error_type: Error model to apply ('clean', 'single', 'multiple', 'burst',
                        'consecutive_burst', 'multiple_burst', 'manual').
            error_amount: Quantity/span of corruption or parameters dict.
            forced_indices: Optional explicit indices to invert.
            
        Returns:
            ChannelTransmissionResult containing the output bitstream and diagnostics.
        """
        err_type = error_type.lower().strip()
        flipped_indices: List[int] = []

        if forced_indices is not None:
            corrupted_frame, flipped_indices = manual_error(
                frame, positions=forced_indices, return_indices=True
            )
        elif err_type in ("clean", "none", "0"):
            corrupted_frame, flipped_indices = clean_transmission(frame, return_indices=True)

        elif err_type == "single":
            corrupted_frame, flipped_indices = single_bit_error(frame, return_indices=True)

        elif err_type == "multiple":
            count = int(error_amount) if isinstance(error_amount, (int, float)) else 2
            corrupted_frame, flipped_indices = multiple_bit_error(
                frame, number_of_errors=count, return_indices=True
            )

        elif err_type == "burst":
            span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
            corrupted_frame, flipped_indices = burst_error(
                frame, burst_length=span, mode="textbook", return_indices=True
            )

        elif err_type in ("consecutive_burst", "consecutive"):
            span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
            corrupted_frame, flipped_indices = consecutive_burst_error(
                frame, burst_length=span, return_indices=True
            )

        elif err_type in ("multiple_burst", "multi_burst"):
            if isinstance(error_amount, dict):
                num_b = int(error_amount.get("num_bursts", 2))
                b_len = int(error_amount.get("burst_length", 3))
            elif isinstance(error_amount, (list, tuple)) and len(error_amount) >= 2:
                num_b = int(error_amount[0])
                b_len = int(error_amount[1])
            else:
                num_b = 2
                b_len = int(error_amount) if isinstance(error_amount, (int, float)) else 3
            corrupted_frame, flipped_indices = multiple_burst_error(
                frame, num_bursts=num_b, burst_length=b_len, return_indices=True
            )

        elif err_type == "manual":
            if isinstance(error_amount, list):
                positions = error_amount
            elif isinstance(error_amount, int):
                positions = [error_amount]
            else:
                positions = [int(p.strip()) for p in str(error_amount).split(",") if p.strip().isdigit()]
            corrupted_frame, flipped_indices = manual_error(
                frame, positions=positions, return_indices=True
            )

        else:
            raise ValueError(f"Unsupported error type '{error_type}'.")

        cause, mechanism = self._describe_physical_cause(
            error_type=err_type,
            errors_injected=len(flipped_indices),
            flipped_indices=flipped_indices
        )

        return ChannelTransmissionResult(
            original_frame=frame,
            corrupted_frame=corrupted_frame,
            flipped_indices=flipped_indices,
            errors_injected=len(flipped_indices),
            error_type=err_type,
            error_cause=cause,
            error_mechanism=mechanism
        )

    def _describe_physical_cause(
        self,
        error_type: str,
        errors_injected: int,
        flipped_indices: List[int]
    ) -> Tuple[str, str]:
        """Provide realistic physical layer noise etiology and injection mechanism."""
        if error_type in ("clean", "none", "0") or errors_injected == 0:
            cause = "Ideal transmission environment. Complete absence of thermal noise, cross-talk, and electromagnetic interference on the transmission medium."
            mechanism = "Transparent channel transmission without bit alteration (0 bit flips). Frame integrity is fully preserved."
            return cause, mechanism

        if error_type == "single":
            cause = "Microscopic thermal white noise (Gaussian background disturbance) or a brief localized voltage transient on physical media (copper, optical receiver, or wireless RF)."
            pos_str = str(flipped_indices[0]) if flipped_indices else "random"
            mechanism = f"Inverted exactly 1 isolated bit (0 ↔ 1) at frame bit position {pos_str}."
            return cause, mechanism

        if error_type == "multiple":
            cause = "Inductive crosstalk from adjacent cable pairs, high-frequency atmospheric noise, or multi-user interference causing independent random bit flips."
            mechanism = f"Inverted {errors_injected} independent bit positions scattered across the frame at indices: {flipped_indices}."
            return cause, mechanism

        if error_type == "burst":
            cause = "Short-duration electrical transient, electrostatic discharge (ESD), nearby heavy motor switching, or lightning impulse coupling into copper cabling."
            mechanism = f"Corrupted an end-to-end span of {errors_injected} bits starting and ending with corrupted edges across frame indices: {flipped_indices}."
            return cause, mechanism

        if error_type in ("consecutive_burst", "consecutive"):
            cause = "Sustained physical disturbance, such as severe mechanical vibration on connector contacts, deep multipath RF fading dip, or continuous voltage line drop."
            mechanism = f"Unconditionally inverted 100% of bits within a solid contiguous span of {errors_injected} bits at indices: {flipped_indices}."
            return cause, mechanism

        if error_type in ("multiple_burst", "multi_burst"):
            cause = "Periodic electromagnetic pulse interference, repetitive thyristor power switching, or intermittent radio frequency jamming bursts."
            mechanism = f"Introduced multiple separated burst corruption episodes across the frame, totaling {errors_injected} flipped bits at indices: {flipped_indices}."
            return cause, mechanism

        # Manual
        cause = "Deterministic lab fault injection or deliberate edge-case unit testing by network engineer."
        mechanism = f"Inverted {errors_injected} user-specified bit positions at indices: {flipped_indices}."
        return cause, mechanism
