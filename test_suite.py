import unittest
import json
from app import app
import db_manager

class TestInventoryAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_db_connection(self):
        """Verifica que la conexión a la base de datos Firebird sea exitosa."""
        try:
            con = db_manager.get_connection()
            self.assertIsNotNone(con, "La conexión a la base de datos retornó None")
            con.close()
        except Exception as e:
            self.fail(f"La conexión a la base de datos falló: {e}")

    def test_health_check(self):
        """Verifica que el endpoint de salud esté disponible."""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')

    def test_api_info(self):
        """Verifica que el endpoint de información de la API esté disponible."""
        response = self.app.get('/info')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Especificación", response.data.decode('utf-8'))

    def test_protected_endpoint_unauthorized(self):
        """Verifica que los endpoints protegidos devuelvan 401 si no hay sesión."""
        # Intentar acceder a inventario sin login
        response = self.app.get('/api/inventory')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_db_inventory_query(self):
        """Valida que se puedan realizar consultas de inventario directamente."""
        products = db_manager.get_inventory_all()
        self.assertIsInstance(products, list, "El resultado de inventario debe ser una lista")
        # Si hay productos, validamos la estructura del primero
        if len(products) > 0:
            p = products[0]
            self.assertIn('codigo', p)
            self.assertIn('descripcion', p)
            self.assertIn('inventario', p)

    def test_db_users_query(self):
        """Valida que la tabla de usuarios sea consultable (vital para el login)."""
        users = db_manager.get_all_users()
        self.assertIsInstance(users, list)
        self.assertTrue(len(users) > 0, "Debe haber al menos un usuario (admin)")
        
    def test_login_validation(self):
        """Prueba el proceso de login con credenciales de prueba (debe fallar con datos falsos)."""
        response = self.app.post('/api/auth/login', 
                                data=json.dumps({'username': 'fakeuser', 'password': 'wrongpassword'}),
                                content_type='application/json')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

if __name__ == '__main__':
    unittest.main()
