import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

CONFIG_FILE = 'backup_config.json'
SNAPSHOT_FILE = 'snapshot.json'
LOG_FILE = 'log.txt'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def log_message(message, log_widget, log_to_file=True):
    print(message)
    log_widget.insert(tk.END, message + '\n')
    log_widget.yview(tk.END)
    if log_to_file:
        with open(LOG_FILE, 'a', encoding='utf-8') as file:
            file.write(message + '\n')

def should_copy_file(source_item, snapshot_data):
    """Determine if a file should be copied based on the snapshot data."""
    source_stat = os.stat(source_item)
    if source_item not in snapshot_data:
        return True
    snapshot_stat = snapshot_data[source_item]
    if source_stat.st_size != snapshot_stat['size'] or source_stat.st_mtime > snapshot_stat['mtime']:
        return True
    return False


def update_snapshot(source_item, snapshot_data):
    """Update the snapshot data with the current state of a file."""
    source_stat = os.stat(source_item)
    snapshot_data[source_item] = {
        'size': source_stat.st_size,
        'mtime': source_stat.st_mtime
    }
def sync_file(source_item, destination_item, snapshot_data, log_widget):
    """Synchronize a single file from source to destination."""
    try:
        if should_copy_file(source_item, snapshot_data):
            log_message(f"Copying: {source_item} to {destination_item}", log_widget)
            shutil.copy2(source_item, destination_item)
            update_snapshot(source_item, snapshot_data)
            log_message(f"Finished copying: {source_item} to {destination_item}", log_widget)
        else:
            log_message(f"Skipped (identical): {source_item}", log_widget, log_to_file=False)
    except Exception as e:
        log_message(f"Error copying {source_item}: {str(e)}", log_widget)
        
def sync_folders(source, destination, snapshot_data, log_widget):
    """Synchronize folders between source and destination."""
    if not os.path.exists(destination):
        os.makedirs(destination)
        log_message(f"Created directory: {destination}", log_widget)

    source_items = set(os.listdir(source))
    destination_items = set(os.listdir(destination))

    for item in source_items.union(destination_items):
        source_item = os.path.join(source, item)
        destination_item = os.path.join(destination, item)

        if item in source_items and os.path.isdir(source_item):
            sync_folders(source_item, destination_item, snapshot_data, log_widget)
        elif item in source_items and os.path.isfile(source_item):
            sync_file(source_item, destination_item, snapshot_data, log_widget)
        elif item in destination_items and os.path.isfile(destination_item):
            # Handle files present in destination but not in source
            if item not in source_items:
                log_message(f"New file in destination: {destination_item}", log_widget)
                # Decide on copying back to source or another action
        elif item in destination_items and os.path.isdir(destination_item):
            # Handle new directories in destination
            log_message(f"New directory in destination: {destination_item}", log_widget)
            # Decide on action to sync back to source

def start_sync_thread():
    thread = threading.Thread(target=start_sync)
    thread.start()


# Main sync logic
def start_sync():
    config = load_json(CONFIG_FILE)
    snapshot_data = load_json(SNAPSHOT_FILE)
    destination = destination_folder.get()

    if not destination:
        messagebox.showwarning("Input Error", "Please select a destination folder.")
        return

    log_widget.delete(1.0, tk.END)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    for source in config['source_folders']:
        folder_name = os.path.basename(source)
        destination_path = os.path.join(destination, folder_name)
        sync_folders(source, destination_path, snapshot_data, log_widget)

    save_json(snapshot_data, SNAPSHOT_FILE)
    messagebox.showinfo("Sync Complete", "Folders have been synchronized successfully.")

def browse_source():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        source_listbox.insert(tk.END, folder_selected)
        config = load_json(CONFIG_FILE)
        config['source_folders'].append(folder_selected)
        save_json(config, CONFIG_FILE)

def delete_source():
    selected_indices = source_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select a folder to delete.")
        return

    selected_index = selected_indices[0]
    source_listbox.delete(selected_index)

    config = load_json(CONFIG_FILE)
    del config['source_folders'][selected_index]
    save_json(config, CONFIG_FILE)

def browse_destination():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_folder.set(folder_selected)
        config = load_json(CONFIG_FILE)
        config['destination'] = folder_selected
        save_json(config, CONFIG_FILE)

def load_saved_folders():
    config = load_json(CONFIG_FILE)
    destination_folder.set(config.get('destination', ''))
    for folder in config.get('source_folders', []):
        source_listbox.insert(tk.END, folder)

# Create the main window
root = tk.Tk()
root.title("Folder Sync")

# Create StringVar to hold folder paths
destination_folder = tk.StringVar()

# Create and place widgets
tk.Label(root, text="Source Folders:").grid(row=0, column=0, padx=10, pady=10)
source_listbox = tk.Listbox(root, width=50, height=10)
source_listbox.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Add Source Folder", command=browse_source).grid(row=0, column=2, padx=10, pady=10)
tk.Button(root, text="Delete Source Folder", command=delete_source).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Destination Folder:").grid(row=2, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=destination_folder, width=50).grid(row=2, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_destination).grid(row=2, column=2, padx=10, pady=10)

tk.Button(root, text="Start Sync", command=start_sync_thread).grid(row=3, column=1, pady=20)

log_widget = tk.Text(root, height=10, width=70)
log_widget.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

# Load saved folders on startup
load_saved_folders()

# Run the application
root.mainloop()
