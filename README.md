# Book Scraper & Reader System

A full-stack web application for scraping books from websites, storing them locally, and providing a clean reading interface.

## Features

### Core Functionality
- **PIN Authentication**: Secure 4-digit PIN login with JWT tokens
- **Multi-Mode Scraping**:
  - One-page mode for single articles
  - Index mode for chapter-based books
  - Hybrid mode for combined content
- **Chinese Website Support**: Dedicated mode with character detection (>50% threshold)
- **Local Storage**: Save books with metadata and chapters in markdown format
- **Clean Reader Interface**: Responsive reader with customizable settings
- **Auto-Detection**: Automatic extraction of title, author, and language

### Advanced Features
- **Preview Before Scraping**: Preview content and edit metadata before saving
- **Container Selection**: Choose specific content containers to include/exclude
- **Chapter Preview**: Preview individual chapters in index/hybrid modes
- **URL Clustering**: Intelligent chapter detection using URL pattern analysis
- **Persistent Settings**: Theme and mode preferences saved in localStorage
- **Dark Mode**: Optimized color scheme with darker blue top bar
- **Content Editor**: Edit scraped content and metadata before finalizing

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **BeautifulSoup4** - HTML parsing and content extraction
- **JWT** - Token-based authentication
- **bcrypt** - Password hashing

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vuetify** - Material Design component library
- **Pinia** - State management
- **Axios** - HTTP client
- **Vue Router** - Navigation

## Project Structure

```
web-scrapping/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main application
│   ├── auth.py             # Authentication logic
│   ├── models/             # Pydantic schemas
│   ├── scraper/            # Web scraping modules
│   └── storage/            # File storage management
├── frontend/               # Vue 3 frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── stores/         # Pinia stores
│   │   ├── services/       # API services
│   │   └── router/         # Vue Router config
│   └── package.json
├── data/books/             # Stored books
├── requirements.txt        # Python dependencies
└── .env                    # Environment configuration
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository** (or you're already in it)

2. **Set up the backend:**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Set up the frontend:**

```bash
cd frontend
npm install
```

### Configuration

The `.env` file contains the following configuration:

```env
# Authentication
APP_PIN=1234                  # Default PIN (change this!)
JWT_SECRET_KEY=your-secret... # Change in production
JWT_EXPIRATION_HOURS=24

# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,...
```

### Running the Application

**Terminal 1 - Start Backend:**

```bash
# From project root
source venv/bin/activate
python -m backend.app
```

Backend will start on `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

**Terminal 2 - Start Frontend:**

```bash
# From project root
cd frontend
npm run dev
```

Frontend will start on `http://localhost:3000`

### Usage

1. **Login**: Navigate to `http://localhost:3000` and enter PIN `1234`

2. **Add a Book**:
   - Click "Add New Book"
   - Enter a URL (e.g., Wikipedia article, blog post, novel website)
   - Select scraping mode:
     - **One-page**: Single article or chapter
     - **Index**: Book with chapter links
     - **Hybrid**: Index page with content
   - **For Chinese websites**: Enable "Chinese Website Mode" toggle
   - Preview content and edit metadata
   - Select/deselect chapters (for index/hybrid modes)
   - Preview individual chapters before scraping
   - Click "Start Scraping"

3. **Read**:
   - Click on any book to open the reader
   - Use navigation buttons or arrow keys to move between chapters
   - Customize reading settings (font size, theme, etc.)
   - Toggle dark mode with the sun/moon icon

4. **Tips**:
   - Chinese mode toggle state persists across sessions
   - Dark/light theme preference is saved automatically
   - Preview chapters individually to ensure quality before bulk scraping
   - Use URL clustering to filter out navigation links from chapter lists

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with PIN
- `POST /api/auth/verify` - Verify token
- `POST /api/auth/logout` - Logout

### Scraper
- `POST /api/scraper/preview` - Preview content before scraping (supports chinese_mode)
- `POST /api/scraper/execute` - Execute scraping with selected chapters (supports chinese_mode)
- `POST /api/scraper/create-book` - Create book metadata
- `POST /api/scraper/add-chapter` - Add individual chapter to existing book (supports chinese_mode)

### Books
- `GET /api/books` - List all books
- `GET /api/books/{book_id}` - Get book details
- `GET /api/books/{book_id}/chapters/{chapter_id}` - Get chapter content
- `DELETE /api/books/{book_id}` - Delete a book

### System
- `GET /health` - Health check
- `GET /api/system/stats` - Storage statistics

## Testing

### Backend Tests

```bash
# Make sure backend is running on port 8000
source venv/bin/activate
python test_backend.py
```

## Phase Roadmap

### ✅ Phase 1: Core Functionality (COMPLETED)
- PIN authentication
- One-page scraping mode
- Simple reader interface
- File storage system

### ✅ Phase 2: Advanced Scraping (COMPLETED)
- Index and hybrid modes
- Preview functionality with container selection
- Metadata extraction and editing
- Chapter preview in index/hybrid modes
- URL clustering for intelligent chapter detection
- Chinese website mode with character detection
- Container-based content extraction
- Content editor with markdown support

### ✅ Phase 3: Reader & UI Enhancement (COMPLETED)
- Multi-language support (Chinese, English, and more)
- Theme customization (Dark/Light mode)
- Persistent user preferences (localStorage)
- Optimized dark mode color scheme
- Font size adjustment
- Responsive mobile design

### 🔜 Phase 4: Additional Features
- Reading progress tracking and sync
- Bookmarks within chapters
- Search within books
- Export functionality (EPUB, PDF)
- Offline support (PWA)
- Statistics dashboard
- Font family selection

## Troubleshooting

### Backend Issues

**ImportError / Module not found:**
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**Port already in use:**
- Change `APP_PORT` in `.env`
- Or kill the process using port 8000

### Frontend Issues

**Module not found:**
- Delete `node_modules` and run `npm install` again

**Cannot connect to backend:**
- Make sure backend is running on port 8000
- Check CORS settings in `.env`

**Vite port in use:**
- Vite will automatically use next available port (3001, 3002, etc.)

## Security Notes

- **Change the default PIN** in `.env` before deployment
- **Change the JWT secret key** to a secure random string
- Never commit `.env` file to version control
- Use HTTPS in production
- Implement rate limiting for production use

## License

This project is created for educational and personal use.

## Contributing

Phase 1 is complete! Future phases will add more features. Feel free to suggest improvements or report issues.
