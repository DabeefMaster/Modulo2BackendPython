"""
Endpoints de la API para productos.

Define todos los endpoints relacionados con la gestión de productos.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List
from ...models.product import (
    ProductCreate,
    ProductUpdate,
    ProductStockUpdate,
    ProductResponse,
    ProductListResponse,
    ProductInStockResponse
)
from ...services.product_service import ProductService
from ..dependencies import get_product_service


router = APIRouter(
    prefix="/products",
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}}
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="Crea un nuevo producto en el sistema. El product_id debe ser único."
)
def create_product(
    product: ProductCreate,
    service: ProductService = Depends(get_product_service)
):
    """
    Crea un nuevo producto.
    
    - **product_id**: ID único del producto (debe ser > 0)
    - **name**: Nombre del producto
    - **price**: Precio del producto (debe ser >= 0)
    - **stock**: Cantidad en inventario (debe ser >= 0)
    - **description**: Descripción opcional del producto
    """
    try:
        created_product = service.create_product(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            description=product.description or ""
        )
        return created_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el producto: {str(e)}"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Consultar producto por ID",
    description="Obtiene la información completa de un producto por su ID."
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """
    Obtiene un producto por su ID.
    
    - **product_id**: ID del producto a consultar
    """
    product = service.get_product(product_id)
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    
    return product


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Listar todos los productos",
    description="Obtiene la lista completa de productos ordenados por ID."
)
def get_all_products(
    service: ProductService = Depends(get_product_service)
):
    """
    Obtiene todos los productos.
    
    Retorna los productos ordenados por ID (recorrido in-order del BST).
    """
    products = service.get_all_products()
    return {
        "total": len(products),
        "products": products
    }


@router.get(
    "/filter/in-stock",
    response_model=ProductInStockResponse,
    summary="Listar productos con stock disponible",
    description="Obtiene solo los productos que tienen stock > 0."
)
def get_products_in_stock(
    service: ProductService = Depends(get_product_service)
):
    """
    Obtiene productos con stock disponible.
    
    Filtra solo los productos que tienen stock mayor a 0.
    """
    products = service.get_products_in_stock()
    return {
        "total_available": len(products),
        "products": products
    }


@router.get(
    "/filter/price-range",
    response_model=ProductListResponse,
    summary="Filtrar productos por rango de precio",
    description="Obtiene productos dentro de un rango de precios especificado."
)
def get_products_by_price_range(
    min_price: float = Query(..., ge=0, description="Precio mínimo"),
    max_price: float = Query(..., ge=0, description="Precio máximo"),
    service: ProductService = Depends(get_product_service)
):
    """
    Obtiene productos en un rango de precios.
    
    - **min_price**: Precio mínimo (debe ser >= 0)
    - **max_price**: Precio máximo (debe ser >= 0)
    """
    try:
        products = service.get_products_by_price_range(min_price, max_price)
        return {
            "total": len(products),
            "products": products
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Actualizar un producto",
    description="Actualiza los datos de un producto existente. Todos los campos son opcionales."
)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    service: ProductService = Depends(get_product_service)
):
    """
    Actualiza un producto.
    
    - **product_id**: ID del producto a actualizar
    - Todos los campos son opcionales, se actualizarán solo los proporcionados
    """
    try:
        updated_product = service.update_product(
            product_id=product_id,
            name=product_update.name,
            price=product_update.price,
            stock=product_update.stock,
            description=product_update.description
        )
        
        if updated_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
        
        return updated_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse,
    summary="Actualizar stock de un producto",
    description="Modifica el stock de un producto con un valor positivo (aumentar) o negativo (disminuir)."
)
def update_product_stock(
    product_id: int,
    stock_update: ProductStockUpdate,
    service: ProductService = Depends(get_product_service)
):
    """
    Actualiza el stock de un producto.
    
    - **product_id**: ID del producto
    - **quantity_change**: Cambio en el stock (+ para aumentar, - para disminuir)
    """
    try:
        updated_product = service.update_stock(
            product_id=product_id,
            quantity_change=stock_update.quantity_change
        )
        
        if updated_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
        
        return updated_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un producto",
    description="Elimina un producto del sistema."
)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """
    Elimina un producto.
    
    - **product_id**: ID del producto a eliminar
    """
    success = service.delete_product(product_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    
    return None


@router.get(
    "/stats/summary",
    summary="Estadísticas de productos",
    description="Obtiene estadísticas generales sobre los productos."
)
def get_product_statistics(
    service: ProductService = Depends(get_product_service)
):
    """
    Obtiene estadísticas de productos.
    
    Incluye: total de productos, valor del inventario, productos en stock, etc.
    """
    return service.get_statistics()
