import unittest
import json
from app import app
import db_manager
import event_logger

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
        if len(products) > 0:
            p = products[0]
            self.assertIn('codigo', p)
            self.assertIn('descripcion', p)
            self.assertIn('inventario', p)

    def test_event_logger_local(self):
        """Verifica que el logger de eventos registre y recupere movimientos correctamente."""
        ok = event_logger.log_event(
            category='TEST',
            action='TEST_ACTION',
            entity_id='99999',
            entity_name='Producto de Prueba',
            details='Detalles de prueba unitaria',
            user_name='Tester',
            ip_address='127.0.0.1'
        )
        self.assertTrue(ok)
        events_data = event_logger.get_events(category='TEST', limit=5)
        self.assertGreater(events_data['total'], 0)
        self.assertEqual(events_data['events'][0]['category'], 'TEST')

    def test_api_events_endpoint(self):
        """Verifica que el endpoint /api/events responda correctamente."""
        response = self.app.get('/api/events')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('total', data)

    def test_api_events_summary(self):
        """Verifica que el endpoint /api/events/summary responda correctamente."""
        response = self.app.get('/api/events/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_events', data)
        self.assertIn('today_events', data)

    def test_open_access_auth_check(self):
        """Verifica que /api/auth/check certifique acceso abierto sin login."""
        response = self.app.get('/api/auth/check')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('logged_in'))
        self.assertTrue(data.get('is_admin'))

if __name__ == '__main__':
    unittest.main()
