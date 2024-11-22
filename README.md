# goit-pyweb-hw-11+12
<br>
## MODULE 11
### REST API + FastAPI + CRUD API

**http**
- http://localhost:8000/docs
- http://localhost:8000/contacts
- http://localhost:8000/contacts/upcoming_birthdays/

**Connecting database**
- Host: localhost
- Database: contacts_db
- Username: n0yhz
- Password: module11
<br>

## MODULE 12
### Authentication and authorization

**Changes**
-  Added **"owner_id"** to the **"contacts** in models and  through Docker exec. Using SQL command **ALTER TABLE contacts ADD COLUMN owner_id INTEGER REFERENCES users(id);**
- Added tablename **users**
- Tokens have **expire** and **refresh** interval 
