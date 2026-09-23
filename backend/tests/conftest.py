"""Global pytest fixtures and environment configuration."""

import os
from pathlib import Path
import dotenv

# Load backend/.env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    dotenv.load_dotenv(env_path)
