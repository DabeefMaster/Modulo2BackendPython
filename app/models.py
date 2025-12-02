from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, field_validator


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=50, description="Nombre del usuario")
    email: EmailStr = Field(description="Email válido del usuario")
    edad: int = Field(ge=13, le=120, description="Edad del usuario entre 13 y 120 años")
    listaCanciones: List[str] = Field(default_factory=list, description="Lista de URIs de canciones de Spotify")
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        if len(v.strip()) < 3:
            raise ValueError('El nombre debe tener al menos 3 caracteres')
        if not v.replace(' ', '').isalnum():
            raise ValueError('El nombre solo puede contener letras, números y espacios')
        return v.strip()


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=50, description="Nombre del usuario")
    email: Optional[EmailStr] = Field(None, description="Email válido del usuario")
    edad: Optional[int] = Field(None, ge=13, le=120, description="Edad del usuario entre 13 y 120 años")
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('El nombre no puede estar vacío')
            if len(v.strip()) < 3:
                raise ValueError('El nombre debe tener al menos 3 caracteres')
            if not v.replace(' ', '').isalnum():
                raise ValueError('El nombre solo puede contener letras, números y espacios')
            return v.strip()
        return v


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    edad: int
    listaCanciones: List[str]
    playlist_id: Optional[str] = None
    likes: List[str] = Field(default_factory=list)
    
    @property
    def total_canciones(self) -> int:
        """Número total de canciones en la playlist"""
        return len(self.listaCanciones)
    
    @property
    def total_likes(self) -> int:
        """Número total de canciones con like"""
        return len(self.likes)
    
    @property
    def porcentaje_likes(self) -> float:
        """Porcentaje de canciones que tienen like"""
        if not self.listaCanciones:
            return 0.0
        return round((len(self.likes) / len(self.listaCanciones)) * 100, 2)


class CancionInput(BaseModel):
    nombre_cancion: str = Field(min_length=1, max_length=200, description="Nombre de la canción a buscar")
    
    @field_validator('nombre_cancion')
    @classmethod
    def validar_cancion(cls, v):
        if not v.strip():
            raise ValueError('El nombre de la canción no puede estar vacío')
        return v.strip()


class TrackInfo(BaseModel):
    nombre: str
    artistas: List[str]
    album: str
    uri: str
    id: str


class CancionResponse(BaseModel):
    """Respuesta enriquecida con información de una canción"""
    track_info: TrackInfo
    tiene_like: bool = False
    posicion: Optional[int] = None
