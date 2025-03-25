import csv
import hashlib

def find_sequence_by_hash(hash_value, csv_file='sequence.csv'):
    """Find the encryption sequence corresponding to a hash value."""
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 2 and row[1] == hash_value:
                sequence_str = row[0].strip('"')  # Remove quotes
                methods = [method.strip() for method in sequence_str.split(',')]
                return methods
    
    raise ValueError(f"No sequence found for hash: {hash_value}")

def generate_hash(sequence_str):
    """Generate SHA-256 hash for a sequence string."""
    return hashlib.sha256(sequence_str.encode()).hexdigest()

def verify_sequence_hash(methods, hash_value):
    """Verify that a sequence matches a given hash."""
    sequence_str = ", ".join(methods)
    computed_hash = generate_hash(sequence_str)
    return computed_hash == hash_value