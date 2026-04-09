# gui.py
from __future__ import annotations

import queue
import threading
from datetime import datetime
from tkinter import END, ttk, messagebox

import customtkinter as ctk

from client import APIError, GermanMinerClient, NetworkError
from config import (
    ConfigError,
    CONFIG_FILE,
    get_default_load_chunks,
    get_presets,
    get_ui_settings,
    set_preset,
    delete_preset,
    update_api_key,
    update_default_load_chunks,
    update_ui_settings,
    load_config,
)
from services import GermanMinerService, resolve_location


ctk.set_default_color_theme("blue")


class PresetEditorFrame(ctk.CTkFrame):
    def __init__(self, master, refresh_callback):
        super().__init__(master)
        self.refresh_callback = refresh_callback

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.listbox = ttk.Treeview(self, columns=("x", "y", "z"), show="headings", height=8)
        self.listbox.heading("x", text="X")
        self.listbox.heading("y", text="Y")
        self.listbox.heading("z", text="Z")
        self.listbox.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=(10, 8))

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        form.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.name_entry = ctk.CTkEntry(form)
        self.name_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="X").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.x_entry = ctk.CTkEntry(form)
        self.x_entry.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Y").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.y_entry = ctk.CTkEntry(form)
        self.y_entry.grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Z").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.z_entry = ctk.CTkEntry(form)
        self.z_entry.grid(row=1, column=3, padx=8, pady=8, sticky="ew")

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=4, sticky="ew", padx=8, pady=8)
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_row, text="Speichern", command=self.save_preset).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btn_row, text="Auswahl laden", command=self.load_selected).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btn_row, text="Löschen", fg_color="#B33939", hover_color="#922B2B", command=self.remove_selected).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        self.populate()

    def populate(self):
        for item in self.listbox.get_children():
            self.listbox.delete(item)
        for name, coords in get_presets().items():
            self.listbox.insert("", END, iid=name, values=(coords["x"], coords["y"], coords["z"]))

    def load_selected(self):
        selected = self.listbox.selection()
        if not selected:
            return
        name = selected[0]
        presets = get_presets()
        coords = presets[name]
        self.name_entry.delete(0, END)
        self.name_entry.insert(0, name)
        self.x_entry.delete(0, END)
        self.x_entry.insert(0, str(coords["x"]))
        self.y_entry.delete(0, END)
        self.y_entry.insert(0, str(coords["y"]))
        self.z_entry.delete(0, END)
        self.z_entry.insert(0, str(coords["z"]))

    def save_preset(self):
        try:
            name = self.name_entry.get().strip()
            x = int(self.x_entry.get().strip())
            y = int(self.y_entry.get().strip())
            z = int(self.z_entry.get().strip())

            if not name:
                raise ValueError("Name fehlt.")

            set_preset(name, x, y, z)
            self.populate()
            self.refresh_callback()
        except Exception as exc:
            messagebox.showerror("Preset speichern", str(exc))

    def remove_selected(self):
        selected = self.listbox.selection()
        if not selected:
            return
        name = selected[0]
        if messagebox.askyesno("Preset löschen", f"Soll das Preset '{name}' gelöscht werden?"):
            delete_preset(name)
            self.populate()
            self.refresh_callback()


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app: "GermanMinerApp"):
        super().__init__(app)
        self.app = app
        self.title("Einstellungen")
        self.geometry("720x520")
        self.transient(app)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        cfg = load_config()

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="API-Key").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.api_key_entry = ctk.CTkEntry(top, show="*", width=420)
        self.api_key_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.api_key_entry.insert(0, cfg.get("api_key", ""))

        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            top,
            text="API-Key anzeigen",
            variable=self.show_key_var,
            command=self.toggle_key_visibility
        ).grid(row=0, column=2, padx=8, pady=8)

        self.default_load_var = ctk.BooleanVar(value=bool(cfg.get("default_load_chunks", False)))
        ctk.CTkCheckBox(
            top,
            text="loadChunks standardmäßig aktivieren",
            variable=self.default_load_var,
        ).grid(row=1, column=1, padx=8, pady=8, sticky="w")

        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=(6, 2))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_row, text="Speichern", command=self.save_settings).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btn_row, text="API testen", command=self.test_api).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.preset_editor = PresetEditorFrame(self, refresh_callback=self.app.refresh_presets)
        self.preset_editor.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def toggle_key_visibility(self):
        self.api_key_entry.configure(show="" if self.show_key_var.get() else "*")

    def save_settings(self):
        update_api_key(self.api_key_entry.get().strip())
        update_default_load_chunks(self.default_load_var.get())
        self.app.refresh_presets()
        self.app.log("Einstellungen gespeichert.")
        messagebox.showinfo("Einstellungen", f"Gespeichert in:\n{CONFIG_FILE}")

    def test_api(self):
        self.app.run_background_task(self._test_api_worker, self._test_api_done)

    def _test_api_worker(self):
        client = GermanMinerClient(api_key=self.api_key_entry.get().strip())
        return client.ping()

    def _test_api_done(self, result=None, error=None):
        if error:
            messagebox.showerror("API-Test", str(error))
            self.app.log(f"API-Test fehlgeschlagen: {error}", level="error")
            return
        messagebox.showinfo("API-Test", "API-Verbindung erfolgreich.")
        self.app.log(f"API-Test erfolgreich: {result}")


class InventoryPanel(ctk.CTkFrame):
    def __init__(self, master, title: str, select_callback=None):
        super().__init__(master)
        self.title = title
        self.select_callback = select_callback
        self.current_rows = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 8), sticky="w"
        )

        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        mode_row.grid_columnconfigure((0, 1), weight=1)

        self.mode_var = ctk.StringVar(value="preset")
        ctk.CTkRadioButton(mode_row, text="Preset", variable=self.mode_var, value="preset", command=self.update_mode).grid(
            row=0, column=0, padx=4, pady=4, sticky="w"
        )
        ctk.CTkRadioButton(mode_row, text="Manuell", variable=self.mode_var, value="manual", command=self.update_mode).grid(
            row=0, column=1, padx=4, pady=4, sticky="w"
        )

        preset_row = ctk.CTkFrame(self, fg_color="transparent")
        preset_row.grid(row=2, column=0, padx=12, pady=4, sticky="ew")
        preset_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(preset_row, text="Preset").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.preset_menu = ctk.CTkOptionMenu(preset_row, values=["-"])
        self.preset_menu.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        manual_row = ctk.CTkFrame(self, fg_color="transparent")
        manual_row.grid(row=3, column=0, padx=12, pady=4, sticky="ew")
        manual_row.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(manual_row, text="X").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.x_entry = ctk.CTkEntry(manual_row, width=90)
        self.x_entry.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(manual_row, text="Y").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.y_entry = ctk.CTkEntry(manual_row, width=90)
        self.y_entry.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(manual_row, text="Z").grid(row=0, column=4, padx=6, pady=6, sticky="w")
        self.z_entry = ctk.CTkEntry(manual_row, width=90)
        self.z_entry.grid(row=0, column=5, padx=6, pady=6, sticky="ew")

        self.load_button = ctk.CTkButton(self, text="Inventar laden")
        self.load_button.grid(row=4, column=0, padx=12, pady=(6, 8), sticky="ew")

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("slot", "item", "amount", "id", "meta"),
            show="headings",
            height=14
        )
        self.tree.heading("slot", text="Slot")
        self.tree.heading("item", text="Item")
        self.tree.heading("amount", text="Anzahl")
        self.tree.heading("id", text="ID")
        self.tree.heading("meta", text="Meta")

        self.tree.column("slot", width=60, anchor="center")
        self.tree.column("item", width=220, anchor="w")
        self.tree.column("amount", width=80, anchor="center")
        self.tree.column("id", width=80, anchor="center")
        self.tree.column("meta", width=80, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.info_label = ctk.CTkLabel(self, text="Keine Kiste geladen.", text_color="gray")
        self.info_label.grid(row=6, column=0, padx=12, pady=(0, 10), sticky="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.refresh_presets()
        self.update_mode()

    def refresh_presets(self):
        presets = list(get_presets().keys())
        self.preset_menu.configure(values=presets if presets else ["-"])
        if presets:
            self.preset_menu.set(presets[0])
        else:
            self.preset_menu.set("-")

    def update_mode(self):
        is_preset = self.mode_var.get() == "preset"
        self.preset_menu.configure(state="normal" if is_preset else "disabled")
        state = "disabled" if is_preset else "normal"
        self.x_entry.configure(state=state)
        self.y_entry.configure(state=state)
        self.z_entry.configure(state=state)

    def get_location(self):
        if self.mode_var.get() == "preset":
            preset = self.preset_menu.get()
            return resolve_location(preset_name=preset)
        return resolve_location(
            x=int(self.x_entry.get().strip()),
            y=int(self.y_entry.get().strip()),
            z=int(self.z_entry.get().strip()),
        )

    def set_inventory(self, rows, location):
        self.current_rows = rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, row in enumerate(rows):
            self.tree.insert(
                "",
                END,
                iid=str(idx),
                values=(
                    row.get("slot", "-"),
                    row.get("item", "UNKNOWN"),
                    row.get("amount", 1),
                    row.get("id", "-"),
                    row.get("meta", "-"),
                )
            )

        self.info_label.configure(
            text=f"Geladen: x={location[0]}, y={location[1]}, z={location[2]} | {len(rows)} Einträge"
        )

    def clear_inventory(self):
        self.current_rows = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.info_label.configure(text="Keine Kiste geladen.")

    def _on_select(self, _event=None):
        if not self.select_callback:
            return
        selected = self.tree.selection()
        if not selected:
            return
        row_index = int(selected[0])
        if 0 <= row_index < len(self.current_rows):
            self.select_callback(self.current_rows[row_index])


class GermanMinerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.service = GermanMinerService()
        self.info_data = {}

        ui = get_ui_settings()
        ctk.set_appearance_mode(ui.get("appearance_mode", "dark"))

        self.title("GermanMiner Chest Mover")
        self.geometry(f"{ui.get('window_width', 1200)}x{ui.get('window_height', 760)}")
        self.minsize(1100, 700)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_top_bar()
        self._build_main_area()
        self._build_log_area()

        self.after(150, self._poll_task_queue)
        self.refresh_presets()
        self.log(f"Konfiguration: {CONFIG_FILE}")
        self.log("Anwendung gestartet.")

    def _build_top_bar(self):
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="GermanMiner Chest Mover", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=12, pady=12, sticky="w"
        )

        status_frame = ctk.CTkFrame(top, fg_color="transparent")
        status_frame.grid(row=0, column=1, padx=12, pady=12, sticky="e")

        self.status_label = ctk.CTkLabel(status_frame, text="API: Unbekannt")
        self.status_label.grid(row=0, column=0, padx=8)

        self.requests_label = ctk.CTkLabel(status_frame, text="Requests: -")
        self.requests_label.grid(row=0, column=1, padx=8)

        self.level_label = ctk.CTkLabel(status_frame, text="Level: -")
        self.level_label.grid(row=0, column=2, padx=8)

        ctk.CTkButton(status_frame, text="API testen", command=self.api_test).grid(row=0, column=3, padx=8)
        ctk.CTkButton(status_frame, text="Einstellungen", command=self.open_settings).grid(row=0, column=4, padx=8)

    def _build_main_area(self):
        main = ctk.CTkFrame(self)
        main.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        main.grid_columnconfigure((0, 2), weight=1)
        main.grid_columnconfigure(1, weight=0)
        main.grid_rowconfigure(0, weight=1)

        self.source_panel = InventoryPanel(main, "Quelle", select_callback=self.on_source_item_selected)
        self.source_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=10)

        center = ctk.CTkFrame(main)
        center.grid(row=0, column=1, sticky="ns", padx=6, pady=10)

        ctk.CTkLabel(center, text="Transfer", font=ctk.CTkFont(size=20, weight="bold")).pack(padx=10, pady=(10, 14))

        self.slot_entry = ctk.CTkEntry(center, width=220, placeholder_text="Quellslot")
        self.slot_entry.pack(padx=10, pady=6)

        self.item_entry = ctk.CTkEntry(center, width=220, placeholder_text="Itemname (Info)")
        self.item_entry.pack(padx=10, pady=6)

        self.amount_entry = ctk.CTkEntry(center, width=220, placeholder_text="Anzahl")
        self.amount_entry.pack(padx=10, pady=6)

        self.target_slot_entry = ctk.CTkEntry(center, width=220, placeholder_text="Zielslot (optional, Standard 0)")
        self.target_slot_entry.pack(padx=10, pady=6)

        self.load_chunks_var = ctk.BooleanVar(value=get_default_load_chunks())
        self.reload_after_var = ctk.BooleanVar(value=True)
        self.confirm_move_all_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(center, text="loadChunks", variable=self.load_chunks_var).pack(anchor="w", padx=12, pady=(8, 4))
        ctk.CTkCheckBox(center, text="Nach Transfer neu laden", variable=self.reload_after_var).pack(anchor="w", padx=12, pady=4)
        ctk.CTkCheckBox(center, text="Move-All bestätigen", variable=self.confirm_move_all_var).pack(anchor="w", padx=12, pady=4)

        ctk.CTkButton(center, text="Item verschieben", command=self.move_single).pack(fill="x", padx=10, pady=(14, 6))
        ctk.CTkButton(center, text="Alles verschieben", command=self.move_all).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(center, text="Quelle/Ziel tauschen", command=self.swap_locations).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(center, text="Quelle laden", command=lambda: self.load_inventory("source")).pack(fill="x", padx=10, pady=(18, 6))
        ctk.CTkButton(center, text="Ziel laden", command=lambda: self.load_inventory("target")).pack(fill="x", padx=10, pady=6)

        self.progress = ttk.Progressbar(center, mode="determinate", length=220)
        self.progress.pack(padx=10, pady=(18, 8))

        self.target_panel = InventoryPanel(main, "Ziel")
        self.target_panel.grid(row=0, column=2, sticky="nsew", padx=(6, 10), pady=10)

        self.source_panel.load_button.configure(command=lambda: self.load_inventory("source"))
        self.target_panel.load_button.configure(command=lambda: self.load_inventory("target"))

    def _build_log_area(self):
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="Status / Log", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w"
        )

        self.log_box = ctk.CTkTextbox(log_frame, height=170)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.log_box.configure(state="disabled")

    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "info": "INFO",
            "error": "FEHLER",
            "warn": "WARNUNG",
            "success": "OK",
        }.get(level, "INFO")
        line = f"[{timestamp}] [{prefix}] {message}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert(END, line)
        self.log_box.see(END)
        self.log_box.configure(state="disabled")

    def refresh_presets(self):
        self.source_panel.refresh_presets()
        self.target_panel.refresh_presets()

    def open_settings(self):
        SettingsWindow(self)

    def on_source_item_selected(self, row):
        self.slot_entry.delete(0, END)
        self.slot_entry.insert(0, str(row.get("slot", "")))

        self.item_entry.delete(0, END)
        self.item_entry.insert(0, row.get("item", ""))

        self.amount_entry.delete(0, END)
        self.amount_entry.insert(0, str(row.get("amount", 1)))

        self.log(
            f"Slot aus Quelle übernommen: Slot {row.get('slot', '-')}, "
            f"{row.get('amount', '?')}x {row.get('item', 'UNKNOWN')}"
        )

    def api_test(self):
        self.run_background_task(self._worker_api_test, self._done_api_test)

    def _worker_api_test(self):
        return self.service.ping()

    def _done_api_test(self, result=None, error=None):
        if error:
            self.status_label.configure(text="API: Fehler", text_color="#E74C3C")
            self.log(f"API-Test fehlgeschlagen: {error}", level="error")
            messagebox.showerror("API-Test", str(error))
            return

        self.info_data = result if isinstance(result, dict) else {}
        self.status_label.configure(text="API: Verbunden", text_color="#2ECC71")

        level = "-"
        requests_left = "-"
        if isinstance(result, dict):
            level = result.get("level", result.get("apiLevel", "-"))
            requests_left = result.get("requests", result.get("requestsLeft", result.get("remainingRequests", "-")))

        self.level_label.configure(text=f"Level: {level}")
        self.requests_label.configure(text=f"Requests: {requests_left}")
        self.log("API-Verbindung erfolgreich.", level="success")

    def load_inventory(self, which: str):
        panel = self.source_panel if which == "source" else self.target_panel
        try:
            location = panel.get_location()
        except Exception as exc:
            messagebox.showerror("Koordinaten", str(exc))
            self.log(f"Ungültige Koordinaten im Bereich {panel.title}: {exc}", level="error")
            return

        self.log(f"Lade Inventar für {panel.title}: x={location[0]}, y={location[1]}, z={location[2]}")

        self.run_background_task(
            lambda: self._worker_load_inventory(location),
            lambda result=None, error=None: self._done_load_inventory(which, location, result, error)
        )

    def _worker_load_inventory(self, location):
        return self.service.load_inventory(*location, load_chunks=self.load_chunks_var.get())

    def _done_load_inventory(self, which, location, result=None, error=None):
        panel = self.source_panel if which == "source" else self.target_panel
        if error:
            panel.clear_inventory()
            self.log(f"Inventar {panel.title} konnte nicht geladen werden: {error}", level="error")
            messagebox.showerror("Inventar laden", str(error))
            return

        panel.set_inventory(result, location)
        self.log(f"Inventar {panel.title} geladen: {len(result)} Einträge", level="success")

    def move_single(self):
        try:
            source = self.source_panel.get_location()
            target = self.target_panel.get_location()
            source_slot = int(self.slot_entry.get().strip())
            amount = int(self.amount_entry.get().strip())
            target_slot_text = self.target_slot_entry.get().strip()
            target_slot = int(target_slot_text) if target_slot_text else 0

            if amount <= 0:
                raise ValueError("Die Anzahl muss größer als 0 sein.")
        except Exception as exc:
            messagebox.showerror("Eingabefehler", str(exc))
            self.log(f"Eingabefehler beim Verschieben: {exc}", level="error")
            return

        item_info = self.item_entry.get().strip() or f"Slot {source_slot}"
        self.log(f"Starte Einzeltransfer: {amount}x {item_info} aus Slot {source_slot} nach Slot {target_slot}")

        self.run_background_task(
            lambda: self.service.move_single_item(
                source,
                target,
                source_slot=source_slot,
                amount=amount,
                target_slot=target_slot,
                load_chunks=self.load_chunks_var.get(),
                precheck=True,
            ),
            lambda result=None, error=None: self._done_move_single(source, target, source_slot, target_slot, amount, item_info, result, error)
        )

    def _done_move_single(self, source, target, source_slot, target_slot, amount, item_info, result=None, error=None):
        if error:
            self.log(f"Einzeltransfer fehlgeschlagen: {error}", level="error")
            messagebox.showerror("Item verschieben", str(error))
            return

        self.log(
            f"Erfolgreich verschoben: {amount}x {item_info} "
            f"von Slot {source_slot} in ({source[0]},{source[1]},{source[2]}) "
            f"nach Slot {target_slot} in ({target[0]},{target[1]},{target[2]})",
            level="success"
        )
        messagebox.showinfo("Transfer", f"Transfer erfolgreich.\nQuelle Slot: {source_slot}\nZiel Slot: {target_slot}")
        if self.reload_after_var.get():
            self.load_inventory("source")
            self.load_inventory("target")

    def move_all(self):
        try:
            source = self.source_panel.get_location()
            target = self.target_panel.get_location()
        except Exception as exc:
            messagebox.showerror("Koordinaten", str(exc))
            self.log(f"Fehler bei move-all: {exc}", level="error")
            return

        if self.confirm_move_all_var.get():
            ok = messagebox.askyesno(
                "Alles verschieben",
                "Sollen alle belegten Slots aus der Quellkiste nacheinander verschoben werden?\n"
                "Hinweis: Bei loadChunks=true können zusätzliche Requests vom Limit abgezogen werden."
            )
            if not ok:
                self.log("Move-All abgebrochen.")
                return

        self.log("Starte Move-All ...")
        self.progress["value"] = 5

        def worker():
            return self.service.move_all_items(source, target, load_chunks=self.load_chunks_var.get())

        self.run_background_task(worker, self._done_move_all)

    def _done_move_all(self, result=None, error=None):
        self.progress["value"] = 100
        if error:
            self.log(f"Move-All fehlgeschlagen: {error}", level="error")
            messagebox.showerror("Move-All", str(error))
            self.progress["value"] = 0
            return

        success_count = 0
        fail_count = 0
        total_items = len(result) if isinstance(result, list) else 0

        if isinstance(result, list):
            for idx, row in enumerate(result, start=1):
                self.progress["value"] = int((idx / max(total_items, 1)) * 100)
                source_slot = row.get("slot", "-")
                target_slot = row.get("target_slot", "-")
                amount = row.get("amount", "?")
                item = row.get("item", "UNKNOWN")

                if row.get("success"):
                    success_count += 1
                    self.log(
                        f"Verschoben: Quelle Slot {source_slot} -> Ziel Slot {target_slot} | "
                        f"{amount}x {item}",
                        level="success"
                    )
                else:
                    fail_count += 1
                    self.log(
                        f"Fehlgeschlagen: Quelle Slot {source_slot} -> Ziel Slot {target_slot} | "
                        f"{amount}x {item} -> {row.get('error', 'Unbekannter Fehler')}",
                        level="error"
                    )

        self.log(f"Move-All beendet. Erfolgreich: {success_count}, Fehlgeschlagen: {fail_count}")
        messagebox.showinfo(
            "Move-All abgeschlossen",
            f"Erfolgreich verschobene Slots: {success_count}\nFehlgeschlagene Slots: {fail_count}"
        )

        if self.reload_after_var.get():
            self.load_inventory("source")
            self.load_inventory("target")

        self.progress["value"] = 0

    def swap_locations(self):
        try:
            src_mode = self.source_panel.mode_var.get()
            tgt_mode = self.target_panel.mode_var.get()

            if src_mode == "preset" and tgt_mode == "preset":
                src_preset = self.source_panel.preset_menu.get()
                tgt_preset = self.target_panel.preset_menu.get()
                self.source_panel.preset_menu.set(tgt_preset)
                self.target_panel.preset_menu.set(src_preset)
            elif src_mode == "manual" and tgt_mode == "manual":
                sx, sy, sz = self.source_panel.x_entry.get(), self.source_panel.y_entry.get(), self.source_panel.z_entry.get()
                tx, ty, tz = self.target_panel.x_entry.get(), self.target_panel.y_entry.get(), self.target_panel.z_entry.get()

                self.source_panel.x_entry.delete(0, END)
                self.source_panel.x_entry.insert(0, tx)
                self.source_panel.y_entry.delete(0, END)
                self.source_panel.y_entry.insert(0, ty)
                self.source_panel.z_entry.delete(0, END)
                self.source_panel.z_entry.insert(0, tz)

                self.target_panel.x_entry.delete(0, END)
                self.target_panel.x_entry.insert(0, sx)
                self.target_panel.y_entry.delete(0, END)
                self.target_panel.y_entry.insert(0, sy)
                self.target_panel.z_entry.delete(0, END)
                self.target_panel.z_entry.insert(0, sz)
            else:
                messagebox.showwarning(
                    "Tauschen",
                    "Quelle und Ziel können nur getauscht werden, wenn beide Panels denselben Modus nutzen."
                )
                return

            self.log("Quelle und Ziel wurden getauscht.")
        except Exception as exc:
            messagebox.showerror("Tauschen", str(exc))
            self.log(f"Fehler beim Tauschen: {exc}", level="error")

    def run_background_task(self, worker, callback):
        def runner():
            try:
                result = worker()
                self.task_queue.put((callback, result, None))
            except Exception as exc:
                self.task_queue.put((callback, None, exc))
        threading.Thread(target=runner, daemon=True).start()

    def _poll_task_queue(self):
        try:
            while True:
                callback, result, error = self.task_queue.get_nowait()
                callback(result=result, error=error)
        except queue.Empty:
            pass
        self.after(150, self._poll_task_queue)

    def on_close(self):
        try:
            width = self.winfo_width()
            height = self.winfo_height()
            update_ui_settings(window_width=width, window_height=height)
        except Exception:
            pass
        self.destroy()


def run_app():
    app = GermanMinerApp()
    app.mainloop()