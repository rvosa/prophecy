"""Prophecy: An agentic system for processing Hebrew bible stories with yes/no prompts."""

__version__ = "0.1.0"
__author__ = "Prophecy Team"
__email__ = "prophecy@example.com"

from .agent import ProphecyAgent
from .bible_data import BibleDataManager
from .prompts import PromptsManager

__all__ = ["ProphecyAgent", "BibleDataManager", "PromptsManager"]