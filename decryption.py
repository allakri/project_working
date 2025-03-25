import base64
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES, DES, DES3, PKCS1_OAEP
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from sequence_utils import find_sequence_by_hash

# AES Decryption (GCM Mode)
def aes_gcm_decrypt(nonce, ct, tag, key):
    nonce = base64.b64decode(nonce)
    ct = base64.b64decode(ct)
    tag = base64.b64decode(tag)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ct, tag)
    return plaintext.decode()

# AES Decryption (CBC Mode)
def aes_decrypt(iv, ct, key):
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode()

# DES Decryption
def des_decrypt(iv, ct, key):
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = DES.new(key, DES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), DES.block_size)
    return pt.decode()

# Triple DES Decryption
def tdes_decrypt(iv, ct, key):
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), DES3.block_size)
    return pt.decode()

# RSA Decryption
def rsa_decrypt(encrypted_data, private_key):
    encrypted_data = base64.b64decode(encrypted_data)
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data.decode()

# ECC Decryption
def ecc_decrypt(encrypted_data, private_key):
    # Parse the encrypted components
    components = dict(comp.split(':') for comp in encrypted_data.split('|'))
    
    # Reconstruct the ephemeral public key
    ephem_x = int(components['ephem_x'])
    ephem_y = int(components['ephem_y'])
    ephemeral_pub = ECC.construct(curve='P-256', point_x=ephem_x, point_y=ephem_y)
    
    # Compute the shared point
    shared_point = (ephemeral_pub.pointQ * private_key.d).x
    
    # Derive the same symmetric key
    shared_key = HKDF(
        str(shared_point).encode(),
        32,
        b'ECC-Encryption',
        SHA256
    )
    
    # Decode the encrypted components
    nonce = base64.b64decode(components['nonce'])
    ciphertext = base64.b64decode(components['ciphertext'])
    tag = base64.b64decode(components['tag'])
    
    # Decrypt using AES-GCM
    cipher = AES.new(shared_key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode()

def decrypt_data(ivs, encrypted_data, tags, methods, key_aes, key_des, key_tdes, private_key_rsa, private_key_ecc):
    decrypted_data = encrypted_data
    methods = list(reversed(methods))
    ivs = list(reversed(ivs))
    tags = list(reversed(tags)) if tags else [None] * len(methods)
    
    print("\n--- Decryption Stages ---\n")
    for i, method in enumerate(methods):
        print(f"\nDecrypting with {method.upper()}...\n")
        print(f"\nInput: {decrypted_data}\n")
        
        iv = ivs[i]
        tag = tags[i]
        
        if method == 'ecc':
            decrypted_data = ecc_decrypt(decrypted_data, private_key_ecc)
        elif method == 'aes':
            decrypted_data = aes_decrypt(iv, decrypted_data, key_aes)
        elif method == 'aes-gcm':
            decrypted_data = aes_gcm_decrypt(iv, decrypted_data, tag, key_aes)
        elif method == 'des':
            decrypted_data = des_decrypt(iv, decrypted_data, key_des)
        elif method == 'tdes':
            decrypted_data = tdes_decrypt(iv, decrypted_data, key_tdes)
        elif method == 'rsa':
            decrypted_data = rsa_decrypt(decrypted_data, private_key_rsa)
            
        print(f"Output: {decrypted_data}")
    
    return decrypted_data

def decrypt_with_hash(ivs, encrypted_data, tags, sequence_hash, key_aes, key_des, key_tdes, private_key_rsa, private_key_ecc):
    """Decrypt data using the sequence identified by its hash."""
    # Find the encryption sequence using the hash
    methods = find_sequence_by_hash(sequence_hash)
    print(f"Found encryption sequence: {' -> '.join(methods)}")
    
    # Decrypt using the identified sequence
    return decrypt_data(ivs, encrypted_data, tags, methods, key_aes, key_des, key_tdes, private_key_rsa, private_key_ecc)