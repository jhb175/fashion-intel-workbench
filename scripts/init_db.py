#!/usr/bin/env python
"""Database initialization script.

Run migrations and create the default admin user.

Usage (from project root):
    python scripts/init_db.py
"""

import asyncio
import os
import sys
import subprocess

# ---------------------------------------------------------------------------
# Ensure the backend package is importable
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

import bcrypt
from sqlalchemy import select

from app.database import async_session_factory
from app.models.user import User


async def run_migrations() -> None:
    """Run Alembic migrations via subprocess."""
    print("[init_db] Running Alembic migrations …")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[init_db] Migration stderr:\n{result.stderr}")
        raise RuntimeError("Alembic migration failed")
    print("[init_db] Migrations applied successfully.")


async def create_default_admin() -> None:
    """Create the default admin user if it does not already exist."""
    print("[init_db] Checking for default admin user …")

    async with async_session_factory() as session:
        stmt = select(User).where(User.username == "admin")
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing is not None:
            print("[init_db] Admin user already exists — skipping.")
            return

        password = "admin123"  # default password for development
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        admin = User(
            username="admin",
            password_hash=password_hash,
            display_name="管理员",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"[init_db] Default admin user created (username=admin).")


async def main() -> None:
    await run_migrations()
    await create_default_admin()
    print("[init_db] Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
