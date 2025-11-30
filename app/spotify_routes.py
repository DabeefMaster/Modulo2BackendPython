import os
import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from .models import CancionInput, TrackInfo, UsuarioResponse
from .storage import get_user_by_id

router = APIRouter(tags=["Spotify"])


def _require_spotify_env():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    user_id = os.getenv("SPOTIFY_USER_ID")

    missing = []
    if not client_id:
        missing.append("SPOTIFY_CLIENT_ID")
    if not client_secret:
        missing.append("SPOTIFY_CLIENT_SECRET")
    if not refresh_token:
        missing.append("SPOTIFY_REFRESH_TOKEN")
    if not user_id:
        missing.append("SPOTIFY_USER_ID")

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Faltan variables de entorno para Spotify: {', '.join(missing)}",
        )
    return client_id, client_secret, refresh_token, user_id


def _spotify_access_token():
    client_id, client_secret, refresh_token, _ = _require_spotify_env()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(client_id, client_secret),
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo obtener token de Spotify: {resp.text}",
        )
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Respuesta de Spotify sin token")
    return token


def crear_playlist_spotify(nombre_usuario: str) -> str:
    _, _, _, user_id = _require_spotify_env()
    token = _spotify_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": f"Playlist de {nombre_usuario}",
        "description": "Playlist generada automaticamente por la API",
        "public": False,
    }
    resp = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo crear playlist en Spotify: {resp.text}",
        )
    playlist_id = resp.json().get("id")
    if not playlist_id:
        raise HTTPException(
            status_code=502, detail="Spotify no devolvio playlist_id al crear playlist"
        )
    return playlist_id


def _anadir_cancion_spotify(playlist_id: str, track_uri: str):
    token = _spotify_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        json={"uris": [track_uri]},
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo anadir la cancion en Spotify: {resp.text}",
        )


def _eliminar_cancion_spotify(playlist_id: str, track_uri: str):
    token = _spotify_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"tracks": [{"uri": track_uri}]}
    resp = requests.request(
        "DELETE",
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo eliminar la cancion en Spotify: {resp.text}",
        )


def eliminar_playlist_spotify(playlist_id: str):
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.delete(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/followers",
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo eliminar la playlist en Spotify: {resp.text}",
        )


def _buscar_uri_por_nombre(nombre_cancion: str) -> str:
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": nombre_cancion, "type": "track", "limit": 1}
    resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params=params,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo buscar la cancion en Spotify: {resp.text}",
        )
    items = resp.json().get("tracks", {}).get("items", [])
    if not items:
        raise HTTPException(
            status_code=404,
            detail="No se encontro una cancion con ese nombre en Spotify",
        )
    return items[0].get("uri")


def _track_info_from_uri(uri: str) -> TrackInfo:
    if not uri.startswith("spotify:track:"):
        raise HTTPException(status_code=400, detail="URI de pista invalida")
    track_id = uri.split(":")[-1]
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo obtener informacion de la cancion: {resp.text}",
        )
    data = resp.json()
    return TrackInfo(
        nombre=data.get("name", ""),
        artistas=[a.get("name", "") for a in data.get("artists", [])],
        album=(data.get("album") or {}).get("name", ""),
        uri=uri,
        id=data.get("id", track_id),
    )


async def _get_playlist_tracks(playlist_id: str) -> list[TrackInfo]:
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    tracks: list[TrackInfo] = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    params = {"limit": 100}
    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if not resp.ok:
            raise HTTPException(
                status_code=502,
                detail=f"No se pudo obtener canciones de la playlist: {resp.text}",
            )
        data = resp.json()
        items = data.get("items", [])
        for it in items:
            track = it.get("track") or {}
            uri = track.get("uri")
            if not uri:
                continue
            tracks.append(
                TrackInfo(
                    nombre=track.get("name", ""),
                    artistas=[a.get("name", "") for a in track.get("artists", [])],
                    album=(track.get("album") or {}).get("name", ""),
                    uri=uri,
                    id=track.get("id", uri.split(":")[-1]),
                )
            )
        url = data.get("next")
        params = None  # next already has params
    return tracks


async def _tracks_saved_status(uris: list[str]) -> list[bool]:
    if not uris:
        return []
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    ids = [uri.split(":")[-1] for uri in uris]
    results: list[bool] = []
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        resp = requests.get(
            "https://api.spotify.com/v1/me/tracks/contains",
            headers=headers,
            params={"ids": ",".join(chunk)},
            timeout=10,
        )
        if not resp.ok:
            raise HTTPException(
                status_code=502,
                detail=f"No se pudo comprobar likes en Spotify: {resp.text}",
            )
        results.extend(resp.json())
    return results


async def _add_saved_tracks(uris: list[str]):
    if not uris:
        return
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ids = [uri.split(":")[-1] for uri in uris]
    resp = requests.put(
        "https://api.spotify.com/v1/me/tracks",
        headers=headers,
        json={"ids": ids},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502, detail=f"No se pudo dar like en Spotify: {resp.text}"
        )


async def _remove_saved_tracks(uris: list[str]):
    if not uris:
        return
    token = _spotify_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ids = [uri.split(":")[-1] for uri in uris]
    resp = requests.request(
        "DELETE",
        "https://api.spotify.com/v1/me/tracks",
        headers=headers,
        json={"ids": ids},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=502, detail=f"No se pudo quitar like en Spotify: {resp.text}"
        )


@router.post("/usuarios/{id}/canciones", response_model=UsuarioResponse)
async def anadir_cancion(id: int, cancion: CancionInput):
    """Anade una cancion a la playlist del usuario en Spotify"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not usuario.get("playlist_id"):
        raise HTTPException(status_code=400, detail="El usuario no tiene playlist asociada")
    track_uri = await run_in_threadpool(_buscar_uri_por_nombre, cancion.nombre_cancion)
    playlist_tracks = await _get_playlist_tracks(usuario["playlist_id"])
    if any(t.uri == track_uri for t in playlist_tracks):
        raise HTTPException(status_code=400, detail="La cancion ya esta en la playlist")

    await run_in_threadpool(_anadir_cancion_spotify, usuario["playlist_id"], track_uri)
    usuario = get_user_by_id(id)
    return usuario


@router.delete("/usuarios/{id}/canciones", response_model=UsuarioResponse)
async def eliminar_cancion(id: int, cancion: CancionInput):
    """Elimina una cancion de la playlist del usuario en Spotify"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    track_uri = await run_in_threadpool(_buscar_uri_por_nombre, cancion.nombre_cancion)
    playlist_tracks = await _get_playlist_tracks(usuario["playlist_id"])
    if not any(t.uri == track_uri for t in playlist_tracks):
        raise HTTPException(status_code=404, detail="La cancion no esta en la playlist")
    if not usuario.get("playlist_id"):
        raise HTTPException(status_code=400, detail="El usuario no tiene playlist asociada")

    await run_in_threadpool(_eliminar_cancion_spotify, usuario["playlist_id"], track_uri)
    usuario = get_user_by_id(id)
    return usuario


@router.post("/usuarios/{id}/likes", response_model=UsuarioResponse)
async def dar_like(id: int, cancion: CancionInput):
    """Marca una cancion de la playlist como like"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    track_uri = await run_in_threadpool(_buscar_uri_por_nombre, cancion.nombre_cancion)
    playlist_tracks = await _get_playlist_tracks(usuario["playlist_id"])
    if not any(t.uri == track_uri for t in playlist_tracks):
        raise HTTPException(status_code=404, detail="La cancion no esta en la playlist")
    saved = await _tracks_saved_status([track_uri])
    if saved[0]:
        raise HTTPException(status_code=400, detail="El like ya existe")
    await _add_saved_tracks([track_uri])
    usuario = get_user_by_id(id)
    return usuario


@router.delete("/usuarios/{id}/likes", response_model=UsuarioResponse)
async def eliminar_like(id: int, cancion: CancionInput):
    """Elimina un like de una cancion"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    track_uri = await run_in_threadpool(_buscar_uri_por_nombre, cancion.nombre_cancion)
    saved = await _tracks_saved_status([track_uri])
    if not saved[0]:
        raise HTTPException(status_code=404, detail="El like no existe")
    await _remove_saved_tracks([track_uri])
    usuario = get_user_by_id(id)
    return usuario


@router.get("/usuarios/{id}/canciones", response_model=list[TrackInfo])
async def obtener_canciones(id: int):
    """Devuelve las canciones en la playlist del usuario con nombre y artistas"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    tracks = await _get_playlist_tracks(usuario["playlist_id"])
    return tracks


@router.get("/usuarios/{id}/likes", response_model=list[TrackInfo])
async def obtener_likes(id: int):
    """Devuelve las canciones marcadas con like por el usuario con detalles"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    playlist_tracks = await _get_playlist_tracks(usuario["playlist_id"])
    if not playlist_tracks:
        return []
    uris = [t.uri for t in playlist_tracks]
    statuses = await _tracks_saved_status(uris)
    return [t for t, saved in zip(playlist_tracks, statuses) if saved]


@router.get("/usuarios/{id}/canciones/por-artista", response_model=list[TrackInfo])
async def canciones_por_artista(id: int, nombre_artista: str = Query(..., description="Nombre del artista a filtrar")):
    """Filtra canciones de la playlist de un usuario por nombre de artista (coincidencia parcial, sin distincion de mayusculas)."""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    tracks = await _get_playlist_tracks(usuario["playlist_id"])
    nombre_busqueda = nombre_artista.lower()
    filtradas = [
        t for t in tracks
        if any(nombre_busqueda in artista.lower() for artista in t.artistas)
    ]
    return filtradas
