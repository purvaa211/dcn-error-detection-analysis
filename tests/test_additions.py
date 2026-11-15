"""Unit tests for newly added DCN features:
1. Hamming (7,4) encode/decode round trip with no error
2. Every single-bit flip position (0 to 6) in a 7-bit block is corrected
3. A 2-bit flip is not reported as successfully corrected
4. Parity misses an even-bit error
5. CRC-8 detects a single-bit error
6. get_theoretical_detection returns 1.0 for parity with odd errors and 0.0 for even errors
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from algorithms.hamming import (
    hamming_encode,
    hamming_decode,
    encode_74_block,
    decode_74_block,
    format_hamming_working
)
from algorithms.parity import check_parity, add_parity
from algorithms.crc import crc_encode, crc_check_detailed
from core.detection import HammingCode, get_detection_strategy
from experiments.theory import get_theoretical_detection


class TestAdditions(unittest.TestCase):
    def test_hamming_roundtrip_no_error(self):
        """Hamming encode then decode round trip with no error."""
        payloads = ["1011", "0000", "1111", "10110011", "1011001111001100", "101"]
        for data in payloads:
            encoded = hamming_encode(data)
            # Length must be multiple of 7
            self.assertEqual(len(encoded) % 7, 0)
            corr_frame, extracted_data, block_info = hamming_decode(encoded, original_payload_len=len(data))
            self.assertEqual(corr_frame, encoded)
            self.assertEqual(extracted_data, data)
            # No errors detected in any block
            for b in block_info:
                self.assertFalse(b["error_detected"])
                self.assertEqual(b["syndrome_int"], 0)
                self.assertIsNone(b["error_position"])

    def test_hamming_all_single_bit_flip_positions_corrected(self):
        """Every single-bit flip position (0 to 6) in a 7-bit block is corrected."""
        nibble = "1011"
        codeword = encode_74_block(nibble)  # 7-bit string: '0110011'
        self.assertEqual(len(codeword), 7)

        for pos in range(7):
            # Flip bit at index pos (0-based)
            corrupted_list = list(codeword)
            corrupted_list[pos] = "0" if corrupted_list[pos] == "1" else "1"
            corrupted = "".join(corrupted_list)

            corr_block, extracted, diag = decode_74_block(corrupted)

            # 1-based error position must equal pos + 1
            self.assertTrue(diag["error_detected"])
            self.assertEqual(diag["error_position"], pos + 1)
            # Corrected block must match original codeword
            self.assertEqual(corr_block, codeword)
            # Extracted nibble must match original data nibble
            self.assertEqual(extracted, nibble)

    def test_hamming_2bit_flip_not_successfully_corrected(self):
        """A 2-bit flip is not reported as successfully corrected."""
        h = HammingCode()
        data = "1011"
        frame = h.encode(data)  # '0110011'

        # Invert 2 bits in the 7-bit block (e.g. index 2 and index 4)
        bits = list(frame)
        bits[2] = "0" if bits[2] == "1" else "1"
        bits[4] = "0" if bits[4] == "1" else "1"
        corrupted_frame = "".join(bits)

        is_valid, diagnostics = h.verify(corrupted_frame)

        # An error must be detected
        self.assertTrue(diagnostics["error_detected"])
        self.assertFalse(is_valid)

        # Must NOT report successful correction because 2-bit error caused miscorrection
        self.assertFalse(diagnostics["successfully_corrected"])
        self.assertTrue(diagnostics["miscorrected"])
        self.assertNotEqual(diagnostics["decoded_payload"], data)

    def test_parity_misses_even_bit_error(self):
        """Parity misses an even-bit error (even bit flips leave parity invariant)."""
        data = "10110011"
        frame = add_parity(data, mode="even")  # Even parity

        # Invert exactly 2 bits (e.g. indices 0 and 1)
        frame_chars = list(frame)
        frame_chars[0] = "0" if frame_chars[0] == "1" else "1"
        frame_chars[1] = "0" if frame_chars[1] == "1" else "1"
        corrupted_frame = "".join(frame_chars)

        is_valid, details = check_parity(corrupted_frame, mode="even")

        # Parity erroneously accepts the frame as valid because parity bit still matches!
        self.assertTrue(is_valid)
        self.assertTrue(details["parity_match"])

    def test_crc8_detects_single_bit_error(self):
        """CRC-8 detects a single-bit error."""
        data = "1011001111001100"
        generator = "100000111"  # CRC-8
        frame = crc_encode(data, generator=generator)

        # Flip any single bit in the frame
        for flip_pos in [0, 4, len(data) - 1, len(frame) - 1]:
            frame_chars = list(frame)
            frame_chars[flip_pos] = "0" if frame_chars[flip_pos] == "1" else "1"
            corrupted_frame = "".join(frame_chars)

            is_valid, details = crc_check_detailed(corrupted_frame, generator=generator)
            self.assertFalse(is_valid)
            self.assertNotEqual(details["syndrome_remainder"], "0" * (len(generator) - 1))

    def test_theoretical_detection_parity(self):
        """get_theoretical_detection returns 1.0 for parity with odd errors and 0.0 for even errors."""
        # Single bit
        res_single = get_theoretical_detection("VRC / Parity", "single", 1)
        self.assertEqual(res_single["value"], 1.0)

        # Odd numbers
        for odd_k in [1, 3, 5, 7, 9]:
            res_odd = get_theoretical_detection("VRC / Parity", "multiple", odd_k)
            self.assertEqual(res_odd["value"], 1.0)
            self.assertIn("100%", res_odd["note"])

        # Even numbers
        for even_k in [2, 4, 6, 8]:
            res_even = get_theoretical_detection("VRC / Parity", "multiple", even_k)
            self.assertEqual(res_even["value"], 0.0)
            self.assertIn("0%", res_even["note"])

    def test_theoretical_detection_crc8(self):
        """get_theoretical_detection returns accurate bounds for CRC-8."""
        # Single bit
        self.assertEqual(get_theoretical_detection("CRC", "single", 1)["value"], 1.0)

        # Odd bit errors
        self.assertEqual(get_theoretical_detection("CRC", "multiple", 3)["value"], 1.0)
        self.assertEqual(get_theoretical_detection("CRC", "multiple", 5)["value"], 1.0)

        # Even bit errors -> None (no universal guarantee)
        self.assertIsNone(get_theoretical_detection("CRC", "multiple", 2)["value"])

        # Bursts <= 8
        self.assertEqual(get_theoretical_detection("CRC", "burst", 4)["value"], 1.0)
        self.assertEqual(get_theoretical_detection("CRC", "burst", 8)["value"], 1.0)

        # Long burst (16)
        long_burst = get_theoretical_detection("CRC", "burst", 16)
        self.assertAlmostEqual(long_burst["value"], 1.0 - 2.0**-8, places=5)


if __name__ == "__main__":
    unittest.main()
