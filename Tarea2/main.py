"""
Punto de entrada principal de la aplicación FastAPI.

Sistema de Gestión de Pedidos para tienda en línea.
Utiliza estructuras de datos avanzadas (BST para productos, Lista Enlazada para pedidos).
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.routes import products, orders
import os


# Crear directorio de datos si no existe
os.makedirs(settings.data_dir, exist_ok=True)


# Metadatos para la documentación
tags_metadata = [
    {
        "name": "Productos",
        "description": """
        Operaciones para gestionar productos utilizando un **Árbol Binario de Búsqueda (BST)**.
        
        ### Características de la estructura BST:
        - **Complejidad de búsqueda**: O(log n) en promedio
        - **Ordenamiento**: Los productos están ordenados por ID
        - **Operaciones soportadas**: Inserción, búsqueda, actualización, eliminación
        
        ### Funcionalidades disponibles:
        - Crear productos con validación de unicidad de ID
        - Buscar productos por ID de forma eficiente
        - Listar todos los productos ordenados
        - Filtrar por stock disponible
        - Filtrar por rango de precios
        - Actualizar información y stock
        - Eliminar productos
        - Obtener estadísticas del inventario
        """,
    },
    {
        "name": "Pedidos",
        "description": """
        Operaciones para gestionar pedidos utilizando una **Lista Enlazada Simple**.
        
        ### Características de la estructura Lista Enlazada:
        - **Complejidad de inserción**: O(1) con puntero tail
        - **Gestión flexible**: Inserción y eliminación eficientes
        - **Relación con productos**: Cada pedido contiene referencias a productos del BST
        
        ### Funcionalidades disponibles:
        - Crear pedidos con validación automática de stock
        - Consultar pedidos con información detallada
        - Actualizar estado y contenido de pedidos
        - Eliminar pedidos con restauración de stock
        - Filtrar por estado (pendiente, procesando, enviado, entregado, cancelado)
        - Buscar por cliente
        - Obtener estadísticas e ingresos
        
        ### Sincronización con productos:
        Al crear un pedido, el stock se reduce automáticamente.
        Al eliminar o actualizar un pedido, el stock se ajusta en consecuencia.
        """,
    },
    {
        "name": "Sistema",
        "description": """
        Endpoints de información y monitoreo del sistema.
        
        Incluye health checks y metadatos sobre la arquitectura de datos.
        """,
    },
]


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
API de gestion de pedidos:
- Productos: CRUD, filtros (stock, precio) y estadisticas.
- Pedidos: crear con validacion de stock, consultar, listar, actualizar estado/items,
  eliminar con restauracion de stock y estadisticas.
Estructuras usadas: BST para productos y lista enlazada para pedidos.
""",

    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Sistema de Gestión de Pedidos",
        "url": "https://github.com/tu-usuario/tu-repo",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir routers
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")


# Endpoint raíz
@app.get("/", include_in_schema=False)
async def root():
    """Redirige a la documentación de la API."""
    return RedirectResponse(url="/docs")


# Endpoint de health check
@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Health check endpoint para verificar que la API está funcionando.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# Endpoint de información
@app.get("/info", tags=["Sistema"])
async def info():
    """
    Información sobre la API y las estructuras de datos utilizadas.
    """
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "description": "Sistema de gestión de pedidos con estructuras de datos avanzadas",
        "data_structures": {
            "products": {
                "type": "Binary Search Tree (BST)",
                "complexity": {
                    "search": "O(log n) average",
                    "insert": "O(log n) average",
                    "delete": "O(log n) average"
                },
                "description": "Árbol binario de búsqueda para almacenar productos ordenados por ID"
            },
            "orders": {
                "type": "Linked List (Simple)",
                "complexity": {
                    "append": "O(1) with tail pointer",
                    "search": "O(n)",
                    "delete": "O(n)"
                },
                "description": "Lista enlazada simple para gestionar pedidos con referencias a productos"
            }
        },
        "endpoints": {
            "products": "/api/products",
            "orders": "/api/orders",
            "documentation": "/docs"
        }
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Ejecutado al iniciar la aplicacion.
    """
    print(f"Iniciando {settings.app_name} v{settings.app_version}")
    print(f"Directorio de datos: {settings.data_dir}")
    print(f"Documentacion disponible en: http://{settings.host}:{settings.port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Ejecutado al cerrar la aplicacion.
    """
    print(f"Cerrando {settings.app_name}")

# Para ejecutar directamente con python main.py
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
