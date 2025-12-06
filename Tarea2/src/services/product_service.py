"""
Servicio de lógica de negocio para productos.

Actúa como intermediario entre la API y la estructura de datos BST.
Contiene toda la lógica de negocio y validaciones relacionadas con productos.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

from ..data_structures.binary_search_tree import BinarySearchTree, ProductNode
from ..config import settings


class ProductService:
    """
    Servicio para gestionar operaciones de productos.
    
    Attributes:
        bst (BinarySearchTree): Árbol binario de búsqueda que almacena los productos
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.bst = BinarySearchTree()
        self.storage_path = storage_path or settings.products_file_path
        self._load_from_file()

    def _load_from_file(self):
        """Carga productos desde archivo JSON si existe."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return  # Archivo ilegible o vacío

        for product in data if isinstance(data, list) else []:
            try:
                self.bst.insert(
                    product_id=product["product_id"],
                    name=product["name"],
                    price=product["price"],
                    stock=product.get("stock", 0),
                    description=product.get("description", "")
                )
                node = self.bst.search(product["product_id"])
                created_at = product.get("created_at")
                if node and created_at:
                    try:
                        node.created_at = datetime.fromisoformat(created_at)
                    except Exception:
                        pass
            except Exception:
                continue

    def _persist_products(self):
        """Guarda todos los productos en archivo JSON."""
        if not self.storage_path:
            return
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        products = self.get_all_products()
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    
    def create_product(
        self,
        product_id: int,
        name: str,
        price: float,
        stock: int,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Crea un nuevo producto.
        
        Args:
            product_id: ID único del producto
            name: Nombre del producto
            price: Precio del producto
            stock: Cantidad en inventario
            description: Descripción opcional
        
        Returns:
            Diccionario con los datos del producto creado
        
        Raises:
            ValueError: Si los datos son inválidos o el ID ya existe
        """
        # Verificar si el producto ya existe
        existing = self.bst.search(product_id)
        if existing is not None:
            raise ValueError(f"Ya existe un producto con el ID {product_id}")
        
        # Intentar insertar
        success = self.bst.insert(product_id, name, price, stock, description)
        
        if not success:
            raise ValueError("No se pudo crear el producto")
        
        # Buscar el producto recién creado para retornarlo
        product = self.bst.search(product_id)
        result = product.to_dict() if product else None
        self._persist_products()
        return result
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su ID.
        
        Args:
            product_id: ID del producto
        
        Returns:
            Diccionario con los datos del producto o None si no existe
        """
        product = self.bst.search(product_id)
        return product.to_dict() if product else None
    
    def get_product_node(self, product_id: int) -> Optional[ProductNode]:
        """
        Obtiene el nodo del producto (para uso interno).
        
        Args:
            product_id: ID del producto
        
        Returns:
            ProductNode o None si no existe
        """
        return self.bst.search(product_id)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos ordenados por ID.
        
        Returns:
            Lista de diccionarios con todos los productos
        """
        return self.bst.get_all_products()
    
    def get_products_in_stock(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos que tienen stock disponible.
        
        Returns:
            Lista de productos con stock > 0
        """
        return self.bst.get_products_in_stock()
    
    def get_products_by_price_range(
        self,
        min_price: float,
        max_price: float
    ) -> List[Dict[str, Any]]:
        """
        Obtiene productos dentro de un rango de precios.
        
        Args:
            min_price: Precio mínimo
            max_price: Precio máximo
        
        Returns:
            Lista de productos en el rango
        
        Raises:
            ValueError: Si el rango es inválido
        """
        if min_price < 0 or max_price < 0:
            raise ValueError("Los precios no pueden ser negativos")
        
        if min_price > max_price:
            raise ValueError("El precio mínimo no puede ser mayor que el máximo")
        
        return self.bst.get_products_by_price_range(min_price, max_price)
    
    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        stock: Optional[int] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza los datos de un producto.
        
        Args:
            product_id: ID del producto a actualizar
            name: Nuevo nombre (opcional)
            price: Nuevo precio (opcional)
            stock: Nuevo stock (opcional)
            description: Nueva descripción (opcional)
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        success = self.bst.update_product(
            product_id=product_id,
            name=name,
            price=price,
            stock=stock,
            description=description
        )
        
        if not success:
            return None
        
        # Retornar el producto actualizado
        updated = self.get_product(product_id)
        self._persist_products()
        return updated
    
    def update_stock(self, product_id: int, quantity_change: int) -> Optional[Dict[str, Any]]:
        """
        Actualiza el stock de un producto.
        
        Args:
            product_id: ID del producto
            quantity_change: Cambio en el stock (+ para aumentar, - para disminuir)
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        
        Raises:
            ValueError: Si el stock resultante sería negativo
        """
        success = self.bst.update_stock(product_id, quantity_change)
        
        if not success:
            return None
        
        updated = self.get_product(product_id)
        self._persist_products()
        return updated
    
    def delete_product(self, product_id: int) -> bool:
        """
        Elimina un producto.
        
        Args:
            product_id: ID del producto a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        deleted = self.bst.delete(product_id)
        if deleted:
            self._persist_products()
        return deleted
    
    def validate_product_availability(
        self,
        product_id: int,
        quantity: int
    ) -> tuple[bool, Optional[str], Optional[ProductNode]]:
        """
        Valida si un producto existe y tiene stock suficiente.
        
        Args:
            product_id: ID del producto
            quantity: Cantidad requerida
        
        Returns:
            Tupla (es_válido, mensaje_error, nodo_producto)
        """
        product = self.bst.search(product_id)
        
        if product is None:
            return False, f"El producto con ID {product_id} no existe", None
        
        if product.stock < quantity:
            return (
                False,
                f"Stock insuficiente para {product.name}. "
                f"Disponible: {product.stock}, Solicitado: {quantity}",
                None
            )
        
        return True, None, product
    
    def get_total_products(self) -> int:
        """Retorna el número total de productos."""
        return self.bst.get_size()
    
    def product_exists(self, product_id: int) -> bool:
        """Verifica si un producto existe."""
        return self.bst.search(product_id) is not None
    
    def clear_all_products(self):
        """Elimina todos los productos (usar con precaución)."""
        self.bst.clear()
        self._persist_products()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los productos.
        
        Returns:
            Diccionario con estadísticas
        """
        products = self.bst.inorder_traversal()
        
        if not products:
            return {
                "total_products": 0,
                "total_inventory_value": 0.0,
                "products_in_stock": 0,
                "products_out_of_stock": 0,
                "average_price": 0.0,
                "total_units": 0
            }
        
        total_value = sum(p.price * p.stock for p in products)
        in_stock = sum(1 for p in products if p.stock > 0)
        out_of_stock = len(products) - in_stock
        avg_price = sum(p.price for p in products) / len(products)
        total_units = sum(p.stock for p in products)
        
        return {
            "total_products": len(products),
            "total_inventory_value": round(total_value, 2),
            "products_in_stock": in_stock,
            "products_out_of_stock": out_of_stock,
            "average_price": round(avg_price, 2),
            "total_units": total_units
        }
