"""
Modelos Pydantic para la validación de datos de productos en la API.

Estos schemas definen la estructura de datos que acepta y devuelve la API
para las operaciones relacionadas con productos.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Schema base con campos comunes de producto."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del producto")
    price: float = Field(..., ge=0, description="Precio del producto (debe ser >= 0)")
    stock: int = Field(..., ge=0, description="Cantidad en inventario (debe ser >= 0)")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción del producto")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que el nombre no esté vacío después de eliminar espacios."""
        if not v or not v.strip():
            raise ValueError('El nombre del producto no puede estar vacío')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> str:
        """Limpia la descripción."""
        if v is None:
            return ""
        return v.strip()


class ProductCreate(ProductBase):
    """
    Schema para crear un nuevo producto.
    
    Requiere un product_id único.
    """
    product_id: int = Field(..., gt=0, description="ID único del producto (debe ser > 0)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "name": "Laptop Dell XPS 15",
                "price": 1299.99,
                "stock": 15,
                "description": "Laptop de alto rendimiento con pantalla 4K"
            }
        }
    )


class ProductUpdate(BaseModel):
    """
    Schema para actualizar un producto existente.
    
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre del producto no puede estar vacío')
        return v.strip() if v else None
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Laptop Dell XPS 15 (Actualizado)",
                "price": 1199.99,
                "stock": 20
            }
        }
    )


class ProductStockUpdate(BaseModel):
    """
    Schema para actualizar solo el stock de un producto.
    
    Útil para operaciones de inventario.
    """
    quantity_change: int = Field(
        ...,
        description="Cambio en el stock (positivo para aumentar, negativo para disminuir)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quantity_change": -5  # Reducir 5 unidades
            }
        }
    )


class ProductResponse(ProductBase):
    """
    Schema para la respuesta de la API con datos completos del producto.
    
    Incluye todos los campos más el product_id y fecha de creación.
    """
    product_id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": 1,
                "name": "Laptop Dell XPS 15",
                "price": 1299.99,
                "stock": 15,
                "description": "Laptop de alto rendimiento con pantalla 4K",
                "created_at": "2025-12-06T10:30:00"
            }
        }
    )


class ProductListResponse(BaseModel):
    """
    Schema para la respuesta de listado de productos.
    
    Incluye metadata útil.
    """
    total: int = Field(..., description="Número total de productos")
    products: list[ProductResponse] = Field(..., description="Lista de productos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Laptop Dell XPS 15",
                        "price": 1299.99,
                        "stock": 15,
                        "description": "Laptop de alto rendimiento",
                        "created_at": "2025-12-06T10:30:00"
                    },
                    {
                        "product_id": 2,
                        "name": "Mouse Logitech MX Master 3",
                        "price": 99.99,
                        "stock": 50,
                        "description": "Mouse ergonómico profesional",
                        "created_at": "2025-12-06T10:35:00"
                    }
                ]
            }
        }
    )


class ProductInStockResponse(BaseModel):
    """Schema para consulta de productos con stock disponible."""
    total_available: int = Field(..., description="Número de productos con stock > 0")
    products: list[ProductResponse]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_available": 5,
                "products": []
            }
        }
    )
