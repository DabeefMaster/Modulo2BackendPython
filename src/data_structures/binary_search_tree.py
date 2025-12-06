"""
Árbol Binario de Búsqueda (BST) para gestión de productos.

Este módulo implementa un BST donde cada nodo representa un producto,
utilizando el product_id como clave de búsqueda para operaciones eficientes.

Complejidad temporal:
- Búsqueda: O(log n) promedio, O(n) peor caso
- Inserción: O(log n) promedio, O(n) peor caso
- Recorrido completo: O(n)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime


class ProductNode:
    """
    Nodo del árbol que representa un producto.
    
    Attributes:
        product_id (int): Identificador único del producto (clave de búsqueda)
        name (str): Nombre del producto
        price (float): Precio del producto
        stock (int): Cantidad disponible en inventario
        description (str): Descripción opcional del producto
        created_at (datetime): Fecha de creación del producto
        left (ProductNode): Hijo izquierdo (productos con ID menor)
        right (ProductNode): Hijo derecho (productos con ID mayor)
    """
    
    def __init__(
        self,
        product_id: int,
        name: str,
        price: float,
        stock: int,
        description: str = ""
    ):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock
        self.description = description
        self.created_at = datetime.now()
        self.left: Optional[ProductNode] = None
        self.right: Optional[ProductNode] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el nodo a un diccionario para serialización JSON.
        
        Returns:
            Dict con los datos del producto
        """
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }
    
    def __str__(self) -> str:
        return f"Product(id={self.product_id}, name={self.name}, price={self.price}, stock={self.stock})"
    
    def __repr__(self) -> str:
        return self.__str__()


class BinarySearchTree:
    """
    Árbol Binario de Búsqueda para almacenar productos de forma ordenada.
    
    El árbol mantiene los productos ordenados por product_id, permitiendo
    búsquedas, inserciones y eliminaciones eficientes.
    
    Attributes:
        root (ProductNode): Nodo raíz del árbol
        size (int): Número de productos en el árbol
    """
    
    def __init__(self):
        self.root: Optional[ProductNode] = None
        self.size: int = 0
    
    def insert(
        self,
        product_id: int,
        name: str,
        price: float,
        stock: int,
        description: str = ""
    ) -> bool:
        """
        Inserta un nuevo producto en el árbol.
        
        Args:
            product_id: ID único del producto
            name: Nombre del producto
            price: Precio del producto
            stock: Cantidad en inventario
            description: Descripción opcional
        
        Returns:
            True si la inserción fue exitosa, False si el ID ya existe
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validaciones
        if product_id <= 0:
            raise ValueError("El product_id debe ser mayor que 0")
        if price < 0:
            raise ValueError("El precio no puede ser negativo")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo")
        if not name or not name.strip():
            raise ValueError("El nombre del producto no puede estar vacío")
        
        # Crear nuevo nodo
        new_node = ProductNode(product_id, name.strip(), price, stock, description)
        
        # Si el árbol está vacío, el nuevo nodo es la raíz
        if self.root is None:
            self.root = new_node
            self.size += 1
            return True
        
        # Insertar recursivamente
        if self._insert_recursive(self.root, new_node):
            self.size += 1
            return True
        
        return False
    
    def _insert_recursive(self, current: ProductNode, new_node: ProductNode) -> bool:
        """
        Método auxiliar recursivo para insertar un nodo.
        
        Args:
            current: Nodo actual en el recorrido
            new_node: Nodo a insertar
        
        Returns:
            True si se insertó, False si el ID ya existe
        """
        # Si el ID ya existe, no insertamos (no permitimos duplicados)
        if new_node.product_id == current.product_id:
            return False
        
        # Si el ID es menor, ir al subárbol izquierdo
        if new_node.product_id < current.product_id:
            if current.left is None:
                current.left = new_node
                return True
            else:
                return self._insert_recursive(current.left, new_node)
        
        # Si el ID es mayor, ir al subárbol derecho
        else:
            if current.right is None:
                current.right = new_node
                return True
            else:
                return self._insert_recursive(current.right, new_node)
    
    def search(self, product_id: int) -> Optional[ProductNode]:
        """
        Busca un producto por su ID.
        
        Args:
            product_id: ID del producto a buscar
        
        Returns:
            ProductNode si se encuentra, None si no existe
        
        Complexity: O(log n) promedio, O(n) peor caso
        """
        return self._search_recursive(self.root, product_id)
    
    def _search_recursive(self, current: Optional[ProductNode], product_id: int) -> Optional[ProductNode]:
        """
        Método auxiliar recursivo para buscar un nodo.
        
        Args:
            current: Nodo actual en el recorrido
            product_id: ID a buscar
        
        Returns:
            ProductNode si se encuentra, None si no existe
        """
        # Caso base: nodo vacío o encontrado
        if current is None or current.product_id == product_id:
            return current
        
        # Si el ID buscado es menor, buscar en el subárbol izquierdo
        if product_id < current.product_id:
            return self._search_recursive(current.left, product_id)
        
        # Si el ID buscado es mayor, buscar en el subárbol derecho
        return self._search_recursive(current.right, product_id)
    
    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """
        Actualiza el stock de un producto.
        
        Args:
            product_id: ID del producto
            quantity_change: Cambio en el stock (positivo para aumentar, negativo para disminuir)
        
        Returns:
            True si se actualizó correctamente, False si el producto no existe
        
        Raises:
            ValueError: Si el stock resultante es negativo
        """
        product = self.search(product_id)
        
        if product is None:
            return False
        
        new_stock = product.stock + quantity_change
        
        if new_stock < 0:
            raise ValueError(f"Stock insuficiente. Stock actual: {product.stock}, cambio solicitado: {quantity_change}")
        
        product.stock = new_stock
        return True
    
    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        stock: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Actualiza los datos de un producto.
        
        Args:
            product_id: ID del producto a actualizar
            name: Nuevo nombre (opcional)
            price: Nuevo precio (opcional)
            stock: Nuevo stock (opcional)
            description: Nueva descripción (opcional)
        
        Returns:
            True si se actualizó, False si el producto no existe
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        product = self.search(product_id)
        
        if product is None:
            return False
        
        # Validaciones
        if name is not None:
            if not name or not name.strip():
                raise ValueError("El nombre no puede estar vacío")
            product.name = name.strip()
        
        if price is not None:
            if price < 0:
                raise ValueError("El precio no puede ser negativo")
            product.price = price
        
        if stock is not None:
            if stock < 0:
                raise ValueError("El stock no puede ser negativo")
            product.stock = stock
        
        if description is not None:
            product.description = description
        
        return True
    
    def delete(self, product_id: int) -> bool:
        """
        Elimina un producto del árbol.
        
        Args:
            product_id: ID del producto a eliminar
        
        Returns:
            True si se eliminó, False si no existe
        """
        if self.root is None:
            return False
        
        self.root, deleted = self._delete_recursive(self.root, product_id)
        
        if deleted:
            self.size -= 1
        
        return deleted
    
    def _delete_recursive(self, current: Optional[ProductNode], product_id: int) -> tuple[Optional[ProductNode], bool]:
        """
        Método auxiliar recursivo para eliminar un nodo.
        
        Args:
            current: Nodo actual en el recorrido
            product_id: ID del producto a eliminar
        
        Returns:
            Tupla (nuevo nodo en esta posición, si se eliminó)
        """
        if current is None:
            return None, False
        
        # Buscar el nodo a eliminar
        if product_id < current.product_id:
            current.left, deleted = self._delete_recursive(current.left, product_id)
            return current, deleted
        
        elif product_id > current.product_id:
            current.right, deleted = self._delete_recursive(current.right, product_id)
            return current, deleted
        
        # Nodo encontrado, proceder con la eliminación
        else:
            # Caso 1: Nodo sin hijos (hoja)
            if current.left is None and current.right is None:
                return None, True
            
            # Caso 2: Nodo con un solo hijo
            if current.left is None:
                return current.right, True
            
            if current.right is None:
                return current.left, True
            
            # Caso 3: Nodo con dos hijos
            # Encontrar el sucesor in-order (mínimo del subárbol derecho)
            successor = self._find_min(current.right)
            
            # Copiar los datos del sucesor al nodo actual
            current.product_id = successor.product_id
            current.name = successor.name
            current.price = successor.price
            current.stock = successor.stock
            current.description = successor.description
            current.created_at = successor.created_at
            
            # Eliminar el sucesor
            current.right, _ = self._delete_recursive(current.right, successor.product_id)
            
            return current, True
    
    def _find_min(self, node: ProductNode) -> ProductNode:
        """
        Encuentra el nodo con el valor mínimo en un subárbol.
        
        Args:
            node: Raíz del subárbol
        
        Returns:
            Nodo con el valor mínimo
        """
        current = node
        while current.left is not None:
            current = current.left
        return current
    
    def inorder_traversal(self) -> List[ProductNode]:
        """
        Recorrido in-order del árbol (devuelve productos ordenados por ID).
        
        Returns:
            Lista de productos en orden ascendente por ID
        
        Complexity: O(n)
        """
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[ProductNode], result: List[ProductNode]):
        """
        Método auxiliar recursivo para recorrido in-order.
        
        Args:
            node: Nodo actual
            result: Lista donde se acumulan los resultados
        """
        if node is not None:
            self._inorder_recursive(node.left, result)
            result.append(node)
            self._inorder_recursive(node.right, result)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos como diccionarios (para serialización).
        
        Returns:
            Lista de diccionarios con los datos de todos los productos
        """
        nodes = self.inorder_traversal()
        return [node.to_dict() for node in nodes]
    
    def get_products_by_price_range(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """
        Obtiene productos dentro de un rango de precios.
        
        Args:
            min_price: Precio mínimo
            max_price: Precio máximo
        
        Returns:
            Lista de productos en el rango especificado
        """
        all_products = self.inorder_traversal()
        filtered = [
            node.to_dict() 
            for node in all_products 
            if min_price <= node.price <= max_price
        ]
        return filtered
    
    def get_products_in_stock(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos que tienen stock disponible.
        
        Returns:
            Lista de productos con stock > 0
        """
        all_products = self.inorder_traversal()
        return [node.to_dict() for node in all_products if node.stock > 0]
    
    def is_empty(self) -> bool:
        """Verifica si el árbol está vacío."""
        return self.root is None
    
    def get_size(self) -> int:
        """Retorna el número de productos en el árbol."""
        return self.size
    
    def clear(self):
        """Elimina todos los productos del árbol."""
        self.root = None
        self.size = 0
    
    def __len__(self) -> int:
        return self.size
    
    def __str__(self) -> str:
        if self.is_empty():
            return "BinarySearchTree(empty)"
        
        products = self.inorder_traversal()
        product_ids = [p.product_id for p in products]
        return f"BinarySearchTree(size={self.size}, ids={product_ids})"
    
    def __repr__(self) -> str:
        return self.__str__()
