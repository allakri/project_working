import itertools
import hashlib
import csv

def generate_hash(sequence_str):
    """Generate SHA-256 hash for a sequence string."""
    return hashlib.sha256(sequence_str.encode()).hexdigest()

def generate_rsa_first_sequences(algorithms, min_length=2, max_length=6, limit=100):
    """Generate permutations of encryption algorithms with RSA always first."""
    sequences = []
    count = 0
    
    # Remove RSA from the algorithms list since we'll always put it first
    other_algorithms = [algo for algo in algorithms if algo != 'rsa']
    
    for length in range(min_length - 1, max_length):  # -1 because we're adding RSA separately
        if count >= limit:
            break
            
        for perm in itertools.permutations(other_algorithms, length):
            if count >= limit:
                break
                
            # Add RSA as the first algorithm
            full_perm = ('rsa',) + perm
            
            # Format the sequence as a string
            sequence_str = ", ".join(full_perm)
            
            # Generate hash
            hash_value = generate_hash(sequence_str)
            
            # Add to sequences
            sequences.append((sequence_str, hash_value))
            count += 1
            
    return sequences

def save_sequences_to_csv(sequences, filename='sequence.csv'):
    """Save sequences and their hashes to a CSV file."""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Sequence', 'SHA-256 Hash'])
        for sequence, hash_value in sequences:
            writer.writerow([f'"{sequence}"', hash_value])
    
    print(f"Generated {len(sequences)} sequences and saved to {filename}")

def main():
    # Define the encryption algorithms
    algorithms = ['rsa', 'aes', 'des', 'tdes', 'aes-gcm', 'ecc']
    
    # Generate sequences with RSA always first
    sequences = generate_rsa_first_sequences(algorithms, min_length=2, max_length=6, limit=100)
    
    # Save to CSV
    save_sequences_to_csv(sequences)

if __name__ == "__main__":
    main()