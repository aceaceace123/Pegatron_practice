import unittest
import io
import json
from fastapi.testclient import TestClient
from main import app, users_db
from typing import Dict, List

class TestUserAPI(unittest.TestCase):
    def setUp(self):
        # Clear the in-memory database before each test
        users_db.clear()
        self.client = TestClient(app)

    def tearDown(self):
        # Clean up after each test
        users_db.clear()

    def test_create_user(self):
        response = self.client.post("/users", json={"name": "Alice", "age": 30})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Alice")
        self.assertEqual(data["age"], 30)
        self.assertIn("id", data)
        # Check if user is actually in the db
        self.assertIn(data["id"], users_db)
        self.assertEqual(users_db[data["id"]]["name"], "Alice")

    def test_create_duplicate_user(self):
        # Create first user
        self.client.post("/users", json={"name": "Bob", "age": 25})
        # Attempt to create user with the same name
        response = self.client.post("/users", json={"name": "Bob", "age": 26})
        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", response.json()["detail"])

    def test_get_users_empty(self):
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_users(self):
        # Add some users first
        user1_resp = self.client.post("/users", json={"name": "Charlie", "age": 35})
        user2_resp = self.client.post("/users", json={"name": "David", "age": 40})
        user1 = user1_resp.json()
        user2 = user2_resp.json()

        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        # Check if the returned list contains the users we added (order might vary)
        self.assertTrue(user1 in data)
        self.assertTrue(user2 in data)

    def test_delete_user(self):
        # Add a user
        user_resp = self.client.post("/users", json={"name": "Eve", "age": 28})
        user_id = user_resp.json()["id"]
        self.assertIn(user_id, users_db)

        # Delete the user
        response = self.client.delete(f"/users/{user_id}")
        self.assertEqual(response.status_code, 204)
        self.assertNotIn(user_id, users_db) # Verify deletion from db

        # Try getting the deleted user
        get_response = self.client.get("/users")
        self.assertFalse(user_resp.json() in get_response.json())

    def test_delete_nonexistent_user(self):
        response = self.client.delete("/users/nonexistent-id")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    def test_upload_csv(self):
        # Prepare CSV data with correct headers
        csv_content = "Name,Age\nFrank,50\nGrace,55"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))

        response = self.client.post(
            "/users/upload_csv",
            files={"file": ("users.csv", csv_file, "text/csv")}
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["added_users"], 2)
        self.assertEqual(data["skipped_users"], 0)
        self.assertEqual(data["skipped_names"], [])

        # Verify users were added
        get_response = self.client.get("/users")
        users = get_response.json()
        self.assertEqual(len(users), 2)
        names = {user['name'] for user in users}
        self.assertEqual(names, {"Frank", "Grace"})

    def test_upload_csv_with_duplicates_and_errors(self):
        # Add one user initially
        self.client.post("/users", json={"name": "Heidi", "age": 60})

        # Prepare CSV data with a duplicate name and a row with missing age
        csv_content = "Name,Age\nHeidi,61\nIvy,65\nJudy," # Judy has missing age
        csv_file = io.BytesIO(csv_content.encode('utf-8'))

        response = self.client.post(
            "/users/upload_csv",
            files={"file": ("users_mixed.csv", csv_file, "text/csv")}
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        # Ivy should be added, Heidi skipped (duplicate), Judy skipped (error)
        self.assertEqual(data["added_users"], 1)
        self.assertEqual(data["skipped_users"], 2)
        # Order might vary, check content
        self.assertIn("Heidi", data["skipped_names"])
        self.assertIn("Judy", data["skipped_names"])

        # Verify final users list
        get_response = self.client.get("/users")
        users = get_response.json()
        self.assertEqual(len(users), 2) # Initial Heidi + Ivy from CSV
        names = {user['name'] for user in users}
        self.assertEqual(names, {"Heidi", "Ivy"})

    def test_upload_csv_invalid_format(self):
        # Missing 'age' column
        csv_content = "name\nKevin"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        response = self.client.post(
            "/users/upload_csv",
            files={"file": ("invalid.csv", csv_file, "text/csv")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("CSV must contain 'Name' and 'Age' columns", response.json()["detail"])

    def test_upload_csv_wrong_file_type(self):
        # Send a non-CSV file
        txt_content = "this is not csv"
        txt_file = io.BytesIO(txt_content.encode('utf-8'))
        response = self.client.post(
            "/users/upload_csv",
            files={"file": ("not_a_csv.txt", txt_file, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file type", response.json()["detail"])

    def test_get_average_age_empty(self):
        response = self.client.get("/users/average_age")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "No users available to calculate average age."})

    def test_get_average_age(self):
        # Add users
        self.client.post("/users", json={"name": "Liam", "age": 22})
        self.client.post("/users", json={"name": "Linda", "age": 28}) # L group avg = (22+28)/2 = 25
        self.client.post("/users", json={"name": "Mason", "age": 35}) # M group avg = 35
        self.client.post("/users", json={"name": "Mia", "age": 30})   # M group avg = (35+30)/2 = 32.5

        response = self.client.get("/users/average_age")
        self.assertEqual(response.status_code, 200)
        expected_averages: Dict[str, float] = {
            "L": 25.0,
            "M": 32.5
        }
        self.assertEqual(response.json(), expected_averages)

    def test_get_average_age_with_non_numeric_age_in_db(self):
        # Simulate potentially bad data if validation wasn't perfect (though Pydantic helps)
        # Directly manipulate the db for this test case, as API prevents non-int age
        users_db["manual1"] = {"id": "manual1", "name": "Noah", "age": 40}
        users_db["manual2"] = {"id": "manual2", "name": "Nora", "age": "invalid_age"} # Simulate bad data

        response = self.client.get("/users/average_age")
        self.assertEqual(response.status_code, 200)
        # 'Nora' should be ignored due to non-numeric age during calculation
        expected_averages: Dict[str, float] = {
            "N": 40.0
        }
        self.assertEqual(response.json(), expected_averages)

if __name__ == '__main__':
    unittest.main()
