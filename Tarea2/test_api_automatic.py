"""
Pruebas automaticas end-to-end para la API del sistema de pedidos.

Caracteristicas:
- Usa solo peticiones secuenciales y un retardo configurable para no sobrecargar el servidor.
- Cubre flujos felices y casos de validacion basicos para productos y pedidos.
- Limpia los datos creados al finalizar.

Ejemplo de uso:
    python test_api_automatic.py --base-url http://localhost:8001/api --pause 0.15
"""

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class StepResult:
    name: str
    success: bool
    status: Optional[int]
    detail: str = ""


class ApiTestRunner:
    def __init__(self, base_url: str, pause: float = 0.2, timeout: int = 8) -> None:
        self.base_url = base_url.rstrip("/")
        self.root_url = (
            self.base_url[: -len("/api")] if self.base_url.endswith("/api") else self.base_url
        )
        self.health_url = f"{self.root_url}/health"
        self.info_url = f"{self.root_url}/info"
        self.pause = pause
        self.timeout = timeout
        self.session = requests.Session()
        self.results: List[StepResult] = []
        self.products_created: List[int] = []
        self.orders_created: List[str] = []
        self.stock_snapshot: Dict[int, int] = {}
        self.current_order_items: Dict[int, int] = {}

    # --------------------------- infra helpers --------------------------- #
    def _sleep(self) -> None:
        if self.pause > 0:
            time.sleep(self.pause)

    def _full_url(self, path: str) -> str:
        return path if path.startswith("http") else f"{self.base_url}{path}"

    def _send(self, method: str, path: str, **kwargs) -> Optional[requests.Response]:
        kwargs.setdefault("timeout", self.timeout)
        url = self._full_url(path)
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.RequestException as exc:  # network or timeout issues
            self.results.append(
                StepResult(
                    name=f"{method.upper()} {path}",
                    success=False,
                    status=None,
                    detail=f"Error de conexion: {exc}",
                )
            )
            print(f"[FAIL] {method.upper()} {path} -> {exc}")
            self._sleep()
            return None
        self._sleep()
        return response

    def _record(self, name: str, response: Optional[requests.Response], success: bool, note: str = "") -> None:
        status = response.status_code if response is not None else None
        detail = note or ""
        if response is not None and not success and not note:
            try:
                detail = json.dumps(response.json(), ensure_ascii=False)
            except Exception:
                detail = response.text
        self.results.append(StepResult(name=name, success=success, status=status, detail=detail))
        label = "OK" if success else "FAIL"
        extra = f" [{detail[:120]}]" if detail else ""
        print(f"[{label}] {name} (status: {status}){extra}")

    def _perform(
        self,
        name: str,
        method: str,
        path: str,
        expected: Optional[int] = None,
        allowed: Optional[List[int]] = None,
        note: str = "",
        **kwargs,
    ) -> Optional[requests.Response]:
        response = self._send(method, path, **kwargs)
        if response is None:
            self._record(name, None, False, note or "Sin respuesta del servidor")
            return None
        allowed = allowed or []
        success = False
        if expected is not None:
            success = response.status_code == expected
        elif allowed:
            success = response.status_code in allowed
        else:
            success = response.ok
        self._record(name, response, success, note)
        return response

    # --------------------------- test suites --------------------------- #
    def check_system(self) -> None:
        print("\n== Verificando health/info ==")
        self._perform("Health check", "get", self.health_url, expected=200)
        self._perform("Info de sistema", "get", self.info_url, expected=200)

    def create_products(self) -> None:
        print("\n== Creando productos base ==")
        base_id = int(time.time()) % 80000 + 1000
        catalog = [
            {"product_id": base_id + 1, "name": "Laptop Demo", "price": 1200.0, "stock": 8, "description": "Equipo principal"},
            {"product_id": base_id + 2, "name": "Mouse Demo", "price": 35.5, "stock": 20, "description": "Periferico"},
            {"product_id": base_id + 3, "name": "Monitor Demo", "price": 420.0, "stock": 6, "description": "Pantalla 27"},
            {"product_id": base_id + 4, "name": "Producto Stock Limitado", "price": 15.0, "stock": 1, "description": "Para validar errores de stock"},
        ]
        for product in catalog:
            resp = self._perform(
                f"Crear producto {product['product_id']}",
                "post",
                "/products",
                json=product,
                expected=201,
            )
            if resp and resp.status_code == 201:
                data = resp.json()
                product_id = data["product_id"]
                self.products_created.append(product_id)
                self.stock_snapshot[product_id] = data["stock"]

        # Intento duplicado
        dup_payload = catalog[0].copy()
        self._perform(
            "Rechazar producto duplicado",
            "post",
            "/products",
            json=dup_payload,
            allowed=[400],
            note="Debe devolver 400 por ID duplicado",
        )

        # Payload invalido (precio negativo) -> valida 400 o 422 segun la capa
        invalid_payload = catalog[1].copy()
        invalid_payload["product_id"] = catalog[1]["product_id"] + 1000
        invalid_payload["price"] = -10
        self._perform(
            "Rechazar producto invalido",
            "post",
            "/products",
            json=invalid_payload,
            allowed=[400, 422],
            note="Precio negativo debe ser rechazado",
        )

    def product_queries(self) -> None:
        print("\n== Consultas y actualizaciones de productos ==")
        if len(self.products_created) < 3:
            self._record("Preparacion de productos insuficiente", None, False, note="No hay datos para probar productos")
            return
        primary_id = self.products_created[0]
        monitor_id = self.products_created[2]

        self._perform("Obtener producto principal", "get", f"/products/{primary_id}", expected=200)
        self._perform("Listar todos los productos", "get", "/products", expected=200)
        self._perform("Productos con stock", "get", "/products/filter/in-stock", expected=200)
        self._perform(
            "Productos en rango de precio",
            "get",
            "/products/filter/price-range",
            params={"min_price": 10, "max_price": 500},
            expected=200,
        )

        update_payload = {"price": 1100.0, "stock": 10}
        resp = self._perform(
            "Actualizar producto principal",
            "put",
            f"/products/{primary_id}",
            json=update_payload,
            expected=200,
        )
        if resp and resp.ok:
            data = resp.json()
            self.stock_snapshot[primary_id] = data["stock"]

        # Ajustar stock del monitor para probar PATCH
        stock_delta = -1
        resp = self._perform(
            "Ajustar stock monitor",
            "patch",
            f"/products/{monitor_id}/stock",
            json={"quantity_change": stock_delta},
            expected=200,
        )
        if resp and resp.ok:
            self.stock_snapshot[monitor_id] += stock_delta

        self._perform("Estadisticas de productos", "get", "/products/stats/summary", expected=200)

    def order_flow(self) -> None:
        print("\n== Flujos de pedidos ==")
        if len(self.products_created) < 4:
            self._record("Preparacion de productos insuficiente", None, False, note="Faltan productos para probar pedidos")
            return
        primary_id, mouse_id, limited_id = (
            self.products_created[0],
            self.products_created[1],
            self.products_created[3],
        )

        order_payload = {
            "customer_name": "Cliente Demo",
            "items": [
                {"product_id": primary_id, "quantity": 2},
                {"product_id": mouse_id, "quantity": 3},
            ],
            "notes": "Pedido de prueba automatica",
        }
        resp = self._perform("Crear pedido valido", "post", "/orders", json=order_payload, expected=201)
        if resp and resp.status_code == 201:
            order = resp.json()
            order_id = order["order_id"]
            self.orders_created.append(order_id)
            self.current_order_items = {item["product_id"]: item["quantity"] for item in order["items"]}
            # reflejar stock descontado
            for pid, qty in self.current_order_items.items():
                self.stock_snapshot[pid] -= qty

        if not self.orders_created:
            return

        order_id = self.orders_created[0]
        self._perform("Obtener pedido completo", "get", f"/orders/{order_id}", expected=200)
        self._perform("Listar pedidos", "get", "/orders", expected=200)
        self._perform(
            "Actualizar estado a procesando",
            "patch",
            f"/orders/{order_id}/status",
            json={"status": "procesando"},
            expected=200,
        )

        # Actualizacion completa con nuevas cantidades
        updated_items = [
            {"product_id": primary_id, "quantity": 1},
            {"product_id": mouse_id, "quantity": 4},
        ]
        resp = self._perform(
            "Actualizar items del pedido",
            "put",
            f"/orders/{order_id}",
            json={"items": updated_items, "notes": "Ajuste de cantidades"},
            expected=200,
        )
        if resp and resp.ok:
            new_items = {item["product_id"]: item["quantity"] for item in resp.json()["items"]}
            for pid, new_qty in new_items.items():
                old_qty = self.current_order_items.get(pid, 0)
                self.stock_snapshot[pid] += old_qty - new_qty
            self.current_order_items = new_items

        self._perform("Pedidos por estado procesando", "get", "/orders/filter/status/procesando", expected=200)
        self._perform("Pedidos por cliente parcial", "get", "/orders/filter/customer/demo", expected=200)
        self._perform("Estadisticas de pedidos", "get", "/orders/stats/summary", expected=200)

        # Pedido invalido por falta de stock
        self._perform(
            "Rechazar pedido sin stock suficiente",
            "post",
            "/orders",
            json={
                "customer_name": "Cliente Sin Stock",
                "items": [{"product_id": limited_id, "quantity": 5}],
            },
            allowed=[400],
            note="Stock limitado debe generar 400",
        )

        # Eliminar pedido y verificar restauracion de stock
        self._perform("Eliminar pedido", "delete", f"/orders/{order_id}", expected=204)
        for pid, qty in self.current_order_items.items():
            self.stock_snapshot[pid] += qty
        self.orders_created.clear()
        self.current_order_items = {}

        # Confirmar stock restaurado
        for pid, expected_stock in self.stock_snapshot.items():
            resp = self._perform(
                f"Verificar stock restaurado producto {pid}",
                "get",
                f"/products/{pid}",
                expected=200,
            )
            if resp and resp.ok:
                real_stock = resp.json()["stock"]
                ok = real_stock == expected_stock
                self._record(
                    f"Stock esperado {expected_stock} para producto {pid}",
                    resp,
                    success=ok,
                    note="" if ok else f"Stock devuelto {real_stock}",
                )

    def cleanup_products(self) -> None:
        if not self.products_created:
            return
        print("\n== Limpieza de productos creados ==")
        for pid in self.products_created:
            self._perform(f"Eliminar producto {pid}", "delete", f"/products/{pid}", expected=204)
        self.products_created.clear()

    # --------------------------- runner --------------------------- #
    def run(self) -> None:
        print(f"Iniciando pruebas contra {self.base_url}")
        try:
            self.check_system()
            self.create_products()
            self.product_queries()
            self.order_flow()
        finally:
            self.cleanup_products()
            self.summary()

    def summary(self) -> None:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        print("\n== Resumen ==")
        print(f"Pasados: {passed}/{total}")
        failures = [r for r in self.results if not r.success]
        for item in failures:
            detail = f" | {item.detail}" if item.detail else ""
            print(f"- {item.name} (status: {item.status}){detail}")
        if failures:
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner de pruebas secuenciales para la API")
    parser.add_argument("--base-url", default="http://localhost:8001/api", help="URL base de la API (por defecto http://localhost:8001/api)")
    parser.add_argument("--pause", type=float, default=0.2, help="Segundos de espera entre llamadas (default 0.2)")
    parser.add_argument("--timeout", type=int, default=8, help="Timeout por peticion en segundos")
    args = parser.parse_args()

    runner = ApiTestRunner(base_url=args.base_url, pause=args.pause, timeout=args.timeout)
    runner.run()


if __name__ == "__main__":
    main()
