"""Compatibility entrypoint for deployments that start ``main:app``.

The canonical application lives in ``backend.main`` so local and hosted
launches share the same routes, database schema, and frontend assets.
"""
import os

from backend.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
