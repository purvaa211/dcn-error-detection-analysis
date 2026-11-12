"""DCN Error Control Architecture Core OOP Package.

Provides high-level object-oriented models for:
- Error Detection strategies (ErrorDetection, ParityCheck, LRC, Checksum, CRC)
- Transmission Channel (TransmissionChannel)
- Host entities (Sender, Receiver, NetworkSimulator)
- Experiment Analysis (ExperimentConfig, ExperimentResult, ExperimentAnalyzer)
- Experiment History (HistoryManager, history_manager)
"""

from core.detection import (
    ErrorDetection,
    ParityCheck,
    LRC,
    Checksum,
    CRC,
    get_detection_strategy
)
from core.channel import TransmissionChannel, ChannelTransmissionResult
from core.networking import Sender, Receiver, NetworkSimulator
from core.analysis import ExperimentConfig, ExperimentResult, ExperimentAnalyzer
from core.history import HistoryManager, history_manager

__all__ = [
    "ErrorDetection",
    "ParityCheck",
    "LRC",
    "Checksum",
    "CRC",
    "get_detection_strategy",
    "TransmissionChannel",
    "ChannelTransmissionResult",
    "Sender",
    "Receiver",
    "NetworkSimulator",
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentAnalyzer",
    "HistoryManager",
    "history_manager"
]
