import sqlite3
from pathlib import Path

from anime_pipeline.domain.models import MediaAssetRecord, ProjectRecord, ShotRecord


class ProjectRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def insert(self, record: ProjectRecord) -> None:
        connection = sqlite3.connect(self._db_path)
        try:
            connection.execute(
                "INSERT INTO projects (name, slug, ratio, target_duration) VALUES (?, ?, ?, ?)",
                (record.name, record.slug, record.ratio, record.target_duration),
            )
            connection.commit()
        finally:
            connection.close()

    def list_all(self) -> list[ProjectRecord]:
        connection = sqlite3.connect(self._db_path)
        try:
            rows = connection.execute(
                "SELECT name, slug, ratio, target_duration FROM projects ORDER BY id"
            ).fetchall()
        finally:
            connection.close()
        return [ProjectRecord(*row) for row in rows]


class ShotRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def insert(self, record: ShotRecord) -> None:
        connection = sqlite3.connect(self._db_path)
        try:
            connection.execute(
                """
                INSERT INTO shots (
                    shot_no, title, prompt_text, script_text,
                    target_duration, pipeline_status, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.shot_no,
                    record.title,
                    record.prompt_text,
                    record.script_text,
                    record.target_duration,
                    record.pipeline_status,
                    record.review_status,
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Shot '{record.shot_no}' already exists.") from exc
        finally:
            connection.close()

    def list_all(self) -> list[ShotRecord]:
        connection = sqlite3.connect(self._db_path)
        try:
            rows = connection.execute(
                """
                SELECT shot_no, title, prompt_text, script_text,
                       target_duration, pipeline_status, review_status
                FROM shots
                ORDER BY id
                """
            ).fetchall()
        finally:
            connection.close()
        return [ShotRecord(*row) for row in rows]

    def exists(self, shot_no: str) -> bool:
        connection = sqlite3.connect(self._db_path)
        try:
            row = connection.execute(
                "SELECT 1 FROM shots WHERE shot_no = ? LIMIT 1",
                (shot_no,),
            ).fetchone()
        finally:
            connection.close()
        return row is not None

    def get(self, shot_no: str) -> ShotRecord:
        connection = sqlite3.connect(self._db_path)
        try:
            row = connection.execute(
                """
                SELECT shot_no, title, prompt_text, script_text,
                       target_duration, pipeline_status, review_status
                FROM shots
                WHERE shot_no = ?
                LIMIT 1
                """,
                (shot_no,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise ValueError(f"Shot '{shot_no}' does not exist.")
        return ShotRecord(*row)

    def update_pipeline_status(self, shot_no: str, pipeline_status: str) -> None:
        connection = sqlite3.connect(self._db_path)
        try:
            cursor = connection.execute(
                "UPDATE shots SET pipeline_status = ? WHERE shot_no = ?",
                (pipeline_status, shot_no),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Shot '{shot_no}' does not exist.")
            connection.commit()
        finally:
            connection.close()

    def list_by_pipeline_status(self, pipeline_status: str) -> list[ShotRecord]:
        connection = sqlite3.connect(self._db_path)
        try:
            rows = connection.execute(
                """
                SELECT shot_no, title, prompt_text, script_text,
                       target_duration, pipeline_status, review_status
                FROM shots
                WHERE pipeline_status = ?
                ORDER BY id
                """,
                (pipeline_status,),
            ).fetchall()
        finally:
            connection.close()
        return [ShotRecord(*row) for row in rows]


class MediaAssetRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def insert(self, shot_no: str, record: MediaAssetRecord) -> None:
        connection = sqlite3.connect(self._db_path)
        try:
            connection.execute(
                "INSERT INTO media_assets (shot_no, asset_type, file_path) VALUES (?, ?, ?)",
                (shot_no, record.asset_type, str(record.file_path)),
            )
            connection.commit()
        finally:
            connection.close()
