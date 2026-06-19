import os
from pathlib import Path

TEST_DB = Path("/tmp/finagent-ai-tests.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["MARKET_DATA_MODE"] = "demo"
os.environ["OPENAI_API_KEY"] = ""
