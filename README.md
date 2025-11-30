# Guía rápida para levantar el proyecto

Pasos para clonar y poner en marcha la API con tus credenciales (usas tu `.env` existente).

## 1. Prerrequisitos
- Python 3.10+
- Cuenta de Spotify con una app en el dashboard y refresh token con scopes:
  `user-library-read user-library-modify playlist-modify-private playlist-modify-public`.
- Variables de entorno en `.env` (ya las tienes):
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REFRESH_TOKEN`
  - `SPOTIFY_USER_ID`
  - Opcional: `DB_PATH` (ruta del SQLite, por defecto `data.sqlite` en la raíz).

## 2. Instalar dependencias
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Ejecutar la API
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs  
OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## 4. Probar endpoints
- Swagger (`/docs`) permite probar todo. Orden sugerido:
  1. `POST /usuarios/` (crea usuario y playlist en tu cuenta Spotify).
  2. `POST /usuarios/{id}/canciones` con `{"nombre_cancion": "..."}`.
  3. `POST /usuarios/{id}/likes` para dar like (opera sobre tu biblioteca de Spotify).
  4. `GET /usuarios/{id}/canciones` y `/likes` para ver estado.
  5. `GET /usuarios/{id}/canciones/por-artista?nombre_artista=...` para filtrar.
  6. Limpieza: `DELETE /usuarios/{id}/likes`, `DELETE /usuarios/{id}/canciones`, `DELETE /usuarios/{id}`.
- Prueba automatizada:
  ```bash
  python tests/smoke.py
  ```
  

## 5. Notas
- El SQLite guarda solo usuarios/playlist_id. Canciones y likes se consultan directamente en Spotify; no se almacenan localmente.

