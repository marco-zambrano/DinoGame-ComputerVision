import sqlite3
import time
from pathlib import Path

import config


class Leaderboard:
    def __init__(self):
        self._db_path = Path(config.LEADERBOARD_DB)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS scores ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  name TEXT NOT NULL,"
            "  score INTEGER NOT NULL,"
            "  date TEXT NOT NULL"
            ")"
        )
        self._deduplicate()
        self._conn.commit()

    def add_score(self, name, score):
        name = name.strip() or "JUGADOR"
        best = self.get_player_best(name)
        if score <= best:
            return
        self._conn.execute("DELETE FROM scores WHERE name = ?", (name,))
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        self._conn.execute(
            "INSERT INTO scores (name, score, date) VALUES (?, ?, ?)",
            (name, score, date),
        )
        self._conn.commit()

    def get_top(self, limit=None):
        if limit is None:
            limit = config.LEADERBOARD_DISPLAY_COUNT
        cur = self._conn.execute(
            "SELECT name, score, date FROM scores ORDER BY score DESC, date ASC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()

    def get_player_best(self, name):
        cur = self._conn.execute(
            "SELECT MAX(score) FROM scores WHERE name = ?", (name,)
        )
        row = cur.fetchone()
        return row[0] if row[0] is not None else 0

    def get_high_score(self):
        cur = self._conn.execute("SELECT MAX(score) FROM scores")
        row = cur.fetchone()
        return row[0] if row[0] is not None else 0

    def close(self):
        self._conn.close()

    def _deduplicate(self):
        self._conn.execute(
            "DELETE FROM scores WHERE id NOT IN ("
            "  SELECT id FROM ("
            "    SELECT id, ROW_NUMBER() OVER ("
            "      PARTITION BY name ORDER BY score DESC, id ASC"
            "    ) AS rn FROM scores"
            "  ) WHERE rn = 1"
            ")"
        )
