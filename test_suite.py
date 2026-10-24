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

    def test_direct_inventory_access(self):
        """Verifica que el inventario sea accesible directamente sin requerir login."""
        response = self.app.get('/api/inventory', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

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

if __name__ == '__main__':
    unittest.main()
