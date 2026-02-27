
# Message Subscription System

A multi-functional message subscription system that supports collecting messages from multiple sources, AI-powered analysis, and publishing to target platforms with various notification channels.

## Features

- **Message Collection**: Twitter/X, RSS, Webhook, Keyword monitoring
- **AI Analysis**: Auto-summary, classification, sentiment analysis using OpenAI
- **Notifications**: Telegram Bot, Email
- **Publishing**: Webhook, Telegram Channel, Email newsletter
- **Management UI**: Vue 3 + Element Plus dashboard

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Database**: SQLite (file-based, no external DB needed)
- **Frontend**: Vue 3 + Element Plus
- **Deployment**: Docker + Docker Compose / Railway

## Quick Start

### Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and configure your API keys:
```bash
# Required for basic functionality
SECRET_KEY=your-secret-key-here

# Optional: Twitter API
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_BEARER_TOKEN=

# Optional: Telegram Bot
TELEGRAM_BOT_TOKEN=

# Optional: Email SMTP
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=

# Optional: OpenAI for AI features
OPENAI_API_KEY=
```

### Running with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Subscriptions
- `GET /api/subscriptions` - List subscriptions
- `POST /api/subscriptions` - Create subscription
- `PUT /api/subscriptions/{id}` - Update subscription
- `DELETE /api/subscriptions/{id}` - Delete subscription

### Messages
- `GET /api/messages` - List messages (paginated)
- `GET /api/messages/{id}` - Get message detail
- `POST /api/messages/webhook` - Receive webhook messages
- `POST /api/messages/{id}/analyze` - Trigger AI analysis

### Publishing
- `POST /api/publish` - Publish multiple messages
- `POST /api/publish/{id}` - Publish single message
- `GET /api/publish/records` - List publish records

### Notifications
- `GET /api/notifications/settings` - Get notification settings
- `PUT /api/notifications/settings` - Update settings
- `POST /api/notifications/notify` - Send notification
- `POST /api/notifications/telegram/test` - Test Telegram
- `POST /api/notifications/email/test` - Test Email

## Deployment to Railway

1. Push code to GitHub
2. Connect Railway to your GitHub repo
3. Configure environment variables (SECRET_KEY is required)
4. Deploy!

No external database needed - SQLite file database is used for simplicity.

See [Railway documentation](https://docs.railway.app/) for more details.

## Project Structure

```
message-subscription-system/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   │   ├── collector/  # Message collection
│   │   │   ├── notifier/   # Notifications
│   │   │   ├── publisher/  # Publishing
│   │   │   └── ai/         # AI analysis
│   │   ├── tasks/        # Background tasks
│   │   └── utils/        # Utilities
│   ├── data/             # SQLite database files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # Vue components
│   │   ├── stores/       # Pinia stores
│   │   └── api/          # API client
│   └── package.json
├── docker-compose.yml
└── README.md
```

## License

MIT License
