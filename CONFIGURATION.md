# Configuration Guide

## Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and adjust as needed.

### Core Settings

- `API_HOST` - Backend host (default: 0.0.0.0)
  - Use `0.0.0.0` for Docker containers to bind to all interfaces
  - Use `localhost` or `127.0.0.1` for local development
  - Example: `API_HOST=0.0.0.0`

- `API_PORT` - Backend port (default: 5050)
  - The port where the FastAPI backend will listen
  - Common alternatives: 8000, 8080
  - Example: `API_PORT=5050`

- `DEBUG` - Debug mode (default: true)
  - Enables detailed error messages and development features
  - Set to `false` in production for security
  - Example: `DEBUG=true`

- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING)
  - Controls the verbosity of application logs
  - `DEBUG`: Most verbose, includes all messages
  - `INFO`: Standard operational messages
  - `WARNING`: Only warnings and errors
  - Example: `LOG_LEVEL=INFO`

### Game Settings

- `MAX_SCORE` - Winning score (default: 50)
  - First player to reach this score wins the game
  - Can be adjusted for shorter/longer games
  - Example: `MAX_SCORE=50`

- `MAX_ROUNDS` - Maximum rounds (default: 20)
  - Game ends after this many rounds if no winner
  - Player with highest score wins
  - Example: `MAX_ROUNDS=20`

- `BOT_ENABLED` - Enable AI bots (default: true)
  - Allows AI players to fill empty slots
  - Useful for testing or playing with fewer humans
  - Example: `BOT_ENABLED=true`

### Rate Limiting

- `RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
  - Protects against API abuse and DDoS attacks
  - Recommended to keep enabled in production
  - Example: `RATE_LIMIT_ENABLED=true`

- `RATE_LIMIT_GLOBAL_RPM` - Global requests per minute (default: 100)
  - Maximum requests per minute from a single IP
  - Applies to all endpoints unless overridden
  - Example: `RATE_LIMIT_GLOBAL_RPM=100`

### Endpoint-Specific Rate Limits

- `RATE_LIMIT_CREATE_ROOM_RPM` - Room creation limit (default: 10)
- `RATE_LIMIT_JOIN_ROOM_RPM` - Room joining limit (default: 20)
- `RATE_LIMIT_GAME_MOVE_RPM` - Game move limit (default: 60)
- `RATE_LIMIT_HEALTH_CHECK_RPM` - Health check limit (default: 200)

### Database Configuration

- `DATABASE_PATH` - SQLite database location (default: ./game_events.db)
  - Path to the event sourcing database
  - Use absolute paths in production
  - Example: `DATABASE_PATH=/data/game_events.db`

### Docker-Specific

- `RUNNING_IN_DOCKER` - Docker detection (auto-set)
  - Automatically set to `true` when running in Docker
  - Disables file logging when true (uses stdout instead)
  - Do not set manually

### Production Settings

- `CORS_ORIGINS` - Allowed CORS origins (default: ["*"])
  - List of allowed frontend URLs for CORS
  - Restrict in production for security
  - Example: `CORS_ORIGINS=["https://castellan.andynenth.dev"]`

- `SECRET_KEY` - Application secret key
  - Used for session security and tokens
  - Generate a secure random key for production
  - Example: `SECRET_KEY=your-secret-key-here`

## Complete Example

Here's a complete `.env` file for production:

```bash
# Core Settings
API_HOST=0.0.0.0
API_PORT=5050
DEBUG=false
LOG_LEVEL=INFO

# Game Settings
MAX_SCORE=50
MAX_ROUNDS=20
BOT_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GLOBAL_RPM=100
RATE_LIMIT_CREATE_ROOM_RPM=10
RATE_LIMIT_JOIN_ROOM_RPM=20
RATE_LIMIT_GAME_MOVE_RPM=60
RATE_LIMIT_HEALTH_CHECK_RPM=200

# Database
DATABASE_PATH=/data/game_events.db

# Security
CORS_ORIGINS=["https://castellan.andynenth.dev"]
SECRET_KEY=your-secure-random-key-here
```

## Configuration Best Practices

1. **Never commit `.env` files** - Use `.env.example` as a template
2. **Use strong secrets** - Generate random keys for production
3. **Restrict CORS** - Only allow your frontend domain in production
4. **Monitor rate limits** - Adjust based on actual usage patterns
5. **Secure database** - Use proper file permissions for SQLite database

For more details, see the complete configuration in [`.env.example`](.env.example).