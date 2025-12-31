# Authentication & User Management API (In-progress)

A production-ready FastAPI application providing JWT-based authentication and user management with role-based access control.

## Technologies

### Core Framework
- **FastAPI 0.115.6** - Modern, high-performance web framework
- **Python 3.13.6** - Programming language
- **Pydantic 2.10.6** - Data validation using Python type annotations

### Database
- **PostgreSQL 17** - Primary database (production)
- **SQLAlchemy 2.0.36** - SQL toolkit and ORM
- **SQLite** - In-memory database (testing)

### Authentication & Security
- **python-jose 3.3.0** - JWT token handling
- **passlib 1.7.4** - Password hashing (bcrypt)
- **python-multipart 0.0.20** - Form data parsing

### Development & Testing
- **pytest 8.3.4** - Testing framework
- **pytest-asyncio 0.24.0** - Async test support
- **httpx 0.28.1** - HTTP client for testing
- **Docker & Docker Compose** - Containerization

### Additional Tools
- **uvicorn 0.34.0** - ASGI server
- **python-dotenv 1.0.1** - Environment variable management

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Configuration](#environment-configuration)
4. [Running the Application](#running-the-application)
5. [Database Management](#database-management)
6. [Testing](#testing)
7. [API Documentation](#api-documentation)
8. [Project Structure](#project-structure)

---

## Prerequisites

### Required Software

#### 1. Docker Desktop

Docker is required to run the PostgreSQL database and the application in containers.

**Installation Instructions:**

- **Windows**: 
  - Download Docker Desktop from [https://docs.docker.com/desktop/setup/install/windows-install/](https://docs.docker.com/desktop/setup/install/windows-install/)
  - Video Tutorial: [How to Install Docker on Windows](https://www.youtube.com/watch?v=DesRnZ-e1zI&list=PLsvFipOXuSp09Uo_1DmBe0oXmsu1vwquf&index=1)
  - Requires Windows 10 64-bit: Pro, Enterprise, or Education (Build 16299 or later)

- **macOS**: 
  - Download Docker Desktop from [https://docs.docker.com/desktop/setup/install/mac-install/](https://docs.docker.com/desktop/setup/install/mac-install/)
  - Video Tutorial: [How to Install Docker on macOS](https://www.youtube.com/watch?v=-EXlfSsP49A)
  - Requires macOS 10.15 or newer

- **Linux**: 
  - Follow the official guide at [https://docs.docker.com/desktop/setup/install/linux/](https://docs.docker.com/desktop/setup/install/linux/)
  - Video Tutorial: [How to Install Docker on Linux (Ubuntu)](https://www.youtube.com/watch?v=tjqd1Fxo6HQ)
  - Available for Ubuntu, Debian, Fedora, CentOS, and other distributions

**Verify Docker Installation:**

```bash
docker --version
docker-compose --version
```

You should see version numbers for both commands.

#### 2. Python 3.13.6

Download and install Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)

**Verify Python Installation:**

```bash
python --version
# or on some systems:
python3 --version
```

#### 3. Git (Optional but Recommended)

Download from [https://git-scm.com/](https://git-scm.com/)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd auth-user-api
```

Or download and extract the ZIP file from the repository.

### Step 2: Create Python Virtual Environment

A virtual environment isolates project dependencies from your system Python installation.

**On Windows:**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

**On macOS/Linux:**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

**Verify Activation:**

You should see `(.venv)` at the beginning of your command prompt.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all required packages including FastAPI, SQLAlchemy, pytest, and others.

---

## Environment Configuration

### Step 1: Create Environment File

The application uses environment variables for configuration. A template is provided in `.env.example`.

**Copy the template:**

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

### Step 2: Configure Environment Variables

Open `.env` in a text editor and configure the following variables:

```ini
# =========================
# Database Configuration
# =========================
# Database credentials (used by PostgreSQL container)
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION
POSTGRES_DB=auth_db

# Full database connection URL (used by API)
# Format: postgresql://username:password@host:port/database
# For Docker: use @db:5432
# For local development: use @localhost:5433
DATABASE_URL=postgresql://auth_user:CHANGE_ME_IN_PRODUCTION@db:5432/auth_db

# =========================
# Security & Authentication
# =========================
# JWT Secret Key - MUST be changed for production!
# Generate with: openssl rand -hex 32
# Windows PowerShell: [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
JWT_SECRET_KEY=GENERATE_A_SECRET_KEY_WITH_OPENSSL_RAND_HEX_32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# =========================
# Application Settings
# =========================
APP_NAME=auth-user-api
DEBUG=true

# =========================
# Password Hashing
# =========================
PASSWORD_HASH_SCHEME=bcrypt
```

**Important Notes:**

- **Database Password**: Replace `CHANGE_ME_IN_PRODUCTION` with a strong password
- **JWT Secret Key**: Generate a new secret key using the command for your operating system:
  
  **Linux/macOS:**
  ```bash
  openssl rand -hex 32
  ```
  
  **Windows (PowerShell):**
  ```powershell
  [System.BitConverter]::ToString((1..32 | ForEach-Object { Get-Random -Maximum 256 })) -replace '-',''
  ```
  
  **Alternative (Any OS with Python):**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- **Database Host**: Set to `db` for Docker (service name defined in `docker-compose.yml`)
- **Access Token Expiry**: Default is 15 minutes (recommended for security)
- **Debug Mode**: Set to `false` in production
- **Never commit the `.env` file** to version control (it's in `.gitignore`)

---

## Running the Application

### Using Docker (Recommended)

Docker Compose will start both the PostgreSQL database and the FastAPI application.

**Start the application:**

```bash
docker-compose up --build
```

The `--build` flag ensures the Docker image is rebuilt with any code changes.

**What happens:**

1. PostgreSQL database starts on port 7000 (mapped from container port 5432)
2. FastAPI application starts on port 8000
3. Database tables are automatically created on first run

**Access the application:**

- API: [http://localhost:8000](http://localhost:8000)
- Interactive API Documentation (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative API Documentation (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

**Stop the application:**

Press `Ctrl+C` in the terminal, then:

```bash
docker-compose down
```

**View logs:**

```bash
# View logs from all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs from specific service
docker-compose logs api
docker-compose logs db
```

---

## Database Management

### Connecting to PostgreSQL

You can connect to the PostgreSQL database using database administration tools.

#### Connection Details

When connecting from **outside Docker** (e.g., from pgAdmin on your host machine):

```
Host: localhost
Port: 7000
Database: auth_db (or whatever you set in POSTGRES_DB)
Username: your_db_user (from .env)
Password: your_secure_password (from .env)
```

**Important**: Note the port is **7000** on your host machine, not 5432. This is because we map the container's port 5432 to the host's port 7000 to avoid conflicts with any local PostgreSQL installation.

#### Using pgAdmin

**1. Download and Install pgAdmin:**

Download from [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)

**2. Add New Server:**

- Right-click "Servers" → "Register" → "Server"
- **General Tab:**
  - Name: Auth API Database (or any name you prefer)
- **Connection Tab:**
  - Host name/address: `localhost`
  - Port: `7000`
  - Maintenance database: `postgres`
  - Username: (from your `.env` file)
  - Password: (from your `.env` file)
  - Save password: Check this for convenience

**3. Connect:**

Click "Save" and pgAdmin will connect to your database.

**Alternative Database Tools:**

You can also use other PostgreSQL clients such as:
- **DBeaver** - Universal database tool ([https://dbeaver.io/download/](https://dbeaver.io/download/))
- **DataGrip** - JetBrains database IDE
- **psql** - PostgreSQL command-line client

All tools use the same connection details listed above (host: localhost, port: 7000).

#### Connecting from Inside Docker

If you need to connect from within the Docker network (e.g., from another container):

```
Host: db
Port: 5432
```

Note the different host (`db` instead of `localhost`) and port (`5432` instead of `7000`).

---

## Testing

The project includes comprehensive test coverage using pytest.

### Running Tests

Tests use an in-memory SQLite database for speed and isolation.

**Run all tests:**

```bash
# Activate virtual environment first
pytest
```

**Run with verbose output:**

```bash
pytest -v
```

**Run specific test file:**

```bash
pytest tests/test_auth.py
pytest tests/test_users.py
```

**Run specific test:**

```bash
pytest tests/test_auth.py::test_register_user_success
```

**Run with coverage report:**

```bash
pytest --cov=app tests/
```

**Run and show print statements:**

```bash
pytest -s
```

### Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_auth.py         # Authentication endpoint tests (19 tests)
└── test_users.py        # User management endpoint tests (24 tests)
```

The test suite includes:

- 19 authentication tests (registration, login, token refresh, logout)
- 24 user management tests (profile, admin operations, permissions)
- Total: 43 comprehensive tests

---

## API Documentation

### Interactive Documentation

Once the application is running, visit:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Interactive API explorer
  - Test endpoints directly from browser
  - View request/response schemas

- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - Alternative documentation format
  - Better for reading and sharing

### API Endpoints

#### Authentication

```
POST   /api/v1/auth/register     - Register new user
POST   /api/v1/auth/login        - Login and get tokens
POST   /api/v1/auth/refresh      - Refresh access token
POST   /api/v1/auth/logout       - Logout (revoke refresh token)
```

#### User Management

```
GET    /api/v1/users/me          - Get current user profile
PUT    /api/v1/users/me          - Update current user profile
GET    /api/v1/users             - List all users (admin only)
GET    /api/v1/users/{user_id}   - Get user by ID (admin only)
PATCH  /api/v1/users/{user_id}/active - Activate/deactivate user (admin only)
```

#### Health Check

```
GET    /health                   - Health check endpoint
```

### Authentication Flow

1. **Register**: Create a new user account
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"SecurePass123!","full_name":"John Doe"}'
   ```

2. **Login**: Get access and refresh tokens
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"SecurePass123!"}'
   ```

3. **Access Protected Endpoints**: Use the access token
   ```bash
   curl -X GET http://localhost:8000/api/v1/users/me \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

4. **Refresh Token**: Get a new access token when it expires
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
   ```

---

## Project Structure

```
auth-user-api/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── auth.py          # Authentication endpoints
│   │           └── users.py         # User management endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Application configuration
│   │   ├── logging.py               # Logging configuration
│   │   └── security.py              # JWT token utilities
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                  # SQLAlchemy base
│   │   └── session.py               # Database session management
│   ├── models/
│   │   ├── __init__.py              # Model registry
│   │   ├── refresh_token.py         # Refresh token model
│   │   └── user.py                  # User model
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── token_repo.py            # Token database operations
│   │   └── user_repo.py             # User database operations
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication schemas
│   │   └── user.py                  # User schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication business logic
│   │   └── user_service.py          # User management business logic
│   ├── utils/
│   │   ├── __init__.py
│   │   └── time.py                  # Time utilities
│   ├── __init__.py
│   ├── deps.py                      # Dependency injection
│   └── main.py                      # Application entry point
├── docker/
│   └── Dockerfile                   # Docker image definition
├── docs/
│   ├── api.md                       # API documentation
│   ├── architecture.md              # Architecture overview
│   └── diagrams.md                  # System diagrams
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Test configuration
│   ├── test_auth.py                 # Authentication tests
│   └── test_users.py                # User management tests
├── .env.example                     # Environment template
├── .gitattributes                   # Git attributes
├── .gitignore                       # Git ignore rules
├── docker-compose.yml               # Docker Compose configuration
├── README.md                        # This file
└── requirements.txt                 # Python dependencies
```

### Architecture

The application follows a layered architecture:

1. **Routes Layer** (`app/api/v1/routes/`)
   - HTTP endpoint definitions
   - Request/response handling
   - Input validation using Pydantic schemas

2. **Services Layer** (`app/services/`)
   - Business logic
   - Orchestrates repository operations
   - Handles complex workflows

3. **Repository Layer** (`app/repositories/`)
   - Database operations
   - Data access abstraction
   - Query construction

4. **Models Layer** (`app/models/`)
   - SQLAlchemy ORM models
   - Database schema definition

5. **Schemas Layer** (`app/schemas/`)
   - Pydantic models for request/response validation
   - Data transfer objects (DTOs)

---

## Alternative: Running Without Docker

If you prefer not to use Docker, you can run the application directly with Python.

**Requirements:**
- Install PostgreSQL locally on your machine
- Create a database manually
- Update `.env` to use localhost instead of Docker service names

**Steps:**

1. **Install and start PostgreSQL** on your local machine

2. **Update `.env` file:**
   ```ini
   # Change database URL to use localhost
   DATABASE_URL=postgresql://auth_user:CHANGE_ME_IN_PRODUCTION@localhost:5432/auth_db
   ```

3. **Activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The `--reload` flag enables auto-reload on code changes (development only).

**Note:** Docker is the recommended approach as it ensures consistent environments across different machines and simplifies database setup.

---

## Common Issues and Solutions

### Port Already in Use

**Problem**: Error message "port is already allocated" or "address already in use"

**Solution**: 
- Stop any other services using ports 8000 or 7000
- Or modify the ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Change host port
  ```

### Docker Permission Denied (Linux)

**Problem**: Permission denied when running docker commands

**Solution**: 
- Add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  ```
- Log out and log back in for changes to take effect

### Database Connection Failed

**Problem**: Cannot connect to database

**Solution**:
- Verify PostgreSQL container is running: `docker-compose ps`
- Check `.env` file has correct credentials
- Ensure using correct port (7000 from host, 5432 from Docker)
- Wait a few seconds after `docker-compose up` for database to initialize

### Import Errors

**Problem**: "ModuleNotFoundError" or "No module named 'app'"

**Solution**:
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify you're in the project root directory

### Tests Failing

**Problem**: Tests fail with database errors

**Solution**:
- Ensure you've created `app/utils/time.py` utility file
- Check that `token_repo.py` uses `now_utc()` instead of `datetime.now(timezone.utc)`
- Verify `conftest.py` in tests directory is properly configured

---

## Security Notes

### Production Deployment

Before deploying to production:

1. **Change Secret Keys**: Generate new JWT secret keys using the command for your operating system:
   
   **Linux/macOS:**
   ```bash
   openssl rand -hex 32
   ```
   
   **Windows (PowerShell):**
   ```powershell
   [System.BitConverter]::ToString((1..32 | ForEach-Object { Get-Random -Maximum 256 })) -replace '-',''
   ```
   
   **Alternative (Any OS with Python):**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Disable Debug Mode**: Set `DEBUG=false` in `.env`

3. **Update CORS Origins**: Restrict to your actual frontend domain(s)

4. **Use HTTPS**: Always use HTTPS in production

5. **Secure Database**: 
   - Use strong database passwords
   - Restrict database access by IP
   - Enable SSL/TLS for database connections

6. **Environment Variables**: Never commit `.env` file to version control

### Password Requirements

Current password requirements:
- Minimum 8 characters
- No maximum length (hashed before storage)
- Passwords are hashed using bcrypt

To modify requirements, update the validation in `app/schemas/user.py`.

---

## Support

For issues, questions, or contributions, please [open an issue](https://github.com/jesseKyomuhendo/auth-user-api/issues) on GitHub.