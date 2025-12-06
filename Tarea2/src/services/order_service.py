"""
Servicio de lógica de negocio para pedidos.

Actúa como intermediario entre la API y la estructura de datos LinkedList.
Gestiona la creación, actualización y consulta de pedidos, coordinando
con ProductService para validar productos y gestionar stock.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import re

from ..data_structures.linked_list import LinkedList, OrderNode, OrderItem, OrderStatus
from .product_service import ProductService
from ..config import settings


class OrderService:
    """
    Servicio para gestionar operaciones de pedidos.
    
    Attributes:
        linked_list (LinkedList): Lista enlazada que almacena los pedidos
        product_service (ProductService): Servicio de productos para validaciones
        order_counter (int): Contador para generar IDs únicos de pedidos
    """
    
    def __init__(self, product_service: ProductService, storage_path: Optional[str] = None):
        self.linked_list = LinkedList()
        self.product_service = product_service
        self.order_counter = 0
        self.storage_path = storage_path or settings.orders_file_path
        self._load_from_file()

    def _extract_counter(self, order_id: str) -> int:
        """Obtiene la parte numérica de un order_id como entero."""
        match = re.search(r"(\d+)", order_id)
        return int(match.group(1)) if match else 0

    def _load_from_file(self):
        """Carga pedidos desde archivo JSON sin alterar stock."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        max_counter = 0
        for order in data if isinstance(data, list) else []:
            try:
                items = [
                    OrderItem(
                        product_id=item["product_id"],
                        product_name=item.get("product_name", ""),
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                    )
                    for item in order.get("items", [])
                ]
                order_node = OrderNode(
                    order_id=order["order_id"],
                    customer_name=order["customer_name"],
                    items=items,
                    notes=order.get("notes", ""),
                )
                status_str = order.get("status")
                if status_str:
                    try:
                        order_node.status = OrderStatus(status_str)
                    except Exception:
                        pass
                created_at = order.get("created_at")
                updated_at = order.get("updated_at")
                if created_at:
                    try:
                        order_node.created_at = datetime.fromisoformat(created_at)
                    except Exception:
                        pass
                if updated_at:
                    try:
                        order_node.updated_at = datetime.fromisoformat(updated_at)
                    except Exception:
                        pass

                self.linked_list.append(order_node)
                max_counter = max(max_counter, self._extract_counter(order_node.order_id))
            except Exception:
                continue

        self.order_counter = max_counter

    def _persist_orders(self):
        """Guarda todos los pedidos en archivo JSON."""
        if not self.storage_path:
            return
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        orders = self.linked_list.get_all_as_dict(include_items=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    
    def _generate_order_id(self) -> str:
        """
        Genera un ID único para un pedido.
        
        Returns:
            String con formato ORD + número de 6 dígitos
        """
        self.order_counter += 1
        return f"ORD{self.order_counter:06d}"
    
    def create_order(
        self,
        customer_name: str,
        items_data: List[Dict[str, Any]],
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Crea un nuevo pedido.
        
        Valida que todos los productos existan y tengan stock suficiente,
        crea el pedido, reduce el stock y lo agrega a la lista.
        
        Args:
            customer_name: Nombre del cliente
            items_data: Lista de dicts con product_id y quantity
            notes: Notas adicionales del pedido
        
        Returns:
            Diccionario con los datos del pedido creado
        
        Raises:
            ValueError: Si hay productos inválidos o sin stock
        """
        if not items_data:
            raise ValueError("El pedido debe contener al menos un producto")
        
        # Fase 1: Validar todos los productos antes de modificar stock
        validated_items = []
        
        for item_data in items_data:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity")
            
            if not product_id or not quantity:
                raise ValueError("Cada item debe tener product_id y quantity")
            
            # Validar disponibilidad
            is_valid, error_msg, product = self.product_service.validate_product_availability(
                product_id, quantity
            )
            
            if not is_valid:
                raise ValueError(error_msg)
            
            validated_items.append((product, quantity))
        
        # Fase 2: Crear OrderItems y reducir stock
        order_items = []
        
        try:
            for product, quantity in validated_items:
                # Crear OrderItem con snapshot de datos
                order_item = OrderItem(
                    product_id=product.product_id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price
                )
                order_items.append(order_item)
                
                # Reducir stock
                self.product_service.update_stock(product.product_id, -quantity)
            
            # Fase 3: Crear y agregar el pedido
            order_id = self._generate_order_id()
            order_node = OrderNode(
                order_id=order_id,
                customer_name=customer_name,
                items=order_items,
                notes=notes
            )
            
            success = self.linked_list.append(order_node)
            
            if not success:
                raise ValueError(f"No se pudo crear el pedido con ID {order_id}")
            
            self._persist_orders()
            return order_node.to_dict()
        
        except Exception as e:
            # Si algo falla, intentar restaurar el stock
            for i, (product, quantity) in enumerate(validated_items[:len(order_items)]):
                try:
                    self.product_service.update_stock(product.product_id, quantity)
                except:
                    pass  # Log error but continue restoration
            
            raise e
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un pedido por su ID.
        
        Args:
            order_id: ID del pedido
        
        Returns:
            Diccionario con los datos del pedido o None si no existe
        """
        order = self.linked_list.find_by_id(order_id)
        return order.to_dict() if order else None
    
    def get_order_node(self, order_id: str) -> Optional[OrderNode]:
        """
        Obtiene el nodo del pedido (para uso interno).
        
        Args:
            order_id: ID del pedido
        
        Returns:
            OrderNode o None si no existe
        """
        return self.linked_list.find_by_id(order_id)
    
    def get_all_orders(self, include_items: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene todos los pedidos.
        
        Args:
            include_items: Si incluir items detallados de cada pedido
        
        Returns:
            Lista de diccionarios con todos los pedidos
        """
        return self.linked_list.get_all_as_dict(include_items=include_items)
    
    def update_order_status(
        self,
        order_id: str,
        new_status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza el estado de un pedido.
        
        Args:
            order_id: ID del pedido
            new_status: Nuevo estado
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        
        Raises:
            ValueError: Si el estado es inválido
        """
        order = self.linked_list.find_by_id(order_id)
        
        if order is None:
            return None
        
        try:
            status_enum = OrderStatus(new_status)
            order.update_status(status_enum)
            self._persist_orders()
            return order.to_dict()
        except ValueError:
            raise ValueError(f"Estado inválido: {new_status}")
    
    def update_order(
        self,
        order_id: str,
        status: Optional[str] = None,
        items_data: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un pedido existente.
        
        Permite cambiar el estado, los items o las notas.
        Si se cambian los items, se ajusta el stock automáticamente.
        
        Args:
            order_id: ID del pedido
            status: Nuevo estado (opcional)
            items_data: Nueva lista de items (opcional)
            notes: Nuevas notas (opcional)
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        order = self.linked_list.find_by_id(order_id)
        
        if order is None:
            return None
        
        # Actualizar estado
        if status is not None:
            try:
                status_enum = OrderStatus(status)
                order.update_status(status_enum)
            except ValueError:
                raise ValueError(f"Estado inválido: {status}")
        
        # Actualizar items
        if items_data is not None:
            if not items_data:
                raise ValueError("Si actualiza items, debe incluir al menos uno")
            
            # Guardar items antiguos para restaurar stock
            old_items = order.items.copy()
            
            try:
                # Restaurar stock de items antiguos
                for old_item in old_items:
                    self.product_service.update_stock(
                        old_item.product_id,
                        old_item.quantity
                    )
                
                # Validar nuevos items
                validated_items = []
                for item_data in items_data:
                    product_id = item_data.get("product_id")
                    quantity = item_data.get("quantity")
                    
                    is_valid, error_msg, product = self.product_service.validate_product_availability(
                        product_id, quantity
                    )
                    
                    if not is_valid:
                        raise ValueError(error_msg)
                    
                    validated_items.append((product, quantity))
                
                # Crear nuevos OrderItems y reducir stock
                new_order_items = []
                for product, quantity in validated_items:
                    order_item = OrderItem(
                        product_id=product.product_id,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=product.price
                    )
                    new_order_items.append(order_item)
                    self.product_service.update_stock(product.product_id, -quantity)
                
                # Actualizar orden
                order.items = new_order_items
                order.total = sum(item.subtotal for item in new_order_items)
                order.updated_at = datetime.now()
            
            except Exception as e:
                # Si falla, restaurar stock original
                for old_item in old_items:
                    try:
                        self.product_service.update_stock(
                            old_item.product_id,
                            -old_item.quantity
                        )
                    except:
                        pass
                
                raise e
        
        # Actualizar notas
        if notes is not None:
            order.notes = notes
            order.updated_at = datetime.now()
        
        self._persist_orders()
        return order.to_dict()
    
    def delete_order(self, order_id: str) -> bool:
        """
        Elimina un pedido y restaura el stock de los productos.
        
        Args:
            order_id: ID del pedido a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        order = self.linked_list.find_by_id(order_id)
        
        if order is None:
            return False
        
        # Restaurar stock antes de eliminar
        for item in order.items:
            try:
                self.product_service.update_stock(item.product_id, item.quantity)
            except:
                pass  # Producto podría haber sido eliminado
        
        # Eliminar el pedido
        deleted = self.linked_list.delete(order_id)
        if deleted:
            self._persist_orders()
        return deleted
    
    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Filtra pedidos por estado.
        
        Args:
            status: Estado a filtrar
        
        Returns:
            Lista de pedidos con el estado especificado
        
        Raises:
            ValueError: Si el estado es inválido
        """
        try:
            status_enum = OrderStatus(status)
            orders = self.linked_list.filter_by_status(status_enum)
            return [order.to_dict(include_items=False) for order in orders]
        except ValueError:
            raise ValueError(f"Estado inválido: {status}")
    
    def get_orders_by_customer(self, customer_name: str) -> List[Dict[str, Any]]:
        """
        Filtra pedidos por nombre de cliente.
        
        Args:
            customer_name: Nombre del cliente (búsqueda parcial)
        
        Returns:
            Lista de pedidos del cliente
        """
        orders = self.linked_list.filter_by_customer(customer_name)
        return [order.to_dict(include_items=False) for order in orders]
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los pedidos.
        
        Returns:
            Diccionario con estadísticas
        """
        all_orders = self.linked_list.get_all()
        
        if not all_orders:
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "orders_by_status": {},
                "revenue_by_status": {},
                "average_order_value": 0.0
            }
        
        # Contar pedidos por estado
        orders_by_status = {}
        revenue_by_status = {}
        
        for status in OrderStatus:
            count = len(self.linked_list.filter_by_status(status))
            revenue = self.linked_list.get_revenue_by_status(status)
            orders_by_status[status.value] = count
            revenue_by_status[status.value] = revenue
        
        total_revenue = self.linked_list.get_total_revenue()
        avg_order_value = total_revenue / len(all_orders) if all_orders else 0.0
        
        return {
            "total_orders": len(all_orders),
            "total_revenue": total_revenue,
            "orders_by_status": orders_by_status,
            "revenue_by_status": revenue_by_status,
            "average_order_value": round(avg_order_value, 2)
        }
    
    def get_total_orders(self) -> int:
        """Retorna el número total de pedidos."""
        return self.linked_list.get_size()
    
    def order_exists(self, order_id: str) -> bool:
        """Verifica si un pedido existe."""
        return self.linked_list.find_by_id(order_id) is not None
    
    def clear_all_orders(self, restore_stock: bool = True):
        """
        Elimina todos los pedidos.
        
        Args:
            restore_stock: Si restaurar el stock de los productos
        """
        if restore_stock:
            all_orders = self.linked_list.get_all()
            for order in all_orders:
                for item in order.items:
                    try:
                        self.product_service.update_stock(item.product_id, item.quantity)
                    except:
                        pass
        
        self.linked_list.clear()
        self._persist_orders()
