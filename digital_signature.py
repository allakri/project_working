import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

def generate_signature(data, private_key):
    """
    Generate a digital signature for the given data using the private key.
    
    Args:
        data (str): The data to sign
        private_key: RSA private key object
    
    Returns:
        str: Base64 encoded signature
    """
    # Create a hash of the data
    h = SHA256.new(data.encode())
    
    # Sign the hash with the private key
    signature = pkcs1_15.new(private_key).sign(h)
    
    # Return the base64 encoded signature
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(data, signature, public_key):
    """
    Verify the digital signature for the given data using the public key.
    
    Args:
        data (str): The data that was signed
        signature (str): Base64 encoded signature
        public_key: RSA public key object
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Decode the signature from base64
    signature = base64.b64decode(signature)
    
    # Create a hash of the data
    h = SHA256.new(data.encode())
    
    try:
        # Verify the signature
        pkcs1_15.new(public_key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False