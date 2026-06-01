import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.database import init_db
from app.seed.seed_data import run_seed

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Running seed...")
    run_seed()
    print("Done!")
