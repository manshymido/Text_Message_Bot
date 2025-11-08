# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- SQLite database for tracking processed messages and events
- Rate limiting to prevent abuse
- Input validation and sanitization
- Circuit breaker pattern for external services
- Dead letter queue for failed message processing
- Comprehensive metrics collection
- Health check system
- Docker and Docker Compose support
- Webhook support for production deployment
- Caching for duplicate detection
- Async operations for Google APIs
- Log rotation and structured logging
- New bot commands: `/stats`, `/health`, `/metrics`
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions

### Changed
- Improved error handling and resilience
- Enhanced logging with rotation
- Better duplicate detection with caching
- Optimized API calls with async operations

### Security
- Added rate limiting per user/chat
- Input validation to prevent injection attacks
- Sanitization of user input

## [1.0.0] - Initial Release

### Added
- Basic message extraction using pattern matching
- LLM-based extraction using Google Gemini
- Google Calendar integration
- Google Tasks integration
- Message filtering for school-related content
- Basic error handling and retry logic

