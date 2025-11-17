"""
FastAPI application for Book Scraper & Reader System.
Phase 1: Core Functionality - PIN auth, one-page scraping, reader, storage.
"""
import os
import gzip
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.auth import init_auth, get_auth_manager, require_auth
from backend.storage.manager import StorageManager
from backend.scraper.extractor import ContentExtractor
from backend.scraper.modes import ScrapeMode
from backend.models.schemas import (
    AuthRequest,
    AuthResponse,
    TokenVerifyRequest,
    ScrapeRequest,
    ScrapeResponse,
    CreateBookRequest,
    CreateBookResponse,
    AddChapterRequest,
    AddChapterResponse,
    PreviewRequest,
    PreviewResponse,
    PreviewMetadata,
    ContentSizeInfo,
    ContainerInfo,
    ChapterLink,
    IndexPagePreview,
    BookListResponse,
    BookDetailResponse,
    ChapterContent,
    ErrorResponse,
    SuccessResponse
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Book Scraper & Reader API",
    description="API for scraping books from web pages and reading them",
    version="1.0.0 (Phase 1)"
)

# Configure CORS
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# Handle wildcard for development
if CORS_ORIGINS_ENV == "*":
    CORS_ORIGINS = ["*"]
else:
    CORS_ORIGINS = CORS_ORIGINS_ENV.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize authentication
APP_PIN = os.getenv("APP_PIN", "1234")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

init_auth(
    pin=APP_PIN,
    secret_key=JWT_SECRET_KEY,
    algorithm=JWT_ALGORITHM,
    expiration_hours=JWT_EXPIRATION_HOURS
)

# Initialize storage manager
DATA_DIR = os.getenv("DATA_DIR", "./data/books")
storage = StorageManager(data_dir=DATA_DIR)

# Initialize content extractor
MAX_CONTENT_SIZE_MB = int(os.getenv("MAX_CONTENT_SIZE_MB", "50"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
extractor = ContentExtractor(
    timeout=REQUEST_TIMEOUT_SECONDS,
    max_size_mb=MAX_CONTENT_SIZE_MB
)


# ==================== Utility Functions ====================

def format_bytes(bytes_count: int) -> str:
    """
    Format bytes into human-readable size.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "234.5 KB")
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


# ==================== API Endpoints ====================

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Book Scraper & Reader API",
        "version": "1.0.0",
        "phase": "Phase 1 - Core Functionality",
        "features": [
            "PIN authentication",
            "One-page scraping mode",
            "Book storage and management",
            "Reading interface"
        ],
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "book-scraper-api"}


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(auth_request: AuthRequest):
    """
    Authenticate with PIN and receive JWT token.

    Args:
        auth_request: Contains 4-digit PIN

    Returns:
        JWT token and expiration time
    """
    auth_manager = get_auth_manager()
    token = auth_manager.authenticate(auth_request.pin)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )

    return AuthResponse(
        success=True,
        token=token,
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )


@app.post("/api/auth/verify", tags=["Authentication"])
async def verify_token(token_request: TokenVerifyRequest):
    """
    Verify if a JWT token is valid.

    Args:
        token_request: Contains JWT token

    Returns:
        Validation result
    """
    auth_manager = get_auth_manager()
    payload = auth_manager.verify_token(token_request.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {"valid": True, "payload": payload}


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(_: dict = Depends(require_auth)):
    """
    Logout endpoint (client should discard token).

    Note: JWT tokens are stateless, so actual logout happens client-side.
    """
    return {"success": True, "message": "Logged out successfully"}


# ==================== Scraper Endpoints ====================

@app.post(
    "/api/scraper/preview-html",
    response_model=PreviewResponse,
    tags=["Scraper"],
    dependencies=[Depends(require_auth)]
)
async def preview_from_html(raw_html: str, mode: ScrapeMode = ScrapeMode.ONE_PAGE, chinese_mode: bool = False):
    """
    Preview content from raw HTML (for manual import when URL scraping fails).

    Args:
        raw_html: Raw HTML content
        mode: Scraping mode
        chinese_mode: Use Chinese character detection

    Returns:
        Preview with content sample and extracted metadata
    """
    try:
        if mode == ScrapeMode.ONE_PAGE:
            # Extract content from HTML
            content, containers = extractor.extract_content(raw_html, track_containers=True, chinese_mode=chinese_mode)

            if not content:
                return PreviewResponse(
                    success=False,
                    mode=mode,
                    content_preview="",
                    full_length=0,
                    metadata=PreviewMetadata(),
                    error="No content found in HTML"
                )

            # Extract metadata
            metadata = extractor.extract_metadata(raw_html, "manual-import")

            # Create preview
            content_preview = content[:500]
            if len(content) > 500:
                content_preview += "..."

            preview_metadata = PreviewMetadata(
                title=metadata.get('title'),
                author=metadata.get('author'),
                language=metadata.get('language', 'en'),
                description=metadata.get('description'),
                tags=metadata.get('tags', [])
            )

            # Size info
            content_bytes = len(content.encode('utf-8'))
            compressed_content = gzip.compress(content.encode('utf-8'))
            compressed_size = len(compressed_content)

            size_info = ContentSizeInfo(
                character_count=len(content),
                estimated_bytes=content_bytes,
                formatted_size=format_bytes(content_bytes),
                compression_estimate=format_bytes(compressed_size)
            )

            # Containers
            containers_list = None
            if containers:
                containers_list = [
                    ContainerInfo(
                        type=c['type'],
                        id=c.get('id'),
                        classes=c.get('classes'),
                        content_length=c['content_length'],
                        content_preview=c['content_preview'],
                        selected=True
                    )
                    for c in containers
                ]

            return PreviewResponse(
                success=True,
                mode=mode,
                content_preview=content_preview,
                full_length=len(content),
                full_content=content,
                metadata=preview_metadata,
                size_info=size_info,
                containers=containers_list
            )
        else:
            return PreviewResponse(
                success=False,
                mode=mode,
                content_preview="",
                full_length=0,
                metadata=PreviewMetadata(),
                error="HTML import only supports ONE_PAGE mode currently"
            )

    except Exception as e:
        return PreviewResponse(
            success=False,
            mode=mode,
            content_preview="",
            full_length=0,
            metadata=PreviewMetadata(),
            error=f"Error processing HTML: {str(e)}"
        )


@app.post(
    "/api/scraper/preview",
    response_model=PreviewResponse,
    tags=["Scraper"],
    dependencies=[Depends(require_auth)]
)
async def preview_scrape(preview_request: PreviewRequest):
    """
    Preview content from a URL before scraping.
    Supports: ONE_PAGE, INDEX_PAGE, and HYBRID modes.

    Args:
        preview_request: Preview configuration

    Returns:
        Preview with content sample and extracted metadata
    """
    # Handle ONE_PAGE mode
    if preview_request.mode == ScrapeMode.ONE_PAGE:
        # Scrape the page with container tracking enabled
        result, error = extractor.scrape_page(
            preview_request.url,
            track_containers=True,
            selected_containers=preview_request.selected_containers,
            chinese_mode=preview_request.chinese_mode
        )

        if error:
            return PreviewResponse(
                success=False,
                mode=preview_request.mode,
                content_preview="",
                full_length=0,
                metadata=PreviewMetadata(),
                error=error
            )

        try:
            # Extract data
            content = result['content']
            metadata = result['metadata']

            # Create preview (first 500 characters)
            content_preview = content[:500]
            if len(content) > 500:
                content_preview += "..."

            # Create preview metadata
            preview_metadata = PreviewMetadata(
                title=metadata.get('title'),
                author=metadata.get('author'),
                language=metadata.get('language', 'en'),
                description=metadata.get('description'),
                tags=metadata.get('tags', [])
            )

            # Calculate size information
            content_bytes = len(content.encode('utf-8'))
            compressed_content = gzip.compress(content.encode('utf-8'))
            compressed_size = len(compressed_content)

            size_info = ContentSizeInfo(
                character_count=len(content),
                estimated_bytes=content_bytes,
                formatted_size=format_bytes(content_bytes),
                compression_estimate=format_bytes(compressed_size)
            )

            # Include full content if requested (for editing)
            full_content_response = content if preview_request.include_full_content else None

            # Process containers if available
            containers_list = None
            if 'containers' in result and result['containers']:
                containers_list = [
                    ContainerInfo(
                        type=c['type'],
                        id=c.get('id'),
                        classes=c.get('classes'),
                        content_length=c['content_length'],
                        content_preview=c['content_preview'],
                        selected=True  # Default to selected
                    )
                    for c in result['containers']
                ]

            # Debug logging
            print(f"Preview request - include_full_content: {preview_request.include_full_content}")
            print(f"Full content length: {len(content)} chars")
            print(f"Returning full_content: {full_content_response is not None}")
            print(f"Containers found: {len(containers_list) if containers_list else 0}")
            if full_content_response:
                print(f"Full content first 100 chars: {full_content_response[:100]}")

            return PreviewResponse(
                success=True,
                mode=preview_request.mode,
                content_preview=content_preview,
                full_length=len(content),
                full_content=full_content_response,
                metadata=preview_metadata,
                size_info=size_info,
                containers=containers_list
            )

        except Exception as e:
            return PreviewResponse(
                success=False,
                mode=preview_request.mode,
                content_preview="",
                full_length=0,
                metadata=PreviewMetadata(),
                error=f"Error generating preview: {str(e)}"
            )

    # Handle INDEX_PAGE and HYBRID modes
    elif preview_request.mode in [ScrapeMode.INDEX_PAGE, ScrapeMode.HYBRID]:
        # Fetch the index page HTML
        html, error = extractor.fetch_page(preview_request.url)
        if error:
            return PreviewResponse(
                success=False,
                mode=preview_request.mode,
                content_preview="",
                full_length=0,
                metadata=PreviewMetadata(),
                error=error
            )

        try:
            # Extract chapter links
            links = extractor.extract_links(html, preview_request.url)

            if not links:
                return PreviewResponse(
                    success=False,
                    mode=preview_request.mode,
                    content_preview="",
                    full_length=0,
                    metadata=PreviewMetadata(),
                    error="No chapter links found on this page. Try using ONE_PAGE mode instead."
                )

            # Build chapter links list
            chapter_links = [
                ChapterLink(
                    name=link['name'],
                    url=link['url'],
                    selected=True,
                    order=idx
                )
                for idx, link in enumerate(links)
            ]

            # For HYBRID mode, also extract content from index page
            index_content = None
            index_length = 0
            if preview_request.mode == ScrapeMode.HYBRID:
                content, _ = extractor.extract_content(html, track_containers=False, chinese_mode=preview_request.chinese_mode)
                if content:
                    index_content = content[:500] + "..." if len(content) > 500 else content
                    index_length = len(content)

            # Extract metadata from index page
            metadata = extractor.extract_metadata(html, preview_request.url)

            # Create preview metadata
            preview_metadata = PreviewMetadata(
                title=metadata.get('title'),
                author=metadata.get('author'),
                language=metadata.get('language', 'en'),
                description=metadata.get('description'),
                tags=metadata.get('tags', [])
            )

            # Build index preview
            index_preview = IndexPagePreview(
                chapters=chapter_links,
                total_chapters_found=len(chapter_links),
                index_content=index_content,
                index_content_length=index_length
            )

            print(f"Found {len(chapter_links)} chapter links")
            if index_content:
                print(f"Index content length: {index_length} chars")

            return PreviewResponse(
                success=True,
                mode=preview_request.mode,
                content_preview="",  # Not used for INDEX/HYBRID
                full_length=0,
                metadata=preview_metadata,
                index_preview=index_preview
            )

        except Exception as e:
            return PreviewResponse(
                success=False,
                mode=preview_request.mode,
                content_preview="",
                full_length=0,
                metadata=PreviewMetadata(),
                error=f"Error analyzing index page: {str(e)}"
            )

    # Invalid mode
    else:
        return PreviewResponse(
            success=False,
            mode=preview_request.mode,
            content_preview="",
            full_length=0,
            metadata=PreviewMetadata(),
            error=f"Unknown mode: {preview_request.mode}"
        )


@app.post(
    "/api/scraper/execute",
    response_model=ScrapeResponse,
    tags=["Scraper"],
    dependencies=[Depends(require_auth)]
)
async def execute_scrape(scrape_request: ScrapeRequest):
    """
    Execute scraping for a URL.
    Supports: ONE_PAGE, INDEX_PAGE, and HYBRID modes.

    Args:
        scrape_request: Scraping configuration

    Returns:
        Scraping result with book ID
    """
    # Handle ONE_PAGE mode
    if scrape_request.mode == ScrapeMode.ONE_PAGE:
        try:
            # Check if user provided custom content (edited)
            if scrape_request.custom_content:
                # Use user-edited content
                content = scrape_request.custom_content

                # For custom content, metadata must come from overrides or defaults
                metadata = scrape_request.metadata_overrides or {}
                if 'title' not in metadata:
                    metadata['title'] = 'Untitled'
                if 'language' not in metadata:
                    metadata['language'] = 'en'
            else:
                # Scrape the page
                result, error = extractor.scrape_page(scrape_request.url, chinese_mode=scrape_request.chinese_mode)

                if error:
                    return ScrapeResponse(
                        success=False,
                        errors=[error],
                        message="Failed to scrape page"
                    )

                # Extract data
                content = result['content']
                metadata = result['metadata']

                # Apply metadata overrides if provided
                if scrape_request.metadata_overrides:
                    metadata.update(scrape_request.metadata_overrides)

            # Save book
            book_id = storage.save_book(
                title=metadata.get('title', 'Untitled'),
                content=content,
                source_url=scrape_request.url,
                author=metadata.get('author'),
                language=metadata.get('language', 'en'),
                tags=metadata.get('tags', []),
                description=metadata.get('description'),
                scrape_mode=scrape_request.mode
            )

            # Calculate size
            content_size = len(content.encode('utf-8'))
            size_str = f"{content_size / 1024:.2f}KB"
            if content_size > 1024 * 1024:
                size_str = f"{content_size / (1024 * 1024):.2f}MB"

            return ScrapeResponse(
                success=True,
                book_id=book_id,
                chapters_saved=1,
                total_size=size_str,
                message="Book scraped and saved successfully"
            )

        except Exception as e:
            return ScrapeResponse(
                success=False,
                errors=[f"Error saving book: {str(e)}"],
                message="Failed to save book"
            )

    # Handle INDEX_PAGE and HYBRID modes
    elif scrape_request.mode in [ScrapeMode.INDEX_PAGE, ScrapeMode.HYBRID]:
        try:
            chapters_content = []
            errors = []

            # If HYBRID mode, scrape index page content first
            if scrape_request.mode == ScrapeMode.HYBRID:
                html, error = extractor.fetch_page(scrape_request.url)
                if not error:
                    content, _ = extractor.extract_content(html, track_containers=False, chinese_mode=scrape_request.chinese_mode)
                    if content:
                        chapters_content.append({
                            'title': 'Index',
                            'content': content,
                            'url': scrape_request.url
                        })
                else:
                    errors.append(f"Failed to scrape index page: {error}")

            # Scrape selected chapter URLs
            if scrape_request.selected_chapters:
                for idx, chapter_url in enumerate(scrape_request.selected_chapters):
                    print(f"Scraping chapter {idx + 1}/{len(scrape_request.selected_chapters)}: {chapter_url}")

                    result, error = extractor.scrape_page(chapter_url, chinese_mode=scrape_request.chinese_mode)
                    if error:
                        errors.append(f"Failed to scrape {chapter_url}: {error}")
                        continue

                    # Extract title from chapter or use URL
                    chapter_title = result['metadata'].get('title', f"Chapter {idx + 1}")
                    # Remove domain from title if it's just a URL
                    if chapter_title.startswith('Scraped from'):
                        chapter_title = f"Chapter {idx + 1}"

                    chapters_content.append({
                        'title': chapter_title,
                        'content': result['content'],
                        'url': chapter_url
                    })

            # Check if we have any chapters
            if not chapters_content:
                return ScrapeResponse(
                    success=False,
                    errors=errors or ["No chapters were scraped successfully"],
                    message="Failed to scrape any chapters"
                )

            # Get metadata (from overrides or first scraped content)
            metadata = scrape_request.metadata_overrides or {}
            if not metadata.get('title'):
                # Use book title from overrides, or default
                metadata['title'] = 'Untitled Book'
            if not metadata.get('language'):
                metadata['language'] = 'en'

            # Save book with multiple chapters
            book_id = storage.save_multi_chapter_book(
                title=metadata.get('title'),
                chapters=chapters_content,
                source_url=scrape_request.url,
                author=metadata.get('author'),
                language=metadata.get('language', 'en'),
                tags=metadata.get('tags', []),
                description=metadata.get('description'),
                scrape_mode=scrape_request.mode
            )

            # Calculate total size
            total_chars = sum(len(ch['content']) for ch in chapters_content)
            content_size = total_chars * 2  # Rough estimate for UTF-8
            size_str = f"{content_size / 1024:.2f}KB"
            if content_size > 1024 * 1024:
                size_str = f"{content_size / (1024 * 1024):.2f}MB"

            success_msg = "Book scraped and saved successfully"
            if errors:
                success_msg += f" (with {len(errors)} errors)"

            return ScrapeResponse(
                success=True,
                book_id=book_id,
                chapters_saved=len(chapters_content),
                total_size=size_str,
                errors=errors,
                message=success_msg
            )

        except Exception as e:
            return ScrapeResponse(
                success=False,
                errors=[f"Error saving book: {str(e)}"],
                message="Failed to save book"
            )

    # Invalid mode
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown mode: {scrape_request.mode}"
        )


@app.post(
    "/api/scraper/create-book",
    response_model=CreateBookResponse,
    tags=["Scraper"],
    dependencies=[Depends(require_auth)]
)
async def create_book(request: CreateBookRequest):
    """
    Create a book with metadata only (no chapters).
    Used for progressive chapter scraping workflow.

    Args:
        request: Book metadata

    Returns:
        Book ID for the newly created book
    """
    try:
        book_id = storage.create_book_with_metadata(
            title=request.title,
            source_url=request.source_url,
            author=request.author,
            language=request.language,
            tags=request.tags,
            description=request.description,
            scrape_mode=request.scrape_mode
        )

        return CreateBookResponse(
            success=True,
            book_id=book_id,
            message="Book created successfully"
        )

    except Exception as e:
        return CreateBookResponse(
            success=False,
            message=f"Failed to create book: {str(e)}"
        )


@app.post(
    "/api/scraper/add-chapter",
    response_model=AddChapterResponse,
    tags=["Scraper"],
    dependencies=[Depends(require_auth)]
)
async def add_chapter(request: AddChapterRequest):
    """
    Add a single chapter to an existing book.
    Scrapes the chapter URL and appends it to the book, or uses provided custom content.

    Args:
        request: Chapter information (book_id, chapter_url, chapter_index, chapter_name, custom_content, selected_containers)

    Returns:
        Success status
    """
    try:
        # Verify book exists
        if not storage.book_exists(request.book_id):
            return AddChapterResponse(
                success=False,
                error="Book not found",
                message=f"Book {request.book_id} does not exist"
            )

        # Check if custom content is provided
        if request.custom_content:
            # Use custom content instead of scraping
            chapter_content = request.custom_content
            chapter_title = request.chapter_name
        else:
            # Scrape the chapter
            if request.selected_containers is not None:
                # Use selected containers
                html, error = extractor.fetch_page(request.chapter_url)
                if error:
                    return AddChapterResponse(
                        success=False,
                        error=error,
                        message=f"Failed to fetch chapter: {error}"
                    )

                # Extract content and get containers
                chapter_content, containers = extractor.extract_content(
                    html,
                    track_containers=True,
                    chinese_mode=request.chinese_mode
                )

                # Re-extract with only selected containers
                if containers:
                    chapter_content = extractor.extract_content_from_selected_containers(
                        html, containers, request.selected_containers
                    )
            else:
                # Normal scraping
                result, error = extractor.scrape_page(request.chapter_url, chinese_mode=request.chinese_mode)

                if error:
                    return AddChapterResponse(
                        success=False,
                        error=error,
                        message=f"Failed to scrape chapter: {error}"
                    )

                chapter_content = result['content']

            chapter_title = request.chapter_name

        # Add chapter to book
        success = storage.add_chapter_to_book(
            book_id=request.book_id,
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            chapter_index=request.chapter_index
        )

        if success:
            return AddChapterResponse(
                success=True,
                chapter_id=request.chapter_index,
                message=f"Chapter '{chapter_title}' added successfully"
            )
        else:
            return AddChapterResponse(
                success=False,
                error="Storage error",
                message="Failed to add chapter to book"
            )

    except Exception as e:
        return AddChapterResponse(
            success=False,
            error=str(e),
            message=f"Error adding chapter: {str(e)}"
        )


# ==================== Books Endpoints ====================

@app.get(
    "/api/books",
    response_model=BookListResponse,
    tags=["Books"],
    dependencies=[Depends(require_auth)]
)
async def list_books():
    """
    List all saved books.

    Returns:
        List of books with metadata
    """
    books = storage.list_books()

    return BookListResponse(
        books=books,
        total=len(books)
    )


@app.get(
    "/api/books/{book_id}",
    response_model=BookDetailResponse,
    tags=["Books"],
    dependencies=[Depends(require_auth)]
)
async def get_book(book_id: str):
    """
    Get detailed information about a specific book.

    Args:
        book_id: Book ID

    Returns:
        Book metadata and chapter list
    """
    metadata = storage.get_book(book_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book '{book_id}' not found"
        )

    chapters = storage.get_chapters(book_id)

    return BookDetailResponse(
        metadata=metadata,
        chapters=chapters or []
    )


@app.get(
    "/api/books/{book_id}/chapters/{chapter_id}",
    response_model=ChapterContent,
    tags=["Books"],
    dependencies=[Depends(require_auth)]
)
async def get_chapter(book_id: str, chapter_id: int):
    """
    Get content for a specific chapter.

    Args:
        book_id: Book ID
        chapter_id: Chapter ID (0-indexed)

    Returns:
        Chapter content with navigation info
    """
    chapter_content = storage.get_chapter_content(book_id, chapter_id)

    if not chapter_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found in book '{book_id}'"
        )

    return chapter_content


@app.delete(
    "/api/books/{book_id}",
    response_model=SuccessResponse,
    tags=["Books"],
    dependencies=[Depends(require_auth)]
)
async def delete_book(book_id: str):
    """
    Delete a book and all its files.

    Args:
        book_id: Book ID

    Returns:
        Success message
    """
    success = storage.delete_book(book_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book '{book_id}' not found"
        )

    return SuccessResponse(
        success=True,
        message=f"Book '{book_id}' deleted successfully"
    )


# ==================== System Endpoints ====================

@app.get(
    "/api/system/stats",
    tags=["System"],
    dependencies=[Depends(require_auth)]
)
async def get_storage_stats():
    """
    Get storage statistics.

    Returns:
        Storage information
    """
    stats = storage.get_storage_stats()
    return stats


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail) if hasattr(exc, 'detail') else None,
            status_code=exc.status_code
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            status_code=500
        ).dict()
    )


# Main entry point
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))

    print(f"\n{'='*60}")
    print(f"📚 Book Scraper & Reader API - Phase 1")
    print(f"{'='*60}")
    print(f"🚀 Starting server on http://{host}:{port}")
    print(f"📖 API docs available at http://{host}:{port}/docs")
    print(f"🔒 PIN: {APP_PIN}")
    print(f"{'='*60}\n")

    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=True
    )
