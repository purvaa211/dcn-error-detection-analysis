"""Simulation Engine for DCN Error Detection and Analysis.

Coordinates the complete 3-stage communication pipeline:
[1. Transmitter / Sender] -> Encodes payload with redundant check bits.
[2. Physical Channel]     -> Injects errors (Clean, Single-bit, Multiple-bit, Burst, Consecutive, Multi-burst, Manual).
[3. Receiver]             -> Performs integrity verification and error detection.

Architectural Note:
This module integrates with the object-oriented `core.NetworkSimulator`
while preserving complete backward compatibility for existing callers and CLI scripts.
"""

from typing import Dict, Any, List, Optional, Union
from core.networking import NetworkSimulator
from core.history import history_manager

# Singleton instance of the object-oriented NetworkSimulator
_simulator_instance = NetworkSimulator()


def simulate(
    data: str,
    technique: str = "CRC",
    error_type: str = "single",
    error_amount: Union[int, float, List[int], Dict[str, Any]] = 1,
    crc_generator: str = "100000111",
    checksum_word_size: int = 8,
    forced_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Execute a single end-to-end transmission simulation.
    
    Delegates to the object-oriented NetworkSimulator pipeline (Sender -> Channel -> Receiver).
    """
    res = _simulator_instance.simulate(
        data=data,
        technique=technique,
        error_type=error_type,
        error_amount=error_amount,
        crc_generator=crc_generator,
        checksum_word_size=checksum_word_size,
        forced_indices=forced_indices
    )
    return res


def compare_all_techniques(
    data: str,
    error_type: str = "multiple",
    error_amount: Union[int, float, List[int], Dict[str, Any]] = 2
) -> List[Dict[str, Any]]:
    """Run all four techniques on the same input under equivalent error conditions.
    
    Delegates to the object-oriented NetworkSimulator pipeline.
    """
    return _simulator_instance.compare_all(
        data=data,
        error_type=error_type,
        error_amount=error_amount
    )
