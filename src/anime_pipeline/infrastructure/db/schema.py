import sqlite3
from pathlib import Path


def initialize_database(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                ratio TEXT NOT NULL,
                target_duration INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_no TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                script_text TEXT NOT NULL,
                target_duration INTEGER NOT NULL,
                pipeline_status TEXT NOT NULL,
                review_status TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS media_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_no TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
