import os
import json
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = 'backup_config.json'
SNAPSHOT_FILE = 'snapshot.json'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def update_snapshot(source_item, snapshot_data):
    """Update the snapshot data with the current state of a file."""
    source_stat = os.stat(source_item)
    snapshot_data[source_item] = {
        'size': source_stat.st_size,
        'mtime': source_stat.st_mtime
    }

def create_initial_snapshot(source, snapshot_data):
    """Create an initial snapshot without copying files."""
    for item in os.listdir(source):
        source_item = os.path.join(source, item)
        if os.path.isdir(source_item):
            create_initial_snapshot(source_item, snapshot_data)
        else:
            update_snapshot(source_item, snapshot_data)

def start_snapshot_creation():
    config = load_json(CONFIG_FILE)
    snapshot_data = {}

    if 'source_folders' not in config:
        messagebox.showerror("Error", "No source folders specified in the configuration file.")
        return

    for source in config['source_folders']:
        if not os.path.exists(source):
            messagebox.showerror("Error", f"Source folder not found: {source}")
            continue
        create_initial_snapshot(source, snapshot_data)

    save_json(snapshot_data, SNAPSHOT_FILE)
    messagebox.showinfo("Success", "Initial snapshot created successfully.")

def create_gui():
    root = tk.Tk()
    root.title("Create Initial Snapshot")

    label = tk.Label(root, text="Create Initial Snapshot for Synchronization", padx=20, pady=20)
    label.pack()

    create_button = tk.Button(root, text="Create Snapshot", command=start_snapshot_creation, padx=20, pady=10)
    create_button.pack()

    root.mainloop()

if __name__ == "__main__":
    create_gui()
