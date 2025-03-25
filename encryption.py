import base64
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES, DES, DES3, PKCS1_OAEP
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

# AES Encryption (GCM Mode)
def aes_gcm_encrypt(data, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    nonce = base64.b64encode(cipher.nonce).decode('utf-8')
    ct = base64.b64encode(ciphertext).decode('utf-8')
    tag = base64.b64encode(tag).decode('utf-8')
    return nonce, ct, tag

# AES Encryption (CBC Mode)
def aes_encrypt(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv, ct

# DES Encryption
def des_encrypt(data, key):
    cipher = DES.new(key, DES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), DES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv, ct

# Triple DES Encryption
def tdes_encrypt(data, key):
    cipher = DES3.new(key, DES3.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), DES3.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv, ct

# RSA Encryption
def rsa_encrypt(data, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_data = cipher.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode('utf-8')

# ECC Encryption
def ecc_encrypt(data, public_key):
    # Generate an ephemeral key pair
    from Crypto.PublicKey import ECC
    ephemeral_key = ECC.generate(curve='P-256')
    shared_point = (public_key.pointQ * ephemeral_key.d).x
    
    # Derive a symmetric key using HKDF
    shared_key = HKDF(
        str(shared_point).encode(),
        32,
        b'ECC-Encryption',
        SHA256
    )
    
    # Use AES-GCM for the actual encryption
    cipher = AES.new(shared_key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    
    # Encode all components
    enc_components = {
        'ephem_x': str(ephemeral_key.public_key().pointQ.x),
        'ephem_y': str(ephemeral_key.public_key().pointQ.y),
        'nonce': base64.b64encode(cipher.nonce).decode('utf-8'),
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
        'tag': base64.b64encode(tag).decode('utf-8')
    }
    
    # Combine all components into a single string
    return '|'.join(f"{k}:{v}" for k, v in enc_components.items())

def encrypt_data(data, methods, key_aes, key_des, key_tdes, public_key_rsa, public_key_ecc):
    encrypted_data = data
    ivs = []
    tags = []
    
    print("\n--- Encryption Stages ---")
    for method in methods:
        print(f"\nEncrypting with {method.upper()}...\n")
        print(f"\nInput: {encrypted_data}\n")
        
        if method == 'ecc':
            encrypted_data = ecc_encrypt(encrypted_data, public_key_ecc)
            ivs.append(None)
            tags.append(None)
        elif method == 'aes':
            iv, encrypted_data = aes_encrypt(encrypted_data, key_aes)
            ivs.append(iv)
            tags.append(None)
        elif method == 'aes-gcm':
            nonce, encrypted_data, tag = aes_gcm_encrypt(encrypted_data, key_aes)
            ivs.append(nonce)
            tags.append(tag)
        elif method == 'des':
            iv, encrypted_data = des_encrypt(encrypted_data, key_des)
            ivs.append(iv)
            tags.append(None)
        elif method == 'tdes':
            iv, encrypted_data = tdes_encrypt(encrypted_data, key_tdes)
            ivs.append(iv)
            tags.append(None)
        elif method == 'rsa':
            encrypted_data = rsa_encrypt(encrypted_data, public_key_rsa)
            ivs.append(None)
            tags.append(None)
            
        print(f"Output: {encrypted_data}")
    
    return ivs, encrypted_data, tags