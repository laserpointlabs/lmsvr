# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- GPU support for Ollama with NVIDIA Container Toolkit integration
- Cloudflare Tunnel Docker container configuration
- GPU testing scripts (`scripts/test_gpu.sh` and `scripts/test_gpu.py`)
- Comprehensive CI/CD pipeline using Ollama's official `setup-ollama` GitHub Action
- Integration tests for Ollama connectivity (`tests/test_ollama_integration.py`)
- Model caching in CI for faster test runs
- Docker Compose profiles for selective service startup
- Credentials directory structure for Cloudflare tunnel

### Changed
- Updated Docker Compose configuration to use Docker Compose v2 syntax (removed obsolete `version` field)
- Cloudflare tunnel setup scripts now generate Docker-compatible configurations
- API Gateway port changed from 8000 to 8001 to avoid conflicts
- Cloudflare tunnel service URL changed from `localhost:8000` to `api_gateway:8000` (Docker network)
- Improved test fixtures to use unique identifiers to avoid conflicts
- Enhanced documentation with GPU setup, testing, and troubleshooting sections

### Fixed
- SQLAlchemy reserved attribute name conflict (`metadata` → `metadata_json`)
- Missing email-validator dependency for Pydantic EmailStr validation
- Import path issues in CLI tools
- Test cleanup and isolation improvements
- Docker Compose configuration validation

### Security
- Cloudflare credentials stored in separate directory with `.gitignore` protection
- Read-only volume mounts for credentials in Docker containers

## [Initial Release]

### Added
- API Gateway with FastAPI
- API key authentication and hashing
- Customer and API key management CLI
- Usage tracking and billing system
- Per-request and per-model pricing
- Budget limits per customer
- OpenAI and Claude API pass-through
- Cloudflare Tunnel setup scripts
- Health check endpoints
- Usage reports and exports
- Model discovery and metadata sync

