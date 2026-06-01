import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.database import get_db_context, engine
from sqlalchemy import inspect

def verify():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Available tables in DB:", tables)
    assert "plans" in tables, "Table 'plans' not found"
    assert "execution_steps" in tables, "Table 'execution_steps' not found"
    print("Verification SUCCESS: Tables 'plans' and 'execution_steps' successfully created!")

if __name__ == "__main__":
    verify()
