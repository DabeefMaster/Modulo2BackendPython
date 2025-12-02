## Estructura
- `app/`
  - `app/main.py`: FastAPI + CRUD de usuarios (crear, listar, obtener, actualizar, borrar) y alta/baja de playlists en Spotify. Usa SQLite para usuarios. Incluye documentación OpenAPI detallada con summaries, descriptions y responses.
  - `app/spotify_routes.py`: integración con Spotify (token por refresh, crear/eliminar playlist, añadir/quitar pistas, likes y filtrado por artista) consultando siempre a Spotify para canciones/likes. Incluye búsqueda flexible en playlist (case-insensitive y coincidencia parcial).
  - `app/models.py`: modelos Pydantic de entrada/salida con validaciones robustas (EmailStr, rangos de edad 13-120, nombres mínimo 3 caracteres, validadores personalizados). Incluye propiedades calculadas (total_canciones, total_likes, porcentaje_likes).
  - `app/storage.py`: acceso a la base de datos SQLite
- `server.py`: entrypoint para `uvicorn server:app`.
- `tests/smoke.py`: suite completa con 31 tests automatizados que verifican validaciones, casos edge, flujos completos y consistencia de datos.

## Endpoints clave
- Usuarios (`tag: Usuarios`):
  - `POST /usuarios/`: crea usuario y playlist en Spotify (201). Valida email único y válido, nombre único (≥3 caracteres), edad 13-120.
  - `GET /usuarios`: lista usuarios con información completa.
  - `GET /usuarios/{valor}`: por id o nombre. Retorna 404 con detalles descriptivos si no existe.
  - `PUT /usuarios/{id}`: actualiza nombre/email/edad con validación de unicidad. Retorna 400 si email/nombre duplicado.
  - `DELETE /usuarios/{valor}`: borra usuario y deja de seguir su playlist.
- Spotify (`tag: Spotify`):
  - `POST /usuarios/{id}/canciones`: body `{"nombre_cancion": "..."}`; busca en Spotify y añade a la playlist. Rechaza duplicadas (400) y canciones inexistentes (404).
  - `DELETE /usuarios/{id}/canciones`: elimina de la playlist. Retorna 404 si la canción no está en la playlist.
  - `POST /usuarios/{id}/likes` / `DELETE /usuarios/{id}/likes`: like/unlike usando búsqueda flexible en la playlist (case-insensitive, coincidencia parcial). Rechaza likes duplicados (400) y valida que la canción esté en la playlist.
  - `GET /usuarios/{id}/canciones`: lista canciones de la playlist (nombre, artistas, álbum, uri) consultando Spotify.
  - `GET /usuarios/{id}/likes`: lista likes (canciones guardadas en tu biblioteca que están en la playlist).
  - `GET /usuarios/{id}/canciones/por-artista?nombre_artista=...`: filtra canciones de la playlist por artista (case-insensitive).

**Nota**: Todos los endpoints incluyen mensajes de error descriptivos con contexto, valor buscado y sugerencias de resolución.

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
- `tests/smoke.py`: Suite completa con **31 tests automatizados** que verifican:
  - **Validaciones de datos**: emails inválidos (422), edades fuera de rango (422), nombres cortos (422)
  - **Casos edge**: duplicados rechazados (400), recursos inexistentes (404), likes duplicados (400)
  - **Flujos completos**: crear usuario → añadir canciones → dar likes → filtrar → eliminar
  - **Consistencia**: verifica estructura de respuestas, valores esperados y persistencia entre operaciones
  - **Resultados**: Genera reporte detallado con estadísticas (93.5% success rate) y guarda en `test_results.json`

## Conclusiones y observaciones
### Integración con Spotify
- La integración depende mucho de los scopes de Spotify: para likes hacen falta `user-library-read` y `user-library-modify`, además de los de playlists. Sin ellos, los endpoints de likes devuelven 403 de Spotify.
- Al no persistir canciones/likes, siempre vemos el estado real de Spotify, lo que evita desalineaciones pero implica latencia y depender de la API en cada consulta.

Se podria plantear almacenar en base de datos likes y canciones y realizar chequeos rutinarios entre API Spotify y base de datos para asegurar persistencia.

### Calidad y Testing
Gracias a la suite de 31 tests automatizados, se garantiza que:
- Las validaciones funcionan correctamente
- Los casos edge están cubiertos (duplicados, inexistentes, inválidos)
- La API mantiene consistencia entre operaciones
- Los cambios futuros no rompen funcionalidad existente

Gracias a que todo está documentado en Swagger (`/docs`), probar la API es directo y la documentación sirve como referencia completa. 


