# Lexivion - Advanced Document Search System

A modern Retrieval-Augmented Generation (RAG) system with a beautiful web interface for uploading PDF documents and performing semantic search with image retrieval. The system combines state-of-the-art embedding models with Google's Gemini AI to provide intelligent, context-aware answers from your document collection.

## 🌟 Features

### Core Capabilities
- 📄 **PDF Processing**: Extract text and images from PDF documents with page-level granularity
- 🔍 **Semantic Search**: AI-powered retrieval using sentence transformers for intelligent document search
- 🖼️ **Image Retrieval**: Automatically associate images with relevant text chunks using CLIP embeddings
- 🤖 **AI-Powered Answers**: Integration with Google Gemini for generating contextual responses
- 📑 **Chunk-to-PDF Preview**: Click any context segment to view the original PDF page in-app
- 🎨 **Modern UI**: Beautiful, responsive React frontend with dark theme
- 🚀 **RESTful API**: Clean Flask backend with proper error handling and CORS support
- 💾 **PostgreSQL Storage**: Efficient storage with pgvector for O(log n) vector search, JSONB for compatibility

### Advanced Features
- **High-Dimensional Embeddings**: 1024-dimensional embeddings for maximum accuracy (BGE-large-en-v1.5 for text, CLIP-ViT-H-14 for images)
- **Efficient Vector Search**: pgvector with HNSW indexes for O(log n) similarity search performance
- **Multimodal Embeddings**: Separate embeddings for text and images with state-of-the-art models
- **Structured Responses**: Gemini organizes results into sections with chunk references
- **Document Management**: Track document metadata, source paths, and relationships
- **Image-Text Linking**: Explicit relationships between text chunks and associated images
- **Robust Image Processing**: Multiple decoding methods handle various PDF image formats
- **Health Monitoring**: Startup checks and health endpoints for system validation
- **Dual Storage**: Both JSONB (backward compatibility) and vector columns (performance)

## 🏗️ Architecture

### System Overview
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   React     │  HTTP   │   Flask     │  SQL    │ PostgreSQL  │
│  Frontend   │◄───────►│   Backend   │◄───────►│  Database   │
│ (Port 3000) │         │ (Port 8000) │         │  (Port 5432)│
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ API Calls
                              ▼
                        ┌─────────────┐
                        │   Gemini    │
                        │     API     │
                        └─────────────┘
```

### Technology Stack

#### Backend
- **Framework**: Flask 2.3+ (Python web framework)
- **Database**: PostgreSQL 12+ with pgvector extension for efficient vector search
- **ML Models**:
  - Text Embeddings: `BAAI/bge-large-en-v1.5` (1024 dimensions) - State-of-the-art retrieval
  - Image Embeddings: `laion/CLIP-ViT-H-14-laion2B-s32B-b79K` (1024 dimensions) - High-quality multimodal
- **PDF Processing**: `pdfplumber` for text and image extraction
- **Image Processing**: PIL/Pillow for image manipulation
- **Vector Operations**: pgvector for O(log n) similarity search, NumPy fallback
- **LLM Integration**: Google Generative AI (Gemini 2.0 Flash)

#### Frontend
- **Framework**: React 18 with Hooks
- **Build Tool**: Vite 5.0+
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Styling**: Modern CSS with CSS Variables

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18 or higher
- **PostgreSQL**: 12 or higher with pgvector extension
- **npm** or **yarn** package manager
- **Google Gemini API Key** (optional, for AI responses)
- **GPU** (recommended for production, especially for image embeddings)

## 🚀 Quick Start

### 1. Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE RAG_Bot;

# Connect to the database
\c RAG_Bot

# Install pgvector extension (requires superuser privileges)
# If you don't have pgvector installed, install it first:
# - Ubuntu/Debian: sudo apt-get install postgresql-14-pgvector (or your PostgreSQL version)
# - macOS: brew install pgvector
# - Or build from source: https://github.com/pgvector/pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# Run migrations
\i scripts/migrations/001_init.sql
\i scripts/migrations/002_rag_pipeline.sql
\i scripts/migrations/003_high_dim_embeddings.sql
```

### 2. Backend Setup

```bash
# Navigate to project root
cd Lexivion

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file in project root
# Copy the template below and fill in your values
```

**`.env` file template:**
```env
# Database Configuration
DB_HOST=localhost
DB_NAME=RAG_Bot
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

# File Storage
UPLOAD_FOLDER=./data/uploads

# Chunking Configuration
CHUNK_SIZE=450
CHUNK_OVERLAP=75
MAX_CONTEXT_CHUNKS=8
DEFAULT_TOP_K=5

# Embedding Models (High-Dimensional)
TEXT_EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
IMAGE_EMBEDDING_MODEL=laion/CLIP-ViT-H-14-laion2B-s32B-b79K
TEXT_EMBEDDING_DIM=1024
IMAGE_EMBEDDING_DIM=1024
USE_PGVECTOR=true

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
GEMINI_RESPONSE_MIME_TYPE=application/json
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional, defaults to localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 4. Running the Application

#### Development Mode

**Terminal 1 - Backend:**
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Run Flask server
cd backend
python server.py
```

The API will be available at `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The web app will be available at `http://localhost:3000`

#### Using Startup Scripts

**Windows:**
```bash
# Terminal 1
start_backend.bat

# Terminal 2
start_frontend.bat
```

**Linux/Mac:**
```bash
# Terminal 1
./start_backend.sh

# Terminal 2
./start_frontend.sh
```

### 5. Production Build

**Backend:**
```bash
# Install production WSGI server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the dist/ folder with a web server like nginx
```

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Lexivion API",
  "gemini_enabled": true,
  "model": "gemini-2.0-flash"
}
```

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data

Body: file (PDF file)
```

**Response:**
```json
{
  "message": "document.pdf processed successfully!",
  "filename": "document.pdf",
  "document_id": 1,
  "chunks_stored": 45,
  "images_stored": 12
}
```

### Search
```http
POST /api/search
Content-Type: application/json

Body: {
  "query": "your search query",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "your search query",
  "top_k": 5,
  "answer": "Gemini-generated answer...",
  "sections": [
    {
      "title": "Section Title",
      "text": "Detailed explanation...",
      "chunk_ids": [1, 2, 3],
      "images": [...],
      "documents": [...]
    }
  ],
  "context": [...],
  "chunks_used": [1, 2, 3, 4, 5],
  "model": "gemini-2.0-flash"
}
```

### Get Document
```http
GET /api/documents/<document_id>
```

### Stream Document File
```http
GET /api/documents/<document_id>/file
```

## 📁 Project Structure

```
Lexivion/
├── backend/
│   ├── server.py              # Flask entry point
│   └── app/
│       ├── __init__.py        # App factory
│       ├── config.py          # Configuration management
│       ├── db.py              # Database connection
│       ├── startup_checks.py  # System validation
│       ├── repository/
│       │   └── rag_repository.py  # Data access layer
│       ├── routes/
│       │   ├── ingest.py      # /upload endpoint
│       │   ├── search.py      # /search endpoint
│       │   └── documents.py   # /documents endpoints
│       └── services/
│           ├── embedding.py   # Text/image embedding logic
│           ├── pdf_processing.py  # PDF extraction
│           ├── search.py      # RAG search implementation
│           └── gemini.py      # Gemini LLM integration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadSection.jsx      # PDF upload UI
│   │   │   ├── SearchSection.jsx     # Search interface
│   │   │   └── ResultsDisplay.jsx    # Results with images
│   │   ├── App.jsx            # Main app component
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   └── migrations/
│       ├── 001_init.sql       # Initial schema
│       ├── 002_rag_pipeline.sql  # Enhanced schema
│       └── 003_high_dim_embeddings.sql  # pgvector support
├── data/
│   └── uploads/               # Uploaded PDFs storage
├── tests/
│   └── test_chunking.py      # Unit tests
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── PROJECT_ANALYSIS.md        # Detailed project analysis
└── QUICKSTART.md              # Quick setup guide
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_NAME` | Database name | `RAG_Bot` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | (required) |
| `DB_PORT` | Database port | `5432` |
| `UPLOAD_FOLDER` | PDF storage path | `./data/uploads` |
| `CHUNK_SIZE` | Text chunk size (words) | `450` |
| `CHUNK_OVERLAP` | Chunk overlap (words) | `75` |
| `MAX_CONTEXT_CHUNKS` | Max chunks for LLM | `8` |
| `DEFAULT_TOP_K` | Default search results | `5` |
| `TEXT_EMBEDDING_MODEL` | Text embedding model | `BAAI/bge-large-en-v1.5` |
| `IMAGE_EMBEDDING_MODEL` | Image embedding model | `laion/CLIP-ViT-H-14-laion2B-s32B-b79K` |
| `TEXT_EMBEDDING_DIM` | Text embedding dimensions | `1024` |
| `IMAGE_EMBEDDING_DIM` | Image embedding dimensions | `1024` |
| `USE_PGVECTOR` | Enable pgvector for vector search | `true` |
| `GEMINI_API_KEY` | Gemini API key | (required) |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |

### Chunking Strategy

The system uses a sliding window approach:
- **Chunk Size**: 450 words (configurable)
- **Overlap**: 75 words (configurable)
- **Purpose**: Ensures context continuity across chunk boundaries

## 🔍 How It Works

### Document Ingestion Flow

1. **PDF Upload**: User uploads PDF via web interface
2. **Text Extraction**: Extract text from each page using `pdfplumber`
3. **Image Extraction**: Extract images from each page
4. **Text Chunking**: Split text into overlapping chunks
5. **Embedding Generation**:
   - Text chunks → BGE-large-en-v1.5 embeddings (1024-dim)
   - Images → CLIP-ViT-H-14-laion2B-s32B-b79K embeddings (1024-dim)
6. **Storage**: Store chunks, embeddings (JSONB + vector columns), and metadata in PostgreSQL
7. **Vector Indexing**: pgvector HNSW indexes for fast similarity search
8. **Linking**: Link images to their associated text chunks

### Search Flow

1. **Query Input**: User enters search query
2. **Query Embedding**: Encode query using BGE-large-en-v1.5 (1024 dimensions)
3. **Similarity Search**: 
   - **With pgvector**: O(log n) HNSW index search for fast retrieval
   - **Fallback**: O(n) linear scan with cosine similarity (if pgvector unavailable)
4. **Ranking**: Sort by similarity score, select top-k
5. **Image Retrieval**: Fetch associated images for top chunks
6. **Context Assembly**: Prepare context segments with metadata
7. **LLM Generation**: Send context to Gemini for answer generation
8. **Response Formatting**: Structure response with sections and references
9. **Display**: Render results with images and chunk previews

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Errors:**
- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check database exists: `psql -U postgres -l`

**Model Loading Issues:**
- First run downloads models (~2-3GB for high-dimensional models)
- BGE-large-en-v1.5: ~1.3GB
- CLIP-ViT-H-14: ~1.5GB
- Ensure stable internet connection
- Check disk space availability (at least 5GB free recommended)
- Models are cached after first download
- GPU recommended for faster inference

**Gemini API Errors:**
- Verify `GEMINI_API_KEY` is set in `.env`
- Check API key validity
- Ensure `google-generativeai` package is installed
- Restart backend after changing environment variables

### Frontend Issues

**API Connection Errors:**
- Verify backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env`
- Ensure CORS is enabled (already configured)
- Check browser console for errors

**Build Errors:**
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)
- Clear Vite cache: `rm -rf frontend/.vite`

**pgvector Issues:**
- Ensure pgvector extension is installed: `CREATE EXTENSION vector;`
- Check extension is enabled: `SELECT * FROM pg_extension WHERE extname = 'vector';`
- If pgvector unavailable, system falls back to JSONB (slower but functional)
- Install pgvector: https://github.com/pgvector/pgvector

### Performance Issues

**Slow Search:**
- Ensure pgvector is enabled (`USE_PGVECTOR=true`)
- With pgvector: O(log n) search performance
- Without pgvector: O(n) linear scan (slower for large datasets)
- Reduce `MAX_CONTEXT_CHUNKS` for faster responses
- GPU recommended for embedding generation

**Slow Upload:**
- PDF processing is synchronous
- Large PDFs may take time
- Consider implementing async processing (Celery/RQ)

## 🔒 Security Considerations

### Current State
- ✅ Parameterized SQL queries (SQL injection protection)
- ✅ File type validation (PDF only)
- ✅ Filename sanitization
- ⚠️ No authentication/authorization
- ⚠️ No rate limiting
- ⚠️ No input sanitization for search queries

### Recommendations for Production
- Implement JWT-based authentication
- Add rate limiting (Flask-Limiter)
- Sanitize user inputs
- Add file size limits (currently 50MB)
- Implement HTTPS
- Add request logging and monitoring

## 📊 Performance Characteristics

### Current Capabilities
- **Search**: O(log n) with pgvector HNSW indexes (efficient for millions of chunks)
- **Fallback**: O(n) linear scan when pgvector unavailable (JSONB mode)
- **Upload**: Synchronous processing blocks API (async recommended for production)
- **Memory**: Efficient index-based search with pgvector (no need to load all chunks)

### Scalability Considerations
- ✅ **Vector Search**: pgvector with HNSW indexes scales to millions of chunks
- ✅ **High-Quality Embeddings**: 1024-dimensional embeddings provide superior accuracy
- **Consider implementing**:
  - ✅ `pgvector` for efficient vector search - **IMPLEMENTED**
  - Redis for caching query results
  - Async task queue for PDF processing (Celery/RQ)
  - Connection pooling for database
  - GPU acceleration for embedding generation

## 🧪 Testing

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=backend/app
```

### Test Structure
- Unit tests for chunking logic
- Integration tests for API endpoints (to be added)
- End-to-end tests for search flow (to be added)

## 🚢 Deployment

### Docker (Recommended)

Create `Dockerfile` and `docker-compose.yml` for containerized deployment.

### Manual Deployment

1. **Backend**: Use Gunicorn with multiple workers
2. **Frontend**: Build and serve static files with Nginx
3. **Database**: Configure PostgreSQL with proper backups
4. **Environment**: Set production environment variables

## 📚 Additional Documentation

- [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) - Detailed architecture and pipeline analysis
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [CHANGES.md](CHANGES.md) - Recent changes and migration notes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is for educational and development purposes.

## 🙏 Acknowledgments

- **BAAI (Beijing Academy of AI)** for BGE-large-en-v1.5 text embeddings
- **LAION** for CLIP-ViT-H-14 image embeddings
- **Google Gemini** for LLM capabilities
- **pgvector** for efficient vector search
- **pdfplumber** for PDF processing
- **Flask** and **React** communities

## 🔮 Future Enhancements

- [x] Implement `pgvector` for efficient vector search ✅
- [x] Upgrade to high-dimensional embeddings (1024-dim) ✅
- [x] Improve image processing robustness ✅
- [ ] Add async PDF processing with Celery
- [ ] Implement user authentication and authorization
- [ ] Add document management (list, delete, update)
- [ ] Implement advanced search filters
- [ ] Add export functionality for results
- [ ] Create API documentation with Swagger/OpenAPI
- [ ] Add monitoring and observability (Prometheus, Grafana)
- [ ] Implement caching layer (Redis)
- [ ] Add multi-document search and filtering
- [ ] GPU acceleration optimization
- [ ] Batch embedding generation for faster uploads

---

**Built with ❤️ for intelligent document search**
