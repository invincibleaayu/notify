# Notification Management Service

A stateless, event-driven notification management service built with FastAPI and Firebase Cloud Messaging (FCM). This service follows Domain-Driven Design (DDD) principles and is designed for horizontal scaling and production deployment.

## Architecture Overview

### Core Principles
- **Stateless**: No internal database or persistent storage
- **Event-driven**: Uses Valkey (Redis-compatible) for async message flows
- **Type-based**: Template-driven notification system
- **Modular**: Clear domain boundaries and dependency injection
- **Scalable**: Ready for horizontal scaling and load balancing

### Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   REST API      │  │   Middleware    │  │   Schemas   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Use Cases     │  │   DTOs         │  │  Interfaces │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Entities      │  │ Value Objects   │  │   Services  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   FCM Gateway   │  │   Valkey Client │  │  Templates  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-platform Support**: Send notifications to web, Android, and iOS clients
- **Type-based Notifications**: Template-driven system for different notification types
- **Topic-based Messaging**: Broadcast to devices subscribed to topics
- **Event-driven Architecture**: Async processing using Valkey pub/sub
- **Production Ready**: Monitoring, metrics, and health checks
- **Stateless Design**: No internal persistence, perfect for horizontal scaling

## Quick Start

### Prerequisites
- Python 3.11+
- UV package manager
- Docker (for local Valkey)

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd notification-service
uv sync
```

2. **Environment setup**:
```bash
cp .env.example .env
# Edit .env with your FCM credentials
```

3. **Start Valkey**:
```bash
docker-compose up -d valkey
```

4. **Run the service**:
```bash
uv run python -m src.notification_service.main
```

### API Usage

#### Send Notification to Device Token
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "device_tokens": ["device_token_1", "device_token_2"],
    "notification_type": "alert",
    "title": "Important Alert",
    "body": "This is an important notification",
    "data": {"key": "value"}
  }'
```

#### Send Topic Notification
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/topic" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "news",
    "notification_type": "silent",
    "data": {"news_id": "123", "category": "technology"}
  }'
```

## Development

### Project Structure
```
notification-service/
├── src/notification_service/
│   ├── domain/          # Business logic and entities
│   ├── application/     # Use cases and DTOs
│   ├── infrastructure/  # External services (FCM, Valkey)
│   └── presentation/    # REST API and schemas
├── tests/               # Unit and integration tests
└── scripts/            # Development and deployment scripts
```

### Running Tests
```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# All tests with coverage
uv run pytest --cov=src
```

### Code Quality
```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Configuration

### Environment Variables
- `FCM_PROJECT_ID`: Firebase project ID
- `FCM_PRIVATE_KEY_ID`: Firebase private key ID
- `FCM_PRIVATE_KEY`: Firebase private key
- `FCM_CLIENT_EMAIL`: Firebase client email
- `VALKEY_URL`: Valkey connection URL
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)

### Notification Types
The service supports different notification types with predefined templates:

- **alert**: Standard notification with title and body
- **silent**: Data-only notification for background processing
- **custom**: Custom payload structure

## Deployment

### Docker
```bash
docker build -t notification-service .
docker run -p 8000:8000 notification-service
```

### Kubernetes
See `k8s/` directory for Kubernetes manifests.

## Monitoring

The service exposes metrics at `/metrics` endpoint and health checks at `/health`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
