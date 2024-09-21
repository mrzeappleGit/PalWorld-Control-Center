import subprocess
import os
import sys
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
import json


def is_application_running(app_name):
    """Check if the application is currently running."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == app_name:
            return True
    return False

def run_bat_file(file_path, steam_cmd):
    try:
        subprocess.run(file_path, shell=True, cwd=steam_cmd)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start the server: {e}")

def close_application(app_name):
    try:
        os.system(f"taskkill /f /im {app_name}")
        messagebox.showinfo("Info", "Server stopped successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop the server: {e}")

def restart_application(file_path, app_name, steam_cmd):
    close_application(app_name)
    run_bat_file(file_path, steam_cmd)

class ApplicationControlGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        sv_ttk.set_theme("dark")
        cursor_point = "hand2" if platform != "darwin" else "pointinghand"

        self.app_name = 'PalworldControlCenter'  # Replace with your application's name
        self.config_file_name = 'app_config.json'
        self.config_dir = os.path.join(os.environ['APPDATA'], self.app_name)
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.first_time_setup()
        self.update_players_active = False
        self.application_name = 'PalServer.exe'

        if getattr(sys, 'frozen', False):
            # If bundled, the icon is in the same folder as the executable
            icon_path = os.path.join(sys._MEIPASS, 'logoPalWorldControlCenter.ico')
        else:
            # If standalone, the icon is in the root folder
            icon_path = 'logoPalWorldControlCenter.ico'

        # Set the window icon
        master.iconbitmap(icon_path)

        # Status Indicator
        self.status_canvas = tk.Canvas(self, width=20, height=20)
        self.status_canvas.grid(column=3, row=2, padx=(0, 20), pady=20, sticky=tk.W)
        self.status_canvas.create_oval(5, 5, 15, 15, fill="red", tags="status_circle")
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

        restart_button = ttk.Button(self.app_control_frame, text="Restart", command=self.restart_app)
        restart_button.grid(column=3, row=0, padx=20, pady=20, sticky=tk.W)

        save_button = ttk.Button(self.app_control_frame, text="Save", command=self.save_app)
        save_button.grid(column=4, row=0, padx=20, pady=20, sticky=tk.W)

        change_steamcmd_button = ttk.Button(self.app_control_frame, text="Change SteamCMD Folder", cursor=cursor_point, command=self.choose_steamcmd_folder)
        change_steamcmd_button.grid(column=0, row=3, padx=20, pady=20, sticky=tk.W)
        change_palserver_button = ttk.Button(self.app_control_frame, text="Change PalServer Folder", cursor=cursor_point, command=self.choose_palserver_folder)
        change_palserver_button.grid(column=1, row=3, padx=20, pady=20, sticky=tk.W)


        # Label for Online Players Listbox
        online_players_label = ttk.Label(self.app_control_frame, text="Online Players")
        online_players_label.grid(column=0, row=1, padx=20, pady=(10, 0), sticky="w")

        # Player Names Listbox
        self.player_names_listbox = tk.Listbox(self.app_control_frame, height=10)
        self.player_names_listbox.grid(column=0, row=2, columnspan=3, padx=20, pady=(0, 10), sticky="ew")

        kick_button = ttk.Button(self.app_control_frame, text="Kick", command=self.kick_player)
        kick_button.grid(column=3, row=2, padx=(5, 0), pady=10, sticky="nw")

        ban_button = ttk.Button(self.app_control_frame, text="Ban", command=self.ban_player)
        ban_button.grid(column=4, row=2, padx=(5, 0), pady=10, sticky="nw")



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

         # Add new tab for Banned Players
        self.banned_players_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.banned_players_frame, text='Banned Players')

        # Listbox for Banned Players
        self.banned_players_listbox = tk.Listbox(self.banned_players_frame, height=10)
        self.banned_players_listbox.pack(side="left", fill="both", expand=True)

        # Scrollbar for Banned Players Listbox
        self.banned_players_scrollbar = ttk.Scrollbar(self.banned_players_frame, orient="vertical", command=self.banned_players_listbox.yview)
        self.banned_players_scrollbar.pack(side="right", fill="y")
        self.banned_players_listbox.config(yscrollcommand=self.banned_players_scrollbar.set)

        # Load banned players into the listbox
        self.load_banned_players()

        # Unban Button
        unban_button = ttk.Button(self.banned_players_frame, text="Unban", command=self.unban_player)
        unban_button.pack(pady=10)

        refresh_ban_button = ttk.Button(self.banned_players_frame, text="Refresh", command=self.load_banned_players)
        refresh_ban_button.pack(pady=10)

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
        self.update_status_indicator()
        
        
    def choose_palserver_folder(self):
        new_palserver_folder = filedialog.askdirectory(title="Select PalServer Folder")
        if new_palserver_folder:
            self.palserver_path = new_palserver_folder
            self.save_paths_to_config(self.steamcmd_path, new_palserver_folder)
            messagebox.showinfo("Info", "PalServer folder updated successfully.")

    def update_palserver_paths(self, palserver_folder):
        """Update application paths based on the new PalServer folder."""
        self.config_path = os.path.join(palserver_folder, "Pal/Saved/Config/WindowsServer/PalWorldSettings.ini")
        self.banlist = os.path.join(palserver_folder, "Pal/Saved/SaveGames/banlist.txt")
            
    def save_paths_to_config(self, steamcmd_path, palserver_path):
        config = {'steamcmd': steamcmd_path, 'palserver': palserver_path}
        config_file_path = os.path.join(self.config_dir, self.config_file_name)
        with open(config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

            
    def update_bat_file(self, palserver_folder):
        """Update or create the start.bat file to use the new PalServer path."""
        bat_file_path = os.path.join(self.steamcmd_path, "start.bat")
        steamcmd_exe_path = os.path.join(self.steamcmd_path, "steamcmd.exe")
        bat_content = f"""@echo off
        echo Checking for updates...
        "{steamcmd_exe_path}" +force_install_dir "{self.palserver_path}" +login anonymous +app_update 2394010 +quit

        echo Launching server
        cd "{palserver_folder}"
        start PalServer.exe -log -nosteam -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS EpicApp=PalServer
        """
        with open(bat_file_path, 'w') as file:
            file.write(bat_content)
            messagebox.showinfo("Info", "start.bat updated successfully.")
            
    def read_paths_from_config(self):
        config_file_path = os.path.join(self.config_dir, self.config_file_name)
        try:
            with open(config_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {'steamcmd': None, 'palserver': None}

    def delete_old_config(self):
        old_config_path = os.path.join(self.config_dir, 'app_config.txt')
        if os.path.exists(old_config_path):
            os.remove(old_config_path)


    def choose_steamcmd_folder(self):
        new_steamcmd_folder = filedialog.askdirectory(title="Select SteamCMD Folder")
        if new_steamcmd_folder:
            self.steamcmd_path = new_steamcmd_folder
            self.save_paths_to_config(new_steamcmd_folder, self.palserver_path)
            messagebox.showinfo("Info", "SteamCMD folder updated successfully.")

    def save_steamcmd_path(self, path):
        """Save the steamcmd folder path to the config file."""
        config_file_path = os.path.join(self.config_dir, self.config_file_name)
        with open(config_file_path, 'w') as file:
            file.write(path + "," + self.steamcmd_path)

    def initialize_paths(self):
        """Initialize or update paths based on the new steamcmd folder."""
        self.bat_file_path = os.path.join(self.steamcmd_path, "start.bat")
        self.config_path = os.path.join(self.palserver_path, "Pal/Saved/Config/WindowsServer/PalWorldSettings.ini")
        self.banlist = os.path.join(self.palserver_path, "Pal/Saved/SaveGames/banlist.txt")


    def kick_player(self):
        selected = self.player_names_listbox.curselection()
        if selected:
            player_name, player_id = self.get_player_info(selected[0])
            self.send_rcon_command("KickPlayer", player_id)
            messagebox.showinfo("Info", f"Kicked {player_name}")

    def ban_player(self):
        selected = self.player_names_listbox.curselection()
        if selected:
            player_name, player_id = self.get_player_info(selected[0])
            self.send_rcon_command("BanPlayer", player_id)
            messagebox.showinfo("Info", f"Banned {player_name}")
            self.load_banned_players()

    def send_rcon_command(self, command, args):
        try:
            rcon_ip = self.config_vars['PublicIP'].get() or '127.0.0.1'
            rcon_port = int(self.config_vars['RCONPort'].get())
            rcon_password = self.config_vars['AdminPassword'].get()
            server_name = "this"
            pal = PalworldUtil("", server_name, rcon_ip, rcon_port, rcon_password)
            pal.rcon.run_command(command, [args])
        except Exception as e:
            messagebox.showerror("Error", str(e))

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

    def load_banned_players(self):
        try:
            with open(self.banlist, 'r') as file:
                banned_players = file.readlines()
                for player in banned_players:
                    self.banned_players_listbox.insert(tk.END, player.strip())
        except FileNotFoundError:
            messagebox.showerror('Error', 'Banlist file not found.')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def unban_player(self):
        selected = self.banned_players_listbox.curselection()
        if selected:
            player_name = self.banned_players_listbox.get(selected[0])
            # Remove player from Listbox
            self.banned_players_listbox.delete(selected[0])
            # Remove player from banlist file
            self.remove_player_from_banlist(player_name)

    def remove_player_from_banlist(self, player_name):
        try:
            with open(self.banlist, 'r') as file:
                banned_players = file.readlines()

            # Remove the player from the list
            banned_players = [player for player in banned_players if player.strip() != player_name]

            # Write the updated list back to the file
            with open(self.banlist, 'w') as file:
                file.writelines(banned_players)

            messagebox.showinfo('Info', f'Unbanned {player_name}')
        except Exception as e:
            messagebox.showerror('Error', str(e))


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
            # Clear the listbox and update the label to show zero players
            self.player_names_listbox.delete(0, tk.END)
            self.player_count_label.config(text="Player Count: 0")
            return

        player_data = self.get_player_count()
        csv_data = io.StringIO(player_data)
        reader = csv.reader(csv_data)

        self.player_names_listbox.delete(0, tk.END)  # Clear the current list

        player_count = 0
        for row in reader:
            if player_count > 0:  # Skip the header row
                # Ensure that row has the expected number of elements
                if len(row) >= 2:
                    player_name = row[0]
                    player_id = row[1]
                    self.player_names_listbox.insert(tk.END, f"{player_name}, {player_id}")
            player_count += 1

        if player_count > 0:
            self.player_count_label.config(text=f"Player Count: {player_count - 1}")
        else:
            self.player_count_label.config(text="Player Count: 0")

        self.after(10000, self.update_player_count)

    def get_player_info(self, index):
        item = self.player_names_listbox.get(index)
        player_data = item.split(", ")
        if len(player_data) >= 2:
            player_name = player_data[0]
            player_id = player_data[1]
            return player_name, player_id
        else:
            raise ValueError("Invalid player data format")
        

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
        # Run the batch file to start the application
        run_bat_file(self.bat_file_path, self.steamcmd_path)

        # Attempt to check if the application started for a certain period
        for _ in range(5):  # Try for 5 intervals
            time.sleep(2)  # Wait for 2 seconds between checks
            if is_application_running(self.application_name):
                if not self.is_running:
                    self.is_running = True
                    self.start_resource_monitoring_thread()
                self.update_status_indicator()
                self.update_players_active = True
                messagebox.showinfo('Info', 'Server started successfully')
                break
        else:
            # If the application didn't start after the attempts
            messagebox.showerror("Error", f"Failed to start the server: {self.application_name}")


    def stop_app(self):
        close_application(self.application_name)
        self.after(5000, self.deactivate_player_updates)

    def restart_app(self):
        self.deactivate_player_updates
        restart_application(self.bat_file_path, self.application_name, self.steamcmd_path)
        self.update_players_active = True
        threading.Timer(10, self.update_status_indicator).start()
    
    def prompt_for_directory(self, title):
        folder_path = filedialog.askdirectory(title=title)
        if not folder_path:
            messagebox.showerror("Error", f"{title} selection is required.")
            sys.exit(1)
        return folder_path


    def first_time_setup(self):
        self.delete_old_config()
        paths = self.read_paths_from_config()
        if not paths['steamcmd'] or not paths['palserver']:
            if not paths['steamcmd']:
                paths['steamcmd'] = self.prompt_for_directory("Select SteamCMD Folder")
            if not paths['palserver']:
                paths['palserver'] = self.prompt_for_directory("Select PalServer Folder")
            self.save_paths_to_config(paths['steamcmd'], paths['palserver'])
        
        self.steamcmd_path = paths['steamcmd']
        self.palserver_path = paths['palserver']
        self.initialize_paths()

    def create_bat_file(self, bat_file_path):
        bat_file_path = os.path.join(self.steamcmd_path, "start.bat")
        steamcmd_exe_path = os.path.join(self.steamcmd_path, "steamcmd.exe")
        bat_content = f"""@echo off
        echo Checking for updates...
        "{steamcmd_exe_path}" +force_install_dir "{self.palserver_path}" +login anonymous +app_update 2394010 +quit

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