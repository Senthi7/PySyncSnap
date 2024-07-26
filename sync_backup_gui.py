import os
import shutil
import filecmp
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading
import time

CONFIG_FILE = 'backup_config.json'  # The configuration file to save/load source and destination folders
LOG_FILE = 'log.txt'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {'source_folders': [], 'destination': ''}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)

def log_message(message, log_widget, log_file):
    print(message)  # Print message for debugging in console
    log_widget.insert(tk.END, message + '\n')
    log_widget.yview(tk.END)
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(message + '\n')

def should_copy_file(source_item, destination_item):
    """Check if a file should be copied based on its metadata and content."""
    if not os.path.exists(destination_item):
        return True

    source_stat = os.stat(source_item)
    destination_stat = os.stat(destination_item)

    if source_stat.st_size != destination_stat.st_size or source_stat.st_mtime > destination_stat.st_mtime:
        return True

    return False

def sync_folders(source, destination, log_widget):
    if not os.path.exists(destination):
        os.makedirs(destination)
        log_message(f"Created directory: {destination}", log_widget, LOG_FILE)
    
    for item in os.listdir(source):
        source_item = os.path.join(source, item)
        destination_item = os.path.join(destination, item)

        log_message(f"Processing item: {source_item}", log_widget, LOG_FILE)
        start_time = time.time()

        if os.path.isdir(source_item):
            log_message(f"Entering directory: {source_item}", log_widget, LOG_FILE)
            sync_folders(source_item, destination_item, log_widget)
        else:
            if should_copy_file(source_item, destination_item):
                try:
                    pre_copy_time = time.time()
                    log_message(f"Preparing to copy: {source_item} to {destination_item}", log_widget, LOG_FILE)
                    if not os.path.exists(os.path.dirname(destination_item)):
                        os.makedirs(os.path.dirname(destination_item))
                    copy_start_time = time.time()
                    log_message(f"Start copying: {source_item} to {destination_item}", log_widget, LOG_FILE)
                    shutil.copy2(source_item, destination_item)
                    copy_end_time = time.time()
                    log_message(f"Finished copying: {source_item} to {destination_item} in {copy_end_time - copy_start_time} seconds", log_widget, LOG_FILE)
                except Exception as e:
                    log_message(f"Error copying {source_item} to {destination_item}: {str(e)}", log_widget, LOG_FILE)
            else:
                log_message(f"Skipped (identical): {source_item}", log_widget, LOG_FILE)

        end_time = time.time()
        log_message(f"Time taken to process {source_item}: {end_time - start_time} seconds", log_widget, LOG_FILE)

def start_sync_thread():
    thread = threading.Thread(target=start_sync)
    thread.start()

def start_sync():
    config = load_config()
    destination = destination_folder.get()
    
    if not destination:
        messagebox.showwarning("Input Error", "Please select a destination folder.")
        return
    
    log_widget.delete(1.0, tk.END)  # Clear the log widget
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)  # Remove the old log file if it exists
    
    for source in config['source_folders']:
        folder_name = os.path.basename(source)
        destination_path = os.path.join(destination, folder_name)
        sync_folders(source, destination_path, log_widget)
    
    messagebox.showinfo("Sync Complete", "Folders have been synchronized successfully.")

def browse_source():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        source_listbox.insert(tk.END, folder_selected)
        config = load_config()
        config['source_folders'].append(folder_selected)
        save_config(config)

def delete_source():
    selected_indices = source_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select a folder to delete.")
        return
    
    selected_index = selected_indices[0]
    source_listbox.delete(selected_index)
    
    config = load_config()
    del config['source_folders'][selected_index]
    save_config(config)

def browse_destination():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_folder.set(folder_selected)
        config = load_config()
        config['destination'] = folder_selected
        save_config(config)

def load_saved_folders():
    config = load_config()
    destination_folder.set(config['destination'])
    for folder in config['source_folders']:
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
