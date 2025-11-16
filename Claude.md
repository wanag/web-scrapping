# Book Scraper & Reader System Specification

## Project Overview
A web-based system to scrape books from websites, store them locally, and provide a clean reading interface with the following core features:
- Multiple scraping modes (single page, index page, hybrid)
- Preview before scraping with editing capabilities
- Multi-language support
- PIN-based authentication
- Responsive reader for desktop and mobile

## System Architecture

```
book-reader-system/
├── backend/
│   ├── app.py                 # FastAPI main application
│   ├── auth.py                # PIN authentication
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── modes.py           # Scraping mode definitions
│   │   ├── analyzer.py        # URL analysis and preview
│   │   ├── extractor.py       # Content extraction
│   │   └── cleaner.py         # Ad removal and cleaning
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── manager.py         # File management
│   │   └── multilang.py       # Multi-language support
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Pydantic models
│
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── App.vue
│   │   ├── pages/
│   │   │   ├── Login.vue      # PIN authentication
│   │   │   ├── Welcome.vue    # Main dashboard
│   │   │   ├── Scraper.vue    # Scraping interface
│   │   │   └── Reader.vue     # Reading interface
│   │   └── components/
│   │       ├── PreviewModal.vue
│   │       └── ChapterNav.vue
│   └── package.json
│
└── data/
    └── books/
        └── [book-id]/
            ├── metadata.json
            ├── chapters/
            └── index.json
```

## Module Specifications

### 1. Backend - Scraper Module

#### 1.1 Scraping Modes
```python
from enum import Enum

class ScrapeMode(Enum):
    ONE_PAGE = "one_page"      # Single page with content only
    INDEX_PAGE = "index_page"   # Index page with chapter links
    HYBRID = "hybrid"           # Index page with content + chapter links

class ScraperConfig:
    mode: ScrapeMode
    url: str
    selected_chapters: List[str]  # URLs of selected chapters
    metadata_overrides: dict      # User-edited metadata
```

#### 1.2 Preview Functionality
```python
# API Endpoints

POST /api/scraper/analyze
Request: {
    "url": "https://example.com/book/index",
    "mode": "auto"  # or specific mode
}
Response: {
    "detected_mode": "index_page",
    "preview": {
        "content_sample": "First 500 chars...",  # For ONE_PAGE
        "chapters": [                            # For INDEX_PAGE/HYBRID
            {
                "name": "Chapter 1: Introduction",
                "url": "https://example.com/book/ch1",
                "selected": true
            }
        ],
        "metadata": {
            "title": "Book Title",
            "author": "Author Name",
            "language": "en",
            "tags": ["fiction", "adventure"],
            "description": "Book description"
        }
    },
    "editable_fields": ["title", "author", "language", "tags", "description"]
}

POST /api/scraper/preview
Request: {
    "url": "https://example.com/book/ch1",
    "mode": "one_page"
}
Response: {
    "content_preview": "Chapter 1 content preview (first 500 chars)...",
    "full_length": 15000,
    "detected_elements": ["text", "images"],
    "ads_detected": true
}
```

#### 1.3 Content Extraction
```python
class ContentExtractor:
    def extract_by_mode(self, url: str, mode: ScrapeMode) -> dict:
        """Extract content based on scraping mode"""
        
    def clean_content(self, html: str) -> str:
        """Remove ads, scripts, and unwanted elements"""
        # Remove common ad patterns
        # Strip JavaScript
        # Clean excessive whitespace
        # Preserve paragraph structure
        
    def extract_metadata(self, html: str) -> dict:
        """Auto-extract metadata from page"""
        # Look for: <title>, <meta> tags, <h1>, author info
        # Detect language from content
        # Extract publication date if available
```

#### 1.4 Execution API
```python
POST /api/scraper/execute
Request: {
    "url": "https://example.com/book/index",
    "mode": "index_page",
    "selected_chapters": ["url1", "url2", ...],
    "metadata": {
        "title": "User Edited Title",
        "author": "User Edited Author",
        "language": "zh-CN"
    }
}
Response: {
    "success": true,
    "book_id": "uuid-here",
    "chapters_saved": 25,
    "total_size": "2.5MB",
    "errors": []
}

# Progress endpoint for real-time updates
GET /api/scraper/progress/{task_id}
Response: {
    "status": "processing",
    "current_chapter": 5,
    "total_chapters": 25,
    "current_chapter_name": "Chapter 5: The Journey"
}
```

### 2. Backend - Storage Module

#### 2.1 Multi-language Support
```python
class MultiLangStorage:
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'big5', 'shift-jis']
    
    def detect_encoding(self, content: bytes) -> str:
        """Detect text encoding"""
        
    def save_with_lang(self, content: str, metadata: dict) -> str:
        """Save content with proper encoding and language metadata"""
        
    def handle_rtl(self, content: str, language: str) -> str:
        """Handle right-to-left languages (Arabic, Hebrew)"""
```

#### 2.2 Storage Structure
```python
class StorageManager:
    def save_book(self, book_data: dict) -> str:
        """
        Save book with structure:
        /data/books/{book_id}/
            metadata.json: {
                "id": "uuid",
                "title": "Book Title",
                "author": "Author",
                "language": "en",
                "encoding": "utf-8",
                "created_at": "2024-01-01T00:00:00Z",
                "chapters_count": 25,
                "tags": ["fiction"],
                "source_url": "https://...",
                "scrape_mode": "index_page"
            }
            index.json: {
                "chapters": [
                    {"id": 0, "title": "Prologue", "file": "000.md"},
                    {"id": 1, "title": "Chapter 1", "file": "001.md"}
                ]
            }
            chapters/000.md, 001.md, ...
        """
```

### 3. Backend - Authentication

#### 3.1 PIN Authentication
```python
POST /api/auth/login
Request: {
    "pin": "1234"
}
Response: {
    "success": true,
    "token": "jwt-token-here",
    "expires_in": 86400
}

# PIN stored as environment variable or config file (hashed)
# JWT token for session management
```

### 4. Frontend Specifications

#### 4.1 Login Page
```vue
<!-- Login.vue -->
Features:
- 4-digit PIN input with numeric keypad
- Remember me option (optional)
- Error handling for wrong PIN
- Auto-focus on PIN input
- Support for both keyboard and on-screen input
```

#### 4.2 Welcome/Dashboard Page
```vue
<!-- Welcome.vue -->
Features:
- List of saved books with covers/thumbnails
- Search and filter functionality
- Quick actions: New Scrape, Continue Reading
- Statistics: Total books, reading progress
- Language filter
```

#### 4.3 Scraper Interface
```vue
<!-- Scraper.vue -->
Components:
1. URL Input Section
   - URL input field
   - Mode selector (Auto/One-page/Index/Hybrid)
   - Analyze button

2. Preview Section
   - For ONE_PAGE: Text preview with scroll
   - For INDEX/HYBRID: Chapter list with checkboxes
   - Metadata fields (editable)
   - Language detection display

3. Action Buttons
   - Cancel
   - Start Scraping
   - Save without Scraping (for preview)

4. Progress Modal
   - Real-time progress bar
   - Current chapter being processed
   - Cancel operation button
```

#### 4.4 Reader Interface
```vue
<!-- Reader.vue -->
Features:
1. Navigation
   - Previous/Next chapter buttons
   - Chapter dropdown selector
   - Swipe gestures for mobile
   - Keyboard shortcuts (arrow keys)

2. Display Options
   - Font size adjustment (12px - 24px)
   - Font family selection
   - Light/Dark/Sepia themes
   - Line height adjustment
   - Margin width control

3. Reading Features
   - Progress indicator (% of chapter)
   - Bookmarks
   - Reading time estimate
   - Auto-save reading position
   - Smooth scrolling between chapters

4. Multi-language Support
   - RTL text direction for Arabic/Hebrew
   - Proper font selection for CJK languages
   - Vertical text option for traditional Chinese/Japanese
```

## API Endpoints Summary

### Authentication
- `POST /api/auth/login` - PIN login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/verify` - Verify token

### Scraper
- `POST /api/scraper/analyze` - Analyze URL and detect mode
- `POST /api/scraper/preview` - Get content preview
- `POST /api/scraper/execute` - Start scraping process
- `GET /api/scraper/progress/{task_id}` - Get scraping progress

### Books
- `GET /api/books` - List all books
- `GET /api/books/{book_id}` - Get book metadata
- `GET /api/books/{book_id}/chapters` - List chapters
- `GET /api/books/{book_id}/chapters/{chapter_id}` - Get chapter content
- `DELETE /api/books/{book_id}` - Delete book

### Reading Progress
- `GET /api/progress/{book_id}` - Get reading progress
- `POST /api/progress/{book_id}` - Update reading progress
- `POST /api/bookmarks` - Add bookmark
- `GET /api/bookmarks/{book_id}` - Get bookmarks

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Scraping**: BeautifulSoup4, requests, lxml
- **Language Detection**: langdetect, chardet
- **Authentication**: PyJWT
- **Async Tasks**: Celery (optional for background scraping)

### Frontend
- **Framework**: Vue 3 with Composition API
- **UI Library**: Vuetify or Element Plus
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Mobile Touch**: Hammer.js
- **CSS**: Tailwind CSS

### Dependencies

#### Backend (requirements.txt)
```txt
fastapi==0.104.1
uvicorn==0.24.0
beautifulsoup4==4.12.2
requests==2.31.0
lxml==4.9.3
pydantic==2.5.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
langdetect==1.0.9
chardet==5.2.0
aiofiles==23.2.1
```

#### Frontend (package.json)
```json
{
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "@vueuse/core": "^10.7.0",
    "element-plus": "^2.4.0",
    "hammerjs": "^2.0.8"
  }
}
```

## Implementation Priority

1. **Phase 1: Core Functionality**
   - Basic PIN authentication
   - One-page scraping mode
   - Simple reader interface
   - File storage system

2. **Phase 2: Advanced Scraping**
   - Index and hybrid modes
   - Preview functionality
   - Metadata extraction
   - Progress tracking

3. **Phase 3: Reader Enhancement**
   - Multi-language support
   - Reading progress sync
   - Bookmarks
   - Theme customization

4. **Phase 4: Polish**
   - Mobile optimizations
   - Offline support (PWA)
   - Export functionality
   - Search within books

## Security Considerations

1. **Authentication**
   - PIN stored as hashed value
   - JWT tokens with expiration
   - Rate limiting on login attempts

2. **Scraping**
   - URL validation
   - Timeout limits
   - Size limits for downloaded content
   - Sanitization of scraped HTML

3. **Storage**
   - File size limits
   - Disk space monitoring
   - Input sanitization for filenames

## Performance Optimizations

1. **Scraping**
   - Concurrent chapter downloads
   - Caching of analyzed URLs
   - Progressive content loading

2. **Reading**
   - Lazy loading of chapters
   - Preload next/previous chapter
   - Client-side caching

3. **Storage**
   - Compression for stored content
   - Indexed metadata for fast search
   - Periodic cleanup of old data

## Error Handling

1. **Scraping Errors**
   - Network timeouts
   - Invalid URLs
   - Rate limiting from source
   - Parsing failures

2. **Storage Errors**
   - Disk space issues
   - Encoding problems
   - File system permissions

3. **User Feedback**
   - Clear error messages
   - Retry mechanisms
   - Partial success handling
