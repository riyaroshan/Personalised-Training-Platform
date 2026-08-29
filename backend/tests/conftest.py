import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.training.db")
os.environ["OPENAI_API_KEY"] = ""

from app.db import init_db

init_db()
