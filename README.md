## Contacts Manager

### Authentication and authorization

**Changes**
- Added **"owner_id"** to the **"contacts** in models and  through Docker exec. Using SQL command **ALTER TABLE contacts ADD COLUMN owner_id INTEGER REFERENCES users(id);**
- Added tablename **users**
- Tokens have **expire** and **refresh** interval 
<br>

### Email verification

**Verification**
- Implement email verification for registered users
- Added extra **"resend email verification"**
- Added **Password Reset**
<br>
The API is fully documented
