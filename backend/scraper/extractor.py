"""
Content extraction from web pages.
"""
import re
import requests
import cloudscraper
from typing import Dict, Optional, Tuple, List
from bs4 import BeautifulSoup, Tag
from langdetect import detect, LangDetectException
from urllib.parse import urljoin, urlparse


class ContentExtractor:
    """Extracts and cleans content from web pages."""

    def __init__(self, timeout: int = 30, max_size_mb: int = 50):
        """
        Initialize the content extractor.

        Args:
            timeout: Request timeout in seconds
            max_size_mb: Maximum content size in megabytes
        """
        self.timeout = timeout
        self.max_size_bytes = max_size_mb * 1024 * 1024

        # More realistic browser headers to avoid anti-bot detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        # Create a cloudscraper session to bypass Cloudflare and other anti-bot protections
        # Falls back to regular requests if cloudscraper fails
        try:
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            self.session.headers.update(self.headers)
            self.using_cloudscraper = True
            print("[ContentExtractor] Using cloudscraper for anti-bot bypass")
        except Exception as e:
            print(f"[ContentExtractor] Cloudscraper init failed, using regular requests: {e}")
            self.session = requests.Session()
            self.session.headers.update(self.headers)
            self.using_cloudscraper = False

    def fetch_page(self, url: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch HTML content from a URL with retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Tuple of (html_content, error_message)
        """
        import time
        from urllib.parse import urlparse

        last_error = None

        for attempt in range(max_retries):
            try:
                # Add a small delay between retries to avoid rate limiting
                if attempt > 0:
                    delay = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                    print(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay...")
                    time.sleep(delay)

                # Set Referer header to the domain root for better anti-bot evasion
                domain = urlparse(url)
                referer = f"{domain.scheme}://{domain.netloc}/"

                # Update session headers with Referer
                request_headers = self.session.headers.copy()
                if attempt > 0:
                    # On retry, add Referer to make it look more natural
                    request_headers['Referer'] = referer

                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=self.timeout,
                    stream=True,
                    allow_redirects=True
                )
                response.raise_for_status()

                # Check content size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_size_bytes:
                    return None, f"Content too large: {int(content_length) / (1024*1024):.2f}MB"

                # Get content with proper encoding detection
                # Try to detect encoding from headers or content
                if response.encoding == 'ISO-8859-1':
                    # requests defaults to ISO-8859-1 if no charset specified
                    # Try to detect from content
                    response.encoding = response.apparent_encoding

                content = response.text

                if len(content.encode('utf-8')) > self.max_size_bytes:
                    return None, "Content exceeds size limit"

                return content, None

            except requests.exceptions.Timeout:
                last_error = "Request timed out"
            except requests.exceptions.HTTPError as e:
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if e.response.status_code == 429:
                    last_error = "Rate limited (429)"
                elif 400 <= e.response.status_code < 500:
                    return None, f"Request failed: {str(e)}"
                else:
                    last_error = f"Request failed: {str(e)}"
            except requests.exceptions.RequestException as e:
                last_error = f"Request failed: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"

        # All retries failed
        return None, f"{last_error} (after {max_retries} attempts)"

    def extract_content(self, html: str, track_containers: bool = False, chinese_mode: bool = False) -> Tuple[str, Optional[List[Dict]]]:
        """
        Extract main text content from HTML.

        Args:
            html: HTML content
            track_containers: Whether to track container information
            chinese_mode: Use Chinese character detection for content extraction

        Returns:
            Tuple of (extracted_text, containers_list)
            containers_list is None if track_containers is False
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer',
                            'iframe', 'noscript', 'aside']):
            element.decompose()

        # Chinese mode: find containers with Chinese content
        if chinese_mode:
            body_element = soup.find('body') or soup

            # Find all potential content containers
            potential_containers = body_element.find_all(['div', 'section', 'article', 'main', 'p'])

            chinese_containers = []
            for container in potential_containers:
                # Get text content
                container_text = container.get_text(strip=True)

                # Skip empty or very short containers
                if not container_text or len(container_text) < 50:
                    continue

                # Check if majority Chinese
                chinese_percentage = self._calculate_chinese_percentage(container_text)
                if chinese_percentage > 0.5:
                    # Track this container
                    chinese_containers.append({
                        'element': container,
                        'type': container.name,
                        'id': container.get('id'),
                        'classes': ' '.join(container.get('class', [])) or None,
                        'content_length': len(container_text),
                        'content_preview': container_text[:200] + ('...' if len(container_text) > 200 else ''),
                        'selected': True,
                        'chinese_percentage': round(chinese_percentage * 100, 1)
                    })

            # Sort by content length (largest first)
            chinese_containers.sort(key=lambda x: x['content_length'], reverse=True)

            # Use the largest Chinese container as main content
            if chinese_containers:
                main_content = chinese_containers[0]['element']
            else:
                # No Chinese content found, fallback to body
                main_content = body_element

            # Extract text from the selected container
            text = self._extract_text_with_structure(main_content, None)
            text = self._clean_text(text)

            # Prepare container tracking if requested
            if track_containers and chinese_containers:
                # Return container info without the 'element' key
                containers_tracker = [
                    {k: v for k, v in c.items() if k != 'element'}
                    for c in chinese_containers
                ]
            else:
                containers_tracker = [] if track_containers else None

            return text, containers_tracker

        # Normal mode: use standard selectors
        main_content = None

        # Look for common content containers
        for selector in ['article', 'main', '[role="main"]',
                        '.content', '.post-content', '.article-content',
                        '#content', '#main', '.entry-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            main_content = soup

        # Initialize container tracking if requested
        containers_tracker = [] if track_containers else None

        # Extract text with better formatting
        text = self._extract_text_with_structure(main_content, containers_tracker)

        # Clean up the text
        text = self._clean_text(text)

        return text, containers_tracker

    def _extract_text_with_structure(self, element, containers_tracker=None) -> str:
        """
        Extract text while preserving paragraph structure and converting to markdown.

        Args:
            element: BeautifulSoup element
            containers_tracker: Optional list to track container information

        Returns:
            Formatted markdown text
        """
        return self._process_element(element, [], containers_tracker)

    def _process_element(self, element, processed_elements, containers_tracker=None) -> str:
        """
        Recursively process element and its children to extract structured text.

        Args:
            element: BeautifulSoup element
            processed_elements: List of already processed elements to avoid duplicates
            containers_tracker: Optional list to track container information

        Returns:
            Formatted text
        """
        if element in processed_elements:
            return ""

        processed_elements.append(element)
        result = []

        # Handle different element types
        if isinstance(element, Tag):
            # Headings
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    result.append('\n' + '#' * level + ' ' + text + '\n\n')

            # Paragraphs
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    result.append(text + '\n\n')

            # Line breaks
            elif element.name == 'br':
                result.append('\n')

            # Blockquotes
            elif element.name == 'blockquote':
                text = element.get_text(strip=True)
                if text:
                    # Add > prefix for blockquote
                    quoted = '\n'.join('> ' + line for line in text.split('\n') if line.strip())
                    result.append(quoted + '\n\n')

            # Unordered lists
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        result.append('- ' + text + '\n')
                result.append('\n')

            # Ordered lists
            elif element.name == 'ol':
                for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                    text = li.get_text(strip=True)
                    if text:
                        result.append(f'{idx}. ' + text + '\n')
                result.append('\n')

            # Horizontal rule
            elif element.name == 'hr':
                result.append('\n---\n\n')

            # Code blocks
            elif element.name == 'pre':
                code = element.get_text()
                result.append('\n```\n' + code + '\n```\n\n')

            # Inline code
            elif element.name == 'code' and element.parent.name != 'pre':
                text = element.get_text()
                result.append('`' + text + '`')

            # Bold/Strong
            elif element.name in ['strong', 'b']:
                text = element.get_text(strip=True)
                if text:
                    result.append('**' + text + '**')

            # Italic/Emphasis
            elif element.name in ['em', 'i']:
                text = element.get_text(strip=True)
                if text:
                    result.append('*' + text + '*')

            # Divs and other containers - process children
            elif element.name in ['div', 'section', 'article', 'main']:
                # Track container if tracking is enabled
                container_start_pos = len(''.join(result))

                for child in element.children:
                    if isinstance(child, Tag):
                        result.append(self._process_element(child, processed_elements, containers_tracker))
                    elif child.string and child.string.strip():
                        # Handle text nodes
                        text = child.string.strip()
                        if text:
                            result.append(text + ' ')

                # Record container info if tracking enabled and container has content
                if containers_tracker is not None:
                    container_text = ''.join(result[container_start_pos:] if result else [])
                    if container_text.strip():
                        # Build container identifier
                        container_id = element.get('id', '')
                        container_classes = ' '.join(element.get('class', []))

                        container_info = {
                            'type': element.name,
                            'id': container_id if container_id else None,
                            'classes': container_classes if container_classes else None,
                            'content_length': len(container_text),
                            'content_preview': container_text[:100].strip() + '...' if len(container_text) > 100 else container_text.strip()
                        }

                        # Check if this container is unique (not already tracked)
                        is_duplicate = any(
                            c['type'] == container_info['type'] and
                            c['id'] == container_info['id'] and
                            c['classes'] == container_info['classes']
                            for c in containers_tracker
                        )

                        if not is_duplicate:
                            containers_tracker.append(container_info)

            # Tables (simple conversion)
            elif element.name == 'table':
                result.append('\n')
                for row in element.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = ' | '.join(cell.get_text(strip=True) for cell in cells)
                        result.append('| ' + row_text + ' |\n')
                result.append('\n')

            # Links - preserve URL in markdown format
            elif element.name == 'a':
                text = element.get_text(strip=True)
                href = element.get('href', '')
                if text:
                    if href and href.startswith('http'):
                        result.append(f'[{text}]({href})')
                    else:
                        result.append(text)

            # For other elements, just get their text if they don't have children
            else:
                # Only process if it's a leaf node or doesn't contain block elements
                children_tags = element.find_all(recursive=False)
                if not children_tags:
                    text = element.get_text(strip=True)
                    if text:
                        result.append(text + ' ')

        return ''.join(result)

    def _is_chinese_char(self, char: str) -> bool:
        """
        Check if a character is Chinese (CJK Unicode range).

        Args:
            char: Single character to check

        Returns:
            True if character is in CJK Unicode range
        """
        if len(char) != 1:
            return False
        code = ord(char)
        # CJK Unified Ideographs (most common Chinese characters)
        if 0x4E00 <= code <= 0x9FFF:
            return True
        # CJK Extension A
        if 0x3400 <= code <= 0x4DBF:
            return True
        # CJK Extension B
        if 0x20000 <= code <= 0x2A6DF:
            return True
        return False

    def _calculate_chinese_percentage(self, text: str) -> float:
        """
        Calculate the percentage of Chinese characters in text.

        Args:
            text: Text to analyze

        Returns:
            Percentage of Chinese characters (0.0 to 1.0)
        """
        if not text:
            return 0.0

        # Filter out whitespace for more accurate percentage
        text_no_whitespace = ''.join(text.split())
        if not text_no_whitespace:
            return 0.0

        chinese_count = sum(1 for char in text_no_whitespace if self._is_chinese_char(char))
        return chinese_count / len(text_no_whitespace)

    def _is_majority_chinese(self, text: str) -> bool:
        """
        Check if text is majority Chinese (>50%).

        Args:
            text: Text to check

        Returns:
            True if >50% of characters are Chinese
        """
        return self._calculate_chinese_percentage(text) > 0.5

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def extract_metadata(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """
        Extract metadata from HTML page.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Dictionary with metadata fields
        """
        soup = BeautifulSoup(html, 'lxml')

        metadata = {
            'title': None,
            'author': None,
            'description': None,
            'language': 'en'
        }

        # Extract title
        # Priority: og:title > meta title > h1 > title tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            metadata['title'] = og_title['content']
        else:
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
            else:
                h1 = soup.find('h1')
                if h1:
                    metadata['title'] = h1.get_text(strip=True)

        # Extract author
        # Look for common author meta tags
        author_selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'article:author'}),
            ('.author',),
            ('.post-author',),
            ('[rel="author"]',)
        ]

        for selector in author_selectors:
            if len(selector) == 2 and selector[0] == 'meta':
                element = soup.find(selector[0], selector[1])
                if element and element.get('content'):
                    metadata['author'] = element['content']
                    break
            else:
                element = soup.select_one(selector[0])
                if element:
                    metadata['author'] = element.get_text(strip=True)
                    break

        # Extract description
        desc_tag = soup.find('meta', {'name': 'description'}) or \
                   soup.find('meta', {'property': 'og:description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content']

        # Detect language
        # Priority: html lang attribute > meta tag > content detection
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag['lang'].split('-')[0]
        else:
            lang_meta = soup.find('meta', {'http-equiv': 'content-language'}) or \
                       soup.find('meta', {'name': 'language'})
            if lang_meta and lang_meta.get('content'):
                metadata['language'] = lang_meta['content'].split('-')[0]
            else:
                # Try to detect from content
                try:
                    text_sample, _ = self.extract_content(html, track_containers=False)
                    if text_sample:
                        detected_lang = detect(text_sample[:1000])
                        metadata['language'] = detected_lang
                except LangDetectException:
                    pass  # Keep default 'en'

        # Clean up metadata
        for key in metadata:
            if metadata[key] and isinstance(metadata[key], str):
                metadata[key] = metadata[key].strip()
                if not metadata[key]:
                    metadata[key] = None

        # Set default title if none found
        if not metadata['title']:
            metadata['title'] = f"Scraped from {url}"

        return metadata

    def extract_content_from_selected_containers(self, html: str, containers: List[Dict], selected_indices: List[int]) -> str:
        """
        Extract content from only the selected containers.

        Args:
            html: HTML content
            containers: List of container info from initial extraction
            selected_indices: Indices of containers to include

        Returns:
            Extracted text from selected containers
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer',
                            'iframe', 'noscript', 'aside']):
            element.decompose()

        # Collect selected container identifiers
        selected_containers = []
        for idx in selected_indices:
            if idx < len(containers):
                selected_containers.append(containers[idx])

        if not selected_containers:
            return ""

        # Find and extract content from matching containers
        extracted_parts = []
        for container_info in selected_containers:
            # Find the container element in the soup
            container_type = container_info['type']
            container_id = container_info.get('id')
            container_classes = container_info.get('classes')

            # Build selector
            if container_id:
                # Find by ID (most specific)
                elements = soup.find_all(container_type, id=container_id)
            elif container_classes:
                # Find by classes
                class_list = container_classes.split()
                elements = soup.find_all(container_type, class_=lambda x: x and all(c in x for c in class_list))
            else:
                # Find by type only (less specific, may match multiple)
                elements = soup.find_all(container_type)

            # Extract content from found elements
            for element in elements:
                text = self._process_element(element, [], None)
                if text.strip():
                    extracted_parts.append(text)

        # Combine and clean
        combined = '\n\n'.join(extracted_parts)
        return self._clean_text(combined)

    def scrape_page(self, url: str, track_containers: bool = False, selected_containers: Optional[List[int]] = None, chinese_mode: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Scrape a single page and extract content and metadata.

        Args:
            url: URL to scrape
            track_containers: Whether to track container information
            selected_containers: List of container indices to include (None = all)
            chinese_mode: Use Chinese character detection for content extraction

        Returns:
            Tuple of (result_dict, error_message)
            result_dict contains: content, metadata, containers (if tracked)
        """
        # Fetch page
        html, error = self.fetch_page(url)
        if error:
            return None, error

        try:
            # Extract content
            content, containers = self.extract_content(html, track_containers, chinese_mode)

            if not content:
                return None, "No content found on page"

            # If selected_containers is provided, re-extract with only those containers
            if selected_containers is not None and track_containers and containers:
                content = self.extract_content_from_selected_containers(html, containers, selected_containers)
                if not content:
                    return None, "No content found in selected containers"

            # Extract metadata
            metadata = self.extract_metadata(html, url)

            result = {
                'content': content,
                'metadata': metadata
            }

            # Add containers if tracked
            if track_containers and containers is not None:
                result['containers'] = containers

            return result, None

        except Exception as e:
            return None, f"Error extracting content: {str(e)}"

    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract chapter links from an index page.

        Args:
            html: HTML content of the index page
            base_url: Base URL for resolving relative links

        Returns:
            List of dictionaries with 'name' and 'url' keys
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted elements that might contain links
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Try to find main content area
        main_content = None
        for selector in ['article', 'main', '[role="main"]',
                        '.content', '.post-content', '.article-content',
                        '#content', '#main', '.entry-content',
                        '.chapter-list', '.toc', '.table-of-contents']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            main_content = soup

        # Find all links
        all_links = main_content.find_all('a', href=True)

        # Parse base URL to filter out external links
        base_domain = urlparse(base_url).netloc

        # Stage 1: Extract and filter candidate links
        candidate_links = []
        seen_urls = set()

        for link in all_links:
            href = link.get('href', '').strip()
            if not href or href.startswith('#'):
                continue

            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)

            # Skip external links (different domain)
            link_domain = urlparse(full_url).netloc
            if link_domain != base_domain:
                continue

            # Skip duplicates
            if full_url in seen_urls:
                continue

            # Get link text
            link_text = link.get_text(strip=True)
            if not link_text:
                continue

            # Filter out common navigation links (expanded blacklist)
            lower_text = link_text.lower()
            skip_patterns = [
                'home', 'about', 'contact', 'login', 'register', 'search',
                'privacy', 'terms', 'policy', 'rss', 'subscribe', 'follow',
                'twitter', 'facebook', 'share', 'comment', 'next', 'previous',
                'prev', 'download', 'print', 'bookmark', 'archive', 'latest',
                'recent', 'popular', 'tag', 'category'
            ]
            if any(pattern in lower_text for pattern in skip_patterns):
                continue

            candidate_links.append({
                'name': link_text,
                'url': full_url
            })
            seen_urls.add(full_url)

        # Debug: Log candidate links found
        print(f"[Stage 1] Found {len(candidate_links)} candidate links after filtering")
        if candidate_links and len(candidate_links) <= 10:
            print(f"[Stage 1] Sample links: {[link['name'][:50] for link in candidate_links[:5]]}")

        # Stage 2: Try URL pattern analysis (NEW)
        if len(candidate_links) >= 2:
            # Cluster similar URLs with 90%+ similarity threshold
            url_clusters = self._cluster_similar_urls(candidate_links, threshold=0.9)

            print(f"[Stage 2] Found {len(url_clusters)} URL clusters")
            if url_clusters:
                largest_cluster = url_clusters[0]
                print(f"[Stage 2] Largest cluster has {len(largest_cluster)} links")

                # Check if cluster has sequential pattern
                pattern_info = self._detect_sequential_pattern(largest_cluster)

                if pattern_info:
                    print(f"[Stage 2] Pattern confidence: {pattern_info['confidence']:.2f}, threshold: 0.8")

                    if pattern_info['confidence'] > 0.8:
                        # Found strong URL pattern - return these links
                        print(f"[URL Pattern] ✓ Found {len(largest_cluster)} chapter links with {pattern_info['confidence']:.2f} confidence")
                        print(f"[URL Pattern] Range: {pattern_info['min']}-{pattern_info['max']}, Gaps: {pattern_info['gaps']}")
                        return largest_cluster
                    else:
                        print(f"[Stage 2] Confidence too low ({pattern_info['confidence']:.2f} < 0.8), falling back")
                else:
                    print(f"[Stage 2] No sequential pattern detected in cluster")
            else:
                print(f"[Stage 2] No clusters found with 90%+ similarity")
        else:
            print(f"[Stage 2] Skipped (need at least 2 candidates, have {len(candidate_links)})")

        # Stage 3: Fallback to text-based heuristics
        print("[Stage 3] No strong URL pattern found, falling back to text-based detection")
        chapter_links = []

        for link_dict in candidate_links:
            link_text = link_dict['name']
            lower_text = link_text.lower()

            # More strict text-based check (removed overly permissive length filter)
            is_chapter_like = (
                re.search(r'\bchapter\b', lower_text, re.I) or
                re.search(r'\bch\.?\s*\d+', lower_text, re.I) or
                re.search(r'^\d+[\.\):]', link_text) or  # Starts with number
                re.search(r'^\d+$', link_text)  # Just a number
            )

            if is_chapter_like:
                chapter_links.append(link_dict)

        print(f"[Stage 3] Text-based detection found {len(chapter_links)} chapter-like links")

        # If we found very few links with the strict criteria, try list-based fallback
        if len(chapter_links) < 3:
            print(f"[Stage 4] Only {len(chapter_links)} links found, trying list-based fallback")
            chapter_links = []
            seen_urls = set()

            # Look for links in ordered lists (common for chapter listings)
            for ol in main_content.find_all('ol'):
                for li in ol.find_all('li'):
                    link = li.find('a', href=True)
                    if link:
                        href = link.get('href', '').strip()
                        if href and not href.startswith('#'):
                            full_url = urljoin(base_url, href)
                            if full_url not in seen_urls:
                                link_text = link.get_text(strip=True)
                                if link_text:
                                    chapter_links.append({
                                        'name': link_text,
                                        'url': full_url
                                    })
                                    seen_urls.add(full_url)

            # If still not enough, look for links in unordered lists
            if len(chapter_links) < 3:
                for ul in main_content.find_all('ul'):
                    # Skip if this looks like a navigation menu
                    if ul.get('class') and any('nav' in c.lower() or 'menu' in c.lower() for c in ul.get('class')):
                        continue

                    for li in ul.find_all('li'):
                        link = li.find('a', href=True)
                        if link:
                            href = link.get('href', '').strip()
                            if href and not href.startswith('#'):
                                full_url = urljoin(base_url, href)
                                link_domain = urlparse(full_url).netloc
                                if link_domain == base_domain and full_url not in seen_urls:
                                    link_text = link.get_text(strip=True)
                                    if link_text and len(link_text) < 200:
                                        chapter_links.append({
                                            'name': link_text,
                                            'url': full_url
                                        })
                                        seen_urls.add(full_url)

        print(f"[Final] Returning {len(chapter_links)} chapter links")

        # Stage 5: Last resort - if still nothing found, try more lenient text filter
        if len(chapter_links) == 0 and len(candidate_links) > 0:
            print(f"[Stage 5] No links found via strict methods, trying lenient filter on {len(candidate_links)} candidates")
            # Use a more lenient filter as absolute last resort
            for link_dict in candidate_links:
                link_text = link_dict['name']
                # Accept links with reasonable length as potential chapters
                if len(link_text) < 150 and len(link_text) > 1:
                    chapter_links.append(link_dict)
            print(f"[Stage 5] Lenient filter found {len(chapter_links)} links")

        return chapter_links

    def _tokenize_url(self, url: str) -> List[str]:
        """
        Tokenize a URL into path segments for comparison.

        Args:
            url: URL to tokenize

        Returns:
            List of path segments
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)

        # Get path and split into segments
        path = parsed.path.strip('/')
        if not path:
            return []

        segments = path.split('/')

        # Further split segments by common delimiters
        tokens = []
        for segment in segments:
            # Split by hyphens, underscores, dots
            parts = segment.replace('-', ' ').replace('_', ' ').replace('.', ' ').split()
            tokens.extend(parts)

        return tokens

    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """
        Calculate similarity score between two URLs using token-based comparison.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            Similarity score from 0.0 to 1.0
        """
        from urllib.parse import urlparse

        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)

        # URLs must have same domain
        if parsed1.netloc != parsed2.netloc:
            return 0.0

        # Get path segments (don't tokenize further for structure comparison)
        path1 = parsed1.path.strip('/').split('/')
        path2 = parsed2.path.strip('/').split('/')

        # Must have same depth
        if len(path1) != len(path2):
            return 0.0

        # Calculate segment-by-segment similarity
        matching_segments = 0
        total_segments = len(path1)

        if total_segments == 0:
            return 0.0

        for seg1, seg2 in zip(path1, path2):
            if seg1 == seg2:
                matching_segments += 1
            else:
                # Check if segments are similar (differ only in numbers)
                # Remove all digits and compare
                seg1_no_digits = ''.join(c for c in seg1 if not c.isdigit())
                seg2_no_digits = ''.join(c for c in seg2 if not c.isdigit())

                if seg1_no_digits == seg2_no_digits and seg1_no_digits:
                    # Segments differ only in numbers - consider it a match
                    matching_segments += 0.9  # Slightly less than exact match

        similarity = matching_segments / total_segments
        return similarity

    def _extract_url_template(self, urls: List[Dict[str, str]]) -> Optional[Dict]:
        """
        Extract common URL template from a list of URLs.

        Args:
            urls: List of URL dictionaries with 'url' key

        Returns:
            Template information or None if no clear template
        """
        if len(urls) < 2:
            return None

        from urllib.parse import urlparse

        # Get all URL paths
        paths = [urlparse(u['url']).path.strip('/') for u in urls]

        if not paths:
            return None

        # Find common prefix
        common_prefix = paths[0]
        for path in paths[1:]:
            # Find longest common prefix
            i = 0
            while i < len(common_prefix) and i < len(path) and common_prefix[i] == path[i]:
                i += 1
            common_prefix = common_prefix[:i]

        # Find common suffix
        common_suffix = paths[0]
        for path in paths[1:]:
            # Find longest common suffix
            i = -1
            while abs(i) <= len(common_suffix) and abs(i) <= len(path) and common_suffix[i] == path[i]:
                i -= 1
            if i == -1:
                common_suffix = ""
            else:
                common_suffix = common_suffix[i+1:]

        return {
            'prefix': common_prefix,
            'suffix': common_suffix,
            'count': len(urls),
            'sample_url': urls[0]['url']
        }

    def _cluster_similar_urls(self, urls: List[Dict[str, str]], threshold: float = 0.9) -> List[List[Dict[str, str]]]:
        """
        Cluster URLs by similarity (90%+ threshold).

        Args:
            urls: List of URL dictionaries with 'url' and 'name' keys
            threshold: Similarity threshold (default 0.9 for 90%)

        Returns:
            List of clusters, sorted by size (largest first)
        """
        if len(urls) < 2:
            return [urls] if urls else []

        # Build similarity matrix
        n = len(urls)
        clusters = []
        used = set()

        for i in range(n):
            if i in used:
                continue

            cluster = [urls[i]]
            used.add(i)

            for j in range(i + 1, n):
                if j in used:
                    continue

                similarity = self._calculate_url_similarity(urls[i]['url'], urls[j]['url'])

                if similarity >= threshold:
                    cluster.append(urls[j])
                    used.add(j)

            if len(cluster) > 1:  # Only keep clusters with 2+ members
                clusters.append(cluster)

        # Sort by cluster size (largest first)
        clusters.sort(key=len, reverse=True)

        return clusters

    def _detect_sequential_pattern(self, cluster: List[Dict[str, str]]) -> Optional[Dict]:
        """
        Detect if a cluster of URLs contains sequential numbering.

        Args:
            cluster: List of URL dictionaries

        Returns:
            Pattern metadata with confidence score, or None
        """
        import re

        if len(cluster) < 2:
            return None

        # Extract numbers from each URL
        url_numbers = []
        for item in cluster:
            numbers = re.findall(r'\d+', item['url'])
            if numbers:
                # Use the last number found (usually chapter number)
                url_numbers.append((item, int(numbers[-1])))

        if len(url_numbers) < 2:
            return None

        # Sort by number
        url_numbers.sort(key=lambda x: x[1])
        numbers = [num for _, num in url_numbers]

        # Check for sequence characteristics
        min_num = min(numbers)
        max_num = max(numbers)
        unique_numbers = len(set(numbers))

        # Calculate gaps
        expected_count = max_num - min_num + 1
        actual_count = unique_numbers
        coverage = actual_count / expected_count if expected_count > 0 else 0

        # Calculate confidence
        cluster_size_ratio = len(cluster) / max(len(cluster), 1)  # Always 1.0 for self
        sequential_score = 1.0 if coverage >= 0.5 else coverage * 2  # Penalize large gaps

        confidence = (
            0.5 * cluster_size_ratio +
            0.5 * sequential_score
        )

        return {
            'has_sequence': True,
            'min': min_num,
            'max': max_num,
            'count': unique_numbers,
            'coverage': coverage,
            'confidence': confidence,
            'gaps': expected_count - actual_count
        }
