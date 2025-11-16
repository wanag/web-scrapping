"""
Pydantic models for request/response validation and data structures.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ScrapeMode(str, Enum):
    """Scraping mode enumeration."""
    ONE_PAGE = "one_page"
    INDEX_PAGE = "index_page"
    HYBRID = "hybrid"


# Authentication Models
class AuthRequest(BaseModel):
    """PIN authentication request."""
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit PIN")


class AuthResponse(BaseModel):
    """Authentication response with JWT token."""
    success: bool
    token: str
    expires_in: int = Field(default=86400, description="Token expiration in seconds")


class TokenVerifyRequest(BaseModel):
    """Token verification request."""
    token: str


# Scraper Models
class ScrapeRequest(BaseModel):
    """Request to scrape a book page."""
    url: str = Field(..., description="URL to scrape")
    mode: ScrapeMode = Field(default=ScrapeMode.ONE_PAGE, description="Scraping mode")
    metadata_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User-provided metadata overrides"
    )
    custom_content: Optional[str] = Field(
        default=None,
        description="User-edited content (overrides scraped content)"
    )
    selected_chapters: Optional[List[str]] = Field(
        default=None,
        description="List of chapter URLs to scrape (for INDEX_PAGE and HYBRID modes)"
    )
    chinese_mode: bool = Field(default=False, description="Use Chinese character detection for content extraction")


class ScrapeProgress(BaseModel):
    """Scraping progress information."""
    status: str = Field(..., description="Status: processing, completed, error")
    current_chapter: Optional[int] = None
    total_chapters: Optional[int] = None
    current_chapter_name: Optional[str] = None
    message: Optional[str] = None


class PreviewRequest(BaseModel):
    """Request to preview a page before scraping."""
    url: str = Field(..., description="URL to preview")
    mode: ScrapeMode = Field(default=ScrapeMode.ONE_PAGE, description="Scraping mode")
    include_full_content: bool = Field(default=False, description="Include full content for editing")
    selected_containers: Optional[List[int]] = Field(default=None, description="Indices of containers to include (None = all)")
    chinese_mode: bool = Field(default=False, description="Use Chinese character detection for content extraction")


class PreviewMetadata(BaseModel):
    """Metadata extracted from preview."""
    title: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ContentSizeInfo(BaseModel):
    """Content size information."""
    character_count: int = Field(..., description="Total character count")
    estimated_bytes: int = Field(..., description="Estimated file size in bytes")
    formatted_size: str = Field(..., description="Human-readable size (e.g., '1.5 MB')")
    compression_estimate: Optional[str] = Field(None, description="Estimated compressed size")


class ContainerInfo(BaseModel):
    """Information about an HTML container used during extraction."""
    type: str = Field(..., description="Container element type (div, section, article, main)")
    id: Optional[str] = Field(None, description="Container ID attribute")
    classes: Optional[str] = Field(None, description="Container CSS classes")
    content_length: int = Field(..., description="Length of content from this container")
    content_preview: str = Field(..., description="Preview of content from this container")
    selected: bool = Field(default=True, description="Whether this container is selected for inclusion")


class ChapterLink(BaseModel):
    """Represents a chapter link found on an index page."""
    name: str = Field(..., description="Chapter name/title")
    url: str = Field(..., description="Chapter URL")
    selected: bool = Field(default=True, description="Whether this chapter is selected for scraping")
    order: int = Field(..., description="Sequential order (0-indexed)")


class IndexPagePreview(BaseModel):
    """Preview data specific to INDEX_PAGE and HYBRID modes."""
    chapters: List[ChapterLink] = Field(default_factory=list)
    total_chapters_found: int = Field(default=0)
    index_content: Optional[str] = Field(None, description="Content from index page itself (for HYBRID mode)")
    index_content_length: int = Field(default=0)


class PreviewResponse(BaseModel):
    """Response for preview request."""
    success: bool
    mode: ScrapeMode
    content_preview: str = Field(..., description="First ~500 chars of content")
    full_length: int = Field(..., description="Full content length in characters")
    full_content: Optional[str] = Field(None, description="Full content for editing (only if requested)")
    metadata: PreviewMetadata
    size_info: Optional[ContentSizeInfo] = Field(None, description="Content size information")
    containers: Optional[List[ContainerInfo]] = Field(None, description="HTML containers used during extraction")
    index_preview: Optional[IndexPagePreview] = Field(None, description="Index page preview (for INDEX_PAGE and HYBRID modes)")
    editable_fields: List[str] = Field(
        default_factory=lambda: ["title", "author", "language", "description", "tags"]
    )
    error: Optional[str] = None


class ScrapeResponse(BaseModel):
    """Response after scraping completion."""
    success: bool
    book_id: Optional[str] = None
    chapters_saved: int = 0
    total_size: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class CreateBookRequest(BaseModel):
    """Request to create a book with metadata only (no chapters)."""
    title: str = Field(..., description="Book title")
    source_url: str = Field(..., description="Original source URL")
    author: Optional[str] = Field(None, description="Author name")
    language: str = Field(default="en", description="Content language code")
    tags: List[str] = Field(default_factory=list, description="Book tags/categories")
    description: Optional[str] = Field(None, description="Book description")
    scrape_mode: ScrapeMode = Field(default=ScrapeMode.INDEX_PAGE, description="Scraping mode")


class CreateBookResponse(BaseModel):
    """Response after creating a book."""
    success: bool
    book_id: Optional[str] = None
    message: Optional[str] = None


class AddChapterRequest(BaseModel):
    """Request to add a single chapter to an existing book."""
    book_id: str = Field(..., description="Existing book ID")
    chapter_url: str = Field(..., description="URL of the chapter to scrape")
    chapter_index: int = Field(..., description="Chapter index (0-based)")
    chapter_name: str = Field(..., description="Chapter name/title")
    custom_content: Optional[str] = Field(None, description="User-edited content (overrides scraped content)")
    selected_containers: Optional[List[int]] = Field(None, description="Indices of containers to include (None = all)")
    chinese_mode: bool = Field(default=False, description="Use Chinese character detection for content extraction")


class AddChapterResponse(BaseModel):
    """Response after adding a chapter."""
    success: bool
    chapter_id: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


# Book Models
class ChapterInfo(BaseModel):
    """Chapter metadata information."""
    id: int = Field(..., description="Chapter sequential ID")
    title: str = Field(..., description="Chapter title")
    file: str = Field(..., description="Filename (e.g., 000.md)")


class BookMetadata(BaseModel):
    """Book metadata stored in metadata.json."""
    id: str = Field(..., description="Unique book ID (UUID)")
    title: str = Field(..., description="Book title")
    author: Optional[str] = Field(None, description="Author name")
    language: str = Field(default="en", description="Content language code")
    encoding: str = Field(default="utf-8", description="Text encoding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chapters_count: int = Field(default=0, description="Total number of chapters")
    tags: List[str] = Field(default_factory=list, description="Book tags/categories")
    source_url: str = Field(..., description="Original source URL")
    scrape_mode: ScrapeMode = Field(default=ScrapeMode.ONE_PAGE)
    description: Optional[str] = Field(None, description="Book description")


class BookIndex(BaseModel):
    """Book chapter index stored in index.json."""
    chapters: List[ChapterInfo] = Field(default_factory=list)


class BookListItem(BaseModel):
    """Book item in list response."""
    id: str
    title: str
    author: Optional[str]
    language: str
    chapters_count: int
    created_at: datetime
    tags: List[str]


class BookListResponse(BaseModel):
    """Response for book list endpoint."""
    books: List[BookListItem]
    total: int


class BookDetailResponse(BaseModel):
    """Detailed book information response."""
    metadata: BookMetadata
    chapters: List[ChapterInfo]


class ChapterContent(BaseModel):
    """Chapter content response."""
    chapter_id: int
    title: str
    content: str
    next_chapter: Optional[int] = None
    previous_chapter: Optional[int] = None


# Reading Progress Models (Phase 1 - basic implementation)
class ReadingPosition(BaseModel):
    """Reading position for a book."""
    book_id: str
    chapter_id: int
    scroll_position: float = Field(default=0.0, ge=0.0, le=1.0)
    last_read: datetime = Field(default_factory=datetime.utcnow)


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


# Success Response
class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str
