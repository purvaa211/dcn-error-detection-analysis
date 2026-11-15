"""Object-Oriented Error Detection Module for DCN System.

Demonstrates:
- Abstraction: Abstract Base Class `ErrorDetection` defining the protocol.
- Inheritance & Polymorphism: `ParityCheck`, `LRC`, `Checksum`, `CRC` subclassing `ErrorDetection`.
- Encapsulation: Internal algorithm parameters and diagnostic state hidden inside classes.
- Method Overriding: Specific encoding and verification mechanisms per technique.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional

from algorithms.parity import add_vrc, check_vrc, format_vrc_working
from algorithms.lrc import add_lrc, check_lrc, format_lrc_working
from algorithms.checksum import add_checksum, verify_checksum_detailed, format_checksum_working
from algorithms.crc import crc_encode, crc_check_detailed, format_crc_working, CRC_POLYNOMIALS
from algorithms.hamming import hamming_encode, hamming_decode, format_hamming_working


class ErrorDetection(ABC):
    """Abstract Base Class for Data Link / Network Layer Error Detection Strategies.
    
    Establishes the polymorphic interface for encoding sender payloads with
    redundancy and verifying receiver frames.
    """

    def __init__(self, name: str, category: str):
        self._name = name
        self._category = category

    @property
    def name(self) -> str:
        """Human-readable algorithm designation."""
        return self._name

    @property
    def category(self) -> str:
        """Taxonomic category (e.g. Linear Parity, Polynomial, Arithmetic)."""
        return self._category

    @abstractmethod
    def encode(self, data: str) -> str:
        """Encode raw binary payload by appending redundant check bits.
        
        Args:
            data: Binary payload string ('0' and '1').
            
        Returns:
            Protected transmitted frame string.
        """
        pass

    @abstractmethod
    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify the integrity of a received frame.
        
        Args:
            frame: Received binary frame.
            
        Returns:
            Tuple of (is_valid: bool, diagnostics: dict).
        """
        pass

    @abstractmethod
    def get_working_steps(self, data: str) -> str:
        """Generate structured pedagogical step-by-step mathematical working.
        
        Args:
            data: Binary payload string.
            
        Returns:
            Formatted textual trace.
        """
        pass

    @abstractmethod
    def get_redundancy_bits(self, data: str) -> int:
        """Calculate the exact number of redundant check bits appended."""
        pass

    def get_overhead_percentage(self, data: str) -> float:
        """Calculate redundancy overhead percentage relative to original payload."""
        if not data:
            return 0.0
        r = self.get_redundancy_bits(data)
        return (r / len(data)) * 100.0


class ParityCheck(ErrorDetection):
    """Vertical Redundancy Check (VRC) / Simple Parity Strategy.
    
    Appends a single parity bit to guarantee the total count of '1' bits
    satisfies the chosen parity convention (Even Parity by default).
    Minimum Hamming distance: d_min = 2.
    """

    def __init__(self, mode: str = "even"):
        super().__init__(name="Parity Check (VRC)", category="Linear Parity")
        self.mode = mode.lower()

    def encode(self, data: str) -> str:
        return add_vrc(data, mode=self.mode)

    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        return check_vrc(frame, mode=self.mode)

    def get_working_steps(self, data: str) -> str:
        return format_vrc_working(data, mode=self.mode)

    def get_redundancy_bits(self, data: str) -> int:
        return 1


class LRC(ErrorDetection):
    """Longitudinal Redundancy Check (LRC) / 2D Column Parity Strategy.
    
    Partitions the binary stream into fixed-width blocks (default 8 bits)
    and computes column-wise longitudinal parity (Block Check Character / BCC).
    """

    def __init__(self, block_size: int = 8):
        super().__init__(name="LRC", category="Block Parity")
        self.block_size = block_size

    def encode(self, data: str) -> str:
        return add_lrc(data, block_size=self.block_size)

    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        return check_lrc(frame, block_size=self.block_size)

    def get_working_steps(self, data: str) -> str:
        return format_lrc_working(data, block_size=self.block_size)

    def get_redundancy_bits(self, data: str) -> int:
        # Padded frame plus 1 block of BCC parity bits
        padded_len = ((len(data) + self.block_size - 1) // self.block_size) * self.block_size
        padding = padded_len - len(data)
        return padding + self.block_size


class Checksum(ErrorDetection):
    """1's Complement Internet Checksum Strategy.
    
    Partitions data into m-bit words (default 8 bits, 16 bits for RFC 1071),
    accumulates words using 1's complement addition with end-around carry,
    and appends the bitwise inverted sum.
    """

    def __init__(self, word_size: int = 8):
        name = "16-bit Internet Checksum (RFC 1071)" if word_size == 16 else "8-bit Checksum"
        super().__init__(name=name, category="Arithmetic Checksum")
        self.word_size = word_size

    def encode(self, data: str) -> str:
        return add_checksum(data, word_size=self.word_size)

    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        return verify_checksum_detailed(frame, word_size=self.word_size)

    def get_working_steps(self, data: str) -> str:
        return format_checksum_working(data, word_size=self.word_size)

    def get_redundancy_bits(self, data: str) -> int:
        # Redundant word size plus any padding bits added to align
        rem = len(data) % self.word_size
        pad_bits = (self.word_size - rem) % self.word_size
        return pad_bits + self.word_size


class CRC(ErrorDetection):
    """Cyclic Redundancy Check (CRC) Polynomial Division Strategy.
    
    Treats the bitstream as a polynomial over GF(2), appends r zero bits,
    divides by the generator polynomial G(x) using modulo-2 XOR arithmetic,
    and replaces the zeros with the remainder.
    """

    def __init__(self, generator: str = "100000111"):
        deg = len(generator) - 1
        name = f"CRC-{deg}"
        # Match standard names
        for k, v in CRC_POLYNOMIALS.items():
            if v.get("generator") == generator:
                name = k
                break
        super().__init__(name=name, category="Polynomial Division")
        self.generator = generator

    def encode(self, data: str) -> str:
        return crc_encode(data, generator=self.generator)

    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        return crc_check_detailed(frame, generator=self.generator)

    def get_working_steps(self, data: str) -> str:
        return format_crc_working(data, generator=self.generator)

    def get_redundancy_bits(self, data: str) -> int:
        return len(self.generator) - 1


class HammingCode(ErrorDetection):
    """Hamming (7,4) Single-Bit Error-Correcting Code Strategy.
    
    Partitions binary payload into 4-bit nibbles (zero-padded if necessary),
    computes 3 parity bits (even parity) per nibble, and generates 7-bit codewords.
    
    Characteristics:
    - Minimum Hamming distance d_min = 3.
    - Can detect and correct any single-bit error per 7-bit codeword block.
    - In double-bit error conditions, standard (7,4) detects an error but
      miscorrects unless extended with an overall parity bit (SECDED).
    - 3 redundant bits per 4 data bits (75% overhead).
    """

    def __init__(self):
        super().__init__(name="Hamming (7,4)", category="Error-Correcting Code")
        self._last_payload: Optional[str] = None
        self._last_payload_len: Optional[int] = None

    def encode(self, data: str) -> str:
        self._last_payload = data
        self._last_payload_len = len(data)
        return hamming_encode(data)

    def verify(self, frame: str) -> Tuple[bool, Dict[str, Any]]:
        orig_len = self._last_payload_len
        corr_frame, decoded_payload, block_info = hamming_decode(frame, original_payload_len=orig_len)

        # An error is detected if any block had a non-zero syndrome
        any_error_detected = any(b["error_detected"] for b in block_info)
        is_clean = not any_error_detected

        # Check positions of errors across all blocks
        corrected_positions = []
        syndromes = []
        for b in block_info:
            syndromes.append(b["syndrome_bin"])
            if b["error_position"] is not None:
                # Global frame index (0-based)
                global_pos = b["block_index"] * 7 + (b["error_position"] - 1)
                corrected_positions.append(global_pos)

        # Assess correction validity against original payload if available
        if self._last_payload is not None:
            matches_original = (decoded_payload == self._last_payload)
        else:
            matches_original = is_clean or (len(corrected_positions) == 1)

        successfully_corrected = any_error_detected and matches_original
        miscorrected = any_error_detected and not matches_original

        diagnostics = {
            "syndromes": syndromes,
            "error_detected": any_error_detected,
            "corrected": any_error_detected,
            "successfully_corrected": successfully_corrected,
            "miscorrected": miscorrected,
            "corrected_positions": corrected_positions,
            "corrected_frame": corr_frame,
            "decoded_payload": decoded_payload,
            "block_info": block_info
        }

        # For ErrorDetection protocol: is_valid is True if clean frame (no errors detected)
        is_valid = is_clean
        return is_valid, diagnostics

    def get_working_steps(self, data: str) -> str:
        return format_hamming_working(data)

    def get_redundancy_bits(self, data: str) -> int:
        rem = len(data) % 4
        num_blocks = (len(data) + (4 - rem if rem != 0 else 0)) // 4
        return (num_blocks * 7) - len(data)


def get_detection_strategy(
    technique: str,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    parity_mode: str = "even"
) -> ErrorDetection:
    """Factory function for creating ErrorDetection polymorphic instances.
    
    Args:
        technique: Technique name string.
        crc_generator: Polynomial binary string.
        checksum_word_size: 8 or 16 bits.
        parity_mode: 'even' or 'odd'.
        
    Returns:
        Concrete ErrorDetection subclass instance.
    """
    tech = technique.strip().lower()
    if "parity" in tech or "vrc" in tech:
        return ParityCheck(mode=parity_mode)
    elif "lrc" in tech:
        return LRC(block_size=8)
    elif "checksum" in tech:
        return Checksum(word_size=checksum_word_size)
    elif "hamming" in tech:
        return HammingCode()
    elif "crc" in tech:
        gen = crc_generator
        for k, v in CRC_POLYNOMIALS.items():
            if k.lower() == tech:
                gen = v["generator"]
                break
        return CRC(generator=gen)
    else:
        # Default fallback
        return CRC(generator=crc_generator)
