# File: prototype/met/zbTraffic_main.py

import sys
import pathlib
# Find zbTraffic root by looking for traffic/ folder
_HERE = pathlib.Path(__file__).resolve()
# Check _HERE.parent first (if file is in project root), then all parents
for _p in [_HERE.parent, *_HERE.parents]:
    if (_p / "traffic").is_dir():
        # Found project root
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

import tkinter as tk
from tkinter import ttk
import subprocess, sys, pathlib

# Map button labels to module names
MODULES = [
("zbTraffic System Setup", "prototype.met.zbTraffic_setup"),
("zbTraffic Daily Operations", "prototype.met.zbTraffic_daily"),
("Avails Viewer", "prototype.met.avails_gui"),
("Spots Viewer", "prototype.met.spots_gui"),
("Traffic Board", "prototype.traffic_board"),
("Traffic Days", "prototype.traffic_days"),
("Traffic Days Table", "prototype.traffic_days_table"),
]

class Launcher:
    def __init__(self, root):
        self.root=root
        root.title("zbTraffic - Main CRUD Launcher v3 FIXED")
        root.geometry("500x420")
        ttk.Label(root,text="Throwaway zbTraffic - Main Menu v3 - FIXED",font=("Arial",14,"bold")).pack(pady=10)
        ttk.Label(root,text="Filterable + H/V Scrollbars + Sortable\nLaunches as modules so 'traffic' always found",foreground="gray",justify="center").pack(pady=5)
        for label, mod in MODULES:
            ttk.Button(root,text=label,command=lambda m=mod: self.launch_module(m)).pack(fill='x',padx=20,pady=3)
        ttk.Separator(root).pack(fill='x',pady=10)
        ttk.Label(root,text="Run: python3 -m prototype.met.zbTraffic_main &",foreground="gray").pack(side='bottom',pady=10)

    def launch_module(self, module_name):
        # Launch as module from project root - this is the key fix
        # _HERE is zbTraffic root from path_fix
        import pathlib
        # Find project root
        proj_root = None
        here = pathlib.Path(__file__).resolve()
        for p in [here.parent, *here.parents]:
            if (p / "traffic").is_dir():
                proj_root = p
                break
        if proj_root is None:
            proj_root = pathlib.Path.cwd()
        # Launch python -m module from project root
        subprocess.Popen([sys.executable, "-m", module_name], cwd=str(proj_root))

if __name__=="__main__":
    root=tk.Tk(); Launcher(root); root.mainloop()
