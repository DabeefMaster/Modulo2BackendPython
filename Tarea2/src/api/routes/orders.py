"""
Endpoints de la API para pedidos.

Define todos los endpoints relacionados con la gestión de pedidos.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from ...models.order import (
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    OrderResponse,
    OrderSummaryResponse,
    OrderListResponse,
    OrderStatsResponse
)
from ...services.order_service import OrderService
from ..dependencies import get_order_service


router = APIRouter(
    prefix="/orders",
    tags=["Pedidos"],
    responses={404: {"description": "Pedido no encontrado"}}
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo pedido",
    description="Crea un nuevo pedido validando la existencia de productos y stock disponible."
)
def create_order(
    order: OrderCreate,
    service: OrderService = Depends(get_order_service)
):
    """
    Crea un nuevo pedido.
    
    - **customer_name**: Nombre del cliente
    - **items**: Lista de productos con product_id y quantity
    - **notes**: Notas adicionales (opcional)
    
    El sistema validará automáticamente:
    - Que todos los productos existan
    - Que haya stock suficiente
    - Reducirá el stock de los productos automáticamente
    """
    try:
        # Convertir items de Pydantic a dict
        items_data = [item.model_dump() for item in order.items]
        
        created_order = service.create_order(
            customer_name=order.customer_name,
            items_data=items_data,
            notes=order.notes
        )
        return created_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el pedido: {str(e)}"
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Consultar pedido por ID",
    description="Obtiene la información completa de un pedido incluyendo todos sus items."
)
def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Obtiene un pedido por su ID.
    
    - **order_id**: ID del pedido a consultar
    """
    order = service.get_order(order_id)
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {order_id} no encontrado"
        )
    
    return order


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Listar todos los pedidos",
    description="Obtiene la lista de todos los pedidos (versión resumida sin items detallados)."
)
def get_all_orders(
    include_items: bool = Query(
        False,
        description="Si es True, incluye los items detallados de cada pedido"
    ),
    service: OrderService = Depends(get_order_service)
):
    """
    Obtiene todos los pedidos.
    
    - **include_items**: Si incluir items detallados (por defecto False para mejor rendimiento)
    """
    orders = service.get_all_orders(include_items=include_items)
    return {
        "total": len(orders),
        "orders": orders
    }


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Actualizar un pedido",
    description="Actualiza un pedido existente. Puede cambiar el estado, los items o las notas."
)
def update_order(
    order_id: str,
    order_update: OrderUpdate,
    service: OrderService = Depends(get_order_service)
):
    """
    Actualiza un pedido.
    
    - **order_id**: ID del pedido a actualizar
    - **status**: Nuevo estado (opcional)
    - **items**: Nueva lista de items (opcional) - ajustará stock automáticamente
    - **notes**: Nuevas notas (opcional)
    
    Si se modifican los items, el sistema:
    1. Restaurará el stock de los items anteriores
    2. Validará y reducirá el stock de los nuevos items
    """
    try:
        # Convertir items si existen
        items_data = None
        if order_update.items is not None:
            items_data = [item.model_dump() for item in order_update.items]
        
        updated_order = service.update_order(
            order_id=order_id,
            status=order_update.status.value if order_update.status else None,
            items_data=items_data,
            notes=order_update.notes
        )
        
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido con ID {order_id} no encontrado"
            )
        
        return updated_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el pedido: {str(e)}"
        )


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Actualizar solo el estado de un pedido",
    description="Cambia el estado de un pedido sin modificar otros datos."
)
def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    service: OrderService = Depends(get_order_service)
):
    """
    Actualiza solo el estado de un pedido.
    
    - **order_id**: ID del pedido
    - **status**: Nuevo estado (pendiente, procesando, enviado, entregado, cancelado)
    """
    try:
        updated_order = service.update_order_status(
            order_id=order_id,
            new_status=status_update.status.value
        )
        
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido con ID {order_id} no encontrado"
            )
        
        return updated_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un pedido",
    description="Elimina un pedido y restaura el stock de los productos."
)
def delete_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Elimina un pedido.
    
    - **order_id**: ID del pedido a eliminar
    
    El stock de los productos del pedido será restaurado automáticamente.
    """
    success = service.delete_order(order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {order_id} no encontrado"
        )
    
    return None


@router.get(
    "/filter/status/{status}",
    response_model=OrderListResponse,
    summary="Filtrar pedidos por estado",
    description="Obtiene todos los pedidos con un estado específico."
)
def get_orders_by_status(
    status: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Obtiene pedidos filtrados por estado.
    
    - **status**: Estado a filtrar (pendiente, procesando, enviado, entregado, cancelado)
    """
    try:
        orders = service.get_orders_by_status(status)
        return {
            "total": len(orders),
            "orders": orders
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/filter/customer/{customer_name}",
    response_model=OrderListResponse,
    summary="Filtrar pedidos por cliente",
    description="Busca pedidos por nombre de cliente (búsqueda parcial, no case-sensitive)."
)
def get_orders_by_customer(
    customer_name: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Obtiene pedidos filtrados por nombre de cliente.
    
    - **customer_name**: Nombre o parte del nombre del cliente
    
    La búsqueda es parcial y no distingue mayúsculas/minúsculas.
    """
    orders = service.get_orders_by_customer(customer_name)
    return {
        "total": len(orders),
        "orders": orders
    }


@router.get(
    "/stats/summary",
    response_model=OrderStatsResponse,
    summary="Estadísticas de pedidos",
    description="Obtiene estadísticas generales sobre los pedidos."
)
def get_order_statistics(
    service: OrderService = Depends(get_order_service)
):
    """
    Obtiene estadísticas de pedidos.
    
    Incluye:
    - Total de pedidos
    - Ingresos totales
    - Pedidos por estado
    - Ingresos por estado
    - Valor promedio de pedido
    """
    return service.get_order_statistics()
