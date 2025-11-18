# Book Import Guide

This guide explains how to manually prepare and import books into the Book Reader System.

## Table of Contents
- [Overview](#overview)
- [Book Storage Structure](#book-storage-structure)
- [Import Methods](#import-methods)
- [Metadata Reference](#metadata-reference)
- [Examples](#examples)

---

## Overview

The Book Reader System stores books in a standardized folder structure within the `data/books/` directory. Each book has:
- A unique UUID identifier
- Metadata file (`metadata.json`)
- Chapter index (`index.json`)
- Chapter content files (`.md` markdown format)

---

## Book Storage Structure

### Directory Hierarchy

```
data/books/
├── {book-uuid-1}/
│   ├── metadata.json          # Book metadata
│   ├── index.json             # Chapter index
│   └── chapters/
│       ├── 000.md             # Chapter 0
│       ├── 001.md             # Chapter 1
│       ├── 002.md             # Chapter 2
│       └── ...
├── {book-uuid-2}/
│   ├── metadata.json
│   ├── index.json
│   └── chapters/
│       └── 000.md             # Single chapter book
└── ...
```

### Folder Structure Explained

**Book Folder:**
- Name: UUID v4 format (e.g., `bdd2b104-41fc-4b77-b435-d42683dbe0d7`)
- Generated automatically by the system
- Must be unique across all books

**Required Files:**
- `metadata.json` - Book information and configuration
- `index.json` - List of chapters with titles
- `chapters/` directory - Contains chapter markdown files

**Chapter Files:**
- Format: `{chapter_id:03d}.md` (e.g., `000.md`, `001.md`, `099.md`)
- Zero-padded 3-digit numbering (supports 000-999)
- Sequential numbering starting from 000
- Must be UTF-8 encoded markdown files

---

## Import Methods

### Method 1: Single File Import

**Supported Formats:**
- `.txt` (plain text)
- `.md` (markdown)

**Process:**
1. Upload a single text or markdown file
2. System imports entire file as a single chapter (Chapter 0)
3. Enter metadata manually (title, author, language, tags, description)
4. System generates UUID, creates folder structure automatically

**Best For:**
- Short stories
- Single-chapter content
- Simple text documents
- Blog posts or articles

---

### Method 2: Folder Import

**Requirements:**
- Folder must contain `metadata.json` (optional but recommended)
- Folder must contain `index.json` (optional but recommended)
- Folder must contain `chapters/` directory with `.md` files
- Chapter files must follow naming convention (`000.md`, `001.md`, etc.)

**Process:**
1. Prepare folder with proper structure (see template below)
2. ZIP the folder
3. Upload ZIP file to import interface
4. System validates structure and shows preview
5. Edit/confirm metadata
6. Import to create book

**Best For:**
- Multi-chapter books
- Existing collections with organized structure
- Migrating from other systems
- Large books with many chapters

---

## Metadata Reference

### metadata.json

**Complete Schema:**

```json
{
  "id": "string (UUID v4)",
  "title": "string (required)",
  "author": "string (optional)",
  "language": "string (default: 'en')",
  "encoding": "string (default: 'utf-8')",
  "created_at": "string (ISO 8601 datetime)",
  "chapters_count": "integer (required)",
  "tags": ["array of strings (optional)"],
  "source_url": "string (required)",
  "scrape_mode": "string (one_page|index_page|hybrid)",
  "description": "string (optional)"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique book identifier (UUID v4 format) |
| `title` | string | Yes | Book title |
| `author` | string | No | Author name |
| `language` | string | Yes | Language code (e.g., "en", "zh", "ja", "es") |
| `encoding` | string | Yes | Text encoding (default: "utf-8") |
| `created_at` | datetime | Yes | Creation timestamp (ISO 8601 format) |
| `chapters_count` | integer | Yes | Total number of chapters |
| `tags` | array | No | List of tags/categories (default: []) |
| `source_url` | string | Yes | Original source URL (use "manual" for imports) |
| `scrape_mode` | string | Yes | Scrape mode: "one_page", "index_page", or "hybrid" |
| `description` | string | No | Book description/summary |

**Language Codes:**
- `en` - English
- `zh` - Chinese (Simplified)
- `zh-TW` - Chinese (Traditional)
- `ja` - Japanese
- `es` - Spanish
- `fr` - French
- `de` - German
- `ar` - Arabic
- `ru` - Russian

**Scrape Mode for Manual Imports:**
- Use `"one_page"` for single file/chapter imports
- Use `"index_page"` for multi-chapter folder imports

---

### index.json

**Schema:**

```json
{
  "chapters": [
    {
      "id": "integer (0-indexed)",
      "title": "string (chapter title)",
      "file": "string (filename)"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chapters` | array | Yes | List of chapter information objects |
| `chapters[].id` | integer | Yes | Sequential chapter ID (starts at 0) |
| `chapters[].title` | string | Yes | Chapter title/name |
| `chapters[].file` | string | Yes | Filename in chapters/ directory |

**Important Notes:**
- Chapter IDs must be sequential starting from 0
- Chapter IDs must match the filename number (id: 0 → file: "000.md")
- `chapters_count` in metadata.json must equal `chapters.length` in index.json

---

## Examples

### Example 1: Single Chapter Book

**Folder Structure:**
```
3d7f8e2a-9b4c-4a1d-8f6e-2c9a8b7d6e5f/
├── metadata.json
├── index.json
└── chapters/
    └── 000.md
```

**metadata.json:**
```json
{
  "id": "3d7f8e2a-9b4c-4a1d-8f6e-2c9a8b7d6e5f",
  "title": "The Adventure Begins",
  "author": "John Smith",
  "language": "en",
  "encoding": "utf-8",
  "created_at": "2025-11-18T10:00:00Z",
  "chapters_count": 1,
  "tags": ["fiction", "adventure"],
  "source_url": "manual",
  "scrape_mode": "one_page",
  "description": "A thrilling adventure story about a young explorer."
}
```

**index.json:**
```json
{
  "chapters": [
    {
      "id": 0,
      "title": "The Adventure Begins",
      "file": "000.md"
    }
  ]
}
```

**chapters/000.md:**
```markdown
# The Adventure Begins

It was a dark and stormy night when the adventure began...

[Content continues...]
```

---

### Example 2: Multi-Chapter Book

**Folder Structure:**
```
7a9e5d3c-2f1b-4e8d-9c6a-1b8f7e9d5c4a/
├── metadata.json
├── index.json
└── chapters/
    ├── 000.md
    ├── 001.md
    ├── 002.md
    └── 003.md
```

**metadata.json:**
```json
{
  "id": "7a9e5d3c-2f1b-4e8d-9c6a-1b8f7e9d5c4a",
  "title": "Journey to the Unknown",
  "author": "Jane Doe",
  "language": "en",
  "encoding": "utf-8",
  "created_at": "2025-11-18T12:30:00Z",
  "chapters_count": 4,
  "tags": ["fantasy", "series", "epic"],
  "source_url": "manual",
  "scrape_mode": "index_page",
  "description": "An epic fantasy tale spanning four chapters."
}
```

**index.json:**
```json
{
  "chapters": [
    {
      "id": 0,
      "title": "Chapter 1: The Beginning",
      "file": "000.md"
    },
    {
      "id": 1,
      "title": "Chapter 2: The Journey",
      "file": "001.md"
    },
    {
      "id": 2,
      "title": "Chapter 3: The Battle",
      "file": "002.md"
    },
    {
      "id": 3,
      "title": "Chapter 4: The Resolution",
      "file": "003.md"
    }
  ]
}
```

**chapters/000.md:**
```markdown
# Chapter 1: The Beginning

Once upon a time in a land far away...

[Content continues...]
```

**chapters/001.md:**
```markdown
# Chapter 2: The Journey

The hero set out on their quest...

[Content continues...]
```

---

### Example 3: Book with Chinese Content

**metadata.json:**
```json
{
  "id": "f3e8d7c6-5b4a-3d2c-1e9f-8a7b6c5d4e3f",
  "title": "红楼梦",
  "author": "曹雪芹",
  "language": "zh",
  "encoding": "utf-8",
  "created_at": "2025-11-18T15:00:00Z",
  "chapters_count": 120,
  "tags": ["classic", "literature", "chinese"],
  "source_url": "manual",
  "scrape_mode": "index_page",
  "description": "中国古典长篇小说"
}
```

**index.json:**
```json
{
  "chapters": [
    {
      "id": 0,
      "title": "第一回 甄士隐梦幻识通灵",
      "file": "000.md"
    },
    {
      "id": 1,
      "title": "第二回 贾夫人仙逝扬州城",
      "file": "001.md"
    }
  ]
}
```

---

## Template for Manual Import

### Minimal Folder Template

Use this template when preparing books for folder import:

```
my-book/                           # Your book folder name (will be renamed to UUID)
├── metadata.json                  # Copy and edit from template below
├── index.json                     # Copy and edit from template below
└── chapters/
    ├── 000.md                     # Your first chapter
    ├── 001.md                     # Your second chapter (if multi-chapter)
    └── ...
```

### metadata.json Template

```json
{
  "id": "LEAVE_BLANK_OR_GENERATE_UUID",
  "title": "YOUR_BOOK_TITLE",
  "author": "AUTHOR_NAME",
  "language": "en",
  "encoding": "utf-8",
  "created_at": "2025-11-18T00:00:00Z",
  "chapters_count": 1,
  "tags": ["tag1", "tag2"],
  "source_url": "manual",
  "scrape_mode": "one_page",
  "description": "Brief description of your book"
}
```

### index.json Template (Single Chapter)

```json
{
  "chapters": [
    {
      "id": 0,
      "title": "Chapter Title",
      "file": "000.md"
    }
  ]
}
```

### index.json Template (Multi-Chapter)

```json
{
  "chapters": [
    {
      "id": 0,
      "title": "Chapter 1 Title",
      "file": "000.md"
    },
    {
      "id": 1,
      "title": "Chapter 2 Title",
      "file": "001.md"
    },
    {
      "id": 2,
      "title": "Chapter 3 Title",
      "file": "002.md"
    }
  ]
}
```

---

## Best Practices

### 1. File Naming
- Always use zero-padded 3-digit numbers: `000.md`, `001.md`, `099.md`, `100.md`
- Never skip numbers in the sequence
- Start from `000.md` (not `001.md`)

### 2. Encoding
- Always save files as UTF-8 encoding
- For non-Latin scripts (Chinese, Japanese, Arabic), verify UTF-8 encoding

### 3. Metadata Accuracy
- Set correct `chapters_count` matching actual chapter files
- Use appropriate `language` code for better reading experience
- Add relevant `tags` for easier organization

### 4. Chapter Files
- Keep chapter files reasonable in size (< 5MB per file)
- Use markdown formatting for better display
- Include chapter title as heading (# or ##) at the beginning

### 5. Validation
- Before importing, verify:
  - All chapter files exist (no gaps in numbering)
  - `chapters_count` matches number of files
  - `index.json` chapters array matches files
  - All files are UTF-8 encoded

---

## Common Issues and Solutions

### Issue: "Invalid folder structure"
**Solution:** Ensure you have all required files:
- `metadata.json`
- `index.json`
- `chapters/` directory with `.md` files

### Issue: "Chapter count mismatch"
**Solution:** Make sure:
- `metadata.json` `chapters_count` = number of chapter files
- `index.json` `chapters` array length = number of chapter files
- No missing files in sequence (e.g., 000.md, 002.md without 001.md)

### Issue: "Encoding error when reading"
**Solution:**
- Re-save all `.md` files with UTF-8 encoding
- Update `metadata.json` `encoding` field to "utf-8"

### Issue: "Missing metadata fields"
**Solution:** Ensure all required fields are present:
- `id`, `title`, `language`, `encoding`, `created_at`
- `chapters_count`, `source_url`, `scrape_mode`

---

## Tools for Preparation

### UUID Generation
Use online tools or command line to generate UUID v4:
```bash
# Linux/Mac
uuidgen | tr '[:upper:]' '[:lower:]'

# Python
python3 -c "import uuid; print(uuid.uuid4())"
```

### Timestamp Generation
Generate ISO 8601 timestamp:
```bash
# Linux/Mac
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Python
python3 -c "from datetime import datetime; print(datetime.utcnow().isoformat() + 'Z')"
```

### ZIP Creation
```bash
# Compress folder for import
zip -r my-book.zip my-book/
```

---

## Support

For issues or questions about importing books, please refer to:
- System documentation: `CLAUDE.md`
- Application logs for error details
- Validation preview before import to identify issues

---

**Last Updated:** 2025-11-18
**Version:** 1.0
