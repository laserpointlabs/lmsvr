# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-12-01

### Added
- Cloudflare Tunnel automated setup script (`cloudflare/setup_tunnel_cli.sh`)
- Configuration sync script (`cloudflare/update_config_from_env.sh`) to sync config.yml from .env
- DNS route configuration via CLI (`cloudflared tunnel route dns`)
- Complete Cloudflare tunnel testing procedures
- Comprehensive Cloudflare setup documentation (`docs/CLOUDFLARE_SETUP.md`)
- Multiple tunnels support documentation (running multiple Cloudflare tunnels simultaneously)
- **Enhanced CLI commands:**
  - `update-customer` - Update customer information (name, email, budget, active status)
  - `delete-customer` - Delete customer with confirmation prompt (--force to skip)
  - `refresh-key` - Revoke old API key and generate a new one
  - Enhanced `--help` support with examples and detailed command help

### Changed
- Database name standardized: `lmsvr.db` → `lmapi.db` across all files
- API key authentication: Changed from `APIKeyHeader` to `HTTPBearer` for proper Bearer token handling
- `log_usage()` parameter: Fixed `metadata_json` → `metadata` for consistency
- Setup script (`setup.sh`): Enhanced with Cloudflare tunnel setup integration and testing
- `setup_tunnel_cli.sh`: Now reads domain from `.env` file automatically
- All domain references now come from `.env` file (no hardcoded values)

### Fixed
- API key authentication issues (Bearer token extraction)
- Database path consistency between CLI and Docker container
- `log_usage()` parameter naming inconsistencies
- Cloudflare tunnel DNS route configuration
- Docker Compose YAML indentation issues

### Documentation
- Updated README.md with Cloudflare tunnel troubleshooting and testing
- Updated cloudflare/README.md with DNS setup options and testing
- Updated QUICKSTART.md with Cloudflare tunnel setup and testing examples
- Created comprehensive Cloudflare setup guide (`docs/CLOUDFLARE_SETUP.md`)
- Added curl command examples for all endpoints (localhost and Cloudflare tunnel)

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

