"""
Scraping mode definitions and utilities.
"""
from enum import Enum


class ScrapeMode(str, Enum):
    """
    Scraping mode enumeration.

    - ONE_PAGE: Single page with content only
    - INDEX_PAGE: Index page with chapter links (Phase 2+)
    - HYBRID: Index page with content + chapter links (Phase 2+)
    """
    ONE_PAGE = "one_page"
    INDEX_PAGE = "index_page"
    HYBRID = "hybrid"


def is_mode_supported(mode: ScrapeMode, phase: int = 1) -> bool:
    """
    Check if a scraping mode is supported in the given phase.

    Args:
        mode: Scraping mode to check
        phase: Implementation phase (1-4)

    Returns:
        True if supported, False otherwise
    """
    if phase >= 1:
        return mode == ScrapeMode.ONE_PAGE

    if phase >= 2:
        return mode in [ScrapeMode.ONE_PAGE, ScrapeMode.INDEX_PAGE, ScrapeMode.HYBRID]

    return False


def get_supported_modes(phase: int = 1) -> list[ScrapeMode]:
    """
    Get list of supported scraping modes for the given phase.

    Args:
        phase: Implementation phase (1-4)

    Returns:
        List of supported ScrapeMode values
    """
    if phase >= 2:
        return [ScrapeMode.ONE_PAGE, ScrapeMode.INDEX_PAGE, ScrapeMode.HYBRID]

    return [ScrapeMode.ONE_PAGE]
