import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import hashlib

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

def calculate_file_hash(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def should_copy_file(source_item, snapshot_data):
    source_stat = os.stat(source_item)
    source_hash = calculate_file_hash(source_item)
    if source_item not in snapshot_data:
        log_message(f"New file detected: {source_item}", log_widget)
        return True
    snapshot_stat = snapshot_data[source_item]
    if source_stat.st_size != snapshot_stat['size'] or source_stat.st_mtime > snapshot_stat['mtime']:
        log_message(f"File changed (size/mtime) detected: {source_item}", log_widget)
        return True
    if 'hash' in snapshot_stat and snapshot_stat['hash'] != source_hash:
        log_message(f"File content changed detected: {source_item}", log_widget)
        return True
    return False

def update_snapshot(source_item, snapshot_data):
    source_stat = os.stat(source_item)
    source_hash = calculate_file_hash(source_item)
    snapshot_data[source_item] = {
        'size': source_stat.st_size,
        'mtime': source_stat.st_mtime,
        'hash': source_hash
    }

def find_renamed_file(source_item, destination, destination_items, snapshot_data):
    """Try to find if a source file has been renamed in the destination."""
    source_hash = calculate_file_hash(source_item)
    for dest_item in destination_items:
        dest_path = os.path.join(destination, dest_item)
        if dest_path in snapshot_data:
            dest_hash = calculate_file_hash(dest_path)
            if source_hash == dest_hash:
                return dest_path
    return None

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

    for item in source_items:
        source_item = os.path.join(source, item)
        destination_item = os.path.join(destination, item)

        if os.path.isdir(source_item):
            sync_folders(source_item, destination_item, snapshot_data, log_widget)
        elif os.path.isfile(source_item):
            if not os.path.exists(destination_item):
                renamed = find_renamed_file(source_item, destination, destination_items, snapshot_data)
                if renamed:
                    log_message(f"Detected rename: {renamed} -> {destination_item}", log_widget)
                    os.rename(renamed, destination_item)
                    update_snapshot(source_item, snapshot_data)
                else:
                    sync_file(source_item, destination_item, snapshot_data, log_widget)
            else:
                sync_file(source_item, destination_item, snapshot_data, log_widget)

def start_sync_thread():
    thread = threading.Thread(target=start_sync)
    thread.start()

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

# GUI setup
root = tk.Tk()
root.title("Folder Sync")

destination_folder = tk.StringVar()

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

load_saved_folders()

root.mainloop()
