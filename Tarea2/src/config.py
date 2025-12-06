"""
Configuración de la aplicación.

Carga variables de entorno y define configuraciones globales.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings.
    
    Las variables se cargan desde el archivo .env o desde variables de entorno del sistema.
    """
    
    # Información de la aplicación
    app_name: str = "Sistema de Gestión de Pedidos"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Configuración del servidor
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Configuración de persistencia
    data_dir: str = "./data"
    products_file: str = "products.json"
    orders_file: str = "orders.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def products_file_path(self) -> str:
        """Ruta completa al archivo de productos."""
        return os.path.join(self.data_dir, self.products_file)
    
    @property
    def orders_file_path(self) -> str:
        """Ruta completa al archivo de pedidos."""
        return os.path.join(self.data_dir, self.orders_file)


# Instancia global de configuración
settings = Settings()
