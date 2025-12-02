import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from fastapi.testclient import TestClient

# Permite ejecutar desde la raiz del repo
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def load_env(env_path: Path):
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if line.strip() and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


class TestRunner:
    def __init__(self, client: TestClient):
        self.client = client
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        
    def assert_equal(self, actual, expected, message=""):
        """Verifica que dos valores sean iguales"""
        if actual == expected:
            return True
        raise AssertionError(f"{message}: esperado {expected}, obtenido {actual}")
    
    def assert_in(self, value, container, message=""):
        """Verifica que un valor esté en un contenedor"""
        if value in container:
            return True
        raise AssertionError(f"{message}: {value} no está en {container}")
    
    def assert_status(self, response, expected_status, message=""):
        """Verifica el código de estado"""
        if response.status_code == expected_status:
            return True
        raise AssertionError(f"{message}: esperado status {expected_status}, obtenido {response.status_code}. Body: {response.json()}")
    
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Registra el resultado de un test"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"      └─ {details}")
        
        self.test_results.append({
            "test": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def run_test(self, name: str, test_func):
        """Ejecuta un test y registra el resultado"""
        try:
            result = test_func()
            self.log_test(name, True, result if isinstance(result, str) else "")
            return True
        except AssertionError as e:
            self.log_test(name, False, str(e))
            return False
        except Exception as e:
            self.log_test(name, False, f"Error inesperado: {str(e)}")
            return False
    
    def print_summary(self):
        """Imprime el resumen de tests"""
        total = self.tests_passed + self.tests_failed
        print("\n" + "="*60)
        print(f"RESUMEN DE TESTS")
        print("="*60)
        print(f"Total: {total} | Pasados: {self.tests_passed} | Fallados: {self.tests_failed}")
        print(f"Tasa de éxito: {(self.tests_passed/total*100):.1f}%" if total > 0 else "N/A")
        print("="*60)


def main():
    load_env(ROOT / ".env")
    
    from app.main import app  # import despues de cargar env
    
    client = TestClient(app)
    runner = TestRunner(client)
    
    # Variables para los tests
    username = "ProbadorSmoke"
    email = "tester_smoke@example.com"
    edad = 30
    canciones = ["Shape of You", "Blinding Lights"]
    user_id = None
    
    print("\n" + "="*60)
    print("INICIANDO SUITE DE TESTS COMPLETA")
    print("="*60 + "\n")
    
    try:
        # ==================== TESTS DE VALIDACIÓN ====================
        print("\n--- TESTS DE VALIDACIÓN DE DATOS ---\n")
        
        # Test: Email inválido
        def test_email_invalido():
            resp = client.post("/usuarios/", json={"nombre": "Test", "email": "invalido", "edad": 25})
            runner.assert_status(resp, 422, "Email inválido debe retornar 422")
            return "Email inválido rechazado correctamente"
        runner.run_test("Validación email inválido", test_email_invalido)
        
        # Test: Edad fuera de rango (menor)
        def test_edad_menor():
            resp = client.post("/usuarios/", json={"nombre": "Test", "email": "test@test.com", "edad": 10})
            runner.assert_status(resp, 422, "Edad < 13 debe retornar 422")
            return "Edad menor a 13 rechazada"
        runner.run_test("Validación edad menor a 13", test_edad_menor)
        
        # Test: Edad fuera de rango (mayor)
        def test_edad_mayor():
            resp = client.post("/usuarios/", json={"nombre": "Test", "email": "test@test.com", "edad": 150})
            runner.assert_status(resp, 422, "Edad > 120 debe retornar 422")
            return "Edad mayor a 120 rechazada"
        runner.run_test("Validación edad mayor a 120", test_edad_mayor)
        
        # Test: Nombre muy corto
        def test_nombre_corto():
            resp = client.post("/usuarios/", json={"nombre": "Ab", "email": "test@test.com", "edad": 25})
            runner.assert_status(resp, 422, "Nombre < 3 caracteres debe retornar 422")
            return "Nombre corto rechazado"
        runner.run_test("Validación nombre muy corto", test_nombre_corto)
        
        # ==================== TESTS DE CREACIÓN ====================
        print("\n--- TESTS DE CREACIÓN DE USUARIO ---\n")
        
        # Test: Crear usuario válido
        def test_crear_usuario():
            nonlocal user_id
            resp = client.post("/usuarios/", json={"nombre": username, "email": email, "edad": edad})
            runner.assert_status(resp, 201, "Crear usuario debe retornar 201")
            data = resp.json()
            runner.assert_in("id", data, "Respuesta debe contener ID")
            runner.assert_equal(data["nombre"], username, "Nombre debe coincidir")
            runner.assert_equal(data["email"], email, "Email debe coincidir")
            runner.assert_equal(data["edad"], edad, "Edad debe coincidir")
            runner.assert_in("playlist_id", data, "Usuario debe tener playlist_id")
            user_id = data["id"]
            return f"Usuario creado con ID={user_id} y playlist_id={data['playlist_id']}"
        runner.run_test("Crear usuario válido", test_crear_usuario)
        
        if user_id is None:
            print("\n⚠ No se pudo crear el usuario, abortando tests restantes")
            runner.print_summary()
            return
        
        # Test: Email duplicado
        def test_email_duplicado():
            resp = client.post("/usuarios/", json={"nombre": "OtroNombre", "email": email, "edad": 25})
            runner.assert_status(resp, 400, "Email duplicado debe retornar 400")
            data = resp.json()
            runner.assert_in("detail", data, "Debe incluir detalle del error")
            return "Email duplicado rechazado correctamente"
        runner.run_test("Rechazar email duplicado", test_email_duplicado)
        
        # Test: Nombre duplicado
        def test_nombre_duplicado():
            resp = client.post("/usuarios/", json={"nombre": username, "email": "otro@email.com", "edad": 25})
            runner.assert_status(resp, 400, "Nombre duplicado debe retornar 400")
            return "Nombre duplicado rechazado correctamente"
        runner.run_test("Rechazar nombre duplicado", test_nombre_duplicado)
        
        # ==================== TESTS DE LECTURA ====================
        print("\n--- TESTS DE LECTURA DE USUARIOS ---\n")
        
        # Test: Listar usuarios
        def test_listar_usuarios():
            resp = client.get("/usuarios")
            runner.assert_status(resp, 200, "Listar usuarios debe retornar 200")
            data = resp.json()
            runner.assert_in(user_id, [u["id"] for u in data], "Usuario creado debe estar en la lista")
            return f"Lista contiene {len(data)} usuarios"
        runner.run_test("Listar todos los usuarios", test_listar_usuarios)
        
        # Test: Obtener usuario por ID
        def test_obtener_por_id():
            resp = client.get(f"/usuarios/{user_id}")
            runner.assert_status(resp, 200, "Obtener por ID debe retornar 200")
            data = resp.json()
            runner.assert_equal(data["id"], user_id, "ID debe coincidir")
            return f"Usuario {data['nombre']} obtenido correctamente"
        runner.run_test("Obtener usuario por ID", test_obtener_por_id)
        
        # Test: Obtener usuario por nombre
        def test_obtener_por_nombre():
            resp = client.get(f"/usuarios/{username}")
            runner.assert_status(resp, 200, "Obtener por nombre debe retornar 200")
            data = resp.json()
            runner.assert_equal(data["nombre"], username, "Nombre debe coincidir")
            return "Usuario obtenido por nombre"
        runner.run_test("Obtener usuario por nombre", test_obtener_por_nombre)
        
        # Test: Usuario inexistente
        def test_usuario_inexistente():
            resp = client.get("/usuarios/99999")
            runner.assert_status(resp, 404, "Usuario inexistente debe retornar 404")
            data = resp.json()
            runner.assert_in("detail", data, "Debe incluir detalle del error")
            return "Error 404 con detalles descriptivos"
        runner.run_test("Buscar usuario inexistente", test_usuario_inexistente)
        
        # ==================== TESTS DE ACTUALIZACIÓN ====================
        print("\n--- TESTS DE ACTUALIZACIÓN DE USUARIO ---\n")
        
        # Test: Actualizar edad
        def test_actualizar_edad():
            nueva_edad = 35
            resp = client.put(f"/usuarios/{user_id}", json={"edad": nueva_edad})
            runner.assert_status(resp, 200, "Actualizar debe retornar 200")
            data = resp.json()
            runner.assert_equal(data["edad"], nueva_edad, "Edad debe estar actualizada")
            runner.assert_equal(data["nombre"], username, "Nombre no debe cambiar")
            return f"Edad actualizada de {edad} a {nueva_edad}"
        runner.run_test("Actualizar edad de usuario", test_actualizar_edad)
        
        # Test: Actualizar con email duplicado
        def test_update_email_duplicado():
            # Crear otro usuario temporal
            resp = client.post("/usuarios/", json={"nombre": "Temporal", "email": "temporal@test.com", "edad": 25})
            if resp.status_code == 201:
                temp_id = resp.json()["id"]
                # Intentar actualizar con email del primer usuario
                resp = client.put(f"/usuarios/{temp_id}", json={"email": email})
                runner.assert_status(resp, 400, "Email duplicado debe retornar 400")
                # Limpiar
                client.delete(f"/usuarios/{temp_id}")
                return "Actualización con email duplicado rechazada"
            return "Test omitido: no se pudo crear usuario temporal"
        runner.run_test("Rechazar actualización con email duplicado", test_update_email_duplicado)
        
        # ==================== TESTS DE CANCIONES ====================
        print("\n--- TESTS DE GESTIÓN DE CANCIONES ---\n")
        
        # Test: Añadir primera canción
        def test_add_cancion_1():
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 200, "Añadir canción debe retornar 200")
            data = resp.json()
            runner.assert_in("listaCanciones", data, "Respuesta debe incluir listaCanciones")
            return f"Canción '{canciones[0]}' añadida"
        runner.run_test("Añadir primera canción", test_add_cancion_1)
        
        # Test: Añadir segunda canción
        def test_add_cancion_2():
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": canciones[1]})
            runner.assert_status(resp, 200, "Añadir canción debe retornar 200")
            return f"Canción '{canciones[1]}' añadida"
        runner.run_test("Añadir segunda canción", test_add_cancion_2)
        
        # Test: Listar canciones
        def test_listar_canciones():
            resp = client.get(f"/usuarios/{user_id}/canciones")
            runner.assert_status(resp, 200, "Listar canciones debe retornar 200")
            data = resp.json()
            runner.assert_equal(len(data), 2, "Debe haber 2 canciones")
            for track in data:
                runner.assert_in("nombre", track, "Cada canción debe tener nombre")
                runner.assert_in("artistas", track, "Cada canción debe tener artistas")
                runner.assert_in("uri", track, "Cada canción debe tener URI")
            return f"Playlist contiene {len(data)} canciones"
        runner.run_test("Listar canciones de la playlist", test_listar_canciones)
        
        # Test: Canción duplicada
        def test_cancion_duplicada():
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 400, "Canción duplicada debe retornar 400")
            return "Canción duplicada rechazada"
        runner.run_test("Rechazar canción duplicada", test_cancion_duplicada)
        
        # Test: Canción inexistente en Spotify
        def test_cancion_inexistente():
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": "xyzqweasdzxc123456789"})
            runner.assert_status(resp, 404, "Canción inexistente debe retornar 404")
            return "Canción no encontrada en Spotify"
        runner.run_test("Buscar canción inexistente", test_cancion_inexistente)
        
        # Test: Nombre de canción vacío
        def test_cancion_vacia():
            resp = client.post(f"/usuarios/{user_id}/canciones", json={"nombre_cancion": ""})
            runner.assert_status(resp, 422, "Nombre vacío debe retornar 422")
            return "Nombre vacío rechazado"
        runner.run_test("Validar nombre de canción vacío", test_cancion_vacia)
        
        # ==================== TESTS DE LIKES ====================
        print("\n--- TESTS DE SISTEMA DE LIKES ---\n")
        
        # Test: Dar like a canción
        def test_dar_like():
            resp = client.post(f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 200, "Dar like debe retornar 200")
            return f"Like dado a '{canciones[0]}'"
        runner.run_test("Dar like a canción", test_dar_like)
        
        # Test: Like duplicado
        def test_like_duplicado():
            resp = client.post(f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 400, "Like duplicado debe retornar 400")
            return "Like duplicado rechazado"
        runner.run_test("Rechazar like duplicado", test_like_duplicado)
        
        # Test: Listar likes
        def test_listar_likes():
            resp = client.get(f"/usuarios/{user_id}/likes")
            runner.assert_status(resp, 200, "Listar likes debe retornar 200")
            data = resp.json()
            runner.assert_equal(len(data), 1, "Debe haber 1 like")
            return f"Usuario tiene {len(data)} like(s)"
        runner.run_test("Listar canciones con like", test_listar_likes)
        
        # Test: Like a canción no en playlist
        def test_like_cancion_no_playlist():
            resp = client.post(f"/usuarios/{user_id}/likes", json={"nombre_cancion": "Imagine Dragons Thunder"})
            runner.assert_status(resp, 404, "Like a canción no en playlist debe retornar 404")
            return "Like a canción fuera de playlist rechazado"
        runner.run_test("Like a canción no en playlist", test_like_cancion_no_playlist)
        
        # Test: Eliminar like
        def test_eliminar_like():
            resp = client.request("DELETE", f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 200, "Eliminar like debe retornar 200")
            # Verificar que se eliminó
            resp = client.get(f"/usuarios/{user_id}/likes")
            data = resp.json()
            runner.assert_equal(len(data), 0, "No debe haber likes")
            return "Like eliminado correctamente"
        runner.run_test("Eliminar like", test_eliminar_like)
        
        # Test: Eliminar like inexistente
        def test_eliminar_like_inexistente():
            resp = client.request("DELETE", f"/usuarios/{user_id}/likes", json={"nombre_cancion": canciones[1]})
            runner.assert_status(resp, 404, "Eliminar like inexistente debe retornar 404")
            return "Like inexistente retorna 404"
        runner.run_test("Eliminar like inexistente", test_eliminar_like_inexistente)
        
        # ==================== TESTS DE FILTRADO ====================
        print("\n--- TESTS DE FILTRADO POR ARTISTA ---\n")
        
        # Test: Filtrar por artista
        def test_filtrar_artista():
            # Obtener un artista de las canciones actuales
            resp = client.get(f"/usuarios/{user_id}/canciones")
            if resp.status_code == 200 and len(resp.json()) > 0:
                artista = resp.json()[0]["artistas"][0]
                resp = client.get(f"/usuarios/{user_id}/canciones/por-artista", params={"nombre_artista": artista})
                runner.assert_status(resp, 200, "Filtrar por artista debe retornar 200")
                data = resp.json()
                return f"Filtrado por '{artista}': {len(data)} resultado(s)"
            return "Test omitido: no hay canciones"
        runner.run_test("Filtrar canciones por artista", test_filtrar_artista)
        
        # Test: Filtrar artista inexistente
        def test_filtrar_artista_inexistente():
            resp = client.get(f"/usuarios/{user_id}/canciones/por-artista", params={"nombre_artista": "ArtistaInexistenteXYZ"})
            runner.assert_status(resp, 200, "Debe retornar 200 con lista vacía")
            data = resp.json()
            runner.assert_equal(len(data), 0, "Lista debe estar vacía")
            return "Artista no encontrado retorna lista vacía"
        runner.run_test("Filtrar por artista inexistente", test_filtrar_artista_inexistente)
        
        # ==================== TESTS DE ELIMINACIÓN ====================
        print("\n--- TESTS DE ELIMINACIÓN ---\n")
        
        # Test: Eliminar canción
        def test_eliminar_cancion():
            resp = client.request("DELETE", f"/usuarios/{user_id}/canciones", json={"nombre_cancion": canciones[0]})
            runner.assert_status(resp, 200, "Eliminar canción debe retornar 200")
            # Verificar que se eliminó
            resp = client.get(f"/usuarios/{user_id}/canciones")
            data = resp.json()
            runner.assert_equal(len(data), 1, "Debe quedar 1 canción")
            return f"Canción '{canciones[0]}' eliminada"
        runner.run_test("Eliminar canción de playlist", test_eliminar_cancion)
        
        # Test: Eliminar canción no en playlist
        def test_eliminar_cancion_inexistente():
            resp = client.request("DELETE", f"/usuarios/{user_id}/canciones", json={"nombre_cancion": "NoExiste123"})
            runner.assert_status(resp, 404, "Eliminar canción inexistente debe retornar 404")
            return "Canción no encontrada retorna 404"
        runner.run_test("Eliminar canción no en playlist", test_eliminar_cancion_inexistente)
        
        # Test: Eliminar usuario
        def test_eliminar_usuario():
            resp = client.delete(f"/usuarios/{user_id}")
            runner.assert_status(resp, 200, "Eliminar usuario debe retornar 200")
            # Verificar que se eliminó
            resp = client.get(f"/usuarios/{user_id}")
            runner.assert_status(resp, 404, "Usuario eliminado no debe existir")
            return "Usuario y playlist eliminados"
        runner.run_test("Eliminar usuario", test_eliminar_usuario)
        
        user_id = None  # Marcar como eliminado
        
        # Test: Eliminar usuario inexistente
        def test_eliminar_usuario_inexistente():
            resp = client.delete("/usuarios/99999")
            runner.assert_status(resp, 404, "Eliminar usuario inexistente debe retornar 404")
            return "Usuario inexistente retorna 404"
        runner.run_test("Eliminar usuario inexistente", test_eliminar_usuario_inexistente)
        
    except Exception as exc:
        print(f"\n⚠ Error crítico durante los tests: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza: eliminar usuario si aún existe
        if user_id is not None:
            try:
                resp = client.delete(f"/usuarios/{user_id}")
                print(f"\n🧹 Limpieza: Usuario {user_id} eliminado (status={resp.status_code})")
            except:
                pass
        
        # Imprimir resumen
        runner.print_summary()
        
        # Guardar resultados en JSON
        results_file = ROOT / "tests" / "test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": runner.tests_passed + runner.tests_failed,
                "passed": runner.tests_passed,
                "failed": runner.tests_failed,
                "success_rate": (runner.tests_passed/(runner.tests_passed + runner.tests_failed)*100) if (runner.tests_passed + runner.tests_failed) > 0 else 0,
                "results": runner.test_results
            }, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Resultados guardados en: {results_file}")


if __name__ == "__main__":
    main()
