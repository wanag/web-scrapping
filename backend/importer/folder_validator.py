"""
Folder Validator for Manual Book Imports

Handles validation and parsing of folder-based book imports.
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class FolderValidator:
    """
    Validator for folder-based book imports.
    Validates structure, extracts metadata, and prepares for import.
    """

    REQUIRED_FILES = ['metadata.json', 'index.json']
    REQUIRED_DIRS = ['chapters']
    CHAPTER_PATTERN = r'^\d{3}\.md$'

    @staticmethod
    def extract_zip(zip_content: bytes, extract_path: Path) -> Path:
        """
        Extract ZIP file to temporary location.

        Args:
            zip_content: ZIP file bytes
            extract_path: Path to extract to

        Returns:
            Path to extracted folder

        Raises:
            ValueError: If ZIP is invalid
        """
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Get root folder name (first component of all paths)
                all_names = zf.namelist()
                if not all_names:
                    raise ValueError("ZIP file is empty")

                # Find the root folder (common prefix of all files)
                root_folder = all_names[0].split('/')[0] if '/' in all_names[0] else ''

                # Extract all
                zf.extractall(extract_path)

                # Return path to extracted folder
                if root_folder:
                    return extract_path / root_folder
                else:
                    return extract_path

        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file")

    @staticmethod
    def validate_structure(folder_path: Path) -> Dict[str, any]:
        """
        Validate folder structure and return validation report.

        Args:
            folder_path: Path to book folder

        Returns:
            Dict containing:
                - valid: bool - Overall validation status
                - errors: List[str] - List of errors found
                - warnings: List[str] - List of warnings
                - metadata_exists: bool
                - index_exists: bool
                - chapters_dir_exists: bool
                - chapter_files: List[str] - Found chapter files
        """
        errors = []
        warnings = []
        metadata_exists = False
        index_exists = False
        chapters_dir_exists = False
        chapter_files = []

        # Check for metadata.json
        metadata_path = folder_path / 'metadata.json'
        if metadata_path.exists():
            metadata_exists = True
        else:
            warnings.append("metadata.json not found (will be generated)")

        # Check for index.json
        index_path = folder_path / 'index.json'
        if index_path.exists():
            index_exists = True
        else:
            warnings.append("index.json not found (will be generated)")

        # Check for chapters directory
        chapters_dir = folder_path / 'chapters'
        if chapters_dir.exists() and chapters_dir.is_dir():
            chapters_dir_exists = True

            # List chapter files
            import re
            pattern = re.compile(r'^\d{3}\.md$')
            for file in sorted(chapters_dir.iterdir()):
                if file.is_file() and pattern.match(file.name):
                    chapter_files.append(file.name)

            if not chapter_files:
                errors.append("No chapter files found in chapters/ directory")
        else:
            errors.append("chapters/ directory not found")

        # Validation logic
        valid = len(errors) == 0 and chapters_dir_exists and len(chapter_files) > 0

        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'metadata_exists': metadata_exists,
            'index_exists': index_exists,
            'chapters_dir_exists': chapters_dir_exists,
            'chapter_files': chapter_files
        }

    @staticmethod
    def parse_metadata(folder_path: Path) -> Optional[Dict]:
        """
        Parse metadata.json if it exists.

        Args:
            folder_path: Path to book folder

        Returns:
            Metadata dict or None if not found/invalid
        """
        metadata_path = folder_path / 'metadata.json'
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata
        except (json.JSONDecodeError, IOError) as e:
            return None

    @staticmethod
    def parse_index(folder_path: Path) -> Optional[Dict]:
        """
        Parse index.json if it exists.

        Args:
            folder_path: Path to book folder

        Returns:
            Index dict or None if not found/invalid
        """
        index_path = folder_path / 'index.json'
        if not index_path.exists():
            return None

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            return index
        except (json.JSONDecodeError, IOError) as e:
            return None

    @staticmethod
    def generate_metadata_from_folder(
        folder_path: Path,
        chapter_files: List[str],
        existing_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate metadata from folder contents.

        Args:
            folder_path: Path to book folder
            chapter_files: List of chapter filenames
            existing_metadata: Existing metadata to merge with

        Returns:
            Generated metadata dict
        """
        # Start with defaults
        metadata = {
            'title': existing_metadata.get('title') if existing_metadata else folder_path.name,
            'author': existing_metadata.get('author') if existing_metadata else None,
            'language': existing_metadata.get('language') if existing_metadata else 'en',
            'encoding': 'utf-8',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'chapters_count': len(chapter_files),
            'tags': existing_metadata.get('tags') if existing_metadata else [],
            'source_url': 'manual',
            'scrape_mode': 'one_page' if len(chapter_files) == 1 else 'index_page',
            'description': existing_metadata.get('description') if existing_metadata else None
        }

        return metadata

    @staticmethod
    def generate_index_from_chapters(
        folder_path: Path,
        chapter_files: List[str],
        existing_index: Optional[Dict] = None
    ) -> Dict:
        """
        Generate index.json from chapter files.

        Args:
            folder_path: Path to book folder
            chapter_files: List of chapter filenames (sorted)
            existing_index: Existing index to use for titles

        Returns:
            Generated index dict
        """
        chapters = []
        existing_chapters = {}

        # Build lookup from existing index
        if existing_index and 'chapters' in existing_index:
            for ch in existing_index['chapters']:
                existing_chapters[ch.get('file')] = ch.get('title', '')

        # Generate chapter entries
        for idx, filename in enumerate(sorted(chapter_files)):
            # Try to get title from existing index or use default
            title = existing_chapters.get(filename, f"Chapter {idx + 1}")

            chapters.append({
                'id': idx,
                'title': title,
                'file': filename
            })

        return {'chapters': chapters}

    @classmethod
    def validate_and_preview(cls, zip_content: bytes, temp_dir: Path) -> Dict[str, any]:
        """
        Main validation and preview method for folder imports.

        Args:
            zip_content: ZIP file bytes
            temp_dir: Temporary directory for extraction

        Returns:
            Dict containing:
                - valid: bool - Can be imported
                - errors: List[str]
                - warnings: List[str]
                - metadata: Dict - Extracted/generated metadata
                - index: Dict - Extracted/generated index
                - chapters_count: int
                - folder_path: str - Path to extracted folder
        """
        # Extract ZIP
        try:
            folder_path = cls.extract_zip(zip_content, temp_dir)
        except ValueError as e:
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'metadata': None,
                'index': None,
                'chapters_count': 0,
                'folder_path': None
            }

        # Validate structure
        validation = cls.validate_structure(folder_path)

        if not validation['valid']:
            return {
                'valid': False,
                'errors': validation['errors'],
                'warnings': validation['warnings'],
                'metadata': None,
                'index': None,
                'chapters_count': 0,
                'folder_path': str(folder_path)
            }

        # Parse existing metadata and index
        existing_metadata = cls.parse_metadata(folder_path)
        existing_index = cls.parse_index(folder_path)

        # Generate or use existing metadata
        metadata = cls.generate_metadata_from_folder(
            folder_path,
            validation['chapter_files'],
            existing_metadata
        )

        # Generate or use existing index
        index = cls.generate_index_from_chapters(
            folder_path,
            validation['chapter_files'],
            existing_index
        )

        return {
            'valid': True,
            'errors': validation['errors'],
            'warnings': validation['warnings'],
            'metadata': metadata,
            'index': index,
            'chapters_count': len(validation['chapter_files']),
            'folder_path': str(folder_path),
            'chapter_files': validation['chapter_files']
        }

    @staticmethod
    def read_chapter_content(folder_path: Path, chapter_filename: str) -> str:
        """
        Read chapter file content.

        Args:
            folder_path: Path to book folder
            chapter_filename: Chapter filename (e.g., '000.md')

        Returns:
            Chapter content

        Raises:
            IOError: If file cannot be read
        """
        chapter_path = folder_path / 'chapters' / chapter_filename
        with open(chapter_path, 'r', encoding='utf-8') as f:
            return f.read()
