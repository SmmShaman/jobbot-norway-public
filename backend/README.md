# 🤖 JobBot Norway - Backend API

FastAPI backend for automated job searching and application system in Norway.

## Features

- ✅ **Multi-user System** - Each user has isolated data with RLS
- ✅ **Settings Management** - Profile, resume, search URLs, preferences
- ✅ **Job Scraping** - Automatic scraping from NAV.no and FINN.no
- ✅ **AI Analysis** - Azure OpenAI GPT-4 relevance scoring
- ✅ **Cover Letter Generation** - AI-generated Norwegian cover letters
- ✅ **Dashboard Statistics** - Real-time job and application stats
- ✅ **Monitoring Logs** - Complete audit trail of all operations

---

## Tech Stack

- **Framework**: FastAPI 0.109
- **Database**: Supabase (PostgreSQL with RLS)
- **AI**: Azure OpenAI GPT-4
- **Scraping**: BeautifulSoup4, Requests
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` file and configure:

```bash
cp .env.example .env
nano .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name

### 3. Start Development Server

**Easy way:**
```bash
./start_dev.sh
```

**Manual way:**
```bash
uvicorn app.main:app --reload --port 8000
```

Server starts at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## API Endpoints

### Settings

- `GET /api/settings/profile/{user_id}` - Get user profile
- `PUT /api/settings/profile/{user_id}` - Update profile
- `GET /api/settings/settings/{user_id}` - Get settings
- `PUT /api/settings/settings/{user_id}` - Update settings
- `POST /api/settings/resume/{user_id}` - Upload resume
- `GET /api/settings/resume/{user_id}` - Get resume URL

### Jobs

- `POST /api/scan-jobs` - Trigger job scanning
- `POST /api/jobs` - Get all jobs (with filters)
- `POST /api/analyze-job` - Re-analyze single job
- `POST /api/approve-job` - Approve job for application
- `GET /api/dashboard-stats/{user_id}` - Get statistics

### System

- `GET /health` - Health check
- `GET /` - API info
- `GET /docs` - Interactive API documentation

See `API_TESTING.md` for detailed examples.

---

## Architecture

### Service Layer

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Environment configuration
│   ├── routers/             # API route handlers
│   │   ├── settings.py      # Settings endpoints
│   │   ├── jobs.py          # Job endpoints
│   │   ├── applications.py  # Application endpoints
│   │   └── monitoring.py    # Monitoring endpoints
│   └── services/            # Business logic
│       ├── database.py      # Supabase operations
│       ├── ai_service.py    # Azure OpenAI integration
│       └── scraper_service.py # Job scraping
```

### Data Flow

```
Frontend → API Router → Service Layer → Supabase
                  ↓
            AI Service → Azure OpenAI
                  ↓
         Scraper Service → NAV/FINN
```

---

## Job Scanning Pipeline

1. **Fetch Search Results** - Scraper fetches job listings from NAV/FINN
2. **Extract Job Links** - Parse HTML to get individual job URLs
3. **Fetch Job Details** - Get full description for each job
4. **AI Analysis** - GPT-4 analyzes relevance based on user profile
5. **Save to Database** - Store jobs with relevance scores
6. **Notify User** - Update dashboard statistics

---

## AI Analysis

### Relevance Scoring

Jobs are analyzed using GPT-4 with user's:
- Skills and experience
- Location preferences
- Career goals

Output:
- **Relevance Score**: 0-100
- **Match Reasons**: Why it's a good fit
- **Concerns**: Potential issues
- **Recommendation**: APPLY, REVIEW, or SKIP

### Cover Letter Generation

Generated in Norwegian (or English) based on:
- Job description
- Company information
- User profile and experience

---

## Database Schema

### Tables

- **profiles** - User profiles (extends Supabase auth.users)
- **user_settings** - All user preferences and configurations
- **jobs** - Discovered jobs with AI analysis
- **cover_letters** - Generated cover letters
- **applications** - Submitted applications tracking
- **monitoring_logs** - System activity logs

All tables have Row Level Security (RLS) policies.

---

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Adding New Endpoints

1. Create route in `app/routers/`
2. Add business logic in `app/services/`
3. Update `app/main.py` to include router
4. Add tests
5. Update API documentation

---

## Deployment

### Railway (Recommended)

Full guide: See `RAILWAY_DEPLOYMENT.md`

**Quick:**
1. Push code to GitHub
2. Connect Railway to repo
3. Set root directory to `backend`
4. Add environment variables
5. Deploy!

### Docker

```bash
# Build image
docker build -t jobbot-backend .

# Run container
docker run -p 8000:8000 --env-file .env jobbot-backend
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Start with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Environment Variables

### Required

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Security
ENCRYPTION_KEY=your-32-char-encryption-key
JWT_SECRET=your-jwt-secret-key
```

### Optional

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-frontend.netlify.app

# Telegram (for notifications)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_DEFAULT_CHAT_ID=your-chat-id

# Skyvern (for future automation)
SKYVERN_API_URL=http://localhost:8000
SKYVERN_API_KEY=your-key
```

---

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

### Logs

All operations are logged to:
- Console (development)
- Supabase `monitoring_logs` table (production)

Monitor via:
```bash
# Watch logs in real-time
tail -f logs/app.log

# Or check Supabase dashboard
```

### Metrics

Track in Railway dashboard:
- Request rate
- Response time
- Error rate
- Memory usage
- CPU usage

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**2. Supabase connection fails**
```bash
# Check .env variables
# Verify Supabase project is active
# Check network connectivity
```

**3. Azure OpenAI errors**
```bash
# Verify API key is correct
# Check deployment name
# Ensure quota is not exceeded
```

**4. CORS errors**
```bash
# Add frontend domain to CORS_ORIGINS
# Restart backend
```

---

## Performance

### Optimization Tips

1. **Use connection pooling** for Supabase
2. **Cache AI responses** for repeated queries
3. **Rate limit scraping** to avoid blocks
4. **Use background tasks** for long-running operations
5. **Enable Redis caching** (optional)

### Scaling

- **Vertical**: Increase Railway instance size
- **Horizontal**: Deploy multiple instances with load balancer
- **Database**: Supabase handles scaling automatically
- **AI**: Azure OpenAI auto-scales

---

## Security

### Best Practices

- ✅ All API requests validated with Pydantic
- ✅ Supabase RLS enforces data isolation
- ✅ Secrets stored in environment variables
- ✅ HTTPS only in production
- ✅ Rate limiting enabled
- ✅ Input sanitization for SQL injection prevention

### Encryption

- NAV passwords encrypted before storage
- Resume files stored securely in Supabase Storage
- JWTs for authentication

---

## Contributing

### Setup Development Environment

```bash
# Clone repo
git clone https://github.com/SmmShaman/jobbot-norway-public
cd jobbot-norway-public/backend

# Create branch
git checkout -b feature/your-feature

# Make changes
# Test changes
# Commit and push
```

### Code Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for public methods
- Add tests for new features
- Update API documentation

---

## Support

### Documentation

- API Testing: `API_TESTING.md`
- Deployment: `RAILWAY_DEPLOYMENT.md`
- Architecture: `../ARCHITECTURE.md`

### Issues

Report bugs or request features:
https://github.com/SmmShaman/jobbot-norway-public/issues

---

## License

MIT License - See LICENSE file for details

---

## Changelog

### v1.0.0 (Current)

- ✅ Complete Settings API
- ✅ Job scraping from NAV and FINN
- ✅ AI relevance analysis with GPT-4
- ✅ Dashboard statistics
- ✅ Resume upload to Supabase Storage
- ✅ Monitoring and logging

### Future Versions

- 🔮 Skyvern integration for automated applications
- 🔮 Telegram notification system
- 🔮 Cover letter generation in UI
- 🔮 NAV automatic reporting
- 🔮 Job recommendation system
- 🔮 Multi-language support

---

**Built with ❤️ for job seekers in Norway**
# Cloud Run deployment
# Cloud Run ready
