

## Estructura
- `app/`
  - `app/main.py`: FastAPI + CRUD de usuarios (crear, listar, obtener, actualizar, borrar) y alta/baja de playlists en Spotify. Usa SQLite para usuarios.
  - `app/spotify_routes.py`: integración con Spotify (token por refresh, crear/eliminar playlist, añadir/quitar pistas, likes y filtrado por artista) consultando siempre a Spotify para canciones/likes.
  - `app/models.py`: modelos Pydantic de entrada/salida.
  - `app/storage.py`: acceso a la base de datos SQLite
- `server.py`: entrypoint para `uvicorn server:app`.

## Endpoints clave
- Usuarios (`tag: Usuarios`):
  - `POST /usuarios/`: crea usuario y playlist en Spotify.
  - `GET /usuarios`: lista usuarios.
  - `GET /usuarios/{valor}`: por id o nombre.
  - `PUT /usuarios/{id}`: actualiza nombre/email/edad con unicidad.
  - `DELETE /usuarios/{valor}`: borra usuario y deja de seguir su playlist.
- Spotify (`tag: Spotify`):
  - `POST /usuarios/{id}/canciones`: body `{"nombre_cancion": "..."}`; busca en Spotify y añade a la playlist.
  - `DELETE /usuarios/{id}/canciones`: elimina de la playlist.
  - `POST /usuarios/{id}/likes` / `DELETE /usuarios/{id}/likes`: like/unlike usando tu biblioteca de Spotify.
  - `GET /usuarios/{id}/canciones`: lista canciones de la playlist (nombre, artistas, álbum, uri) consultando Spotify.
  - `GET /usuarios/{id}/likes`: lista likes (canciones guardadas en tu biblioteca que están en la playlist).
  - `GET /usuarios/{id}/canciones/por-artista?nombre_artista=...`: filtra canciones de la playlist por artista.

## Persistencia y datos
- SQLite (`data.sqlite`) guarda solo usuarios: `id`, `nombre`, `email`, `edad`, `playlist_id`.
- El resto de informacion sobre la playlists se realiza via consulta API Spotify

## Flujo con Spotify
1) Variables de entorno: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`, `SPOTIFY_USER_ID`, `DB_PATH` (opcional).
2) Se obtiene `access_token` con el refresh token.
3) Alta usuario: crea playlist (POST `/v1/users/{user_id}/playlists`) y guarda `playlist_id`.
4) Añadir/eliminar canciones: resuelve nombre→URI, luego POST/DELETE `/playlists/{id}/tracks`.
5) Likes: usa tu biblioteca (`/me/tracks`: contains/put/delete) filtrando por canciones de la playlist.
6) Consultas: playlist leída con paginación (`/playlists/{id}/tracks`); likes leídos de `/me/tracks/contains`.

## Pruebas
- `tests/smoke.py` Archivo que realiza llamadas a todos los endpoints del proyecto para revisar su funcionamiento

## Conclusiones y observaciones
- La integración depende mucho de los scopes de Spotify: para likes hacen falta `user-library-read` y `user-library-modify`, además de los de playlists. Sin ellos, los endpoints de likes devuelven 403 de Spotify.
- Al no persistir canciones/likes, siempre vemos el estado real de Spotify, lo que evita desalineaciones pero implica latencia y depender de la API en cada consulta.

Se podria plantear almacenar en base de datos likes y canciones y realizar chequeos rutinarios entre API Spotify y base de datos para asegurar persistencia.

Gracias a que todo está documentado en Swagger, probar la API es directo. 


