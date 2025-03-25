import os
import base64
from Crypto.PublicKey import RSA, ECC
import csv

def generate_key_set():
    # Generate AES key (256 bits)
    aes_key = os.urandom(32)
    
    # Generate DES key (64 bits)
    des_key = os.urandom(8)
    
    # Generate Triple DES key (168 bits)
    tdes_key = os.urandom(24)
    
    # Generate RSA key pair (2048 bits)
    rsa_key = RSA.generate(2048)
    private_key_rsa = rsa_key
    public_key_rsa = rsa_key.publickey()
    
    # Generate ECC key pair
    private_key_ecc = ECC.generate(curve='P-256')
    public_key_ecc = private_key_ecc.public_key()
    
    # Create encryption keys dict
    encryption_keys = {
        'aes_key': base64.b64encode(aes_key).decode('utf-8'),
        'des_key': base64.b64encode(des_key).decode('utf-8'),
        'tdes_key': base64.b64encode(tdes_key).decode('utf-8'),
        'public_key_rsa': base64.b64encode(public_key_rsa.export_key()).decode('utf-8'),
        'public_key_ecc': base64.b64encode(f"{public_key_ecc.pointQ.x}|{public_key_ecc.pointQ.y}".encode()).decode('utf-8')
    }
    
    # Create decryption keys dict
    decryption_keys = {
        'aes_key': base64.b64encode(aes_key).decode('utf-8'),
        'des_key': base64.b64encode(des_key).decode('utf-8'),
        'tdes_key': base64.b64encode(tdes_key).decode('utf-8'),
        'private_key_rsa': base64.b64encode(private_key_rsa.export_key()).decode('utf-8'),
        'private_key_ecc': base64.b64encode(str(private_key_ecc.d).encode()).decode('utf-8')
    }
    
    return encryption_keys, decryption_keys

def generate_keys_csv(num_sets=20, enc_filename='encryption_keys.csv', dec_filename='decryption_keys.csv'):
    # Define the CSV headers
    encryption_headers = [
        'aes_key',
        'des_key',
        'tdes_key',
        'public_key_rsa',
        'public_key_ecc'
    ]
    
    decryption_headers = [
        'aes_key',
        'des_key',
        'tdes_key',
        'private_key_rsa',
        'private_key_ecc'
    ]
    
    # Generate the specified number of key sets
    encryption_key_sets = []
    decryption_key_sets = []
    
    for _ in range(num_sets):
        enc_keys, dec_keys = generate_key_set()
        encryption_key_sets.append(enc_keys)
        decryption_key_sets.append(dec_keys)
    
    # Write the encryption key sets to a CSV file
    with open(enc_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=encryption_headers)
        writer.writeheader()
        writer.writerows(encryption_key_sets)
    
    # Write the decryption key sets to a CSV file
    with open(dec_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=decryption_headers)
        writer.writeheader()
        writer.writerows(decryption_key_sets)
    
    print(f"Generated {num_sets} key sets and saved to {enc_filename} and {dec_filename}")

if __name__ == "__main__":
    generate_keys_csv()