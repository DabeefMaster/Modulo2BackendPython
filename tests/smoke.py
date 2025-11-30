import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

from fastapi.testclient import TestClient

# Permite ejecutar desde la raiz del repo
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def load_env(env_path: Path):
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if line.strip() and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


def log(step: str, status: int, body: Any):
    print(f"[{step}] status={status} body={body}")


def main():
    load_env(ROOT / ".env")

    from app.main import app  # import despues de cargar env

    client = TestClient(app)
    summary: List[Dict[str, Any]] = []
    username = "ProbadorSmoke"
    email = "tester_smoke@example.com"
    edad = 30
    canciones = ["ASHE", "Blinding Lights"]
    user_id = None

    try:
        # Crear usuario
        resp = client.post("/usuarios/", json={"nombre": username, "email": email, "edad": edad})
        log("crear_usuario", resp.status_code, resp.json())
        summary.append({"step": "crear_usuario", "status": resp.status_code})
        if resp.status_code != 200:
            return
        user_id = resp.json()["id"]

        # Añadir canciones
        for song in canciones:
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": song})
            log(f"add_cancion:{song}", resp.status_code, resp.json())
            summary.append({"step": f"add_cancion:{song}", "status": resp.status_code})

        # Like a la primera
        resp = client.post(f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[0]})
        log("like_primera", resp.status_code, resp.json())
        summary.append({"step": "like_primera", "status": resp.status_code})

        # Listar canciones y likes
        resp = client.get(f"/usuarios/{user_id}/canciones")
        log("get_canciones", resp.status_code, resp.json())
        summary.append({"step": "get_canciones", "status": resp.status_code, "count": len(resp.json())})

        resp = client.get(f"/usuarios/{user_id}/likes")
        log("get_likes", resp.status_code, resp.json())
        summary.append({"step": "get_likes", "status": resp.status_code, "count": len(resp.json())})

        # Eliminar like y canciones
        resp = client.request("DELETE", f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[0]})
        log("delete_like", resp.status_code, resp.json())
        summary.append({"step": "delete_like", "status": resp.status_code})

        for song in canciones:
            resp = client.request("DELETE", f"/usuarios/{user_id}/canciones", json={"nombre_cancion": song})
            log(f"delete_cancion:{song}", resp.status_code, resp.json())
            summary.append({"step": f"delete_cancion:{song}", "status": resp.status_code})

    except Exception as exc:
        summary.append({"step": "error", "status": "exception", "detail": str(exc)})
        raise
    finally:
        if user_id is not None:
            resp = client.delete(f"/usuarios/{user_id}")
            log("delete_usuario", resp.status_code, resp.json())
            summary.append({"step": "delete_usuario", "status": resp.status_code})

    print("=== RESUMEN ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
