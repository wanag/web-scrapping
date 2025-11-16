"""
Simple test script to verify backend API functionality.
"""
import requests
import sys

# Base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    assert response.status_code == 200
    print("  ✓ Health check passed\n")

def test_auth():
    """Test authentication."""
    print("Testing authentication...")

    # Test with correct PIN
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"pin": "1234"}
    )
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Response: {data}")
    assert response.status_code == 200
    assert data["success"] is True
    assert "token" in data
    token = data["token"]
    print(f"  ✓ Authentication passed\n")

    return token

def test_scrape(token):
    """Test scraping a page."""
    print("Testing scraping...")

    # Use a simple, reliable test page (Wikipedia article)
    test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{BASE_URL}/api/scraper/execute",
        json={
            "url": test_url,
            "mode": "one_page",
            "metadata_overrides": {
                "title": "Test Book: Python Programming"
            }
        },
        headers=headers
    )

    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Response: {data}")

    if response.status_code == 200 and data.get("success"):
        print(f"  ✓ Scraping passed")
        print(f"    Book ID: {data.get('book_id')}")
        print(f"    Chapters: {data.get('chapters_saved')}")
        print(f"    Size: {data.get('total_size')}\n")
        return data.get("book_id")
    else:
        print(f"  ✗ Scraping failed: {data.get('errors', data.get('message'))}\n")
        return None

def test_list_books(token):
    """Test listing books."""
    print("Testing book list...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/books", headers=headers)

    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Total books: {data.get('total')}")

    if data.get("books"):
        print(f"  First book: {data['books'][0]['title']}")

    print("  ✓ Book list passed\n")
    return data.get("books", [])

def test_get_book(token, book_id):
    """Test getting book details."""
    print(f"Testing get book {book_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/books/{book_id}", headers=headers)

    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Title: {data['metadata']['title']}")
    print(f"  Chapters: {len(data['chapters'])}")
    print("  ✓ Get book passed\n")

    return data

def test_get_chapter(token, book_id, chapter_id=0):
    """Test getting chapter content."""
    print(f"Testing get chapter {chapter_id}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/books/{book_id}/chapters/{chapter_id}",
        headers=headers
    )

    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Title: {data['title']}")
    print(f"  Content length: {len(data['content'])} chars")
    print(f"  Preview: {data['content'][:100]}...")
    print("  ✓ Get chapter passed\n")

    return data

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("📚 Book Scraper & Reader API - Backend Tests")
    print("="*60 + "\n")

    try:
        # Test 1: Health check
        test_health()

        # Test 2: Authentication
        token = test_auth()

        # Test 3: Scrape a page
        book_id = test_scrape(token)

        if book_id:
            # Test 4: List books
            books = test_list_books(token)

            # Test 5: Get book details
            test_get_book(token, book_id)

            # Test 6: Get chapter content
            test_get_chapter(token, book_id)

        print("="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\nMake sure the backend server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)

    main()
