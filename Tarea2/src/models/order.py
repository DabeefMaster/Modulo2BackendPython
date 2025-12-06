"""
Modelos Pydantic para la validación de datos de pedidos en la API.

Estos schemas definen la estructura de datos que acepta y devuelve la API
para las operaciones relacionadas con pedidos.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    """Estados posibles de un pedido."""
    PENDING = "pendiente"
    PROCESSING = "procesando"
    SHIPPED = "enviado"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"


class OrderItemCreate(BaseModel):
    """
    Schema para crear un item dentro de un pedido.
    
    Solo requiere product_id y quantity, el resto se obtiene del BST.
    """
    product_id: int = Field(..., gt=0, description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad a pedir (debe ser > 0)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }
    )


class OrderItemResponse(BaseModel):
    """
    Schema para la respuesta de un item del pedido.
    
    Incluye toda la información del producto al momento del pedido.
    """
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "product_name": "Laptop Dell XPS 15",
                "quantity": 2,
                "unit_price": 1299.99,
                "subtotal": 2599.98
            }
        }
    )


class OrderCreate(BaseModel):
    """
    Schema para crear un nuevo pedido.
    
    El cliente especifica su nombre y la lista de productos que desea.
    """
    customer_name: str = Field(..., min_length=1, max_length=200, description="Nombre del cliente")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Lista de productos (mínimo 1)")
    notes: Optional[str] = Field(None, max_length=500, description="Notas adicionales del pedido")
    
    @field_validator('customer_name')
    @classmethod
    def validate_customer_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('El nombre del cliente no puede estar vacío')
        return v.strip()
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> str:
        if v is None:
            return ""
        return v.strip()
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v: List[OrderItemCreate]) -> List[OrderItemCreate]:
        if not v:
            raise ValueError('El pedido debe contener al menos un producto')
        
        # Verificar que no haya product_ids duplicados
        product_ids = [item.product_id for item in v]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError('No se pueden incluir productos duplicados en el mismo pedido')
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_name": "Juan Pérez",
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 3, "quantity": 1}
                ],
                "notes": "Entrega urgente"
            }
        }
    )


class OrderUpdate(BaseModel):
    """
    Schema para actualizar un pedido existente.
    
    Permite cambiar el estado, notas y los items del pedido.
    """
    status: Optional[OrderStatusEnum] = Field(None, description="Nuevo estado del pedido")
    items: Optional[List[OrderItemCreate]] = Field(None, min_length=1, description="Nueva lista de items")
    notes: Optional[str] = Field(None, max_length=500, description="Nuevas notas")
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v: Optional[List[OrderItemCreate]]) -> Optional[List[OrderItemCreate]]:
        if v is not None:
            if not v:
                raise ValueError('Si actualiza items, debe incluir al menos uno')
            
            # Verificar que no haya product_ids duplicados
            product_ids = [item.product_id for item in v]
            if len(product_ids) != len(set(product_ids)):
                raise ValueError('No se pueden incluir productos duplicados')
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "procesando",
                "notes": "Confirmado y listo para envío"
            }
        }
    )


class OrderStatusUpdate(BaseModel):
    """Schema simplificado para actualizar solo el estado de un pedido."""
    status: OrderStatusEnum = Field(..., description="Nuevo estado del pedido")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "enviado"
            }
        }
    )


class OrderResponse(BaseModel):
    """
    Schema para la respuesta completa de un pedido.
    
    Incluye toda la información del pedido con sus items.
    """
    order_id: str
    customer_name: str
    items: List[OrderItemResponse]
    total: float
    status: str
    notes: str
    item_count: int = Field(..., description="Número de productos distintos")
    total_quantity: int = Field(..., description="Cantidad total de productos")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "order_id": "ORD001",
                "customer_name": "Juan Pérez",
                "items": [
                    {
                        "product_id": 1,
                        "product_name": "Laptop Dell XPS 15",
                        "quantity": 2,
                        "unit_price": 1299.99,
                        "subtotal": 2599.98
                    }
                ],
                "total": 2599.98,
                "status": "pendiente",
                "notes": "Entrega urgente",
                "item_count": 1,
                "total_quantity": 2,
                "created_at": "2025-12-06T10:30:00",
                "updated_at": "2025-12-06T10:30:00"
            }
        }
    )


class OrderSummaryResponse(BaseModel):
    """
    Schema resumido de un pedido (sin items detallados).
    
    Útil para listados donde no se necesita el detalle completo.
    """
    order_id: str
    customer_name: str
    total: float
    status: str
    item_count: int
    total_quantity: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "order_id": "ORD001",
                "customer_name": "Juan Pérez",
                "total": 2599.98,
                "status": "pendiente",
                "item_count": 2,
                "total_quantity": 5,
                "created_at": "2025-12-06T10:30:00"
            }
        }
    )


class OrderListResponse(BaseModel):
    """
    Schema para la respuesta de listado de pedidos.
    
    Incluye metadata y lista resumida de pedidos.
    """
    total: int = Field(..., description="Número total de pedidos")
    orders: List[OrderSummaryResponse] = Field(..., description="Lista de pedidos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "orders": [
                    {
                        "order_id": "ORD001",
                        "customer_name": "Juan Pérez",
                        "total": 2599.98,
                        "status": "pendiente",
                        "item_count": 2,
                        "total_quantity": 3,
                        "created_at": "2025-12-06T10:30:00"
                    }
                ]
            }
        }
    )


class OrderStatsResponse(BaseModel):
    """Schema para estadísticas de pedidos."""
    total_orders: int
    total_revenue: float
    orders_by_status: dict[str, int]
    revenue_by_status: dict[str, float]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_orders": 10,
                "total_revenue": 15999.90,
                "orders_by_status": {
                    "pendiente": 3,
                    "procesando": 2,
                    "enviado": 5
                },
                "revenue_by_status": {
                    "pendiente": 4599.97,
                    "procesando": 3299.98,
                    "enviado": 8099.95
                }
            }
        }
    )
