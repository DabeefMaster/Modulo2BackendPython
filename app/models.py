from typing import List, Optional

from pydantic import BaseModel, Field


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    edad: int
    listaCanciones: List[str] = Field(default_factory=list)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    edad: int
    listaCanciones: List[str]
    playlist_id: Optional[str] = None
    likes: List[str] = Field(default_factory=list)


class CancionInput(BaseModel):
    nombre_cancion: str


class TrackInfo(BaseModel):
    nombre: str
    artistas: List[str]
    album: str
    uri: str
    id: str
