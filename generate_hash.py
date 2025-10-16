import hashlib
import secrets

def generate_hash(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f'sha256${salt}${password_hash}'

hash_value = generate_hash('admin')
print(f'UPDATE users SET password_hash = \'{hash_value}\' WHERE username = \'admin\';')