import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.database.models import User, Contact
from src.schemas import UserCreate
from src.repository import users as users_repo

class TestUsers(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(self):
        self.session = MagicMock(spec=Session)

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_create_user(self):
        user_data = UserCreate(username="testuser",
                               email="test@example.com",
                               password="password123")
        verification_token = "test-token"
        user = users_repo.create_user(self.session, user_data, verification_token)
    
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_verified)
        self.assertEqual(user.verification_token, verification_token)

    def test_get_user(self):
        user = User(username="testuser",
                    email="test@example.com",
                    hashed_password="hashed_passw")
        self.session.add(user)
        self.session.commit()

        retrieved_user = users_repo.get_user(self.session, user.id)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")

    def test_get_user_by_email(self):
        user = User(username="testuser",
                    email="test@example.com",
                    hashed_password="hashed_passw")
        self.session.add(user)
        self.session.commit()

        retrieved_user = users_repo.get_user_by_email(self.session, "test@example.com")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")

    def test_verify_user(self):
        user = User(username="testuser",
                    email="test@example.com",
                    hashed_password="hashed_passw",
                    is_verified=False)
        self.session.add(user)
        self.session.commit()

        updated_user = users_repo.verify_user(self.session, "test@example.com")
        self.assertTrue(updated_user.is_verified)
        self.assertIsNone(updated_user.verification_token)

    def test_delete_user(self):
        user = User(username="testuser",
                    email="test@example.com",
                    hashed_password="hashed_passw")
        self.session.add(user)
        self.session.commit()

        result = users_repo.delete_user(self.session, user.id)
        self.assertTrue(result)
        self.assertIsNone(users_repo.get_user(self.session, user.id))

if __name__ == "__main__":
    unittest.main()