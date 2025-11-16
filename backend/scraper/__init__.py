"""
Web scraper module for extracting content from web pages.
"""
from .modes import ScrapeMode, is_mode_supported, get_supported_modes
from .extractor import ContentExtractor

__all__ = [
    'ScrapeMode',
    'is_mode_supported',
    'get_supported_modes',
    'ContentExtractor'
]
