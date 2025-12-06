"""
Lista Enlazada Simple para gestión de pedidos.

Este módulo implementa una lista enlazada donde cada nodo representa un pedido
que contiene múltiples productos. Permite operaciones eficientes de inserción
y eliminación.

Complejidad temporal:
- Inserción al final: O(1) con puntero tail
- Búsqueda: O(n)
- Eliminación: O(n)
- Recorrido completo: O(n)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Estados posibles de un pedido."""
    PENDING = "pendiente"
    PROCESSING = "procesando"
    SHIPPED = "enviado"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"


class OrderItem:
    """
    Representa un producto dentro de un pedido.
    
    Attributes:
        product_id (int): ID del producto
        product_name (str): Nombre del producto (cache)
        quantity (int): Cantidad solicitada
        unit_price (float): Precio unitario al momento del pedido
        subtotal (float): quantity * unit_price
    """
    
    def __init__(
        self,
        product_id: int,
        product_name: str,
        quantity: int,
        unit_price: float
    ):
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        if unit_price < 0:
            raise ValueError("El precio unitario no puede ser negativo")
        
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.subtotal = quantity * unit_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el item a diccionario."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal
        }
    
    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity} = ${self.subtotal:.2f}"
    
    def __repr__(self) -> str:
        return f"OrderItem(product_id={self.product_id}, quantity={self.quantity}, subtotal={self.subtotal})"


class OrderNode:
    """
    Nodo de la lista enlazada que representa un pedido completo.
    
    Attributes:
        order_id (str): Identificador único del pedido
        customer_name (str): Nombre del cliente
        items (List[OrderItem]): Lista de productos en el pedido
        total (float): Total del pedido
        status (OrderStatus): Estado actual del pedido
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de última actualización
        notes (str): Notas adicionales del pedido
        next (OrderNode): Referencia al siguiente pedido en la lista
    """
    
    def __init__(
        self,
        order_id: str,
        customer_name: str,
        items: List[OrderItem],
        notes: str = ""
    ):
        if not items:
            raise ValueError("El pedido debe contener al menos un producto")
        if not customer_name or not customer_name.strip():
            raise ValueError("El nombre del cliente no puede estar vacío")
        
        self.order_id = order_id
        self.customer_name = customer_name.strip()
        self.items = items
        self.total = sum(item.subtotal for item in items)
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.notes = notes
        self.next: Optional[OrderNode] = None
    
    def update_status(self, new_status: OrderStatus):
        """Actualiza el estado del pedido."""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def add_item(self, item: OrderItem):
        """
        Agrega un item al pedido y recalcula el total.
        
        Args:
            item: Item a agregar
        """
        self.items.append(item)
        self.total += item.subtotal
        self.updated_at = datetime.now()
    
    def remove_item(self, product_id: int) -> bool:
        """
        Elimina un item del pedido por product_id.
        
        Args:
            product_id: ID del producto a eliminar
        
        Returns:
            True si se eliminó, False si no se encontró
        """
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                self.total -= item.subtotal
                self.items.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def update_item_quantity(self, product_id: int, new_quantity: int) -> bool:
        """
        Actualiza la cantidad de un item y recalcula subtotal y total.
        
        Args:
            product_id: ID del producto
            new_quantity: Nueva cantidad
        
        Returns:
            True si se actualizó, False si no se encontró
        
        Raises:
            ValueError: Si la cantidad es inválida
        """
        if new_quantity <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        
        for item in self.items:
            if item.product_id == product_id:
                # Restar el subtotal anterior
                self.total -= item.subtotal
                
                # Actualizar cantidad y subtotal
                item.quantity = new_quantity
                item.subtotal = item.quantity * item.unit_price
                
                # Sumar el nuevo subtotal
                self.total += item.subtotal
                self.updated_at = datetime.now()
                return True
        
        return False
    
    def get_item_count(self) -> int:
        """Retorna el número de items distintos en el pedido."""
        return len(self.items)
    
    def get_total_quantity(self) -> int:
        """Retorna la cantidad total de productos en el pedido."""
        return sum(item.quantity for item in self.items)
    
    def to_dict(self, include_items: bool = True) -> Dict[str, Any]:
        """
        Convierte el pedido a diccionario para serialización.
        
        Args:
            include_items: Si incluir la lista detallada de items
        
        Returns:
            Dict con los datos del pedido
        """
        data = {
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "total": round(self.total, 2),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
            "item_count": self.get_item_count(),
            "total_quantity": self.get_total_quantity()
        }
        
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        
        return data
    
    def __str__(self) -> str:
        return f"Order({self.order_id}, {self.customer_name}, ${self.total:.2f}, {self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()


class LinkedList:
    """
    Lista Enlazada Simple para almacenar pedidos.
    
    Mantiene referencias a head (primer pedido) y tail (último pedido)
    para operaciones eficientes de inserción al final.
    
    Attributes:
        head (OrderNode): Primer nodo de la lista
        tail (OrderNode): Último nodo de la lista
        size (int): Número de pedidos en la lista
    """
    
    def __init__(self):
        self.head: Optional[OrderNode] = None
        self.tail: Optional[OrderNode] = None
        self.size: int = 0
    
    def append(self, order: OrderNode) -> bool:
        """
        Agrega un pedido al final de la lista.
        
        Args:
            order: Nodo del pedido a agregar
        
        Returns:
            True si se agregó exitosamente
        
        Complexity: O(1)
        """
        # Verificar que el order_id no exista ya
        if self.find_by_id(order.order_id) is not None:
            return False
        
        if self.head is None:
            # Lista vacía
            self.head = order
            self.tail = order
        else:
            # Agregar al final
            self.tail.next = order
            self.tail = order
        
        self.size += 1
        return True
    
    def prepend(self, order: OrderNode) -> bool:
        """
        Agrega un pedido al inicio de la lista.
        
        Args:
            order: Nodo del pedido a agregar
        
        Returns:
            True si se agregó exitosamente
        
        Complexity: O(1)
        """
        # Verificar que el order_id no exista ya
        if self.find_by_id(order.order_id) is not None:
            return False
        
        if self.head is None:
            # Lista vacía
            self.head = order
            self.tail = order
        else:
            # Agregar al inicio
            order.next = self.head
            self.head = order
        
        self.size += 1
        return True
    
    def find_by_id(self, order_id: str) -> Optional[OrderNode]:
        """
        Busca un pedido por su ID.
        
        Args:
            order_id: ID del pedido a buscar
        
        Returns:
            OrderNode si se encuentra, None si no existe
        
        Complexity: O(n)
        """
        current = self.head
        
        while current is not None:
            if current.order_id == order_id:
                return current
            current = current.next
        
        return None
    
    def delete(self, order_id: str) -> bool:
        """
        Elimina un pedido de la lista.
        
        Args:
            order_id: ID del pedido a eliminar
        
        Returns:
            True si se eliminó, False si no existe
        
        Complexity: O(n)
        """
        if self.head is None:
            return False
        
        # Caso especial: eliminar el primer nodo
        if self.head.order_id == order_id:
            self.head = self.head.next
            
            # Si era el único nodo, actualizar tail
            if self.head is None:
                self.tail = None
            
            self.size -= 1
            return True
        
        # Buscar el nodo anterior al que queremos eliminar
        current = self.head
        
        while current.next is not None:
            if current.next.order_id == order_id:
                # Encontrado, eliminar el siguiente nodo
                node_to_delete = current.next
                current.next = node_to_delete.next
                
                # Si eliminamos el último nodo, actualizar tail
                if node_to_delete == self.tail:
                    self.tail = current
                
                self.size -= 1
                return True
            
            current = current.next
        
        return False
    
    def get_all(self) -> List[OrderNode]:
        """
        Obtiene todos los pedidos de la lista.
        
        Returns:
            Lista con todos los pedidos
        
        Complexity: O(n)
        """
        result = []
        current = self.head
        
        while current is not None:
            result.append(current)
            current = current.next
        
        return result
    
    def get_all_as_dict(self, include_items: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene todos los pedidos como diccionarios.
        
        Args:
            include_items: Si incluir items detallados de cada pedido
        
        Returns:
            Lista de diccionarios con los datos de todos los pedidos
        """
        orders = self.get_all()
        return [order.to_dict(include_items=include_items) for order in orders]
    
    def filter_by_status(self, status: OrderStatus) -> List[OrderNode]:
        """
        Filtra pedidos por estado.
        
        Args:
            status: Estado a filtrar
        
        Returns:
            Lista de pedidos con el estado especificado
        """
        result = []
        current = self.head
        
        while current is not None:
            if current.status == status:
                result.append(current)
            current = current.next
        
        return result
    
    def filter_by_customer(self, customer_name: str) -> List[OrderNode]:
        """
        Filtra pedidos por nombre de cliente (búsqueda parcial, case-insensitive).
        
        Args:
            customer_name: Nombre o parte del nombre del cliente
        
        Returns:
            Lista de pedidos del cliente
        """
        result = []
        search_term = customer_name.lower().strip()
        current = self.head
        
        while current is not None:
            if search_term in current.customer_name.lower():
                result.append(current)
            current = current.next
        
        return result
    
    def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[OrderNode]:
        """
        Obtiene pedidos en un rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
        
        Returns:
            Lista de pedidos en el rango
        """
        result = []
        current = self.head
        
        while current is not None:
            if start_date <= current.created_at <= end_date:
                result.append(current)
            current = current.next
        
        return result
    
    def get_total_revenue(self) -> float:
        """
        Calcula el ingreso total de todos los pedidos.
        
        Returns:
            Suma del total de todos los pedidos
        """
        total = 0.0
        current = self.head
        
        while current is not None:
            total += current.total
            current = current.next
        
        return round(total, 2)
    
    def get_revenue_by_status(self, status: OrderStatus) -> float:
        """
        Calcula el ingreso de pedidos con un estado específico.
        
        Args:
            status: Estado a considerar
        
        Returns:
            Suma del total de pedidos con ese estado
        """
        total = 0.0
        current = self.head
        
        while current is not None:
            if current.status == status:
                total += current.total
            current = current.next
        
        return round(total, 2)
    
    def is_empty(self) -> bool:
        """Verifica si la lista está vacía."""
        return self.head is None
    
    def get_size(self) -> int:
        """Retorna el número de pedidos en la lista."""
        return self.size
    
    def clear(self):
        """Elimina todos los pedidos de la lista."""
        self.head = None
        self.tail = None
        self.size = 0
    
    def reverse(self):
        """
        Invierte el orden de la lista.
        
        Complexity: O(n)
        """
        if self.head is None or self.head.next is None:
            return
        
        prev = None
        current = self.head
        self.tail = self.head  # El head actual se convertirá en tail
        
        while current is not None:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        
        self.head = prev
    
    def __len__(self) -> int:
        return self.size
    
    def __iter__(self):
        """Permite iterar sobre la lista."""
        current = self.head
        while current is not None:
            yield current
            current = current.next
    
    def __str__(self) -> str:
        if self.is_empty():
            return "LinkedList(empty)"
        
        order_ids = [order.order_id for order in self.get_all()]
        return f"LinkedList(size={self.size}, orders={order_ids})"
    
    def __repr__(self) -> str:
        return self.__str__()
