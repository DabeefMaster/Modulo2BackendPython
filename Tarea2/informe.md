# Informe de la tarea: Sistema de Gestión de Pedidos (FastAPI)

## 1. Objetivo general
Construir una API de pedidos para una tienda en línea, apoyada en estructuras de datos clásicas para demostrar eficiencia y claridad didáctica. La API expone CRUD de productos y pedidos, valida stock y devuelve métricas de negocio.

## 2. Estructuras de datos y motivos
- **Binary Search Tree (BST) para productos**: mantiene los productos ordenados por `product_id`, facilita búsquedas y listados in-order sin base de datos. Complejidad promedio O(log n) en insertar/buscar.
  ```py
  # src/data_structures/binary_search_tree.py (validación e inserción)
  if product_id <= 0:
      raise ValueError("El product_id debe ser mayor que 0")
  ...
  if self.root is None:
      self.root = new_node
      self.size += 1
      return True
  ```
- **Lista enlazada simple para pedidos**: inserción O(1) con tail y recorrido secuencial natural, adecuada para flujos continuos de creación de pedidos sin índices aleatorios.
- **Servicios como capa de orquestación**: `ProductService` envuelve el BST y `OrderService` la lista enlazada; ambos coordinan validaciones y ajustes de stock.

### Esquema visual de estructuras
```
BST de productos (ordenado por product_id)
           [5]
          /   \
       [2]    [8]
      /  \      \
    [1]  [3]    [10]

Lista enlazada de pedidos
HEAD -> (ORD000001) -> (ORD000002) -> (ORD000003) -> None
```

## 3. Colaboración entre estructuras
- Validación de disponibilidad antes de crear pedido (consulta al BST):
  ```py
  is_valid, error_msg, product = self.product_service.validate_product_availability(
      product_id, quantity
  )
  if not is_valid:
      raise ValueError(error_msg)
  ```
- Creación de pedido: se generan snapshots de producto en los `OrderItem` y se descuenta stock en el BST:
  ```py
  order_item = OrderItem(..., unit_price=product.price)
  self.product_service.update_stock(product.product_id, -quantity)
  ```
- Eliminación de pedido: recorre la lista enlazada y restaura el stock en el BST antes de borrar:
  ```py
  for item in order.items:
      self.product_service.update_stock(item.product_id, item.quantity)
  ```

### Flujo visual (pedido)
```
1) Cliente envía POST /orders con items:
   items: [{product_id=5, qty=2}, {product_id=2, qty=1}]

2) OrderService valida en BST:
   search(5) -> nodo OK, stock suficiente
   search(2) -> nodo OK, stock suficiente

3) Descuenta stock en BST y crea OrderItems (snapshot):
   stock[5] -= 2, stock[2] -= 1

4) Inserta OrderNode al final de la lista:
   HEAD -> (ORD000001) -> None
```

## 4. Endpoints principales
- **Productos (`/api/products`)**: crear, consultar por ID, listar, filtros (`in-stock`, rango de precio), actualización total/parcial, `PATCH` de stock y estadísticas.
- **Pedidos (`/api/orders`)**: crear (valida stock), consultar, listar, `PATCH` de estado, actualización completa, filtros por estado/cliente, estadísticas y eliminación con restauración de stock.
- **Sistema**: `/health` y `/info` para monitorización básica.

## 4 bis. Serialización / deserialización (JSON en disco)
- Persistencia activada en `data/products.json` y `data/orders.json`.
- **Carga al iniciar los servicios**:
  ```py
  with open(self.storage_path, "r", encoding="utf-8") as f:
      data = json.load(f)
  self.bst.insert(...)               # reconstruye nodos de producto
  OrderNode(... items=OrderItem...)  # reconstruye nodos de pedido
  ```
- **Guardado tras operaciones**:
  - Productos: crear/actualizar/patch stock/eliminar/limpiar → `ProductService._persist_products()`.
  - Pedidos: crear/actualizar estado/actualizar items/eliminar/limpiar → `OrderService._persist_orders()`.
- Se conserva `created_at`/`updated_at` en ISO 8601 en los JSON; al cargar se parsean con `datetime.fromisoformat`.
- El contador de órdenes se recalcula leyendo el sufijo numérico de los IDs ya guardados para no repetirlos.

### Diagrama de serialización
```
       API (FastAPI)
           |
     ProductService            OrderService
        |   ^                      |   ^
        v   |                      v   |
  BinarySearchTree          LinkedList de pedidos
        |                          |
        v                          v
 data/products.json        data/orders.json
   (persistencia)             (persistencia)
```

### Ejemplo de archivos JSON persistidos
`data/products.json`
```json
[
  {
    "product_id": 5,
    "name": "Laptop Demo",
    "price": 1200.0,
    "stock": 8,
    "description": "Equipo principal",
    "created_at": "2025-12-06T13:00:00.123456"
  },
  {
    "product_id": 8,
    "name": "Monitor Demo",
    "price": 420.0,
    "stock": 6,
    "description": "Pantalla 27",
    "created_at": "2025-12-06T13:00:05.654321"
  }
]
```

`data/orders.json`
```json
[
  {
    "order_id": "ORD000001",
    "customer_name": "Cliente Demo",
    "items": [
      {"product_id": 5, "product_name": "Laptop Demo", "quantity": 2, "unit_price": 1200.0, "subtotal": 2400.0},
      {"product_id": 8, "product_name": "Monitor Demo", "quantity": 1, "unit_price": 420.0, "subtotal": 420.0}
    ],
    "total": 2820.0,
    "status": "pendiente",
    "created_at": "2025-12-06T13:02:10.000000",
    "updated_at": "2025-12-06T13:02:10.000000",
    "notes": "Pedido de prueba",
    "item_count": 2,
    "total_quantity": 3
  }
]
```

### Inserción en BST y append en lista
```
Insertar product_id=4 en BST:

    [5]
   /   \
 [2]   [8]
  \      \
 [3]    [10]
  \
  [4]   <-- nuevo nodo (4 > 3, va a la derecha de 3)

Append de pedido en lista:
HEAD -> (ORD000001) -> (ORD000002 nuevo) -> None
           ^tail antes            ^tail después
```

## 5. Lógica de negocio destacada
- Generación determinista de IDs de pedido:
  ```py
  def _generate_order_id(self) -> str:
      self.order_counter += 1
      return f"ORD{self.order_counter:06d}"
  ```
- Actualización de pedido en dos fases: valida y reserva stock antes de aplicar cambios; si algo falla, restaura para evitar inconsistencias.
- Estadísticas en memoria (productos y pedidos) para feedback rápido sin dependencias externas.

## 6. Persistencia y ejecución
Datos en memoria; las rutas de `./data` están preparadas en `.env`, pero esta versión no persiste en disco. Arranque típico:
```bash
python main.py
# o
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 7. Pruebas automáticas incluidas
- **Runner conservado:** `test_api_automatic.py`.
- **Modo de ejecución:** secuencial con sesión HTTP compartida y pausa configurable para no sobrecargar el servidor.
- **Cobertura:** health/info, creación/actualización de productos, filtros, estadísticas, flujo completo de pedido (crear, cambiar estado, actualizar items, filtrar, estadísticas), validaciones de error (ID duplicado, precio negativo, pedido sin stock) y verificación de restauración de stock al eliminar el pedido.
- **Limpieza:** elimina productos y pedidos creados al finalizar para dejar el sistema limpio.

## 8. Conclusión
- La combinación BST + lista enlazada resuelve catálogo ordenado + flujo secuencial de pedidos con complejidad razonable (O(log n) promedio en productos, O(1) inserción pedidos).
- La serialización JSON asegura que los datos sobrevivan reinicios sin depender de BD externa, manteniendo `created_at`/`updated_at` y el contador de órdenes.
- Los servicios separan reglas de negocio de las estructuras y ofrecen puntos únicos de persistencia; esto simplifica mantener consistencia de stock.
- El runner automático cubre el ciclo completo sin concurrencia agresiva, útil para validar regresiones tras cambios.
- Observación: si el volumen creciera, habría que sustituir BST/lista enlazada por estructuras persistentes (BD) o balancear el árbol; para el alcance docente, la solución es clara y suficiente.
