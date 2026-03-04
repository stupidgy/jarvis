import sqlite3
from contextlib import contextmanager
from datetime import datetime


class AppStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS Task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    estimate_min INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tags TEXT DEFAULT '',
                    parent_task_id INTEGER,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_text TEXT NOT NULL,
                    horizon_days INTEGER NOT NULL,
                    strategy TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS PlanItem (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER NOT NULL,
                    task_id INTEGER,
                    milestone TEXT,
                    confidence REAL,
                    FOREIGN KEY(plan_id) REFERENCES Plan(id)
                );

                CREATE TABLE IF NOT EXISTS Review (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    done_summary TEXT NOT NULL,
                    blockers TEXT NOT NULL,
                    tomorrow_focus TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ReminderRule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    time TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    quiet_hours TEXT DEFAULT ''
                );
                """
            )

    def seed_defaults(self):
        with self.connect() as conn:
            existing = conn.execute("SELECT COUNT(*) AS c FROM ReminderRule").fetchone()["c"]
            if existing == 0:
                conn.executemany(
                    "INSERT INTO ReminderRule(type, time, enabled, quiet_hours) VALUES (?, ?, ?, ?)",
                    [
                        ("morning_focus", "09:00", 1, "22:00-08:00"),
                        ("afternoon_check", "15:00", 1, "22:00-08:00"),
                        ("night_review", "21:30", 1, "22:00-08:00"),
                    ],
                )

    def create_task(self, date, title, priority, estimate_min, status, tags="", parent_task_id=None):
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO Task(title, date, priority, estimate_min, status, tags, parent_task_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, date, priority, estimate_min, status, tags, parent_task_id, datetime.utcnow().isoformat()),
            )
            return cur.lastrowid

    def list_tasks(self, start_date, end_date):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM Task WHERE date BETWEEN ? AND ? ORDER BY date, priority DESC",
                (start_date, end_date),
            ).fetchall()
            return [dict(r) for r in rows]

    def save_review(self, day, done_summary, blockers, tomorrow_focus):
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO Review(date, done_summary, blockers, tomorrow_focus) VALUES (?, ?, ?, ?)",
                (day, done_summary, blockers, tomorrow_focus),
            )
            return cur.lastrowid

    def create_plan(self, goal_text, horizon_days, strategy):
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO Plan(goal_text, horizon_days, strategy, created_at) VALUES (?, ?, ?, ?)",
                (goal_text, horizon_days, strategy, datetime.utcnow().isoformat()),
            )
            return cur.lastrowid

    def create_plan_item(self, plan_id, task_id, milestone, confidence):
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO PlanItem(plan_id, task_id, milestone, confidence) VALUES (?, ?, ?, ?)",
                (plan_id, task_id, milestone, confidence),
            )
            return cur.lastrowid


    def update_task_status(self, task_id, status):
        with self.connect() as conn:
            conn.execute("UPDATE Task SET status = ? WHERE id = ?", (status, task_id))

    def move_task(self, task_id, new_date):
        with self.connect() as conn:
            conn.execute("UPDATE Task SET date = ? WHERE id = ?", (new_date, task_id))

    def task_summary(self, start_date, end_date):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) AS todo,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done,
                    COALESCE(SUM(estimate_min), 0) AS total_estimate_min
                FROM Task
                WHERE date BETWEEN ? AND ?
                """,
                (start_date, end_date),
            ).fetchone()
            return {
                "todo": rows["todo"] or 0,
                "done": rows["done"] or 0,
                "total_estimate_min": rows["total_estimate_min"] or 0,
            }
