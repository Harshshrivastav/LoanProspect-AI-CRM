"""
Convenience entry point — run from the backend/ directory:

    python run.py                   # production-style
    python run.py --reload          # dev mode (auto-restart on file change)
"""

import sys

import uvicorn

if __name__ == "__main__":
    reload = "--reload" in sys.argv
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=reload,
    )
