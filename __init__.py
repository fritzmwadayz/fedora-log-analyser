"""
Loganalyzer - A simple log analysis tool.
"""

__version__ = "1.0.0"
__author__ = "Mwadime Mwaiseghe"

# Export main classes
from .cli import LogalyzerCLI
from .tui.app import LogalyzerTUI
from .analysis.core import LogAnalyzer

__all__ = ['LoganalyzerCLI', 'LoganalyzerTUI', 'LogAnalyzer']