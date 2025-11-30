from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from .models import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from .storage import (
    list_users,
    get_user_by_id,
    get_user_by_name,
    create_user,
    update_user,
    delete_user,
)
import app.spotify_routes as spotify_routes
from app.spotify_routes import crear_playlist_spotify, eliminar_playlist_spotify

app = FastAPI()


@app.get("/", tags=["Info"])
def root():
    """Endpoint raiz"""
    return {
        "message": "API de Usuarios con Spotify",
        "endpoints": {
            "GET /": "Informacion de la API",
            "GET /usuarios": "Listar todos los usuarios",
            "POST /usuarios/": "Crear un nuevo usuario",
            "GET /usuarios/{valor}": "Obtener usuario por ID o nombre",
            "PUT /usuarios/{id}": "Modificar un usuario",
            "DELETE /usuarios/{valor}": "Eliminar un usuario",
            "POST /usuarios/{id}/canciones": "Anadir una cancion a la playlist del usuario",
            "DELETE /usuarios/{id}/canciones": "Eliminar una cancion de la playlist del usuario",
            "GET /usuarios/{id}/canciones": "Listar canciones de la playlist del usuario",
            "GET /usuarios/{id}/canciones/por-artista": "Listar canciones de la playlist filtradas por artista",
            "POST /usuarios/{id}/likes": "Dar like a una cancion de la playlist",
            "DELETE /usuarios/{id}/likes": "Quitar like de una cancion",
            "GET /usuarios/{id}/likes": "Listar canciones con like",
            "GET /docs": "Documentacion Swagger",
        },
    }


@app.get("/usuarios", response_model=list[UsuarioResponse], tags=["Usuarios"])
def listar_usuarios():
    """Lista todos los usuarios"""
    return list_users()


@app.get("/usuarios/{valor}", response_model=UsuarioResponse, tags=["Usuarios"])
def obtener_usuario(valor: str):
    """Obtiene un usuario por ID o nombre"""
    usuario = None
    if valor.isdigit():
        usuario = get_user_by_id(int(valor))
    if not usuario:
        usuario = get_user_by_name(valor)
    if usuario:
        return usuario
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@app.put("/usuarios/{id}", response_model=UsuarioResponse, tags=["Usuarios"])
def modificar_usuario(id: int, usuario_update: UsuarioUpdate):
    """Modifica un usuario existente"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario_update.email is not None:
        existente = get_user_by_name(usuario.get("nombre"))
        # verificar email duplicado
        users = list_users()
        if any(u["email"] == usuario_update.email and u["id"] != id for u in users):
            raise HTTPException(status_code=400, detail="El email ya esta registrado")
    if usuario_update.nombre is not None:
        users = list_users()
        if any(u["nombre"] == usuario_update.nombre and u["id"] != id for u in users):
            raise HTTPException(status_code=400, detail="El nombre ya esta registrado")

    updated = update_user(id, usuario_update.nombre, usuario_update.email, usuario_update.edad)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated


app.include_router(spotify_routes.router)


@app.post("/usuarios/", response_model=UsuarioResponse, tags=["Usuarios"])
async def crear_usuario(usuario: UsuarioCreate):
    """Crea un nuevo usuario"""
    users = list_users()
    if any(u["email"] == usuario.email for u in users):
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    if any(u["nombre"] == usuario.nombre for u in users):
        raise HTTPException(status_code=400, detail="El nombre ya esta registrado")

    playlist_id = await run_in_threadpool(crear_playlist_spotify, usuario.nombre)

    nuevo_usuario = create_user(usuario.nombre, usuario.email, usuario.edad, playlist_id)
    return nuevo_usuario


@app.delete("/usuarios/{valor}", tags=["Usuarios"])
async def eliminar_usuario(valor: str):
    """Elimina un usuario por ID o nombre"""
    usuario = None
    if valor.isdigit():
        usuario = get_user_by_id(int(valor))
    if not usuario:
        usuario = get_user_by_name(valor)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    playlist_id = usuario.get("playlist_id")
    if playlist_id:
        await run_in_threadpool(eliminar_playlist_spotify, playlist_id)
    delete_user(usuario["id"])
    return {"message": "Usuario eliminado", "usuario": usuario}
