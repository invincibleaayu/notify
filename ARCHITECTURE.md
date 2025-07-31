# Notification Service Architecture

## Overview

The Notification Service is a stateless, event-driven microservice built using Domain-Driven Design (DDD) principles. It provides a REST API for sending push notifications to web, Android, and iOS clients using Firebase Cloud Messaging (FCM) and integrates with Valkey (Redis-compatible) for event streaming.

## Architecture Principles

### 1. Domain-Driven Design (DDD)
- **Domain Layer**: Contains business logic, entities, and value objects
- **Application Layer**: Orchestrates use cases and coordinates domain objects
- **Infrastructure Layer**: Handles external services (FCM, Valkey)
- **Presentation Layer**: Exposes REST API endpoints

### 2. Stateless Design
- No internal database or persistent storage
- All state externalized to Valkey/Redis
- Perfect for horizontal scaling
- No session management required

### 3. Event-Driven Architecture
- Uses Valkey pub/sub for async message flows
- Decoupled components through events
- Scalable event processing
- Real-time status updates

### 4. Type-Based Notification System
- Template-driven notification types
- Predefined types: alert, silent, custom, promotional, transactional
- Extensible for custom notification types
- Validation based on type requirements

## Architecture Layers

### Domain Layer (`src/notification_service/domain/`)

#### Entities
- **Notification**: Core entity representing a notification message
  - Contains targeting information (device tokens or topic)
  - Manages notification state and lifecycle
  - Validates notification requirements
  - Converts to FCM message format

#### Value Objects
- **NotificationType**: Immutable notification type with validation
- **DeviceToken**: Validated device token with platform information
- **Topic**: FCM topic with name validation
- **DeviceTokenList**: Collection of device tokens with validation

#### Domain Services
- **NotificationDomainService**: Business logic for notification processing
  - Creates and validates notifications
  - Processes notification batches
  - Calculates notification costs
  - Determines retry strategies

### Application Layer (`src/notification_service/application/`)

#### Use Cases
- **SendNotification**: Sends notifications to device tokens
- **SendTopicNotification**: Sends notifications to topics
- **ProcessBatchNotifications**: Handles batch notification processing
- **SubscribeToTopic**: Manages topic subscriptions

#### DTOs (Data Transfer Objects)
- **Request DTOs**: Validate and structure API input
- **Response DTOs**: Format API output consistently
- **Error DTOs**: Standardized error responses

#### Interfaces
- **NotificationGateway**: Abstract interface for FCM integration
- **EventPublisher**: Abstract interface for Valkey integration
- **TemplateRepository**: Abstract interface for template management

### Infrastructure Layer (`src/notification_service/infrastructure/`)

#### FCM Integration
- **FCMClient**: Firebase Admin SDK wrapper
  - Sends notifications to devices and topics
  - Manages topic subscriptions
  - Handles FCM errors and retries
  - Supports multiple platforms (Android, iOS, Web)

#### Valkey Integration
- **ValkeyClient**: Redis-compatible client
  - Pub/sub for event streaming
  - Queues for async processing
  - Streams for ordered message processing
  - Key-value storage for status tracking

#### Monitoring
- **Metrics**: Prometheus metrics collection
- **Health Checks**: Service health monitoring
- **Logging**: Structured logging with structlog

### Presentation Layer (`src/notification_service/presentation/`)

#### REST API
- **Notification Routes**: Core notification endpoints
- **Health Routes**: Service health and status
- **Middleware**: Request logging, CORS, error handling

#### Schemas
- **Request Schemas**: Pydantic models for API input validation
- **Response Schemas**: Pydantic models for API output formatting

## Data Flow

### 1. Send Notification Flow
```
Client Request → API Validation → Domain Service → FCM Gateway → Event Publishing → Response
```

1. **API Validation**: Request DTOs validate input
2. **Domain Service**: Creates and validates notification entity
3. **FCM Gateway**: Sends notification via Firebase
4. **Event Publishing**: Publishes status to Valkey
5. **Response**: Returns structured response to client

### 2. Topic Notification Flow
```
Client Request → Topic Validation → FCM Topic Send → Event Publishing → Response
```

1. **Topic Validation**: Validates topic name and notification type
2. **FCM Topic Send**: Sends to all devices subscribed to topic
3. **Event Publishing**: Publishes topic event to Valkey
4. **Response**: Returns topic notification result

### 3. Batch Processing Flow
```
Client Request → Batch Validation → Parallel Processing → Event Publishing → Response
```

1. **Batch Validation**: Validates multiple notifications
2. **Parallel Processing**: Processes notifications concurrently
3. **Event Publishing**: Publishes batch completion event
4. **Response**: Returns batch processing results

## Event Streaming with Valkey

### Event Types
- **notification.sent**: Individual notification sent
- **notification.topic.sent**: Topic notification sent
- **notification.batch.sent**: Batch processing completed
- **topic.subscription**: Topic subscription event
- **notification.error**: Error events for monitoring

### Event Structure
```json
{
  "notification_id": "uuid",
  "type": "alert",
  "target_count": 5,
  "sent_count": 4,
  "failed_count": 1,
  "status": "partial",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Event Consumers
- **Monitoring**: Track notification metrics
- **Analytics**: Process notification data
- **Retry Logic**: Handle failed notifications
- **Audit Trail**: Log notification history

## Notification Types

### Alert Notifications
- **Purpose**: User-facing notifications with title and body
- **Requirements**: Title and body required
- **Priority**: High by default
- **Use Cases**: Important announcements, alerts

### Silent Notifications
- **Purpose**: Background data processing
- **Requirements**: Data payload only
- **Priority**: Normal
- **Use Cases**: Data synchronization, background updates

### Custom Notifications
- **Purpose**: Flexible notification structure
- **Requirements**: Custom validation rules
- **Priority**: Configurable
- **Use Cases**: Specialized notifications

### Promotional Notifications
- **Purpose**: Marketing and promotional content
- **Requirements**: Title, body, and optional data
- **Priority**: Normal
- **Use Cases**: Marketing campaigns, promotions

### Transactional Notifications
- **Purpose**: Transaction-related notifications
- **Requirements**: Title, body, and transaction data
- **Priority**: High
- **Use Cases**: Order confirmations, payment notifications

## Scaling Strategy

### Horizontal Scaling
- **Stateless Design**: No shared state between instances
- **Load Balancing**: Multiple service instances
- **Event-Driven**: Decoupled components scale independently
- **Valkey Clustering**: Redis cluster for high availability

### Performance Optimization
- **Async Processing**: Non-blocking I/O operations
- **Connection Pooling**: Reuse FCM and Valkey connections
- **Batch Processing**: Efficient bulk operations
- **Caching**: Cache frequently accessed data

### Monitoring and Observability
- **Metrics**: Prometheus metrics for monitoring
- **Logging**: Structured logging for debugging
- **Health Checks**: Service health monitoring
- **Tracing**: Request tracing for performance analysis

## Security Considerations

### API Security
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Prevent abuse
- **Authentication**: Trusted service calls only
- **CORS**: Configured for cross-origin requests

### FCM Security
- **Service Account**: Secure Firebase credentials
- **Token Validation**: Validate device tokens
- **Error Handling**: Secure error responses

### Valkey Security
- **Network Security**: Secure Valkey connections
- **Data Encryption**: Encrypt sensitive data
- **Access Control**: Restrict Valkey access

## Deployment Architecture

### Container Deployment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │  Notification   │    │     Valkey      │
│                 │    │    Service      │    │   (Redis)       │
│   (Nginx/ALB)   │◄──►│   (FastAPI)    │◄──►│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Firebase      │
                       │   Cloud         │
                       │   Messaging     │
                       └─────────────────┘
```

### Kubernetes Deployment
- **Deployment**: Multiple service replicas
- **Service**: Load balancer for internal communication
- **Ingress**: External traffic routing
- **ConfigMap**: Environment configuration
- **Secret**: Sensitive data management

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **AlertManager**: Alert management
- **Jaeger**: Distributed tracing

## Future Enhancements

### Message Brokers
- **Apache Kafka**: High-throughput event streaming
- **RabbitMQ**: Reliable message queuing
- **Apache Pulsar**: Unified messaging platform

### Advanced Features
- **Scheduled Notifications**: Time-based delivery
- **A/B Testing**: Notification variant testing
- **Analytics Dashboard**: Notification performance metrics
- **Template Management**: Dynamic notification templates
- **Multi-tenant Support**: Isolated tenant environments

### Integration Patterns
- **Webhook Support**: External system integration
- **GraphQL API**: Flexible data querying
- **gRPC Support**: High-performance RPC
- **Event Sourcing**: Complete event history

## Best Practices

### Code Organization
- **Clear Separation**: Domain, application, infrastructure layers
- **Dependency Injection**: Loose coupling between components
- **Error Handling**: Comprehensive error management
- **Testing**: Unit, integration, and contract tests

### Performance
- **Async Operations**: Non-blocking I/O
- **Connection Pooling**: Efficient resource usage
- **Caching**: Reduce external service calls
- **Batch Processing**: Optimize bulk operations

### Reliability
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Handle transient failures
- **Health Checks**: Monitor service health
- **Graceful Degradation**: Handle partial failures

### Security
- **Input Validation**: Prevent injection attacks
- **Rate Limiting**: Prevent abuse
- **Secure Communication**: TLS for all connections
- **Audit Logging**: Track all operations 