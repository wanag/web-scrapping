"""
File Parser for Manual Book Imports

Handles parsing of .txt and .md files for single-file book imports.
"""

import chardet
from pathlib import Path
from typing import Dict, Optional


class FileParser:
    """
    Parser for text and markdown files.
    Imports entire file as a single chapter.
    """

    SUPPORTED_EXTENSIONS = ['.txt', '.md']

    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """
        Detect file encoding using chardet.

        Args:
            file_content: Raw file bytes

        Returns:
            Detected encoding (e.g., 'utf-8', 'gbk', 'iso-8859-1')
        """
        result = chardet.detect(file_content)
        encoding = result.get('encoding', 'utf-8')

        # Default to utf-8 if detection fails or confidence is low
        if not encoding or result.get('confidence', 0) < 0.7:
            encoding = 'utf-8'

        return encoding.lower()

    @staticmethod
    def extract_title_from_content(content: str, filename: str) -> str:
        """
        Extract potential title from file content or filename.

        Looks for:
        1. First # heading in markdown
        2. First line if it's short (< 100 chars)
        3. Filename as fallback

        Args:
            content: File text content
            filename: Original filename

        Returns:
            Extracted or fallback title
        """
        lines = content.strip().split('\n')

        # Try to find markdown heading
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()

        # Try first line if short enough
        if lines and len(lines[0].strip()) < 100:
            first_line = lines[0].strip()
            if first_line and not first_line.startswith(('#', '-', '*', '>')):
                return first_line

        # Fallback to filename without extension
        return Path(filename).stem

    @staticmethod
    def detect_language(content: str) -> str:
        """
        Detect language from content (basic heuristics).

        Args:
            content: Text content

        Returns:
            Language code (e.g., 'en', 'zh', 'ja')
        """
        # Simple heuristic: check for Chinese, Japanese, Korean characters
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        japanese_chars = sum(1 for char in content if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        korean_chars = sum(1 for char in content if '\uac00' <= char <= '\ud7af')
        arabic_chars = sum(1 for char in content if '\u0600' <= char <= '\u06ff')
        cyrillic_chars = sum(1 for char in content if '\u0400' <= char <= '\u04ff')

        total_chars = len(content)
        if total_chars == 0:
            return 'en'

        # If >30% CJK characters, classify as respective language
        if chinese_chars / total_chars > 0.3:
            return 'zh'
        if japanese_chars / total_chars > 0.3:
            return 'ja'
        if korean_chars / total_chars > 0.3:
            return 'ko'
        if arabic_chars / total_chars > 0.3:
            return 'ar'
        if cyrillic_chars / total_chars > 0.3:
            return 'ru'

        # Default to English
        return 'en'

    @staticmethod
    def convert_txt_to_markdown(content: str) -> str:
        """
        Convert plain text to markdown format.

        Simple conversion:
        - Preserve paragraphs (double newlines)
        - Wrap in basic markdown structure

        Args:
            content: Plain text content

        Returns:
            Markdown formatted text
        """
        # Split into paragraphs
        paragraphs = content.split('\n\n')

        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Join with proper markdown paragraph spacing
        markdown = '\n\n'.join(paragraphs)

        return markdown

    @classmethod
    def parse_file(
        cls,
        file_content: bytes,
        filename: str,
        file_extension: str
    ) -> Dict[str, any]:
        """
        Parse a text or markdown file for import.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_extension: File extension (.txt or .md)

        Returns:
            Dict containing:
                - content: Parsed markdown content
                - suggested_title: Extracted title
                - detected_language: Detected language code
                - detected_encoding: Detected file encoding
                - original_filename: Original filename

        Raises:
            ValueError: If file type not supported
        """
        if file_extension.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_extension}. Supported: {cls.SUPPORTED_EXTENSIONS}")

        # Detect encoding
        encoding = cls.detect_encoding(file_content)

        # Decode content
        try:
            content = file_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            content = file_content.decode('utf-8', errors='replace')
            encoding = 'utf-8'

        # Convert .txt to markdown
        if file_extension.lower() == '.txt':
            content = cls.convert_txt_to_markdown(content)

        # Extract metadata
        suggested_title = cls.extract_title_from_content(content, filename)
        detected_language = cls.detect_language(content)

        return {
            'content': content,
            'suggested_title': suggested_title,
            'detected_language': detected_language,
            'detected_encoding': encoding,
            'original_filename': filename,
            'chapters_count': 1  # Single file = single chapter
        }

    @classmethod
    def validate_file(cls, filename: str) -> bool:
        """
        Check if file extension is supported.

        Args:
            filename: Filename to check

        Returns:
            True if supported, False otherwise
        """
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
