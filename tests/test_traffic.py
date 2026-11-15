"""Unit tests for Network Traffic Error Detection & Packet Inspection.

Validates:
1. PCAP / PCAPNG parsing and metadata extraction via Scapy.
2. Checksum auditing across IPv4, TCP, UDP, IPv6 (RFC 8200), and checksum offload artefacts.
3. Payload bitstream extraction, hex dumping, and empty-payload handshake handling.
4. Application of canonical error detection (Parity, LRC, Checksum, CRC) and Hamming (7,4)
   to extracted real-world packet payloads.
5. Controlled error injection (single-bit, multiple-bit, burst) and subsequent detection.
6. Synchronized comparative analysis across all techniques.
"""

import os
import unittest

from core.traffic_analysis import (
    generate_sample_pcap,
    parse_pcap_file,
    extract_packet_payload_details,
    evaluate_traffic_error_detection,
    compare_all_traffic_techniques,
    inspect_packet_checksums
)


class TestTrafficAnalysis(unittest.TestCase):
    """Test suite for traffic analysis and real packet error detection."""

    @classmethod
    def setUpClass(cls):
        """Generate a clean synthetic PCAP for testing."""
        cls.test_pcap_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "samples",
            "test_run_capture.pcap"
        )
        generate_sample_pcap(cls.test_pcap_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up the test PCAP file."""
        if os.path.exists(cls.test_pcap_path):
            try:
                os.remove(cls.test_pcap_path)
            except OSError:
                pass

    def test_01_pcap_parsing_and_summary(self):
        """Test parsing PCAP file and calculating summary statistics."""
        data = parse_pcap_file(self.test_pcap_path)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["packets"]), 7)

        summary = data["summary"]
        self.assertEqual(summary["total_packets"], 7)
        self.assertGreater(summary["displayed_packets"], 0)
        self.assertGreater(summary["packets_with_payload"], 0)
        self.assertIn("HTTP", summary["protocols"])
        self.assertIn("DNS", summary["protocols"])
        self.assertIn("ICMP", summary["protocols"])

    def test_02_checksum_auditing(self):
        """Test honest checksum auditing across different protocols and conditions."""
        data = parse_pcap_file(self.test_pcap_path)
        packets = data["packets"]

        # Packet 1 is HTTP GET over IPv4 TCP (clean)
        pkt1 = packets[0]
        self.assertEqual(pkt1["protocol"], "HTTP (TCP)")
        self.assertIn(pkt1["checksum_status"], ["valid", "offload", "unverified"])

        # Packet 5 is TCP SYN (0 payload)
        pkt5 = packets[4]
        self.assertEqual(pkt5["payload_size_bytes"], 0)
        self.assertFalse(pkt5["has_payload"])

        # Packet 6 is IPv6 (RFC 8200: no header checksum)
        pkt6 = packets[5]
        self.assertEqual(pkt6["protocol"], "HTTP (TCP)")  # port 80 identified as HTTP
        self.assertEqual(pkt6["checksum_status"], "no_checksum")
        self.assertIn("RFC 8200", pkt6["checksum_details"])

        # Packet 7 has an intentionally corrupted IPv4 header checksum
        pkt7 = packets[6]
        self.assertEqual(pkt7["checksum_status"], "mismatch")
        self.assertIn("Error Detected", pkt7["checksum_label"])

    def test_03_payload_extraction(self):
        """Test binary bitstream, hex dump, and ASCII extraction from packets."""
        # Packet 1 has HTTP GET payload (index 0)
        details = extract_packet_payload_details(self.test_pcap_path, 0)
        self.assertTrue(details["success"])
        self.assertTrue(details["has_payload"])
        self.assertGreater(details["byte_length"], 0)
        self.assertEqual(details["bit_length"], details["byte_length"] * 8)
        self.assertTrue(all(c in "01" for c in details["binary_string"]))
        self.assertIn("GET /index.html", details["ascii_preview"])
        self.assertIn("47 45 54", details["hex_dump"])

        # Packet 5 (TCP SYN) has 0 payload (index 4)
        empty_details = extract_packet_payload_details(self.test_pcap_path, 4)
        self.assertTrue(empty_details["success"])
        self.assertFalse(empty_details["has_payload"])
        self.assertIn("0 application payload bytes", empty_details["reason"])

    def test_04_error_detection_on_clean_payload(self):
        """Test applying detection algorithms to clean traffic payload."""
        bin_payload = "010000010100001001000011"  # "ABC" = 24 bits
        techniques = ["VRC / Parity", "LRC", "Checksum", "CRC", "Hamming (7,4)"]

        for tech in techniques:
            res = evaluate_traffic_error_detection(
                binary_payload=bin_payload,
                technique=tech,
                inject_error=False
            )
            self.assertTrue(res["success"])
            self.assertEqual(res["errors_injected"], 0)
            self.assertIn("CLEAN", res["verdict"])
            self.assertFalse(res["error_detected"])
            self.assertGreater(res["overhead_bits"], 0)
            self.assertGreater(res["payload_bits"], 0)

    def test_05_error_injection_and_detection(self):
        """Test injecting single, multiple, and burst errors into traffic payload."""
        bin_payload = "0100100001100101011011000110110001101111"  # "Hello" (40 bits)

        # 1. Single-bit error detection with CRC
        crc_res = evaluate_traffic_error_detection(
            binary_payload=bin_payload,
            technique="CRC",
            inject_error=True,
            error_type="single",
            error_amount=1
        )
        self.assertEqual(crc_res["errors_injected"], 1)
        self.assertTrue(crc_res["error_detected"])
        self.assertIn("ERROR DETECTED", crc_res["verdict"])
        self.assertEqual(len(crc_res["flipped_indices"]), 1)

        # 2. Burst error detection with CRC
        burst_res = evaluate_traffic_error_detection(
            binary_payload=bin_payload,
            technique="CRC",
            inject_error=True,
            error_type="burst",
            error_amount=4
        )
        self.assertGreaterEqual(burst_res["errors_injected"], 1)
        self.assertTrue(burst_res["error_detected"])

        # 3. Hamming (7,4) single-bit correction
        hamming_res = evaluate_traffic_error_detection(
            binary_payload=bin_payload,
            technique="Hamming (7,4)",
            inject_error=True,
            error_type="single",
            error_amount=1
        )
        self.assertEqual(hamming_res["errors_injected"], 1)
        self.assertIn("CORRECTED", hamming_res["verdict"])

    def test_06_comparative_traffic_analysis(self):
        """Test synchronized comparison of all 5 techniques on captured traffic."""
        bin_payload = "010100110101100101010011"  # "SYS" (24 bits)

        # Clean comparison
        clean_comp = compare_all_traffic_techniques(bin_payload, inject_error=False)
        self.assertEqual(len(clean_comp["results"]), 5)
        for r in clean_comp["results"]:
            self.assertEqual(r["errors_injected"], 0)
            self.assertFalse(r["error_detected"])

        # Corrupted comparison (2-bit error)
        corrupt_comp = compare_all_traffic_techniques(
            bin_payload,
            inject_error=True,
            error_type="multiple",
            error_amount=2
        )
        self.assertEqual(len(corrupt_comp["results"]), 5)
        self.assertEqual(len(corrupt_comp["forced_indices"]), 2)
        # All 5 techniques evaluate the exact same corrupted bitstream
        tech_names = [r["technique"] for r in corrupt_comp["results"]]
        self.assertEqual(len(tech_names), 5)
        self.assertTrue(any("Parity" in t for t in tech_names))
        self.assertTrue(any("LRC" in t for t in tech_names))
        self.assertTrue(any("Checksum" in t for t in tech_names))
        self.assertTrue(any("CRC" in t for t in tech_names))
        self.assertTrue(any("Hamming" in t for t in tech_names))


if __name__ == "__main__":
    unittest.main()
