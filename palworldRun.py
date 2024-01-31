import subprocess
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sv_ttk
import psutil
from sys import platform
import re
import traceback
import threading
import time
import queue
from utility.palworld_util import PalworldUtil
import csv
import io


def is_application_running(app_name):
    """Check if the application is currently running."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == app_name:
            return True
    return False

def run_bat_file(file_path):
    try:
        subprocess.run(file_path, shell=True)
        messagebox.showinfo("Info", "Application started successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start the application: {e}")

def close_application(app_name):
    try:
        os.system(f"taskkill /f /im {app_name}")
        messagebox.showinfo("Info", "Application stopped successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop the application: {e}")

def restart_application(file_path, app_name):
    close_application(app_name)
    run_bat_file(file_path)

class ApplicationControlGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        sv_ttk.set_theme("dark")
        cursor_point = "hand2" if platform != "darwin" else "pointinghand"

        self.app_name = 'PalworldControlCenter'  # Replace with your application's name
        self.config_file_name = 'app_config.txt'
        self.config_dir = os.path.join(os.environ['APPDATA'], self.app_name)
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.first_time_setup()
        self.update_players_active = False
        self.application_name = 'PalServer-Win64-Test-Cmd.exe'

        # Status Indicator
        self.status_canvas = tk.Canvas(self, width=20, height=20)
        self.status_canvas.grid(column=3, row=2, padx=(0, 20), pady=20, sticky=tk.W)
        self.status_canvas.create_oval(5, 5, 15, 15, fill="red", tags="status_circle")
        self.update_status_indicator()
        self.player_count_label = ttk.Label(self, text="Player Count: N/A")
        self.player_count_label.grid(column=2, row=2, padx=10, pady=10)

        # Notebook (tab control)
        self.notebook = ttk.Notebook(self)
        self.app_control_frame = ttk.Frame(self.notebook)
        self.config_edit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.app_control_frame, text='App Control')
        self.notebook.add(self.config_edit_frame, text='Config Editor')
        self.notebook.grid(row=1, column=0, columnspan=4, sticky='nesw', padx=10, pady=10)

        # Make the notebook expandable
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Application Control tab
        start_button = ttk.Button(self.app_control_frame, text="Start", command=self.start_app)
        start_button.grid(column=0, row=0, padx=20, pady=20, sticky=tk.W)

        shutdown_button = ttk.Button(self.app_control_frame, text="Stop", command=self.shutdown_app)
        shutdown_button.grid(column=1, row=0, padx=20, pady=20, sticky=tk.W)

        kill_button = ttk.Button(self.app_control_frame, text="Kill", command=self.stop_app)
        kill_button.grid(column=2, row=0, padx=20, pady=20, sticky=tk.W)

        restart_button = ttk.Button(self.app_control_frame, text="restart", command=self.restart_app)
        restart_button.grid(column=3, row=0, padx=20, pady=20, sticky=tk.W)

        save_button = ttk.Button(self.app_control_frame, text="Save", command=self.save_app)
        save_button.grid(column=4, row=0, padx=20, pady=20, sticky=tk.W)

        # Label for Online Players Listbox
        online_players_label = ttk.Label(self.app_control_frame, text="Online Players")
        online_players_label.grid(column=0, row=1, padx=20, pady=(10, 0), sticky="w")

        # Player Names Listbox
        self.player_names_listbox = tk.Listbox(self.app_control_frame, height=10)
        self.player_names_listbox.grid(column=0, row=2, columnspan=3, padx=20, pady=(0, 10), sticky="ew")



        # Config Editor tab setup with scrollable area
        self.config_canvas = tk.Canvas(self.config_edit_frame)
        self.config_scrollbar = ttk.Scrollbar(self.config_edit_frame, orient="vertical", command=self.config_canvas.yview)
        self.inner_frame = ttk.Frame(self.config_canvas)

        self.config_canvas.pack(side="left", fill="both", expand=True)
        self.config_scrollbar.pack(side="right", fill="y")
        self.config_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", lambda e: self.config_canvas.configure(scrollregion=self.config_canvas.bbox("all")))
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)

        self.config_vars = {}
        self.create_config_editor_fields()

        # Config Editor Buttons
        save_button = ttk.Button(self.inner_frame, text='Save Config', command=self.save_config)
        save_button.grid(row=len(self.config_vars) + 1, column=0, columnspan=2, pady=10)

        # CPU and Memory usage display for Palworld
        self.pal_cpu_label = ttk.Label(self, text="Palworld CPU Usage: 0%")
        self.pal_cpu_label.grid(column=0, row=2, padx=10, pady=10)

        self.pal_memory_label = ttk.Label(self, text="Palworld Memory Usage: 0%")
        self.pal_memory_label.grid(column=1, row=2, padx=10, pady=10)

        # Set up threading and queue for resource monitoring
        self.is_running = True
        self.resource_usage_queue = queue.Queue()
        self.start_resource_monitoring_thread()
        self.check_resource_usage_queue()

    def update_status_indicator(self):
        """Update the status indicator and player count."""
        if is_application_running(self.application_name):
            self.is_running = True
            self.status_canvas.itemconfig("status_circle", fill="green")
            self.update_player_count()  # Ensure this method exists and is correctly implemented
        else:
            self.status_canvas.itemconfig("status_circle", fill="red")


    def start_resource_monitoring_thread(self):
        """Starts the resource monitoring in a separate thread."""
        self.monitor_thread = threading.Thread(target=self.update_palworld_resource_usage)
        self.monitor_thread.daemon = True  # Ensure that the thread will end when the main program quits.
        self.monitor_thread.start()

    def update_palworld_resource_usage(self):
        while self.is_running:
            palworld_process = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.application_name:
                    palworld_process = proc
                    break
            if palworld_process:
                cpu_usage = palworld_process.cpu_percent(interval=1) / psutil.cpu_count()
                memory_usage_bytes = palworld_process.memory_info().rss
                memory_usage_gb = memory_usage_bytes / (1024 ** 3)
                self.resource_usage_queue.put((f"Palworld CPU Usage: {cpu_usage:.2f}%", f"Palworld Memory Usage: {memory_usage_gb:.2f} GB"))
            else:
                self.resource_usage_queue.put(("Palworld CPU Usage: N/A", "Palworld Memory Usage: N/A"))

            time.sleep(1)

    def check_resource_usage_queue(self):
        try:
            cpu_usage, memory_usage = self.resource_usage_queue.get_nowait()
            self.pal_cpu_label.config(text=cpu_usage)
            self.pal_memory_label.config(text=memory_usage)
        except queue.Empty:
            pass
        self.after(1000, self.check_resource_usage_queue)


    def __del__(self):
        """Ensures the resource monitoring thread is stopped when the GUI is closed."""
        self.is_running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()

    def format_label(self, text):
        """Format the field names to add spaces before uppercase letters, keeping certain abbreviations."""
        exceptions = ["RCON", "PvP", "URL", "UNKO"]  # List of abbreviations to keep intact
        for exc in exceptions:
            text = text.replace(exc, exc.capitalize())
        formatted_text = re.sub(r"(\w)([A-Z])", r"\1 \2", text)
        if formatted_text.startswith('b'):
            formatted_text = formatted_text[1:]
        if formatted_text.startswith(' '):
            formatted_text = formatted_text[1:]
        formatted_text = formatted_text.replace('_', ' ')
        for exc in exceptions:
            formatted_text = formatted_text.replace(exc.capitalize(), exc)
        return formatted_text

    def create_config_editor_fields(self):
        quoted_fields = ["ServerName", "ServerDescription", "AdminPassword", "ServerPassword", "PublicIP", "Region", "BanListURL"]
        try:
            with open(self.config_path, 'r') as file:
                content = file.read()

            settings_line = re.search(r'\((.*)\)', content).group(1)
            settings = dict(item.split('=') for item in settings_line.split(','))

            for idx, (key, value) in enumerate(settings.items()):
                formatted_key = self.format_label(key)
                label = ttk.Label(self.inner_frame, text=formatted_key)
                label.grid(row=idx, column=0, padx=10, pady=5, sticky=tk.W)

                if value in ["True", "False"]:
                    var = tk.StringVar(value=value)
                    dropdown = ttk.Combobox(self.inner_frame, textvariable=var, values=["True", "False"], state="readonly")
                    dropdown.grid(row=idx, column=1, padx=10, pady=5, sticky=tk.W)
                else:
                    if key in quoted_fields:
                        value = value.strip('"')  # Remove quotes
                    var = tk.StringVar(value=value)
                    entry = ttk.Entry(self.inner_frame, textvariable=var, width=30)
                    entry.grid(row=idx, column=1, padx=10, pady=5, sticky=tk.W)

                self.config_vars[key] = var
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load config file: {e}')

    def get_player_count(self):
        try:
            rcon_ip = self.config_vars['PublicIP'].get() or '127.0.0.1'
            rcon_port = int(self.config_vars['RCONPort'].get())  # Assuming you have an RCONPort field
            rcon_password = self.config_vars['AdminPassword'].get()  # Assuming you have an RCONPassword field
            server_name = "this"
            pal = PalworldUtil("", server_name, rcon_ip, rcon_port, rcon_password)
            response = pal.rcon.run_command('ShowPlayers', [])
            return response
            # Process the response here to extract player count and update the label
        except Exception as e:
            print("Error in get_player_count:", e)


    def shutdown_app(self):
        try:
            rcon_ip = self.config_vars['PublicIP'].get() or '127.0.0.1'
            rcon_port = int(self.config_vars['RCONPort'].get())  # Assuming you have an RCONPort field
            rcon_password = self.config_vars['AdminPassword'].get()  # Assuming you have an RCONPassword field
            server_name = "this"
            pal = PalworldUtil("", server_name, rcon_ip, rcon_port, rcon_password)
            response = pal.rcon.run_command('Shutdown', [])
            if response:
                response = response.split(".")[0]
                messagebox.showinfo("Shut Down", response)
                self.after(30000, self.deactivate_player_updates)
            # Process the response here to extract player count and update the label
        except Exception as e:
            print("Error in get_player_count:", e)

    def deactivate_player_updates(self):
        self.update_players_active = False
        self.is_running = False
        self.status_canvas.itemconfig("status_circle", fill="red")


    def save_app(self):
        try:
            rcon_ip = self.config_vars['PublicIP'].get() or '127.0.0.1'
            rcon_port = int(self.config_vars['RCONPort'].get())  # Assuming you have an RCONPort field
            rcon_password = self.config_vars['AdminPassword'].get()  # Assuming you have an RCONPassword field
            server_name = "this"
            pal = PalworldUtil("", server_name, rcon_ip, rcon_port, rcon_password)
            response = pal.rcon.run_command('Save', [])
            if response:
                response = response.split(".")[0]
                messagebox.showinfo("Save", response)
            # Process the response here to extract player count and update the label
        except Exception as e:
            print("Error in get_player_count:", e)



    def update_player_count(self):
        if not self.update_players_active:
            # Clear the player names listbox and update the label to show zero players
            self.player_names_listbox.delete(0, tk.END)
            self.player_count_label.config(text="Player Count: 0")
            return
        player_data = self.get_player_count()
        csv_data = io.StringIO(player_data)
        reader = csv.reader(csv_data)

        # Clear the current list
        self.player_names_listbox.delete(0, tk.END)

        player_count = 0
        for row in reader:
            # Assuming the first column is the player name
            if player_count > 0:  # Skip the header row
                self.player_names_listbox.insert(tk.END, row[0])
            player_count += 1

        if player_count > 0:
            self.player_count_label.config(text=f"Player Count: {player_count - 1}")
        else:
            self.player_count_label.config(text=f"Player Count: 0")
        self.after(10000, self.update_player_count)
        

    def save_config(self):
        quoted_fields = ["ServerName", "ServerDescription", "AdminPassword", "ServerPassword", "PublicIP", "Region", "BanListURL"]
        try:
            with open(self.config_path, 'w') as file:
                settings_str = []
                for key, var in self.config_vars.items():
                    value = var.get()
                    if key in quoted_fields:
                        # Add quotes around specific fields
                        settings_str.append(f"{key}=\"{value}\"")
                    else:
                        # Leave other fields as they are
                        settings_str.append(f"{key}={value}")
                file.write("[/Script/Pal.PalGameWorldSettings]\nOptionSettings=(" + ",".join(settings_str) + ")")
            messagebox.showinfo('Info', 'Config file saved successfully.')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save config file: {e}')



    def start_app(self):
        run_bat_file(self.bat_file_path)
        if self.is_running == False:
            self.is_running = True
            self.start_resource_monitoring_thread()
        threading.Timer(10, self.update_status_indicator).start()
        self.update_players_active = True

    def stop_app(self):
        close_application(self.application_name)
        self.after(5000, self.deactivate_player_updates)

    def restart_app(self):
        self.deactivate_player_updates
        restart_application(self.bat_file_path, self.application_name)
        self.update_players_active = True
        threading.Timer(10, self.update_status_indicator).start()


    def first_time_setup(self):
        config_file_path = os.path.join(self.config_dir, self.config_file_name)
        # Check if the configuration file with the steamcmd path exists
        if os.path.isfile(config_file_path):
            with open(config_file_path, 'r') as file:
                steamcmd_folder = file.read().strip()
        else:
            # If not, prompt the user to select the steamcmd folder
            steamcmd_folder = tk.filedialog.askdirectory(title="Select steamcmd folder")
            if not steamcmd_folder:
                messagebox.showerror("Error", "steamcmd folder selection is required.")
                return
            # Save the selected path for future use
            with open(config_file_path, 'w') as file:
                file.write(steamcmd_folder)

        # Set the paths for .bat file and ini configuration file
        self.bat_file_path = os.path.join(steamcmd_folder, "start.bat")
        self.config_path = os.path.join(steamcmd_folder, "steamapps/common/PalServer/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini")

        # Check if the .bat file exists and create it if not
        if not os.path.isfile(self.bat_file_path):
            self.create_bat_file(self.bat_file_path)

    def create_bat_file(self, bat_file_path):
        bat_content = """@echo off
echo Checking for updates...
steamcmd.exe +login anonymous +app_update 2394010 +quit

echo Launching server
cd .\\steamapps\\common\\PalServer
start PalServer.exe -log -nosteam -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS EpicApp=PalServer
"""
        with open(bat_file_path, 'w') as file:
            file.write(bat_content)

# Tkinter window setup
root = tk.Tk()
root.title("PalWorld Control Center")
app = ApplicationControlGUI(root)
app.pack(expand=True, fill='both')
root.mainloop()
