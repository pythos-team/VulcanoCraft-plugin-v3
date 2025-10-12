import json
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    users_file = 'users.json'
    
    # Load existing users
    users = []
    if os.path.exists(users_file):
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
    
    # Check if admin already exists
    if any(u['username'] == 'admin' for u in users):
        print("Admin user already exists!")
        return
    
    # Add admin user
    admin_user = {
        'username': 'admin',
        'password': hash_password('admin123'),
        'role': 'admin'
    }
    
    users.append(admin_user)
    
    # Save users
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    
    print("Admin user created!")
    print("Username: admin")
    print("Password: admin123")
    print("Role: admin")

if __name__ == '__main__':
    create_admin()