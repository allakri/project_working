import csv
import numpy as np
import pennylane as qml

def quantum_random_selector(num_keys):
    """Quantum-based random selection of a key index."""
    num_selector_qubits = int(np.ceil(np.log2(num_keys)))  # Number of qubits needed to index keys
    dev = qml.device("default.qubit", wires=num_selector_qubits, shots=1)

    @qml.qnode(dev)
    def quantum_index_selector():
        """Quantum circuit for selecting a random index"""
        for i in range(num_selector_qubits):
            qml.Hadamard(wires=i)  # Equal superposition of all indices
        return qml.sample(wires=range(num_selector_qubits))

    # Measure and get index
    binary_index = ''.join(map(str, quantum_index_selector()))
    selected_index = int(binary_index, 2) % num_keys  # Convert to decimal and wrap around
    return selected_index

def get_random_sequence_from_csv(csv_file='sequence.csv'):
    """Get a quantum-randomly selected encryption sequence from the CSV file."""
    sequences = []
    
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 2:  # Ensure row has sequence and hash
                sequence = row[0].strip('"')  # Remove quotes
                hash_value = row[1]
                sequences.append((sequence, hash_value))
    
    if not sequences:
        raise ValueError("No sequences found in the CSV file")
    
    # Select a sequence using quantum randomness
    selected_index = quantum_random_selector(len(sequences))
    sequence_str, hash_value = sequences[selected_index]
    
    # Convert the sequence string to a list of methods
    methods = [method.strip() for method in sequence_str.split(',')]
    
    return methods, hash_value