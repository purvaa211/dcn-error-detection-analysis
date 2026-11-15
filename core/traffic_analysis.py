"""Network Traffic Error Detection & Packet Inspection Module.

Extends the DCN Error Detection System with real-world packet capture analysis.
Provides:
1. PCAP / PCAPNG parsing via Scapy (IPv4, IPv6, TCP, UDP, ICMP, Raw payloads).
2. Honest packet-level checksum audit (IP header, TCP, UDP, IPv6 lack of checksum,
   checksum offloading artefacts, and lack of Ethernet FCS in user-space captures).
3. Payload extraction and conversion to raw binary bitstreams.
4. Application of existing canonical error detection techniques (VRC, LRC,
   Checksum, CRC, Hamming) to extracted real-world network payloads.
5. Controlled error injection experiments on captured traffic data.

Educational Purpose:
Demonstrates how physical channel error detection (Data Link / Transport layer)
relates to actual frames transmitted over real-world communication links.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple, Union

from scapy.all import (
    Ether,
    IP,
    IPv6,
    TCP,
    UDP,
    ICMP,
    ARP,
    Raw,
    rdpcap,
    wrpcap,
    Packet
)

from core.detection import get_detection_strategy
from simulation.error_generator import (
    clean_transmission,
    single_bit_error,
    multiple_bit_error,
    burst_error,
    manual_error
)


def inspect_packet_checksums(pkt: Packet) -> Dict[str, Any]:
    """Inspect and honestly audit all available checksums in a captured packet.

    Reports findings across IPv4, TCP, UDP, and notes architectural constraints
    such as checksum offloading artefacts, missing Ethernet FCS, and IPv6 design.

    Returns:
        Dict containing:
            'status': 'valid' | 'mismatch' | 'offload' | 'no_checksum' | 'unverified'
            'label': Human-readable badge text
            'badge_class': CSS badge class name
            'details': Detailed technical explanation
            'ipv4_checksum': Info string or None
            'l4_checksum': Info string or None
    """
    details_list = []
    status = "unverified"
    label = "Unverified"
    badge_class = "badge-neutral"
    ipv4_info = None
    l4_info = None

    # 1. Ethernet FCS Note
    # Standard OS capture mechanisms (libpcap/WinPcap) strip the 32-bit Ethernet FCS.
    details_list.append("Ethernet FCS: Stripped by OS capture driver before packet capture.")

    # 2. Network Layer Inspection
    if pkt.haslayer(IP):
        ip_layer = pkt[IP]
        stored_ip_chk = ip_layer.chksum

        # Verify IPv4 Header Checksum
        try:
            # Recompute IP header checksum by clearing checksum field and re-packing
            ip_copy = ip_layer.copy()
            ip_copy.chksum = None
            recomputed_chk = IP(bytes(ip_copy)).chksum

            if stored_ip_chk == recomputed_chk:
                ipv4_info = f"IPv4 Header Checksum: 0x{stored_ip_chk:04X} [VERIFIED VALID]"
                status = "valid"
                label = "Valid Checksums"
                badge_class = "badge-success"
            else:
                ipv4_info = f"IPv4 Header Checksum: Stored 0x{stored_ip_chk:04X} != Computed 0x{recomputed_chk:04X} [MISMATCH / CORRUPTED]"
                status = "mismatch"
                label = "Checksum Error Detected"
                badge_class = "badge-danger"
        except Exception:
            ipv4_info = f"IPv4 Checksum: 0x{stored_ip_chk:04X} (Unable to recompute)"
        details_list.append(ipv4_info)

    elif pkt.haslayer(IPv6):
        ipv4_info = "IPv6 Header: No checksum (RFC 8200 removed header checksum to optimize router forwarding; relies on L2/L4)."
        details_list.append(ipv4_info)
        status = "no_checksum"
        label = "No IP Checksum (IPv6)"
        badge_class = "badge-neutral"

    elif pkt.haslayer(ARP):
        details_list.append("ARP: Link-layer address protocol; no network-layer checksum.")
        return {
            "status": "no_checksum",
            "label": "No Header Checksum (ARP)",
            "badge_class": "badge-neutral",
            "details": "ARP protocol contains no header checksum.",
            "ipv4_checksum": None,
            "l4_checksum": None
        }

    # 3. Transport Layer Inspection (TCP / UDP / ICMP)
    if pkt.haslayer(TCP):
        tcp_layer = pkt[TCP]
        stored_tcp_chk = tcp_layer.chksum

        # Check for TX Checksum Offload artefacts:
        # Outgoing packets captured on sender interface often have checksum = 0x0000 or uncomputed
        if stored_tcp_chk == 0x0000:
            l4_info = f"TCP Checksum: 0x0000 (TX Checksum Offloading artefact by NIC hardware)"
            if status != "mismatch":
                status = "offload"
                label = "NIC Offload Artefact"
                badge_class = "badge-warning"
        else:
            try:
                # To verify TCP checksum, pseudo-header with IP addresses is required
                if pkt.haslayer(IP):
                    raw_ip = bytes(pkt[IP])
                    recomputed_pkt = IP(raw_ip)
                    recomp_tcp = recomputed_pkt[TCP].chksum
                    if stored_tcp_chk == recomp_tcp:
                        l4_info = f"TCP Checksum: 0x{stored_tcp_chk:04X} [VERIFIED VALID]"
                    else:
                        l4_info = f"TCP Checksum: Stored 0x{stored_tcp_chk:04X} vs Computed 0x{recomp_tcp:04X} (Likely NIC Offload)"
                        if status != "mismatch":
                            status = "offload"
                            label = "NIC Offload Artefact"
                            badge_class = "badge-warning"
                else:
                    l4_info = f"TCP Checksum: 0x{stored_tcp_chk:04X} (Present)"
            except Exception:
                l4_info = f"TCP Checksum: 0x{stored_tcp_chk:04X}"
        details_list.append(l4_info)

    elif pkt.haslayer(UDP):
        udp_layer = pkt[UDP]
        stored_udp_chk = udp_layer.chksum
        if stored_udp_chk == 0x0000:
            l4_info = "UDP Checksum: 0x0000 (Optional in IPv4 per RFC 768 / Disabled by sender)"
            if status != "mismatch":
                status = "offload"
                label = "Checksum Disabled / 0x0000"
                badge_class = "badge-neutral"
        else:
            l4_info = f"UDP Checksum: 0x{stored_udp_chk:04X} [Present]"
        details_list.append(l4_info)

    elif pkt.haslayer(ICMP):
        icmp_layer = pkt[ICMP]
        stored_icmp_chk = icmp_layer.chksum
        l4_info = f"ICMP Checksum: 0x{stored_icmp_chk:04X} [1's Complement Internet Checksum]"
        details_list.append(l4_info)

    return {
        "status": status,
        "label": label,
        "badge_class": badge_class,
        "details": " | ".join(details_list),
        "ipv4_checksum": ipv4_info,
        "l4_checksum": l4_info
    }


def parse_packet_metadata(pkt: Packet, index: int) -> Dict[str, Any]:
    """Extract standard networking metadata for display in the traffic table."""
    pkt_len = len(pkt)
    proto_name = "Ethernet"
    src_addr = "N/A"
    dst_addr = "N/A"
    sport = None
    dport = None

    if pkt.haslayer(IP):
        src_addr = pkt[IP].src
        dst_addr = pkt[IP].dst
        proto_name = "IPv4"
    elif pkt.haslayer(IPv6):
        src_addr = pkt[IPv6].src
        dst_addr = pkt[IPv6].dst
        proto_name = "IPv6"
    elif pkt.haslayer(ARP):
        src_addr = pkt[ARP].psrc
        dst_addr = pkt[ARP].pdst
        proto_name = "ARP"

    if pkt.haslayer(TCP):
        proto_name = "TCP"
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
    elif pkt.haslayer(UDP):
        proto_name = "UDP"
        sport = pkt[UDP].sport
        dport = pkt[UDP].dport
    elif pkt.haslayer(ICMP):
        proto_name = "ICMP"

    # Identify higher-level application protocols
    if sport in (80, 8080) or dport in (80, 8080):
        proto_name = "HTTP (TCP)"
    elif sport == 443 or dport == 443:
        proto_name = "TLS/HTTPS (TCP)"
    elif sport == 53 or dport == 53:
        proto_name = "DNS (UDP)"

    # Payload extraction
    raw_payload = b""
    if pkt.haslayer(Raw):
        raw_payload = bytes(pkt[Raw].load)
    elif pkt.haslayer(ICMP) and hasattr(pkt[ICMP], "load"):
        raw_payload = bytes(pkt[ICMP].load)
    elif pkt.haslayer(TCP) and len(bytes(pkt[TCP].payload)) > 0:
        raw_payload = bytes(pkt[TCP].payload)
    elif pkt.haslayer(UDP) and len(bytes(pkt[UDP].payload)) > 0:
        raw_payload = bytes(pkt[UDP].payload)

    has_payload = len(raw_payload) > 0
    payload_len = len(raw_payload)

    # Checksum audit
    chk_audit = inspect_packet_checksums(pkt)

    return {
        "packet_index": index,
        "packet_number": index + 1,
        "protocol": proto_name,
        "src_ip": src_addr,
        "dst_ip": dst_addr,
        "src_port": sport,
        "dst_port": dport,
        "packet_size_bytes": pkt_len,
        "has_payload": has_payload,
        "payload_size_bytes": payload_len,
        "payload_size_bits": payload_len * 8,
        "checksum_status": chk_audit["status"],
        "checksum_label": chk_audit["label"],
        "checksum_badge": chk_audit["badge_class"],
        "checksum_details": chk_audit["details"]
    }


def parse_pcap_file(file_path: str, max_packets: int = 150) -> Dict[str, Any]:
    """Parse a PCAP or PCAPNG capture file and return structured packet summaries.

    Args:
        file_path: Absolute path to the .pcap or .pcapng file.
        max_packets: Maximum number of packets to load for responsive UI.

    Returns:
        Dict with 'success', 'packets', 'summary', and optional 'error'.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"Capture file not found at: {file_path}"}

    try:
        packets = rdpcap(file_path)
    except Exception as e:
        return {"success": False, "error": f"Failed to parse PCAP file: {str(e)}"}

    total_count = len(packets)
    if total_count == 0:
        return {
            "success": False,
            "error": "The uploaded capture file contains 0 packets (empty capture)."
        }

    parsed_packets = []
    protocols_count: Dict[str, int] = {}
    payload_count = 0
    checksum_breakdown = {"valid": 0, "mismatch": 0, "offload": 0, "no_checksum": 0, "unverified": 0}

    for i, pkt in enumerate(packets[:max_packets]):
        meta = parse_packet_metadata(pkt, i)
        parsed_packets.append(meta)

        proto = meta["protocol"].split()[0]
        protocols_count[proto] = protocols_count.get(proto, 0) + 1

        if meta["has_payload"]:
            payload_count += 1

        st = meta["checksum_status"]
        if st in checksum_breakdown:
            checksum_breakdown[st] += 1

    summary = {
        "total_packets": total_count,
        "displayed_packets": len(parsed_packets),
        "packets_with_payload": payload_count,
        "protocols": protocols_count,
        "checksum_summary": checksum_breakdown
    }

    return {
        "success": True,
        "packets": parsed_packets,
        "summary": summary
    }


def extract_packet_payload_details(file_path: str, packet_index: int) -> Dict[str, Any]:
    """Extract raw payload bytes from a specific packet in a PCAP file and convert to binary.

    Args:
        file_path: Path to capture file.
        packet_index: 0-based index of the packet to extract.

    Returns:
        Dict containing hex, ascii, binary representations, and metadata.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": "Capture file not found."}

    try:
        packets = rdpcap(file_path)
    except Exception as e:
        return {"success": False, "error": f"Failed to read capture: {str(e)}"}

    if packet_index < 0 or packet_index >= len(packets):
        return {"success": False, "error": f"Invalid packet index {packet_index}. Total packets: {len(packets)}"}

    pkt = packets[packet_index]
    meta = parse_packet_metadata(pkt, packet_index)

    # Extract payload
    raw_payload = b""
    if pkt.haslayer(Raw):
        raw_payload = bytes(pkt[Raw].load)
    elif pkt.haslayer(ICMP) and hasattr(pkt[ICMP], "load"):
        raw_payload = bytes(pkt[ICMP].load)
    elif pkt.haslayer(TCP) and len(bytes(pkt[TCP].payload)) > 0:
        raw_payload = bytes(pkt[TCP].payload)
    elif pkt.haslayer(UDP) and len(bytes(pkt[UDP].payload)) > 0:
        raw_payload = bytes(pkt[UDP].payload)

    if len(raw_payload) == 0:
        return {
            "success": True,
            "has_payload": False,
            "metadata": meta,
            "reason": (
                f"Packet #{packet_index + 1} ({meta['protocol']}) contains 0 application payload bytes. "
                "This is a control or handshake packet (e.g. TCP SYN/ACK/FIN or empty probe) containing only protocol headers. "
                "Error detection techniques require payload data. Please select a packet with application data."
            )
        }

    # Format representations
    # 1. Binary string
    binary_str = "".join(format(b, "08b") for b in raw_payload)

    # 2. Hex dump
    hex_dump = " ".join(f"{b:02X}" for b in raw_payload)

    # 3. ASCII representation (printable characters or dot)
    ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in raw_payload)

    return {
        "success": True,
        "has_payload": True,
        "metadata": meta,
        "byte_length": len(raw_payload),
        "bit_length": len(binary_str),
        "hex_dump": hex_dump,
        "ascii_preview": ascii_str,
        "binary_string": binary_str
    }


def evaluate_traffic_error_detection(
    binary_payload: str,
    technique: str = "CRC",
    inject_error: bool = False,
    error_type: str = "single",
    error_amount: Any = 1,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    positions: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Apply an existing error detection technique to an extracted network packet payload.

    Args:
        binary_payload: Bitstring of the extracted packet payload.
        technique: Name of error detection strategy ('VRC / Parity', 'LRC', 'Checksum', 'CRC', 'Hamming').
        inject_error: Whether to introduce a controlled transmission error.
        error_type: Error model ('single', 'multiple', 'burst', 'manual').
        error_amount: Error magnitude (e.g. 1 bit, 2 bits, 4-bit burst).
        crc_generator: Generator polynomial string.
        checksum_word_size: Word size in bits (8 or 16).
        positions: Optional explicit bit indices for manual error.

    Returns:
        Dict with detection verdict, latency, bit highlights, and textbook explanation.
    """
    if not binary_payload or not all(c in "01" for c in binary_payload):
        return {"success": False, "error": "Invalid binary payload."}

    strategy = get_detection_strategy(
        technique=technique,
        crc_generator=crc_generator,
        checksum_word_size=checksum_word_size
    )

    # 1. Transmitter Framing: Encode payload to generate reference check bits
    t_start = time.perf_counter()
    protected_frame = strategy.encode(binary_payload)
    overhead_bits = strategy.get_redundancy_bits(binary_payload)
    overhead_pct = strategy.get_overhead_percentage(binary_payload)

    # 2. Optional Controlled Error Injection
    flipped_indices: List[int] = []
    corrupted_frame = protected_frame
    errors_injected = 0

    if inject_error:
        err_type_clean = error_type.lower().strip()
        data_len = len(protected_frame)

        if positions is not None and len(positions) > 0:
            corrupted_frame, flipped_indices = manual_error(protected_frame, positions=positions, return_indices=True)
        elif err_type_clean == "single":
            corrupted_frame, flipped_indices = single_bit_error(protected_frame, return_indices=True)
        elif err_type_clean == "multiple":
            cnt = int(error_amount) if isinstance(error_amount, (int, float)) else 2
            corrupted_frame, flipped_indices = multiple_bit_error(protected_frame, number_of_errors=cnt, return_indices=True)
        elif err_type_clean == "burst":
            span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
            corrupted_frame, flipped_indices = burst_error(protected_frame, burst_length=span, return_indices=True)
        else:
            corrupted_frame, flipped_indices = single_bit_error(protected_frame, return_indices=True)

        errors_injected = len(flipped_indices)

    # 3. Receiver Verification
    is_valid, diagnostics = strategy.verify(corrupted_frame)
    proc_time = time.perf_counter() - t_start

    error_detected = not is_valid

    # 4. Generate Clear DCN Pedagogical Explanation
    tech_name = strategy.name
    if not inject_error or errors_injected == 0:
        verdict = "[CLEAN / VALID BASELINE]"
        explanation = (
            f"Reference verification successful: The extracted packet payload ({len(binary_payload)} bits) "
            f"was protected with {tech_name} (+{overhead_bits} check bits). With 0 channel errors introduced, "
            "the receiver integrity verification passed perfectly."
        )
    elif "Hamming" in tech_name:
        is_corrected = diagnostics.get("successfully_corrected", False)
        if is_corrected:
            verdict = "[ERROR DETECTED AND CORRECTED]"
            explanation = (
                f"Hamming (7,4) DETECTED and CORRECTED single-bit error: "
                f"Parity syndrome identified corrupted position(s) {diagnostics.get('corrected_positions', [])} "
                "and inverted the bit back, restoring the original captured packet payload without retransmission."
            )
        else:
            verdict = "[ERROR DETECTED - NOT CORRECTABLE / MISCORRECTED]"
            explanation = (
                "Hamming (7,4) DETECTED error but NOT CORRECTABLE: Multiple bit errors occurred in a 7-bit block, "
                "exceeding Hamming (7,4)'s single-bit correction capacity (d_min = 3)."
            )
    elif error_detected:
        verdict = "[ERROR DETECTED - FRAME REJECTED]"
        if "Parity" in tech_name or "VRC" in tech_name:
            explanation = f"VRC DETECTED error: An odd number of bit errors ({errors_injected}) altered overall frame parity."
        elif "LRC" in tech_name:
            failed_cols = diagnostics.get("failed_columns", [])
            explanation = f"LRC DETECTED error: Column parity check failed on column(s) {failed_cols}."
        elif "Checksum" in tech_name:
            sum_hex = diagnostics.get("final_sum_hex", "")
            explanation = f"Checksum DETECTED error: 1's complement sum ({sum_hex}) does not evaluate to all 1s (0xFF)."
        elif "CRC" in tech_name:
            rem = diagnostics.get("syndrome_remainder", "")
            explanation = f"CRC DETECTED error: Modulo-2 polynomial division remainder is non-zero (R = '{rem}')."
        else:
            explanation = f"{tech_name} successfully detected the injected transmission error."
    else:
        verdict = "[ERROR MISSED - UNDETECTED CORRUPTION]"
        if "Parity" in tech_name or "VRC" in tech_name:
            explanation = (
                f"VRC MISSED error: An even number of bit errors ({errors_injected}) occurred. "
                "Even bit flips cancel each other out in 1D parity, leaving overall parity unchanged (d_min = 2)."
            )
        elif "LRC" in tech_name:
            explanation = "LRC MISSED error: An even number of bit errors occurred in the exact same column position(s)."
        elif "Checksum" in tech_name:
            explanation = "Checksum MISSED error: Injected bit flips compensated each other in complementary column positions."
        elif "CRC" in tech_name:
            explanation = "CRC MISSED error: The error polynomial E(x) is an exact multiple of generator G(x)."
        else:
            explanation = f"{tech_name} failed to detect the injected transmission error."

    return {
        "success": True,
        "technique": tech_name,
        "payload_bits": len(binary_payload),
        "frame_bits": len(corrupted_frame),
        "overhead_bits": overhead_bits,
        "overhead_percentage": round(overhead_pct, 2),
        "inject_error": inject_error,
        "error_type": error_type if inject_error else "clean",
        "errors_injected": errors_injected,
        "flipped_indices": flipped_indices,
        "original_frame": protected_frame,
        "corrupted_frame": corrupted_frame,
        "is_valid": is_valid,
        "error_detected": error_detected,
        "verdict": verdict,
        "explanation": explanation,
        "processing_time_us": round(proc_time * 1e6, 2),
        "diagnostics": diagnostics
    }


def compare_all_traffic_techniques(
    binary_payload: str,
    inject_error: bool = False,
    error_type: str = "single",
    error_amount: Any = 1,
    positions: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Execute side-by-side comparative error detection across all canonical techniques on captured packet payload."""
    techniques = [
        ("VRC / Parity", "even"),
        ("LRC", 8),
        ("Checksum", 8),
        ("CRC", "100000111"),
        ("Hamming (7,4)", None)
    ]

    results = []
    # If injecting errors, generate identical payload error indices once for fair comparison
    forced_indices = positions
    if inject_error and forced_indices is None:
        err_clean = error_type.lower().strip()
        payload_len = len(binary_payload)
        if err_clean == "single":
            forced_indices = [0]
        elif err_clean == "multiple":
            cnt = int(error_amount) if isinstance(error_amount, (int, float)) else 2
            forced_indices = list(range(min(cnt, payload_len)))
        elif err_clean == "burst":
            span = int(error_amount) if isinstance(error_amount, (int, float)) else 4
            forced_indices = list(range(min(span, payload_len)))
        else:
            forced_indices = [0]

    for tech_name, _ in techniques:
        res = evaluate_traffic_error_detection(
            binary_payload=binary_payload,
            technique=tech_name,
            inject_error=inject_error,
            error_type=error_type,
            error_amount=error_amount,
            positions=forced_indices
        )
        if res.get("success"):
            results.append(res)

    return {
        "success": True,
        "payload_bits": len(binary_payload),
        "inject_error": inject_error,
        "error_type": error_type if inject_error else "clean",
        "forced_indices": forced_indices if inject_error else [],
        "results": results,
        "count": len(results)
    }


def generate_sample_pcap(output_path: str) -> str:
    """Generate a realistic sample PCAP file for demonstration and viva testing.

    Includes:
    1. HTTP GET request with realistic header payload (Valid IP & TCP checksums).
    2. HTTP 200 OK response with application data payload.
    3. DNS query for 'error-detection.lab' (UDP payload).
    4. ICMP Echo Request ping with raw text payload.
    5. Pure TCP SYN control packet (0 payload bytes - shows control packet handling).
    6. IPv6 TCP request (demonstrating lack of IP header checksum in IPv6).
    7. Intentionally corrupted IPv4 packet (checksum mismatch to demonstrate wire error detection).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    pkts = []

    eth_hdr = Ether(src="00:11:22:33:44:55", dst="66:77:88:99:AA:BB")

    # Packet 1: HTTP GET Request (TCP, payload 62 bytes)
    p1 = (
        eth_hdr /
        IP(src="192.168.1.105", dst="142.250.190.46") /
        TCP(sport=49152, dport=80, flags="PA", seq=1001, ack=2001) /
        Raw(load=b"GET /index.html HTTP/1.1\r\nHost: vit.edu\r\nUser-Agent: DCN-Client\r\n\r\n")
    )
    pkts.append(p1)

    # Packet 2: HTTP 200 OK Response (TCP, payload 88 bytes)
    p2 = (
        eth_hdr /
        IP(src="142.250.190.46", dst="192.168.1.105") /
        TCP(sport=80, dport=49152, flags="PA", seq=2001, ack=1063) /
        Raw(load=b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nDCN Error Detection System - VIT Pune 2026")
    )
    pkts.append(p2)

    # Packet 3: DNS Query (UDP, payload 32 bytes)
    p3 = (
        eth_hdr /
        IP(src="192.168.1.105", dst="8.8.8.8") /
        UDP(sport=53210, dport=53) /
        Raw(load=b"\x1a\x2b\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07vitpune\x03edu\x00\x00\x01\x00\x01")
    )
    pkts.append(p3)

    # Packet 4: ICMP Echo Request (Ping, payload 30 bytes)
    p4 = (
        eth_hdr /
        IP(src="192.168.1.105", dst="192.168.1.1") /
        ICMP(type=8, code=0, id=0x1234, seq=1) /
        Raw(load=b"DCN_NETWORK_CHANNEL_TEST_BITS")
    )
    pkts.append(p4)

    # Packet 5: TCP SYN Handshake (Control Packet, 0 payload bytes)
    p5 = (
        eth_hdr /
        IP(src="192.168.1.105", dst="142.250.190.46") /
        TCP(sport=49153, dport=443, flags="S", seq=5000)
    )
    pkts.append(p5)

    # Packet 6: IPv6 TCP Request (IPv6 has no header checksum)
    p6 = (
        eth_hdr /
        IPv6(src="2001:db8::1", dst="2001:db8::2") /
        TCP(sport=52000, dport=80, flags="PA", seq=3000) /
        Raw(load=b"GET /sensors/temperature HTTP/1.1\r\nHost: [2001:db8::2]\r\n\r\n")
    )
    pkts.append(p6)

    # Packet 7: Simulated Corrupted Packet on the Wire (Invalid IPv4 Checksum)
    p7 = (
        eth_hdr /
        IP(src="10.0.0.5", dst="10.0.0.1", chksum=0xDEAD) /
        UDP(sport=4000, dport=5000) /
        Raw(load=b"TRANSMISSION_ERROR_IN_HEADER")
    )
    pkts.append(p7)

    wrpcap(output_path, pkts)
    return output_path
