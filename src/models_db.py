import aiosqlite
import uuid
from datetime import datetime, timezone
from src.config import DB_PATH


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            workflow_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            model TEXT,
            lora TEXT,
            lora_strength REAL,
            prompt TEXT,
            seed INTEGER,
            steps INTEGER,
            guidance REAL,
            pulid_weight REAL,
            denoise_strength REAL,
            s3_urls TEXT,
            similarity_score REAL,
            error TEXT,
            execution_time_ms INTEGER,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    await db.commit()
    await db.close()


async def create_job(
    workflow_type: str,
    model: str = None,
    lora: str = None,
    lora_strength: float = None,
    prompt: str = None,
    seed: int = None,
    steps: int = None,
    guidance: float = None,
    pulid_weight: float = None,
    denoise_strength: float = None,
) -> str:
    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    await db.execute(
        """INSERT INTO jobs (id, workflow_type, status, model, lora, lora_strength,
           prompt, seed, steps, guidance, pulid_weight, denoise_strength, created_at)
           VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_id, workflow_type, model, lora, lora_strength, prompt, seed, steps,
         guidance, pulid_weight, denoise_strength, now),
    )
    await db.commit()
    await db.close()
    return job_id


async def update_job_status(job_id: str, status: str, **kwargs):
    db = await get_db()
    if status == "completed":
        kwargs["completed_at"] = datetime.now(timezone.utc).isoformat()
    set_clauses = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values())
    set_clauses = set_clauses + ", status = ?" if set_clauses else "status = ?"
    values.append(status)
    values.append(job_id)
    await db.execute(f"UPDATE jobs SET {set_clauses} WHERE id = ?", values)
    await db.commit()
    await db.close()


async def get_job(job_id: str) -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = await cursor.fetchone()
    await db.close()
    if row:
        return dict(row)
    return None


async def get_jobs(limit: int = 50) -> list:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]
