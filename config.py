import os

# SQLite configuration for local development
sqlite_uri = "sqlite:///tool_set.db"

# Get environment variable (set by Render)
postgres_url = os.getenv("DATABASE_URL")

# Choose the appropriate database URL based on environment
if postgres_url:
    # Replace postgres:// with postgresql:// (SQLAlchemy requirement)
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = postgres_url
else:
    # Use SQLite for local development - easier than MySQL
    DATABASE_URL = sqlite_uri
