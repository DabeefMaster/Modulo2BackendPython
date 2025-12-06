"""
Dependencias de FastAPI.

Define las dependencias inyectables para los endpoints de la API,
incluyendo las instancias de los servicios.
"""

from fastapi import Depends
from ..services.product_service import ProductService
from ..services.order_service import OrderService


# Instancias globales de los servicios (Singleton pattern)
_product_service: ProductService = None
_order_service: OrderService = None


def get_product_service() -> ProductService:
    """
    Dependency injection para ProductService.
    
    Returns:
        Instancia singleton de ProductService
    """
    global _product_service
    
    if _product_service is None:
        _product_service = ProductService()
    
    return _product_service


def get_order_service(
    product_service: ProductService = Depends(get_product_service)
) -> OrderService:
    """
    Dependency injection para OrderService.
    
    OrderService depende de ProductService para validaciones.
    
    Args:
        product_service: Instancia de ProductService (inyectada)
    
    Returns:
        Instancia singleton de OrderService
    """
    global _order_service
    
    if _order_service is None:
        _order_service = OrderService(product_service)
    
    return _order_service
