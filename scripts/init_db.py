"""Initialize the application database.

Usage:
    python scripts/init_db.py            # create tables if missing
    python scripts/init_db.py --reset    # drop and recreate all tables
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the feedback database")
    parser.add_argument(
        "--reset", action="store_true", help="drop all tables before creating them"
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.reset:
            db.drop_all()
            print("Dropped existing tables.")
        db.create_all()
        print(f"Tables created at {app.config['SQLALCHEMY_DATABASE_URI']}")


if __name__ == "__main__":
    main()
