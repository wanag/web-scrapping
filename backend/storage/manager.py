"""
Storage manager for handling book files and metadata.
"""
import os
import json
import uuid
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models.schemas import (
    BookMetadata,
    BookIndex,
    ChapterInfo,
    BookListItem,
    ChapterContent
)


class StorageManager:
    """Manages book storage on the file system."""

    def __init__(self, data_dir: str = "./data/books"):
        """
        Initialize the storage manager.

        Args:
            data_dir: Base directory for storing books
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_book_path(self, book_id: str) -> Path:
        """Get the directory path for a specific book."""
        return self.data_dir / book_id

    def _get_metadata_path(self, book_id: str) -> Path:
        """Get the metadata.json file path for a book."""
        return self._get_book_path(book_id) / "metadata.json"

    def _get_index_path(self, book_id: str) -> Path:
        """Get the index.json file path for a book."""
        return self._get_book_path(book_id) / "index.json"

    def _get_chapters_dir(self, book_id: str) -> Path:
        """Get the chapters directory path for a book."""
        return self._get_book_path(book_id) / "chapters"

    def save_book(
        self,
        title: str,
        content: str,
        source_url: str,
        author: Optional[str] = None,
        language: str = "en",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        scrape_mode: str = "one_page"
    ) -> str:
        """
        Save a book with its content.

        Args:
            title: Book title
            content: Book content (for one-page mode, this is the full content)
            source_url: Original source URL
            author: Author name
            language: Language code
            tags: List of tags
            description: Book description
            scrape_mode: Scraping mode used

        Returns:
            book_id: The generated book ID
        """
        # Generate unique book ID
        book_id = str(uuid.uuid4())
        book_path = self._get_book_path(book_id)
        chapters_dir = self._get_chapters_dir(book_id)

        # Create directories
        book_path.mkdir(parents=True, exist_ok=True)
        chapters_dir.mkdir(parents=True, exist_ok=True)

        # For Phase 1 (one-page mode), save as a single chapter
        chapter_file = "000.md"
        chapter_path = chapters_dir / chapter_file
        chapter_path.write_text(content, encoding="utf-8")

        # Create metadata
        metadata = BookMetadata(
            id=book_id,
            title=title,
            author=author,
            language=language,
            encoding="utf-8",
            created_at=datetime.utcnow(),
            chapters_count=1,
            tags=tags or [],
            source_url=source_url,
            scrape_mode=scrape_mode,
            description=description
        )

        # Save metadata
        metadata_path = self._get_metadata_path(book_id)
        metadata_path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8"
        )

        # Create index
        chapter_info = ChapterInfo(
            id=0,
            title=title,
            file=chapter_file
        )
        book_index = BookIndex(chapters=[chapter_info])

        # Save index
        index_path = self._get_index_path(book_id)
        index_path.write_text(
            book_index.model_dump_json(indent=2),
            encoding="utf-8"
        )

        return book_id

    def save_multi_chapter_book(
        self,
        title: str,
        chapters: List[Dict[str, str]],  # [{'title': '...', 'content': '...', 'url': '...'}]
        source_url: str,
        author: Optional[str] = None,
        language: str = "en",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        scrape_mode: str = "index_page"
    ) -> str:
        """
        Save a book with multiple chapters.

        Args:
            title: Book title
            chapters: List of chapter dictionaries with 'title', 'content', 'url'
            source_url: Original source URL (index page)
            author: Author name
            language: Language code
            tags: List of tags
            description: Book description
            scrape_mode: Scraping mode used (index_page or hybrid)

        Returns:
            book_id: The generated book ID
        """
        # Generate unique book ID
        book_id = str(uuid.uuid4())
        book_path = self._get_book_path(book_id)
        chapters_dir = self._get_chapters_dir(book_id)

        # Create directories
        book_path.mkdir(parents=True, exist_ok=True)
        chapters_dir.mkdir(parents=True, exist_ok=True)

        # Save each chapter
        chapter_infos = []
        for idx, chapter in enumerate(chapters):
            chapter_file = f"{idx:03d}.md"
            chapter_path = chapters_dir / chapter_file
            chapter_path.write_text(chapter['content'], encoding="utf-8")

            chapter_infos.append(ChapterInfo(
                id=idx,
                title=chapter['title'],
                file=chapter_file
            ))

        # Create metadata
        metadata = BookMetadata(
            id=book_id,
            title=title,
            author=author,
            language=language,
            encoding="utf-8",
            created_at=datetime.utcnow(),
            chapters_count=len(chapters),
            tags=tags or [],
            source_url=source_url,
            scrape_mode=scrape_mode,
            description=description
        )

        # Save metadata
        metadata_path = self._get_metadata_path(book_id)
        metadata_path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8"
        )

        # Create and save index
        book_index = BookIndex(chapters=chapter_infos)
        index_path = self._get_index_path(book_id)
        index_path.write_text(
            book_index.model_dump_json(indent=2),
            encoding="utf-8"
        )

        return book_id

    def get_book(self, book_id: str) -> Optional[BookMetadata]:
        """
        Get book metadata by ID.

        Args:
            book_id: Book ID

        Returns:
            BookMetadata or None if not found
        """
        metadata_path = self._get_metadata_path(book_id)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BookMetadata(**data)
        except Exception as e:
            print(f"Error loading metadata for book {book_id}: {e}")
            return None

    def get_chapters(self, book_id: str) -> Optional[List[ChapterInfo]]:
        """
        Get chapter list for a book.

        Args:
            book_id: Book ID

        Returns:
            List of ChapterInfo or None if not found
        """
        index_path = self._get_index_path(book_id)

        if not index_path.exists():
            return None

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                book_index = BookIndex(**data)
                return book_index.chapters
        except Exception as e:
            print(f"Error loading index for book {book_id}: {e}")
            return None

    def get_chapter_content(
        self,
        book_id: str,
        chapter_id: int
    ) -> Optional[ChapterContent]:
        """
        Get content for a specific chapter.

        Args:
            book_id: Book ID
            chapter_id: Chapter ID

        Returns:
            ChapterContent or None if not found
        """
        chapters = self.get_chapters(book_id)

        if not chapters or chapter_id >= len(chapters):
            return None

        chapter_info = chapters[chapter_id]
        chapter_path = self._get_chapters_dir(book_id) / chapter_info.file

        if not chapter_path.exists():
            return None

        try:
            content = chapter_path.read_text(encoding='utf-8')

            # Determine next and previous chapters
            next_chapter = chapter_id + 1 if chapter_id < len(chapters) - 1 else None
            previous_chapter = chapter_id - 1 if chapter_id > 0 else None

            return ChapterContent(
                chapter_id=chapter_id,
                title=chapter_info.title,
                content=content,
                next_chapter=next_chapter,
                previous_chapter=previous_chapter
            )
        except Exception as e:
            print(f"Error loading chapter {chapter_id} for book {book_id}: {e}")
            return None

    def list_books(self) -> List[BookListItem]:
        """
        List all books in the storage.

        Returns:
            List of BookListItem
        """
        books = []

        if not self.data_dir.exists():
            return books

        for book_dir in self.data_dir.iterdir():
            if not book_dir.is_dir() or book_dir.name.startswith('.'):
                continue

            metadata = self.get_book(book_dir.name)
            if metadata:
                books.append(
                    BookListItem(
                        id=metadata.id,
                        title=metadata.title,
                        author=metadata.author,
                        language=metadata.language,
                        chapters_count=metadata.chapters_count,
                        created_at=metadata.created_at,
                        tags=metadata.tags
                    )
                )

        # Sort by created_at descending (newest first)
        books.sort(key=lambda x: x.created_at, reverse=True)

        return books

    def delete_book(self, book_id: str) -> bool:
        """
        Delete a book and all its files.

        Args:
            book_id: Book ID

        Returns:
            True if deleted successfully, False otherwise
        """
        book_path = self._get_book_path(book_id)

        if not book_path.exists():
            return False

        try:
            shutil.rmtree(book_path)
            return True
        except Exception as e:
            print(f"Error deleting book {book_id}: {e}")
            return False

    def book_exists(self, book_id: str) -> bool:
        """
        Check if a book exists.

        Args:
            book_id: Book ID

        Returns:
            True if book exists, False otherwise
        """
        return self._get_book_path(book_id).exists()

    def create_book_with_metadata(
        self,
        title: str,
        source_url: str,
        author: Optional[str] = None,
        language: str = "en",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        scrape_mode: str = "index_page"
    ) -> str:
        """
        Create a book with metadata only (no chapters yet).
        Used for progressive chapter scraping.

        Args:
            title: Book title
            source_url: Original source URL
            author: Author name
            language: Language code
            tags: List of tags
            description: Book description
            scrape_mode: Scraping mode used

        Returns:
            book_id: The generated book ID
        """
        # Generate unique book ID
        book_id = str(uuid.uuid4())
        book_path = self._get_book_path(book_id)
        chapters_dir = self._get_chapters_dir(book_id)

        # Create directories
        book_path.mkdir(parents=True, exist_ok=True)
        chapters_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata with 0 chapters
        metadata = BookMetadata(
            id=book_id,
            title=title,
            author=author,
            language=language,
            encoding="utf-8",
            created_at=datetime.utcnow(),
            chapters_count=0,
            tags=tags or [],
            source_url=source_url,
            scrape_mode=scrape_mode,
            description=description
        )

        # Save metadata
        metadata_path = self._get_metadata_path(book_id)
        metadata_path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8"
        )

        # Create empty index
        book_index = BookIndex(chapters=[])
        index_path = self._get_index_path(book_id)
        index_path.write_text(
            book_index.model_dump_json(indent=2),
            encoding="utf-8"
        )

        return book_id

    def add_chapter_to_book(
        self,
        book_id: str,
        chapter_title: str,
        chapter_content: str,
        chapter_index: int
    ) -> bool:
        """
        Add a single chapter to an existing book.
        Updates both the chapter file and the index.

        Args:
            book_id: Existing book ID
            chapter_title: Chapter title
            chapter_content: Chapter content
            chapter_index: Chapter index (0-based)

        Returns:
            True if successful, False otherwise
        """
        if not self.book_exists(book_id):
            return False

        try:
            # Save chapter file
            chapter_file = f"{chapter_index:03d}.md"
            chapter_path = self._get_chapters_dir(book_id) / chapter_file
            chapter_path.write_text(chapter_content, encoding="utf-8")

            # Update index
            index_path = self._get_index_path(book_id)
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                book_index = BookIndex(**data)

            # Add new chapter info
            new_chapter = ChapterInfo(
                id=chapter_index,
                title=chapter_title,
                file=chapter_file
            )
            book_index.chapters.append(new_chapter)

            # Sort chapters by id to maintain order
            book_index.chapters.sort(key=lambda ch: ch.id)

            # Save updated index
            index_path.write_text(
                book_index.model_dump_json(indent=2),
                encoding="utf-8"
            )

            # Update metadata chapter count
            metadata_path = self._get_metadata_path(book_id)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
                metadata = BookMetadata(**metadata_data)

            metadata.chapters_count = len(book_index.chapters)

            metadata_path.write_text(
                metadata.model_dump_json(indent=2),
                encoding="utf-8"
            )

            return True

        except Exception as e:
            print(f"Error adding chapter to book {book_id}: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        total_books = 0
        total_size = 0

        if self.data_dir.exists():
            for book_dir in self.data_dir.iterdir():
                if book_dir.is_dir() and not book_dir.name.startswith('.'):
                    total_books += 1
                    # Calculate directory size
                    for file_path in book_dir.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size

        return {
            "total_books": total_books,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "data_directory": str(self.data_dir.absolute())
        }
