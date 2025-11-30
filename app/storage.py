import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(os.getenv("DB_PATH", "data.sqlite")).resolve()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                edad INTEGER NOT NULL,
                playlist_id TEXT
            );
            """
        )
        conn.commit()


def _row_to_user(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "email": row["email"],
        "edad": row["edad"],
        "playlist_id": row["playlist_id"],
    }


def list_users() -> List[Dict[str, Any]]:
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT id, nombre, email, edad, playlist_id FROM users")
        users = [_row_to_user(r) for r in cur.fetchall()]
    for u in users:
        u["listaCanciones"] = []
        u["likes"] = []
    return users


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT id, nombre, email, edad, playlist_id FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
    if not row:
        return None
    user = _row_to_user(row)
    user["listaCanciones"] = []
    user["likes"] = []
    return user


def get_user_by_name(name: str) -> Optional[Dict[str, Any]]:
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT id, nombre, email, edad, playlist_id FROM users WHERE nombre = ?", (name,))
        row = cur.fetchone()
    if not row:
        return None
    user = _row_to_user(row)
    user["listaCanciones"] = []
    user["likes"] = []
    return user


def create_user(nombre: str, email: str, edad: int, playlist_id: Optional[str]) -> Dict[str, Any]:
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT INTO users (nombre, email, edad, playlist_id) VALUES (?, ?, ?, ?)",
            (nombre, email, edad, playlist_id),
        )
        conn.commit()
        user_id = cur.lastrowid
    return get_user_by_id(user_id)


def update_user(user_id: int, nombre: Optional[str], email: Optional[str], edad: Optional[int]) -> Dict[str, Any]:
    sets = []
    params: List[Any] = []
    if nombre is not None:
        sets.append("nombre = ?")
        params.append(nombre)
    if email is not None:
        sets.append("email = ?")
        params.append(email)
    if edad is not None:
        sets.append("edad = ?")
        params.append(edad)
    if not sets:
        return get_user_by_id(user_id)
    params.append(user_id)
    query = f"UPDATE users SET {', '.join(sets)} WHERE id = ?"
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute(query, tuple(params))
        conn.commit()
    return get_user_by_id(user_id)


def delete_user(user_id: int):
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


init_db()
