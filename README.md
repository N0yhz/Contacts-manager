# goit-pyweb-hw 11-14
<br>

## MODULE 11

### REST API + FastAPI + CRUD API

**http**
- http://localhost:8000/docs
- http://localhost:8000/contacts
- http://localhost:8000/contacts/upcoming_birthdays/
<br>

## MODULE 12
### Authentication and authorization

**Changes**
-  Added **"owner_id"** to the **"contacts** in models and  through Docker exec. Using SQL command **ALTER TABLE contacts ADD COLUMN owner_id INTEGER REFERENCES users(id);**
- Added tablename **users**
- Tokens have **expire** and **refresh** interval 
<br>
<br>

## MODULE 13
###  CORS and Email verification


**Changes**

- Change "http" route to **localhost:8000/api/**
- Added **avatar for users**
<br>

**Verification**
- Implement email verification for registered users
- Added extra **"resend email verification"**
- Added **Password Reset**

## MODULE 14
### Documentation/Uittest/Pytest

**Documentation**
 - fully worked
<br>
<br>

**Unittest**
 - works perfectly
<br>
<br>
**Pytest (functional test)**
 - defedf
 - **pytest-cov**: 
