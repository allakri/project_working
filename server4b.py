import sys
import socket
import random
import logging
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from typing import Optional, Dict
from tkintermapview import TkinterMapView
import time
import json
import csv
from datetime import datetime

# Import cryptographic modules
from key_loader import get_random_keys, get_keys_by_index
from encryption import encrypt_data
from decryption import decrypt_data
from digital_signature import generate_signature, verify_signature
from quantum_generator import get_random_sequence_from_csv
from sequence_utils import find_sequence_by_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

LOCATIONS_CSV = 'tank_locations.csv'

class CommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Commander Control Center")
        self.root.geometry("1400x800")
        
        # Initialize variables
        self.server_socket = None
        self.connected_tanks = {}
        self.tank_markers = {}
        self.tank_paths = {}
        self.server_running = False
        self.selected_tank = None
        self.show_paths = False

        # Setup styles
        self.setup_styles()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.home_tab = ttk.Frame(self.notebook)
        self.user_management_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.home_tab, text='Home')
        self.notebook.add(self.user_management_tab, text='User Management')
        
        # Create layouts for each tab
        self.create_home_tab()
        self.create_user_management_tab()
        
        # Initialize crypto
        self._initialize_crypto()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", padding=5)
        style.configure("Tank.TButton", padding=10)
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Online.TLabel", foreground="green")
        style.configure("Offline.TLabel", foreground="red")

    def create_home_tab(self):
        # Configure grid weights for home tab
        self.home_tab.grid_rowconfigure(0, weight=1)
        self.home_tab.grid_columnconfigure(1, weight=3)
        self.home_tab.grid_columnconfigure(2, weight=1)

        # Left Panel - Tank List
        left_panel = ttk.Frame(self.home_tab, padding=10)
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        # Tank List
        tank_frame = ttk.LabelFrame(left_panel, text="Connected Tanks", padding=10)
        tank_frame.pack(fill="both", expand=True)

        self.tank_listbox = tk.Listbox(tank_frame, font=("Arial", 10))
        self.tank_listbox.pack(fill="both", expand=True)
        self.tank_listbox.bind('<<ListboxSelect>>', self.on_tank_selected)

        # Control Buttons
        control_frame = ttk.Frame(tank_frame, padding=5)
        control_frame.pack(fill="x", pady=5)

        ttk.Button(
            control_frame,
            text="Show Path",
            command=self.toggle_path_visibility
        ).pack(side="left", padx=2)

        ttk.Button(
            control_frame,
            text="Clear Path",
            command=self.clear_selected_path
        ).pack(side="left", padx=2)

        # Center Panel - Map
        center_panel = ttk.Frame(self.home_tab, padding=10)
        center_panel.grid(row=0, column=1, sticky="nsew")
        
        map_frame = ttk.LabelFrame(center_panel, text="Tactical Map", padding=10)
        map_frame.pack(fill="both", expand=True)

        self.map_widget = TkinterMapView(map_frame, width=800, height=600)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(17.385044, 78.486671)
        self.map_widget.set_zoom(10)

        # Right Panel - Controls and Logs
        right_panel = ttk.Frame(self.home_tab, padding=10)
        right_panel.grid(row=0, column=2, sticky="nsew")
        
        # Server Controls
        control_frame = ttk.LabelFrame(right_panel, text="Server Controls", padding=10)
        control_frame.pack(fill="x")

        self.server_status = ttk.Label(
            control_frame,
            text="Server Status: Stopped",
            font=("Arial", 10)
        )
        self.server_status.pack(fill="x", pady=5)

        self.start_button = ttk.Button(
            control_frame,
            text="Start Server",
            command=self.start_server
        )
        self.start_button.pack(fill="x", pady=5)

        # Log Section
        log_frame = ttk.LabelFrame(right_panel, text="Server Logs", padding=10)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True)

    def create_user_management_tab(self):
        # Tank Management Section
        self.create_tank_management_section()

    def create_tank_management_section(self):
        """Create the tank management section"""
        # Header
        ttk.Label(self.user_management_tab, 
                 text="Tank Management", 
                 style="Header.TLabel").pack(fill="x", pady=(10, 20))

        # Main container
        container = ttk.Frame(self.user_management_tab)
        container.pack(fill="both", expand=True, padx=20)

        # Available Tanks
        tank_frame = ttk.LabelFrame(container, text="Available Tanks", padding=5)
        tank_frame.pack(fill="x", expand=True, pady=5)

        self.available_tanks_list = tk.Listbox(tank_frame, 
                                           height=8,
                                           selectmode=tk.MULTIPLE,
                                           font=("Arial", 10))
        self.available_tanks_list.pack(fill="both", expand=True, pady=5)

        # Populate the listbox with 12 tanks
        for i in range(1, 13):
            self.available_tanks_list.insert(tk.END, f"Tk{i}")

        # Launch Clients Button
        ttk.Button(
            tank_frame,
            text="Launch Selected Clients",
            style="Tank.TButton",
            command=self.launch_clients
        ).pack(fill="x", pady=5)

        # Status Frames Container
        status_container = ttk.Frame(container)
        status_container.pack(fill="x", expand=True)
        
        # Online Tanks
        online_frame = ttk.LabelFrame(status_container, text="Online Tanks", padding=5)
        online_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.online_tanks_list = tk.Listbox(online_frame,
                                          height=6,
                                          selectmode=tk.SINGLE,
                                          font=("Arial", 10),
                                          bg="#d4edda")
        self.online_tanks_list.pack(fill="both", expand=True, pady=5)

        # Offline Tanks
        offline_frame = ttk.LabelFrame(status_container, text="Offline Tanks", padding=5)
        offline_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.offline_tanks_list = tk.Listbox(offline_frame,
                                           height=6,
                                           selectmode=tk.SINGLE,
                                           font=("Arial", 10),
                                           bg="#f8d7da")
        self.offline_tanks_list.pack(fill="both", expand=True, pady=5)

    def launch_clients(self):
        """Launch client GUIs for selected tanks"""
        selected_indices = self.available_tanks_list.curselection()
        selected_tanks = [self.available_tanks_list.get(i) for i in selected_indices]

        if not selected_tanks:
            messagebox.showwarning("No Tanks Selected", "Please select at least one tank to launch clients.")
            return

        for tank_id in selected_tanks:
            self.launch_client_gui(tank_id)

    def launch_client_gui(self, tank_id):
        """Launch a client GUI for the given tank"""
        try:
            # Use sys.executable to ensure the correct Python interpreter is used
            subprocess.Popen([sys.executable, "client_auth_gui.py", tank_id])
            self.log(f"Launched client GUI for {tank_id}")
            
            # Move tank to offline list
            self.move_tank_to_list(tank_id, "offline")
            
        except Exception as e:
            self.log(f"Failed to launch client GUI for {tank_id}: {e}", level="ERROR")

    def move_tank_to_list(self, tank_id, status):
        """Move tank between available, online, and offline lists"""
        # Remove from all lists first
        lists = {
            "available": self.available_tanks_list,
            "online": self.online_tanks_list,
            "offline": self.offline_tanks_list
        }
        
        for lst in lists.values():
            for i in range(lst.size()):
                if tank_id in lst.get(i):
                    lst.delete(i)
                    break
        
        # Add to appropriate list
        if status == "online":
            self.online_tanks_list.insert(tk.END, tank_id)
        elif status == "offline":
            self.offline_tanks_list.insert(tk.END, tank_id)
        else:  # available
            self.available_tanks_list.insert(tk.END, tank_id)

    def create_map_section(self):
        map_frame = ttk.LabelFrame(self.center_panel, text="Tactical Map", padding=10)
        map_frame.pack(fill="both", expand=True)

        self.map_widget = TkinterMapView(map_frame, width=800, height=600)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(17.385044, 78.486671)
        self.map_widget.set_zoom(10)

    def create_control_section(self):
        # Server Controls
        control_frame = ttk.LabelFrame(self.right_panel, text="Server Controls", padding=10)
        control_frame.pack(fill="x")

        self.server_status = ttk.Label(
            control_frame,
            text="Server Status: Stopped",
            font=("Arial", 10)
        )
        self.server_status.pack(fill="x", pady=5)

        self.start_button = ttk.Button(
            control_frame,
            text="Start Server",
            command=self.start_server
        )
        self.start_button.pack(fill="x", pady=5)

        # Log Section
        log_frame = ttk.LabelFrame(self.right_panel, text="Server Logs", padding=10)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True)

    def on_tank_selected(self, event):
        selection = self.tank_listbox.curselection()
        if selection:
            self.selected_tank = self.tank_listbox.get(selection[0])
            self.center_on_tank(self.selected_tank)
            if self.show_paths:
                self.show_tank_path(self.selected_tank)

    def toggle_path_visibility(self):
        self.show_paths = not self.show_paths
        if self.selected_tank:
            if self.show_paths:
                self.show_tank_path(self.selected_tank)
            else:
                self.clear_path(self.selected_tank)

    def show_tank_path(self, tank_id):
        self.clear_path(tank_id)
        locations = self.get_tank_locations(tank_id)
        if len(locations) > 1:
            path_points = [(lat, lon) for _, lat, lon in locations]
            self.tank_paths[tank_id] = self.map_widget.set_path(path_points)

    def clear_path(self, tank_id):
        if tank_id in self.tank_paths:
            self.tank_paths[tank_id].delete()
            del self.tank_paths[tank_id]

    def clear_selected_path(self):
        if self.selected_tank:
            self.clear_path(self.selected_tank)

    def center_on_tank(self, tank_id):
        if tank_id in self.tank_markers:
            marker = self.tank_markers[tank_id]
            self.map_widget.set_position(marker.position[0], marker.position[1])
            self.map_widget.set_zoom(15)

    def get_tank_locations(self, tank_id):
        locations = []
        try:
            with open(LOCATIONS_CSV, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if row[0] == tank_id:
                        timestamp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                        lat, lon = float(row[2]), float(row[3])
                        locations.append((timestamp, lat, lon))
        except FileNotFoundError:
            pass
        return sorted(locations, key=lambda x: x[0])

    def store_location(self, tank_id, lat, lon):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOCATIONS_CSV, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([tank_id, timestamp, lat, lon])

    def update_tank_marker(self, tank_id, lat, lon):
        if tank_id in self.tank_markers:
            self.tank_markers[tank_id].delete()

        # Create new marker with arrow indicating direction
        prev_locations = self.get_tank_locations(tank_id)
        if len(prev_locations) > 1:
            prev_lat, prev_lon = prev_locations[-2][1:3]
            # Calculate direction arrow
            direction = "→"
            if lat > prev_lat:
                direction = "↑"
            elif lat < prev_lat:
                direction = "↓"
            elif lon > prev_lon:
                direction = "→"
            elif lon < prev_lon:
                direction = "←"
        else:
            direction = "→"

        marker = self.map_widget.set_marker(
            lat, lon,
            text=f"{tank_id} {direction}",
            command=lambda: self.show_tank_info(tank_id)
        )
        self.tank_markers[tank_id] = marker

        # Update path if showing
        if self.show_paths and self.selected_tank == tank_id:
            self.show_tank_path(tank_id)

    def show_tank_info(self, tank_id):
        locations = self.get_tank_locations(tank_id)
        if locations:
            latest = locations[-1]
            info = f"Tank: {tank_id}\n"
            info += f"Last Update: {latest[0]}\n"
            info += f"Position: {latest[1]}, {latest[2]}"
            messagebox.showinfo("Tank Information", info)

    def _initialize_crypto(self):
        try:
            keys = get_random_keys()
            (
                self.key_aes,
                self.key_des,
                self.key_tdes,
                self.private_key_rsa,
                self.public_key_rsa,
                self.private_key_ecc,
                self.public_key_ecc,
            ) = keys
            
            self.methods, self.sequence_hash = get_random_sequence_from_csv()
            self.crypto_initialized = True
            self.log("Cryptography initialized successfully")
        except Exception as e:
            self.log(f"Failed to initialize cryptography: {e}", "ERROR")
            self.crypto_initialized = False

    def start_server(self):
        if not self.server_running:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind(("localhost", 12345))
                self.server_socket.listen(5)
                self.server_running = True
                
                self.start_button.config(text="Stop Server")
                self.server_status.config(text="Server Status: Running")
                self.log("Server started successfully")
                
                threading.Thread(target=self.accept_connections, daemon=True).start()
            except Exception as e:
                self.log(f"Failed to start server: {e}", "ERROR")
        else:
            self.stop_server()

    def stop_server(self):
        if self.server_running:
            try:
                self.server_socket.close()
                self.server_running = False
                self.start_button.config(text="Start Server")
                self.server_status.config(text="Server Status: Stopped")
                self.log("Server stopped")
            except Exception as e:
                self.log(f"Error stopping server: {e}", "ERROR")

    def accept_connections(self):
        while self.server_running:
            try:
                conn, addr = self.server_socket.accept()
                self.log(f"New connection from {addr}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.server_running:
                    self.log(f"Connection error: {e}", "ERROR")

    def handle_client(self, conn, addr):
        try:
            tank_id = conn.recv(1024).decode().strip()
            self.log(f"Tank {tank_id} connected")
            
            # Add to tank list
            self.root.after(0, lambda: self.tank_listbox.insert(tk.END, tank_id))
            
            # Generate and send challenge
            challenge_msg, expected_answer = self.generate_challenge()
            conn.send(f"Challenge: {challenge_msg}".encode())
            
            # Handle authentication
            response = conn.recv(1024).decode().strip()
            
            if response == expected_answer:
                conn.send("Authentication Successful".encode())
                self.log(f"Tank {tank_id} authenticated")
                self.handle_tank_communication(conn, tank_id)
            else:
                conn.send("Authentication Failed".encode())
                self.log(f"Tank {tank_id} authentication failed")
            
        except Exception as e:
            self.log(f"Error handling client: {e}", "ERROR")
        finally:
            conn.close()
            # Remove from tank list
            self.root.after(0, lambda: self.remove_tank(tank_id))

    def remove_tank(self, tank_id):
        for i in range(self.tank_listbox.size()):
            if self.tank_listbox.get(i) == tank_id:
                self.tank_listbox.delete(i)
                break
        if tank_id in self.tank_markers:
            self.tank_markers[tank_id].delete()
            del self.tank_markers[tank_id]

    def generate_challenge(self):
        challenge_type = random.randint(0, 9)
        if challenge_type == 0:
            return "0", "OK"
        num = random.randint(2, 20)
        return f"{challenge_type} {num}", self.calculate_expected_answer(challenge_type, num)

    def calculate_expected_answer(self, challenge_type, num):
        if challenge_type == 1:
            return str(num ** 2)
        elif challenge_type == 2:
            return str(num ** 3)
        elif challenge_type == 3:
            return str(num * (num + 1) // 2)
        elif challenge_type == 4:
            return str(num % 2 == 0)
        elif challenge_type == 5:
            return str(num % 2 != 0)
        elif challenge_type == 6:
            return str(num * 2)
        elif challenge_type == 7:
            return "Prime" if all(num % i != 0 for i in range(2, int(num**0.5) + 1)) and num > 1 else "Not Prime"
        elif challenge_type == 8:
            return "".join(reversed(str(num)))
        elif challenge_type == 9:
            return str(len(bin(num)) - 2)
        return "OK"

    def handle_tank_communication(self, conn, tank_id):
        try:
            conn.send("Are you ready?".encode())
            readiness = conn.recv(1024).decode().strip()
            
            if readiness.lower() in ["yes", "ready", "ok"]:
                while True:
                    conn.send("Give me your location".encode())
                    
                    data = ""
                    while True:
                        chunk = conn.recv(1024).decode()
                        if not chunk:
                            break
                        data += chunk
                        if "\n" in data:
                            break
                    
                    if not data:
                        break
                    
                    try:
                        payload = json.loads(data.strip())
                        location = self.decrypt_location(payload, tank_id)
                        
                        if location:
                            lat, lon = map(float, location.split(","))
                            self.store_location(tank_id, lat, lon)
                            self.root.after(0, lambda: self.update_tank_marker(tank_id, lat, lon))
                            self.log(f"Location received from Tank {tank_id}: {lat}, {lon}")
                    except json.JSONDecodeError:
                        self.log(f"Invalid JSON from Tank {tank_id}", "ERROR")
                    except Exception as e:
                        self.log(f"Error processing location from Tank {tank_id}: {e}", "ERROR")
                        
        except Exception as e:
            self.log(f"Communication error with Tank {tank_id}: {e}", "ERROR")

    def decrypt_location(self, payload, tank_id):
        try:
            index = payload["random_index"]
            hash_value = payload["sequence_hash"]
            methods = find_sequence_by_hash(hash_value)
            
            if not methods:
                return None
                
            keys = get_keys_by_index(index)
            if not keys or len(keys) != 7:
                return None
                
            key_aes, key_des, key_tdes, private_key_rsa, public_key_rsa, private_key_ecc, public_key_ecc = keys
            
            decrypted_location = decrypt_data(
                payload["ivs"],
                payload["data"],
                payload["tags"],
                methods,
                key_aes,
                key_des,
                key_tdes,
                private_key_rsa,
                private_key_ecc
            )
            
            is_valid = verify_signature(
                decrypted_location,
                payload["signature"],
                public_key_rsa
            )
            
            if not is_valid:
                return None
                
            return decrypted_location
            
        except Exception as e:
            self.log(f"Decryption error for Tank {tank_id}: {str(e)}", "ERROR")
            return None

    def log(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        
        logging.log(
            getattr(logging, level),
            message
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = CommanderGUI(root)
    root.mainloop()