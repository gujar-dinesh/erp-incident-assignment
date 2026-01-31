# ERP Incident Triage Portal

A full-stack web application for managing and triaging ERP system incidents with AI-powered automatic enrichment using RAG (Retrieval-Augmented Generation).

## What This Project Does

This application provides a comprehensive incident management system for ERP systems that:

- **Automatically Enriches Incidents**: Uses AI (RAG) and rule-based logic to automatically classify incidents with:
  - Severity levels (P1, P2, P3)
  - Categories (Configuration Issue, Data Issue, Integration Failure, Security/Access)
  - Summaries and suggested actions
  - Similar incident detection

- **Learns from History**: Uses RAG to find similar past incidents and learn from successful resolutions

- **Hybrid Intelligence**: Combines fast rule-based classification (90% of cases) with AI-powered RAG enhancement for ambiguous cases

- **Full CRUD Operations**: Create, read, update, and manage incidents through a modern web interface

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **DynamoDB** - AWS NoSQL database (with mock option for development)
- **OpenAI API** - For embeddings and LLM classification (optional RAG feature)
- **Python 3.11+**

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Quick Start

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 16+** and **npm** (for frontend)
- **OpenAI API Key** (optional, for RAG features)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` file** (optional configurations):
   ```bash
   # For development (no AWS needed)
   USE_MOCK=true
   ENVIRONMENT=development

   # For RAG features (optional)
   USE_RAG=false
   OPENAI_API_KEY=your_openai_api_key_here
   RAG_FORCE_ALL=false
   ```

6. **Start the backend server:**
   ```bash
   # Option 1: Mock storage (no AWS required - recommended for testing)
   python run_mock.py

   # Option 2: Real DynamoDB (requires AWS credentials)
   python run.py
   ```

   The API will be available at `http://localhost:8000`

   **API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend:**
   ```bash
   # Option 1: With backend (requires backend running on port 8000)
   npm run dev

   # Option 2: Frontend only with mock data (no backend needed)
   npm run dev:mock
   ```

   The app will be available at `http://localhost:5173`

## Running the Full Application

### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
python run_mock.py
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Features

### Incident Management
- Create incidents with automatic enrichment
- View all incidents with filtering
- Update incident status
- View detailed incident information

### Automatic Enrichment
- **Severity Detection**: P1 (critical), P2 (medium), P3 (low)
- **Category Classification**: Configuration, Data, Integration, Security/Access
- **Summary Generation**: Auto-generated summaries
- **Action Suggestions**: Context-aware recommendations

### RAG Features (Optional)
- Find similar past incidents
- Learn from historical resolutions
- Enhanced classification for ambiguous cases
- Context-aware suggestions

## API Endpoints

- `POST /api/incidents` - Create new incident
- `GET /api/incidents` - List all incidents (with pagination and filters)
- `GET /api/incidents/{id}` - Get specific incident
- `PATCH /api/incidents/{id}` - Update incident
- `GET /api/incidents/{id}/similar` - Get similar incidents (RAG feature)
- `GET /health` - Health check

## Configuration

### Backend Configuration (`.env`)

```bash
# Storage
USE_MOCK=true                    # Use in-memory storage (no AWS needed)
ENVIRONMENT=development

# AWS (only if USE_MOCK=false)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=erp_incidents

# RAG Features (optional)
USE_RAG=false                    # Enable RAG features
OPENAI_API_KEY=sk-...           # Required if USE_RAG=true
RAG_FORCE_ALL=false             # Force RAG for all incidents
RAG_CONFIDENCE_THRESHOLD=0.7
RAG_MAX_SIMILAR_INCIDENTS=5
```

### Frontend Configuration (`.env`)

```bash
VITE_API_URL=http://localhost:8000
VITE_USE_MOCK=false             # Use mock data instead of backend
```

## Testing

### Run Tests
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m rag           # RAG feature tests

# Run specific test file
pytest tests/test_enrichment_service.py
```

### Generate Test Data
```bash
cd backend
source venv/bin/activate
python scripts/generate_mock_data.py
```

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    (http://localhost:5173)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP Requests (REST API)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Frontend (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ IncidentList │  │CreateIncident │  │IncidentDetail│        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                   ┌────────▼────────┐                           │
│                   │   API Service  │                           │
│                   │   (api.js)     │                           │
│                   └────────┬───────┘                           │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│                    (http://localhost:8000)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Router                             │  │
│  │  POST /api/incidents  │  GET /api/incidents/{id}          │  │
│  │  GET /api/incidents   │  PATCH /api/incidents/{id}        │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                                │
│  ┌──────────────▼──────────────────────────────────────────┐  │
│  │              Enrichment Service                          │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ Rule-based      │  │ RAG Service (Optional)        │  │  │
│  │  │ (Keyword Match)│  │ - Embeddings (OpenAI)        │  │  │
│  │  │                │  │ - Vector Search               │  │  │
│  │  │                │  │ - LLM Classification         │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                                │
│  ┌──────────────▼──────────────────────────────────────────┐  │
│  │              Repository Layer                            │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ IncidentRepo    │  │ VectorRepo (RAG)             │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  └──────────────┬───────────────────────────────────────────┘  │
└─────────────────┼──────────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                    │
┌───────▼────────┐  ┌────────▼──────────┐
│   DynamoDB     │  │  In-Memory Mock   │
│   (AWS)        │  │  (Development)    │
│                │  │                   │
│  - Incidents   │  │  - Dictionary     │
│  - Embeddings  │  │  - No persistence│
│  - Metadata    │  │                   │
└────────────────┘  └───────────────────┘
```

### Component Flow

**Incident Creation Flow:**
```
User Input → Frontend Form → API Request → Backend Router
    ↓
Enrichment Service (Rule-based or RAG)
    ↓
Repository → DynamoDB/Mock Storage
    ↓
Response with Enriched Data → Frontend Display
```

**RAG Enhancement Flow (when enabled):**
```
New Incident → Generate Embedding → Vector Search
    ↓
Find Similar Incidents → LLM Classification
    ↓
Enhanced Severity/Category → Store Incident
```

## Technology Choices & Rationale

### Backend: FastAPI
- **Why**: Modern, fast, async-capable Python framework
- **Benefits**: Auto-generated API docs, type validation, excellent performance
- **Alternative Considered**: Flask (chose FastAPI for better async support and docs)

### Database: DynamoDB
- **Why**: AWS free tier requirement, NoSQL flexibility, serverless-friendly
- **Benefits**: Pay-per-request pricing, automatic scaling, no server management
- **Alternative Considered**: PostgreSQL (chose DynamoDB to meet AWS requirement)

### Frontend: React 18
- **Why**: Industry standard, component-based, large ecosystem
- **Benefits**: Reusable components, fast rendering, great developer experience
- **Alternative Considered**: Vue.js (chose React for wider adoption)

### Build Tool: Vite
- **Why**: Faster than Create React App, modern tooling
- **Benefits**: Instant HMR, fast builds, better DX
- **Alternative Considered**: Webpack (chose Vite for speed)

### RAG: OpenAI Embeddings + LLM
- **Why**: Best-in-class embeddings, reliable API, good documentation
- **Benefits**: High-quality semantic search, easy integration
- **Alternative Considered**: Local models (chose OpenAI for accuracy and ease)

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── models/          # Data models (Pydantic)
│   │   ├── repositories/    # Data access layer
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic (enrichment, RAG)
│   │   └── config.py        # Configuration
│   ├── scripts/             # Utility scripts
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   └── run_mock.py          # Run with mock storage
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── services/        # API client
    │   └── App.jsx          # Main app
    └── package.json         # Node dependencies
```

## Development Modes

### Backend Modes

1. **Mock Storage** (`python run_mock.py`):
   - No AWS account needed
   - In-memory storage
   - Perfect for development and testing
   - Data lost on restart

2. **DynamoDB** (`python run.py`):
   - Requires AWS credentials
   - Persistent storage
   - Production-ready

### Frontend Modes

1. **With Backend** (`npm run dev`):
   - Connects to backend API
   - Full functionality
   - Requires backend running

2. **Mock Mode** (`npm run dev:mock`):
   - No backend needed
   - Uses mock data
   - Perfect for UI development

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change port in run_mock.py or run.py
uvicorn app.main:app --reload --port 8001
```

**Import errors:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**RAG not working:**
- Check `USE_RAG=true` in `.env`
- Verify `OPENAI_API_KEY` is set
- Check server logs for errors

### Frontend Issues

**Cannot connect to backend:**
- Ensure backend is running on port 8000
- Check `VITE_API_URL` in `.env`
- Use `npm run dev:mock` for frontend-only development

**Port already in use:**
```bash
# Vite will automatically use next available port
# Or specify: npm run dev -- --port 5174
```

## Assumptions

### Technical Assumptions

1. **DynamoDB for Persistence**
   - Uses AWS DynamoDB to meet free tier requirement
   - PAY_PER_REQUEST billing mode (cost-effective for low volume)
   - No complex queries needed (simple key-value access pattern)

2. **No Authentication Required**
   - MVP assumes internal/trusted network usage
   - Can be added later with JWT/OAuth if needed
   - Rate limiting provides basic protection

3. **UTC Timestamps**
   - All timestamps stored in UTC
   - Frontend handles timezone conversion for display

4. **Enrichment Strategy**
   - Rule-based for 90% of cases (fast, deterministic)
   - RAG enhancement for ambiguous cases (optional)
   - Falls back gracefully if RAG unavailable

5. **Data Model**
   - Incidents are immutable after creation (except status updates)
   - Title/description updates supported but not primary use case
   - Status updates are the main update operation

6. **Scalability**
   - In-memory vector storage for MVP (scales to ~50K incidents)
   - Upgrade path to Pinecone/Weaviate documented
   - Pagination implemented for large datasets

### Business Assumptions

1. **Incident Lifecycle**
   - Simple workflow: Open → In Progress → Resolved → Closed
   - No complex state machine needed

2. **User Roles**
   - Single user type (no role-based access control)
   - All users can create, view, and update incidents

3. **ERP Modules**
   - Fixed set of modules (AP, AR, GL, Inventory, HR, Payroll)
   - Extensible via enum if needed

4. **Enrichment Accuracy**
   - Rule-based provides good accuracy for clear cases
   - RAG improves accuracy for ambiguous cases
   - Human review may be needed for critical incidents

## Future Improvements

### Short-Term Enhancements

1. **Enhanced Search**
   - Full-text search across incidents
   - Search by keywords, dates, or metadata
   - Advanced filtering combinations

2. **Better UI/UX**
   - Incident sorting (by date, severity, status)
   - Bulk operations (update multiple incidents)
   - Export functionality (CSV/PDF)

3. **RAG Improvements**
   - Upgrade to vector database (Pinecone) for scale
   - Better similarity thresholds
   - Learning from user corrections

### Medium-Term Enhancements

4. **Authentication & Authorization**
   - User login/registration
   - Role-based access control
   - Audit logging

5. **Notifications**
   - Email notifications for P1 incidents
   - Slack/Teams integration
   - Escalation workflows

6. **Analytics Dashboard**
   - Incident trends and metrics
   - Category distribution charts
   - Resolution time analytics

### Long-Term Enhancements

7. **Advanced AI Features**
   - Predictive severity assignment
   - Root cause analysis
   - Auto-resolution suggestions
   - Duplicate detection

8. **Integration**
   - Webhook support for external systems
   - API for third-party integrations
   - Import/export from other systems

9. **Performance**
   - Caching layer (Redis)
   - CDN for static assets
   - Database query optimization

## License

This project is for educational/demonstration purposes.
