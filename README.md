
# PalWorld Control Center

## Overview
PalWorld Control Center is a Python-based application designed for managing a PalWorld game server. It features a GUI that allows users to start, stop, restart, and monitor the PalWorld server. The application also includes player management tools like kicking, banning, and unbanning players, along with configuration editing capabilities.
## Features

- Start/Stop/Restart Server: Easily manage the server's state.
- Player Management: Kick, ban, and unban players directly from the GUI.
- Configuration Editing: Edit server settings through a user-friendly interface.
- Resource Monitoring: View real-time CPU and memory usage of the PalWorld server.
- Status Indicator: Check the server's running status at a glance.
- Banned Players List: Manage a list of banned players.
- First-Time Setup Assistance: Guided setup for initial configuration.
- Automatic Server Updates: Check and apply server updates automatically.


## Requirements

- Python 3.x
- Tkinter library
- sv_ttk module for styling
- psutil for process management and monitoring
## Installation

1. Ensure Python 3.x is installed on your system.
2. Ensure [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) is installed on your system
3. Ensure you run Palworld Server at least once [Learn More](https://medium.com/@dmentgen3/palworld-how-to-transfer-world-save-to-dedicated-server-2a7e16d017c0)
2. Install required Python modules:

```bash
  pip install tkinter sv_ttk psutil
```
3. Clone or download the application source code.
4. Run the palworldRun script to start the application:
```bash
python palworldRun.py
```
## Usage


1. Starting the Application: Launch the script to open the GUI.
2. Server Management: Use the 'App Control' tab to start, stop, or restart the server.
3. Player Management: View online players, kick or ban them using the relevant buttons.
4. Editing Configuration: Modify server settings under the 'Config Editor' tab.
5. Monitoring Resources: View CPU and memory usage on the main window.
6. Managing Banned Players: Use the 'Banned Players' tab to view and unban players.
7. First-Time Setup: Follow prompts to set up the server if running for the first time.

## Acknowledgements

 - [Gavinnn101's RCON Scripts PalWorld Dedi Helper](https://github.com/gavinnn101/palworld_dedi_helper)
## Contributing

Contributions to enhance the application or fix bugs are welcome. Please follow the standard fork, branch, and pull request workflow.
## Disclaimer
This application is an independent tool and is not officially associated with the PalWorld game or its creators. Usage is at users' own risk.
