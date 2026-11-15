"""Network Components & Simulation Orchestrator for DCN Error Control Architecture.

Demonstrates:
- Object-Oriented Composition: NetworkSimulator composes Sender, Channel, and Receiver.
- Encapsulation: Network entity state and operational behavior.
- Runtime Polymorphism: Different ErrorDetection subclasses plugged into Sender and Receiver.
"""

import time
import random
from typing import Dict, Any, List, Optional, Tuple, Union

from core.detection import (
    ErrorDetection,
    ParityCheck,
    LRC,
    Checksum,
    CRC,
    get_detection_strategy
)
from core.channel import TransmissionChannel, ChannelTransmissionResult


class Sender:
    """Sender (Transmitter) entity at the Data Link / Transport boundary.
    
    Responsible for accepting, converting, and framing original data payloads
    with redundancy check bits.
    """

    def __init__(self, data: str = "1011011011001100"):
        self._payload = self._validate_data(data)

    @property
    def payload(self) -> str:
        """The binary payload stored at the sender."""
        return self._payload

    @payload.setter
    def payload(self, data: str) -> None:
        self._payload = self._validate_data(data)

    def set_text_payload(self, text: str) -> str:
        """Convert ASCII text into 8-bit binary representation and set as payload."""
        binary_str = "".join(format(ord(c), "08b") for c in text)
        self._payload = binary_str
        return binary_str

    def set_random_payload(self, length: int = 16) -> str:
        """Generate a pseudo-random binary bit sequence and set as payload."""
        length = max(4, min(length, 4096))
        binary_str = "".join(random.choice("01") for _ in range(length))
        self._payload = binary_str
        return binary_str

    def encode(self, detection: ErrorDetection) -> str:
        """Apply the chosen error detection scheme to produce a protected frame."""
        return detection.encode(self._payload)

    @staticmethod
    def _validate_data(data: str) -> str:
        cleaned = (data or "").strip()
        if not cleaned or not all(c in "01" for c in cleaned):
            raise ValueError(f"Payload must be a non-empty binary string ('0' and '1'). Got: '{data}'")
        return cleaned


class Receiver:
    """Receiver entity at the receiving end of the communication channel.
    
    Responsible for receiving the incoming frame from the physical channel,
    executing error detection, and rendering integrity diagnostics.
    """

    def __init__(self, name: str = "Host Receiver"):
        self.name = name

    def receive(self, frame: str, detection: ErrorDetection) -> Tuple[bool, Dict[str, Any]]:
        """Verify the received frame using the specified error detection strategy.
        
        Returns:
            Tuple of (is_valid: bool, diagnostics: dict).
        """
        return detection.verify(frame)


class NetworkSimulator:
    """Coordinates the end-to-end communication pipeline across Sender, Channel, and Receiver."""

    def __init__(self):
        self.sender = Sender()
        self.channel = TransmissionChannel()
        self.receiver = Receiver()

    def simulate(
        self,
        data: str,
        technique: str = "CRC",
        error_type: str = "single",
        error_amount: Union[int, float, List[int], Dict[str, Any]] = 1,
        crc_generator: str = "100000111",
        checksum_word_size: int = 8,
        forced_indices: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Execute a complete end-to-end simulation across Sender, Channel, and Receiver."""
        # 1. Prepare sender
        self.sender.payload = data
        detection_strategy = get_detection_strategy(
            technique=technique,
            crc_generator=crc_generator,
            checksum_word_size=checksum_word_size
        )

        # 2. Stage 1: Sender Encoding
        t_enc_start = time.perf_counter()
        protected_frame = self.sender.encode(detection_strategy)
        encoding_time = time.perf_counter() - t_enc_start

        # 3. Stage 2: Channel Transmission & Noise Injection
        channel_result: ChannelTransmissionResult = self.channel.transmit(
            frame=protected_frame,
            error_type=error_type,
            error_amount=error_amount,
            forced_indices=forced_indices
        )

        # 4. Stage 3: Receiver Verification
        t_chk_start = time.perf_counter()
        is_valid, diag_details = self.receiver.receive(
            channel_result.corrupted_frame,
            detection=detection_strategy
        )
        checking_time = time.perf_counter() - t_chk_start

        # 5. Stage 4: Performance & Diagnostic Evaluation
        error_detected = not is_valid
        total_time = encoding_time + checking_time

        overhead_bits = detection_strategy.get_redundancy_bits(data)
        overhead_pct = detection_strategy.get_overhead_percentage(data)

        # Check for Hamming-specific verdict and diagnostics
        hamming_verdict = None
        if "Hamming" in detection_strategy.name:
            decoded = diag_details.get("decoded_payload")
            if channel_result.errors_injected == 0:
                hamming_verdict = "[CLEAN TRANSMISSION]"
                diag_details["successfully_corrected"] = False
                diag_details["miscorrected"] = False
            elif decoded == data:
                hamming_verdict = "[ERROR DETECTED AND CORRECTED]"
                diag_details["successfully_corrected"] = True
                diag_details["miscorrected"] = False
            else:
                hamming_verdict = "[ERROR DETECTED - NOT CORRECTABLE / MISCORRECTED]"
                diag_details["successfully_corrected"] = False
                diag_details["miscorrected"] = True

        explanation = self._generate_explanation(
            tech_name=detection_strategy.name,
            error_type=channel_result.error_type,
            errors_injected=channel_result.errors_injected,
            error_detected=error_detected,
            diag_details=diag_details
        )

        return {
            "original_data": data,
            "payload_length": len(data),
            "technique": detection_strategy.name,
            "category": detection_strategy.category,
            "protected_frame": protected_frame,
            "corrupted_frame": channel_result.corrupted_frame,
            "flipped_indices": channel_result.flipped_indices,
            "errors_injected": channel_result.errors_injected,
            "error_type": channel_result.error_type,
            "error_cause": channel_result.error_cause,
            "error_introduction": channel_result.error_mechanism,
            "is_valid": is_valid,
            "error_detected": error_detected,
            "overhead_bits": overhead_bits,
            "overhead_percentage": overhead_pct,
            "encoding_time": encoding_time,
            "checking_time": checking_time,
            "processing_time": total_time,
            "diagnostics": diag_details,
            "explanation": explanation,
            "hamming_verdict": hamming_verdict
        }

    def compare_all(
        self,
        data: str,
        error_type: str = "multiple",
        error_amount: Union[int, float, List[int], Dict[str, Any]] = 2
    ) -> List[Dict[str, Any]]:
        """Run all four techniques on the same input under identical payload corruptions."""
        data_len = len(data)
        payload_corrupted_indices: List[int] = []

        if error_type == "clean":
            payload_corrupted_indices = []
        elif error_type == "single":
            payload_corrupted_indices = [random.randrange(data_len)]
        elif error_type == "multiple":
            count = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 2, data_len))
            payload_corrupted_indices = sorted(random.sample(range(data_len), count))
        elif error_type == "burst":
            span = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 4, data_len))
            start = random.randint(0, data_len - span)
            payload_corrupted_indices = [start, start + span - 1]
            for p in range(start + 1, start + span - 1):
                if random.random() < 0.5:
                    payload_corrupted_indices.append(p)
            payload_corrupted_indices = sorted(payload_corrupted_indices)
        elif error_type in ("consecutive_burst", "consecutive"):
            span = max(1, min(int(error_amount) if isinstance(error_amount, (int, float)) else 4, data_len))
            max_start = data_len - span
            start = random.randint(0, max_start) if max_start > 0 else 0
            payload_corrupted_indices = list(range(start, start + span))
        elif error_type in ("multiple_burst", "multi_burst"):
            num_b = 2
            b_len = 3
            if isinstance(error_amount, dict):
                num_b = int(error_amount.get("num_bursts", 2))
                b_len = int(error_amount.get("burst_length", 3))
            elif isinstance(error_amount, (list, tuple)) and len(error_amount) >= 2:
                num_b = int(error_amount[0])
                b_len = int(error_amount[1])
            max_total = num_b * b_len
            if max_total < data_len:
                starts = sorted(random.sample(range(0, data_len - b_len), num_b))
                indices_set = set()
                for s in starts:
                    indices_set.update(range(s, min(s + b_len, data_len)))
                payload_corrupted_indices = sorted(list(indices_set))
            else:
                payload_corrupted_indices = list(range(min(max_total, data_len)))
        elif error_type == "manual":
            if isinstance(error_amount, list):
                payload_corrupted_indices = [p for p in error_amount if p < data_len]
            else:
                payload_corrupted_indices = [
                    int(p.strip()) for p in str(error_amount).split(",")
                    if p.strip().isdigit() and int(p.strip()) < data_len
                ]
        else:
            payload_corrupted_indices = [0]

        techniques = [
            ("VRC / Parity", "even"),
            ("LRC", 8),
            ("Checksum", 8),
            ("CRC", "100000111"),
            ("Hamming (7,4)", None)
        ]

        results = []
        for tech_name, param in techniques:
            res = self.simulate(
                data=data,
                technique=tech_name,
                error_type=error_type,
                error_amount=error_amount,
                crc_generator=param if tech_name == "CRC" else "100000111",
                checksum_word_size=param if tech_name == "Checksum" else 8,
                forced_indices=payload_corrupted_indices
            )
            results.append(res)

        return results

    @staticmethod
    def _generate_explanation(
        tech_name: str,
        error_type: str,
        errors_injected: int,
        error_detected: bool,
        diag_details: Dict[str, Any]
    ) -> str:
        """Produce clear DCN textbook rationale."""
        if errors_injected == 0:
            return "Clean transmission. Frame integrity verified with 0 bit errors."

        err_norm = error_type.lower().strip()

        if "Parity" in tech_name or "VRC" in tech_name:
            if errors_injected % 2 == 1:
                return (
                    f"VRC DETECTED error: An odd number of bit errors ({errors_injected}) occurred, "
                    f"which inverted overall frame parity."
                )
            else:
                return (
                    f"VRC MISSED error: An even number of bit errors ({errors_injected}) occurred. "
                    f"In 1D parity, even bit flips cancel each other out, leaving parity invariant (d_min = 2)."
                )

        elif "LRC" in tech_name:
            failed_cols = diag_details.get("failed_columns", [])
            if error_detected:
                return f"LRC DETECTED error: Column parity check failed on column(s) {failed_cols}."
            else:
                return "LRC MISSED error: Even number of bit errors occurred in the exact same column position(s)."

        elif "Checksum" in tech_name:
            if error_detected:
                sum_hex = diag_details.get("final_sum_hex", "")
                return f"Checksum DETECTED error: 1's complement sum ({sum_hex}) does not evaluate to all 1s (0xFF)."
            else:
                return "Checksum MISSED error: Compensating errors occurred in complementary positions."

        elif "CRC" in tech_name:
            rem = diag_details.get("syndrome_remainder", "")
            if error_detected:
                return f"CRC DETECTED error: Modulo-2 polynomial division remainder is non-zero (R = '{rem}')."
            else:
                return "CRC MISSED error: Error polynomial E(x) is an exact multiple of generator G(x)."

        elif "Hamming" in tech_name:
            if diag_details.get("successfully_corrected"):
                corr_pos = diag_details.get("corrected_positions", [])
                return (
                    f"Hamming (7,4) DETECTED and CORRECTED single-bit error: "
                    f"Syndrome identified corrupted bit position(s) {corr_pos} and inverted back to restore original data."
                )
            elif diag_details.get("miscorrected"):
                return (
                    f"Hamming (7,4) DETECTED error but NOT CORRECTABLE: Multiple bit errors in a 7-bit block "
                    f"caused syndrome miscorrection (d_min = 3 can only reliably correct 1 bit per block)."
                )
            elif error_detected:
                return "Hamming (7,4) DETECTED error: Parity syndrome indicated transmission corruption."
            else:
                return "Hamming (7,4) MISSED error: Corrupted bits formed an undetectable codeword."

        return "Verification completed."
