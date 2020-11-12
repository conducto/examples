import unittest
import json
from app.main import app


class TestCase(unittest.TestCase):
    def test_hello(self):
        c = app.test_client()
        response = c.get("/demo")
        text = response.get_data()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(text, b"Hello, Conducto!")

    def test_user(self):
        c = app.test_client()

        # First add 1 key
        body = {"key": "cool_key", "value": "cool_value"}
        response = c.post("/demo/user/BobLoblaw", json=body)
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["data"]["cool_key"], "cool_value")

        # Then add a second key, result should return both values
        body = {"key": "gr8_key", "value": "gr8_value"}
        response = c.post("/demo/user/BobLoblaw", json=body)
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["data"]["cool_key"], "cool_value")
        self.assertEqual(data["data"]["gr8_key"], "gr8_value")

        # Now a get should return both values as well
        response = c.get("/demo/user/BobLoblaw")
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["data"]["cool_key"], "cool_value")
        self.assertEqual(data["data"]["gr8_key"], "gr8_value")

    def test_hacker(self):
        # 'hacker' is not authorized to access this endpoint
        c = app.test_client()
        response = c.get("/demo/user/hacker")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
