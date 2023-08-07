import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        pass

    @patch('main.httpx.Client.get')
    def test_get_sales_by_customer_id(self):
        # Définissez les données de test, par exemple un customer_id et une page.
        customer_id = 123
        page = 1

        # Effectuez une requête GET vers la route /sales/ avec les données de test.
        response = self.client.get(f"/sales/?customer_id={customer_id}&page={page}")

        # Assurez-vous que la requête a réussi (code 200).
        self.assertEqual(response.status_code, 200)

        # Vérifiez le contenu de la réponse (par exemple, la structure JSON).
        # Par exemple, si vous vous attendez à une liste de ventes :
        self.assertIsInstance(response.json(), list)

    @patch('main.httpx.Client.get')
    def test_get_clients_by_name(self, mock_get):
        # Mock the response from the external API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"id": 1, "name": "John Doe"}]

        # Test the route with a valid name
        response = self.client.get("/clients/?first_name=John")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 1, "name": "John Doe"}])

        # Test the route with an invalid name
        response = self.client.get("/clients/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "le \"nom\" est necessaire"})

    @patch('main.mongodb_connect')
    def test_get_clients_by_name_db(self, mock_mongodb_connect):
        # Mock the database collection
        mock_collection = MagicMock()
        mock_mongodb_connect.return_value.__getitem__.return_value = mock_collection

        # Mock the find result
        mock_collection.find.return_value = [{"_id": 1, "name": "John Doe"}]

        # Test the route with a valid name
        response = self.client.get("/clients_db/?first_name=John")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"_id": 1, "name": "John Doe"}])

        # Test the route with an invalid name
        response = self.client.get("/clients_db/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "le \"nom\" est necessaire"})

    @patch('main.mongodb_connect')
    def test_get_sales_by_customer_id_mongodb(self, mock_mongodb_connect):
        # Mock the database collection
        mock_collection = MagicMock()
        mock_mongodb_connect.return_value.__getitem__.return_value = mock_collection

        # Mock the find result
        mock_collection.find.return_value = [{"_id": 1, "customer_id": 123, "amount": 100}]

        # Test the route with a valid customer_id
        response = self.client.get("/sales_db/?customer_id=123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"_id": 1, "customer_id": 123, "amount": 100}])

if __name__ == '__main__':
    unittest.main()