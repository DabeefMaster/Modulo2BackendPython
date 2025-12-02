from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

app = FastAPI(
    title="API de Usuarios con Spotify",
    description="""
    API REST para gestión de usuarios y sus playlists de Spotify.
    
    ## Funcionalidades principales:
    * **Gestión de Usuarios**: Crear, listar, actualizar y eliminar usuarios
    * **Playlists de Spotify**: Cada usuario tiene una playlist privada asociada
    * **Gestión de Canciones**: Añadir y eliminar canciones de las playlists
    * **Sistema de Likes**: Marcar canciones favoritas
    * **Búsqueda y Filtrado**: Buscar canciones por artista
    
    ## Validaciones incluidas:
    * Email válido con formato correcto
    * Nombres únicos y con longitud mínima de 3 caracteres
    * Edad entre 13 y 120 años
    * Validación de canciones duplicadas en playlists
    """,
    version="2.0.0",
    contact={
        "name": "Soporte API",
    },
    license_info={
        "name": "MIT",
    },
)


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


@app.get(
    "/usuarios",
    response_model=list[UsuarioResponse],
    tags=["Usuarios"],
    summary="Listar todos los usuarios",
    description="Obtiene la lista completa de usuarios registrados en el sistema con sus playlists de Spotify",
    responses={
        200: {"description": "Lista de usuarios obtenida exitosamente"},
    }
)
def listar_usuarios():
    """Lista todos los usuarios"""
    return list_users()


@app.get(
    "/usuarios/{valor}",
    response_model=UsuarioResponse,
    tags=["Usuarios"],
    summary="Obtener usuario por ID o nombre",
    description="Busca y retorna un usuario específico. Puede buscar por ID numérico o por nombre de usuario.",
    responses={
        200: {"description": "Usuario encontrado exitosamente"},
        404: {"description": "Usuario no encontrado"},
    }
)
def obtener_usuario(valor: str):
    """Obtiene un usuario por ID o nombre"""
    usuario = None
    if valor.isdigit():
        usuario = get_user_by_id(int(valor))
    if not usuario:
        usuario = get_user_by_name(valor)
    if usuario:
        return usuario
    raise HTTPException(
        status_code=404,
        detail={
            "error": "Usuario no encontrado",
            "valor_buscado": valor,
            "tipo_busqueda": "ID" if valor.isdigit() else "nombre",
            "sugerencia": "Verifica el ID o nombre del usuario con GET /usuarios"
        }
    )


@app.put(
    "/usuarios/{id}",
    response_model=UsuarioResponse,
    tags=["Usuarios"],
    summary="Modificar un usuario existente",
    description="Actualiza los datos de un usuario. Los campos no proporcionados mantendrán su valor actual.",
    responses={
        200: {"description": "Usuario actualizado exitosamente"},
        400: {"description": "Email o nombre ya registrado por otro usuario"},
        404: {"description": "Usuario no encontrado"},
    }
)
def modificar_usuario(id: int, usuario_update: UsuarioUpdate):
    """Modifica un usuario existente"""
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuario no encontrado",
                "id_buscado": id,
                "sugerencia": "Verifica que el ID del usuario exista con GET /usuarios"
            }
        )
    if usuario_update.email is not None:
        existente = get_user_by_name(usuario.get("nombre"))
        # verificar email duplicado
        users = list_users()
        if any(u["email"] == usuario_update.email and u["id"] != id for u in users):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "El email ya está registrado",
                    "email": usuario_update.email,
                    "sugerencia": "Usa un email diferente o actualiza el usuario existente"
                }
            )
    if usuario_update.nombre is not None:
        users = list_users()
        if any(u["nombre"] == usuario_update.nombre and u["id"] != id for u in users):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "El nombre ya está registrado",
                    "nombre": usuario_update.nombre,
                    "sugerencia": "Usa un nombre diferente"
                }
            )

    updated = update_user(id, usuario_update.nombre, usuario_update.email, usuario_update.edad)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuario no encontrado",
                "id_buscado": id,
                "sugerencia": "El usuario pudo haber sido eliminado"
            }
        )
    return updated


app.include_router(spotify_routes.router)


@app.post(
    "/usuarios/",
    response_model=UsuarioResponse,
    tags=["Usuarios"],
    status_code=201,
    summary="Crear un nuevo usuario",
    description="Crea un nuevo usuario en el sistema y automáticamente genera una playlist privada en Spotify asociada al usuario.",
    responses={
        201: {"description": "Usuario creado exitosamente con playlist de Spotify"},
        400: {"description": "Email o nombre ya registrado"},
        422: {"description": "Datos de entrada inválidos (validación fallida)"},
        502: {"description": "Error al crear la playlist en Spotify"},
    }
)
async def crear_usuario(usuario: UsuarioCreate):
    """Crea un nuevo usuario"""
    users = list_users()
    if any(u["email"] == usuario.email for u in users):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "El email ya está registrado",
                "email": usuario.email,
                "sugerencia": "Usa un email diferente o inicia sesión con el usuario existente"
            }
        )
    if any(u["nombre"] == usuario.nombre for u in users):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "El nombre ya está registrado",
                "nombre": usuario.nombre,
                "sugerencia": "Elige un nombre de usuario diferente"
            }
        )

    playlist_id = await run_in_threadpool(crear_playlist_spotify, usuario.nombre)

    nuevo_usuario = create_user(usuario.nombre, usuario.email, usuario.edad, playlist_id)
    return nuevo_usuario


@app.delete(
    "/usuarios/{valor}",
    tags=["Usuarios"],
    summary="Eliminar un usuario",
    description="Elimina un usuario del sistema por ID o nombre. También elimina su playlist asociada de Spotify si existe.",
    responses={
        200: {"description": "Usuario y playlist eliminados exitosamente"},
        404: {"description": "Usuario no encontrado"},
        502: {"description": "Error al eliminar la playlist de Spotify"},
    }
)
async def eliminar_usuario(valor: str):
    """Elimina un usuario por ID o nombre"""
    usuario = None
    if valor.isdigit():
        usuario = get_user_by_id(int(valor))
    if not usuario:
        usuario = get_user_by_name(valor)
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Usuario no encontrado",
                "valor_buscado": valor,
                "tipo_busqueda": "ID" if valor.isdigit() else "nombre",
                "sugerencia": "Verifica que el usuario exista antes de intentar eliminarlo"
            }
        )
    playlist_id = usuario.get("playlist_id")
    if playlist_id:
        await run_in_threadpool(eliminar_playlist_spotify, playlist_id)
    delete_user(usuario["id"])
    return {"message": "Usuario eliminado", "usuario": usuario}
