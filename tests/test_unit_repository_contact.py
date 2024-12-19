import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.database.models import User, Contact
from src.schemas import ContactCreate
from src.repository import contacts as contacts_repo

class TestContacts(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=7)

    async def test_get_contact(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().offset().limit().all.return_value = contacts
        result = contacts_repo.get_contacts(skip=0, limit=10, user_id=self.user.id, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = contacts_repo.get_contact(contact_id=6, db=self.session, user_id=self.user.id)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = contacts_repo.get_contact(contact_id=6, db=self.session, user_id=self.user.id)
        self.assertIsNone(result)

    async def test_create_contact(self):
        contacts_data = ContactCreate(first_name="Trang",
                                       last_name="Zyonh",
                                        email="trangzyonh@example.com",
                                        phone_number="1234567890",
                                        birthday="2001-12-03",
                                        additional_data="Hello Vietnam")
        result = contacts_repo.create_contact(contact=contacts_data, user_id=self.user.id, db=self.session)
        self.assertEqual(result.first_name, contacts_data.first_name)
        self.assertEqual(result.last_name, contacts_data.last_name)
        self.assertEqual(result.email, contacts_data.email)
        self.assertEqual(result.phone_number, contacts_data.phone_number)
        self.assertEqual(result.birthday, contacts_data.birthday)
        self.assertEqual(result.additional_data, contacts_data.additional_data)
        self.assertEqual(result.owner_id, self.user.id)

    async def test_update_contact_found(self):
        existing_contact = Contact(id=6, owner_id=self.user.id)
        self.session.query().filter().first.return_value = existing_contact
        updated_data = ContactCreate(first_name="Trang",
                                       last_name="Zyonh",
                                        email="trangzyonh@test.com",
                                        phone_number="0123456789",
                                        birthday="2001-12-03",
                                        additional_data="Hello Unittest")
        result = contacts_repo.update_contact(contact_id=6, contact=updated_data, db=self.session, user_id=self.user.id)
        self.assertEqual(result.first_name, updated_data.first_name)
        self.assertEqual(result.last_name, updated_data.last_name)
        self.assertEqual(result.email, updated_data.email)
        self.assertEqual(result.phone_number, updated_data.phone_number)
        self.assertEqual(result.birthday, updated_data.birthday)
        self.assertEqual(result.additional_data, updated_data.additional_data)

    async def test_update_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        updated_data = {"first_name": "Trang", 
                        "last_name": "Zyonh",
                        "email": "trangzyonh@test.com",
                        "phone":"0123456789",
                        "birthday": "2001-12-03",
                        "additional_data": "Hello Unittest"}
        result = contacts_repo.update_contact(contact_id=6, contact=updated_data, db=self.session, user_id=self.user.id)
        self.assertIsNone(result)

    async def test_delete_contact_found(self):
        existing_contact = Contact(id=6, owner_id=self.user.id)
        self.session.query().filter().first.return_value = existing_contact
        result = contacts_repo.delete_contact(contact_id=6, db=self.session, user_id=self.user.id)
        self.assertEqual(result, existing_contact)

    async def test_delete_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = contacts_repo.delete_contact(contact_id=6, db=self.session, user_id=self.user.id)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
