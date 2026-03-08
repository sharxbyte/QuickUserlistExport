import csv
import json
import os
import re
import shutil
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Quick Userlist Export"
APP_VERSION = "4.0"
README_FILENAME = "QUE Readme.md"
SETTINGS_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "QuickUserlistExport"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
DOWNLOADS_DIR = Path.home() / "Downloads"
DEFAULT_SAVE_DIR = DOWNLOADS_DIR if DOWNLOADS_DIR.exists() else Path.home()
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{20,40}\.[A-Za-z0-9_\-]{6,10}\.[A-Za-z0-9_\-]{20,80}$")
SNOWFLAKE_MIN_LEN = 17
SNOWFLAKE_MAX_LEN = 20


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ensure_readme_exists() -> Path:
    bundle_dir = get_bundle_dir()
    bundled_readme = bundle_dir / README_FILENAME
    output_readme = get_app_dir() / README_FILENAME

    if bundled_readme.exists() and not output_readme.exists():
        shutil.copy2(bundled_readme, output_readme)
    return output_readme


README_PATH = ensure_readme_exists()


class DiscordAPI:
    BASE = "https://discord.com/api/v10"

    def __init__(self, bot_token: str, logger=None):
        self.bot_token = bot_token.strip()
        self.logger = logger or (lambda msg: None)

    def _request(self, method: str, path: str, json_data=None, expect_json=True):
        if not self.bot_token:
            raise RuntimeError("Bot token is required.")

        url = f"{self.BASE}{path}"
        data = None
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
        }
        if json_data is not None:
            data = json.dumps(json_data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, method=method, data=data, headers=headers)

        while True:
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read()
                    if not raw:
                        return None
                    if expect_json:
                        return json.loads(raw.decode("utf-8"))
                    return raw
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(body) if body else {}
                except Exception:
                    payload = {}

                if e.code == 429:
                    retry_after = payload.get("retry_after")
                    if retry_after is None:
                        retry_after = e.headers.get("Retry-After", 3)
                    try:
                        wait_seconds = float(retry_after)
                    except Exception:
                        wait_seconds = 3.0
                    self.logger(f"Rate limited by Discord. Waiting {wait_seconds:.2f} seconds.")
                    time.sleep(wait_seconds)
                    continue

                message = payload.get("message") if isinstance(payload, dict) else None
                code = payload.get("code") if isinstance(payload, dict) else None
                detail = f" ({code}: {message})" if code or message else f" ({body})" if body else ""
                raise RuntimeError(f"Discord API error {e.code} on {method} {path}{detail}")
            except urllib.error.URLError as e:
                raise RuntimeError(f"Network error while calling Discord API: {e}") from e

    def get_current_user(self):
        return self._request("GET", "/users/@me")

    def get_guild(self, guild_id: str):
        return self._request("GET", f"/guilds/{guild_id}")

    def get_roles(self, guild_id: str):
        return self._request("GET", f"/guilds/{guild_id}/roles")

    def list_members(self, guild_id: str, after: str = "0", limit: int = 1000):
        return self._request("GET", f"/guilds/{guild_id}/members?limit={limit}&after={after}")

    def list_all_members(self, guild_id: str, progress_callback=None):
        members = []
        seen = set()
        after = "0"
        page = 0

        while True:
            batch = self.list_members(guild_id, after=after, limit=1000)
            if not isinstance(batch, list) or not batch:
                break

            page += 1
            before_count = len(members)
            for member in batch:
                user_id = str(member.get("user", {}).get("id", ""))
                if user_id and user_id not in seen:
                    seen.add(user_id)
                    members.append(member)

            added = len(members) - before_count
            self.logger(
                f"Fetched page {page}; batch size {len(batch)}; added {added}; unique members so far: {len(members)}"
            )
            if progress_callback:
                progress_callback(page=page, batch_size=len(batch), total=len(members))

            if len(batch) < 1000:
                break
            after = str(batch[-1].get("user", {}).get("id", after))

        return members


class MemberExportApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("1000x820")
        self.root.minsize(920, 720)

        self.current_worker = None
        self.bot_user = None
        self.guild_info = None
        self.roles = []
        self.role_map = {}

        self.bot_token_var = tk.StringVar()
        self.guild_id_var = tk.StringVar()
        self.save_dir_var = tk.StringVar(value=str(DEFAULT_SAVE_DIR))
        self.remember_server_var = tk.BooleanVar(value=True)
        self.remember_token_var = tk.BooleanVar(value=False)
        self.show_token_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")
        self.validation_message_var = tk.StringVar(value="Enter your bot token, server ID, and save folder.")
        self.progress_text_var = tk.StringVar(value="Idle")

        self.guild_id_validate_cmd = self.root.register(self._validate_guild_id_input)
        self.token_validate_cmd = self.root.register(self._validate_token_input)

        self._load_settings()
        self._build_ui()
        self._update_action_states()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        connection = ttk.LabelFrame(container, text="Connection")
        connection.pack(fill="x", padx=10, pady=10)

        ttk.Label(connection, text="Bot token").grid(row=0, column=0, sticky="w", **pad)
        self.token_entry = ttk.Entry(
            connection,
            textvariable=self.bot_token_var,
            show="•",
            width=88,
            validate="key",
            validatecommand=(self.token_validate_cmd, "%P"),
        )
        self.token_entry.grid(row=0, column=1, columnspan=2, sticky="ew", **pad)
        self.token_entry.bind("<KeyRelease>", lambda _e: self._update_action_states())
        self.token_entry.bind("<<Paste>>", lambda _e: self.root.after(1, self._update_action_states))

        ttk.Checkbutton(
            connection,
            text="Show",
            variable=self.show_token_var,
            command=self._toggle_token_visibility,
        ).grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(connection, text="Server ID").grid(row=1, column=0, sticky="w", **pad)
        self.guild_entry = ttk.Entry(
            connection,
            textvariable=self.guild_id_var,
            width=40,
            validate="key",
            validatecommand=(self.guild_id_validate_cmd, "%P"),
        )
        self.guild_entry.grid(row=1, column=1, sticky="w", **pad)
        self.guild_entry.bind("<KeyRelease>", lambda _e: self._update_action_states())

        ttk.Label(connection, text="Save folder").grid(row=2, column=0, sticky="w", **pad)
        self.save_dir_entry = ttk.Entry(connection, textvariable=self.save_dir_var, width=75)
        self.save_dir_entry.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)
        self.save_dir_entry.bind("<KeyRelease>", lambda _e: self._update_action_states())
        ttk.Button(connection, text="Browse…", command=self.browse_save_dir).grid(row=2, column=3, sticky="w", **pad)

        ttk.Checkbutton(
            connection,
            text="Remember server ID locally",
            variable=self.remember_server_var,
        ).grid(row=3, column=1, sticky="w", **pad)

        ttk.Checkbutton(
            connection,
            text="Remember bot token locally (plain text on this PC)",
            variable=self.remember_token_var,
        ).grid(row=3, column=2, sticky="w", **pad)

        self.btn_validate = ttk.Button(connection, text="Validate Bot Access", command=self.validate_access)
        self.btn_validate.grid(row=4, column=1, sticky="w", **pad)

        ttk.Button(connection, text="Save Settings", command=self._save_settings).grid(row=4, column=2, sticky="w", **pad)
        ttk.Button(connection, text="Open README", command=self.open_readme).grid(row=4, column=3, sticky="w", **pad)

        self.validation_label = ttk.Label(
            connection,
            textvariable=self.validation_message_var,
            foreground="#666666",
            wraplength=880,
        )
        self.validation_label.grid(row=5, column=0, columnspan=4, sticky="w", **pad)

        connection.columnconfigure(1, weight=1)
        connection.columnconfigure(2, weight=1)

        guild_box = ttk.LabelFrame(container, text="Validated Server")
        guild_box.pack(fill="x", padx=10, pady=(0, 10))

        self.guild_summary = tk.Text(guild_box, height=6, wrap="word")
        self.guild_summary.pack(fill="x", padx=8, pady=8)
        self.guild_summary.insert(
            "1.0",
            "No server validated yet. Enter a bot token and server ID, then click Validate Bot Access.",
        )
        self.guild_summary.configure(state="disabled")

        export = ttk.LabelFrame(container, text="Export")
        export.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(export, text="Role").grid(row=0, column=0, sticky="w", **pad)
        self.role_combo = ttk.Combobox(export, state="readonly", width=70)
        self.role_combo.grid(row=0, column=1, sticky="ew", **pad)
        self.role_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_action_states())

        self.btn_load_roles = ttk.Button(export, text="Load Roles", command=self.load_roles)
        self.btn_load_roles.grid(row=1, column=0, sticky="w", **pad)

        self.btn_export_all = ttk.Button(export, text="Generate Memberlist", command=self.export_all_members)
        self.btn_export_all.grid(row=1, column=1, sticky="w", **pad)

        self.btn_export_role = ttk.Button(export, text="Generate Role List", command=self.export_selected_role)
        self.btn_export_role.grid(row=1, column=1, sticky="e", **pad)

        export.columnconfigure(1, weight=1)

        progress_box = ttk.LabelFrame(container, text="Progress")
        progress_box.pack(fill="x", padx=10, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_box, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(progress_box, textvariable=self.progress_text_var).pack(anchor="w", padx=8, pady=(0, 8))

        status = ttk.LabelFrame(container, text="Status")
        status.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(status, textvariable=self.status_var).pack(anchor="w", padx=8, pady=8)

        log_frame = ttk.LabelFrame(container, text="Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = tk.Text(log_frame, wrap="word", height=18)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

    def _validate_guild_id_input(self, proposed: str):
        if proposed == "":
            return True
        return proposed.isdigit() and len(proposed) <= SNOWFLAKE_MAX_LEN

    def _validate_token_input(self, proposed: str):
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
        return all(ch in allowed for ch in proposed)

    def _toggle_token_visibility(self):
        self.token_entry.configure(show="" if self.show_token_var.get() else "•")

    def browse_save_dir(self):
        initial = self.save_dir_var.get().strip() or str(DEFAULT_SAVE_DIR)
        selected = filedialog.askdirectory(title="Choose save folder", initialdir=initial)
        if selected:
            self.save_dir_var.set(selected)
            self._update_action_states()

    def open_readme(self):
        try:
            ensure_readme_exists()
            if not README_PATH.exists():
                raise FileNotFoundError(f"README not found: {README_PATH}")
            webbrowser.open(README_PATH.resolve().as_uri())
        except Exception as exc:
            messagebox.showerror("Open README", f"Could not open the troubleshooting README.\n\n{exc}")

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.root.after(0, self._append_log, line)

    def _append_log(self, line: str):
        self.log_text.insert("end", line)
        self.log_text.see("end")

    def set_status(self, message: str):
        self.root.after(0, self.status_var.set, message)

    def set_progress_text(self, message: str):
        self.root.after(0, self.progress_text_var.set, message)

    def _start_progress(self, message: str):
        def do_start():
            self.progress_text_var.set(message)
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start(12)
        self.root.after(0, do_start)

    def _stop_progress(self, message: str = "Idle"):
        def do_stop():
            self.progress_bar.stop()
            self.progress_text_var.set(message)
        self.root.after(0, do_stop)

    def _save_settings(self):
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "guild_id": self.guild_id_var.get().strip() if self.remember_server_var.get() else "",
                "remember_server": bool(self.remember_server_var.get()),
                "remember_token": bool(self.remember_token_var.get()),
                "bot_token": self.bot_token_var.get().strip() if self.remember_token_var.get() else "",
                "save_dir": self.save_dir_var.get().strip() or str(DEFAULT_SAVE_DIR),
            }
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.log("Saved local settings.")
        except Exception as e:
            messagebox.showwarning("Save Settings", f"Could not save settings:\n{e}")

    def _load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                self.remember_server_var.set(bool(data.get("remember_server", True)))
                self.remember_token_var.set(bool(data.get("remember_token", False)))
                self.guild_id_var.set(data.get("guild_id", ""))
                self.save_dir_var.set(data.get("save_dir") or str(DEFAULT_SAVE_DIR))
                if self.remember_token_var.get():
                    self.bot_token_var.set(data.get("bot_token", ""))
        except Exception:
            pass

    def _token_is_plausible(self, token: str) -> bool:
        return bool(TOKEN_PATTERN.match(token))

    def _required_field_error(self):
        token = self.bot_token_var.get().strip()
        guild_id = self.guild_id_var.get().strip()
        save_dir = self.save_dir_var.get().strip()

        if not token:
            return "Enter a bot token."
        if not self._token_is_plausible(token):
            return "Bot token format looks invalid."
        if not guild_id:
            return "Enter a numeric server ID."
        if not guild_id.isdigit():
            return "Server ID must contain numbers only."
        if len(guild_id) < SNOWFLAKE_MIN_LEN:
            return "Server ID looks too short to be a Discord snowflake."
        if not save_dir:
            return "Choose a save folder."
        if not Path(save_dir).exists():
            return "Save folder does not exist."
        return ""

    def _update_action_states(self):
        error = self._required_field_error()
        self.validation_message_var.set(error or "All required fields are filled. Validate the bot or generate the export.")
        base_ready = not bool(error)

        self.btn_validate.configure(state="normal" if base_ready else "disabled")
        self.btn_load_roles.configure(state="normal" if base_ready else "disabled")
        self.btn_export_all.configure(state="normal" if base_ready else "disabled")

        role_ready = base_ready and bool(self.role_combo.get().strip())
        self.btn_export_role.configure(state="normal" if role_ready else "disabled")

    def _require_fields(self):
        error = self._required_field_error()
        if error:
            raise RuntimeError(error)
        return self.bot_token_var.get().strip(), self.guild_id_var.get().strip(), self.save_dir_var.get().strip()

    def _handle_not_installed_or_inaccessible(self, exc: Exception):
        message = (
            "The bot could not access that server. This usually means one of these is true:\n\n"
            "• the bot is not installed in the server\n"
            "• the server ID is wrong\n"
            "• the token belongs to a different bot\n"
            "• the token is invalid\n\n"
            f"Error from Discord:\n{exc}\n\n"
            "Open the troubleshooting README now?"
        )
        if messagebox.askyesno("Bot Not Installed or Not Accessible", message):
            self.open_readme()

    def _background(self, label, target):
        if self.current_worker and self.current_worker.is_alive():
            messagebox.showinfo("Busy", "A task is already running.")
            return

        def runner():
            self.set_status(label)
            self._start_progress(label)
            try:
                target()
            except Exception as e:
                self.log(traceback.format_exc())
                e_text = str(e)
                if (
                    "Discord API error 403" in e_text
                    or "Discord API error 404" in e_text
                    or "Missing Access" in e_text
                    or "Unknown Guild" in e_text
                ):
                    self.root.after(0, lambda err=e: self._handle_not_installed_or_inaccessible(err))
                else:
                    self.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))
                self.set_status("Error.")
            finally:
                self.root.after(0, self._update_action_states)
                if self.status_var.get() != "Error.":
                    self.set_status("Ready.")
                self._stop_progress("Idle")

        self.current_worker = threading.Thread(target=runner, daemon=True)
        self.current_worker.start()

    def _refresh_role_combo(self):
        values = [f"{role['name']} ({role['id']})" for role in self.roles]
        self.role_combo["values"] = values
        if values:
            self.role_combo.current(0)
        else:
            self.role_combo.set("")
        self._update_action_states()

    def _update_guild_summary(self):
        if not self.guild_info:
            text = "No server validated yet."
        else:
            guild_name = self.guild_info.get("name", "Unknown")
            guild_id = self.guild_info.get("id", "")
            owner_id = self.guild_info.get("owner_id", "")
            member_count_note = (
                "Discord does not reliably provide full member counts from this endpoint; use export to retrieve the full list."
            )
            bot_name = self.bot_user.get("username", "Unknown") if self.bot_user else "Unknown"
            text = (
                f"Server: {guild_name}\n"
                f"Server ID: {guild_id}\n"
                f"Owner ID: {owner_id}\n"
                f"Validated bot: {bot_name}\n"
                f"Roles loaded: {len(self.roles)}\n"
                f"Default save filename: {self._default_file_name()}\n"
                f"Save folder: {self.save_dir_var.get().strip()}\n"
                f"Note: {member_count_note}"
            )

        self.guild_summary.configure(state="normal")
        self.guild_summary.delete("1.0", "end")
        self.guild_summary.insert("1.0", text)
        self.guild_summary.configure(state="disabled")

    def _sanitized_name(self, value: str) -> str:
        cleaned = "".join(c if c.isalnum() or c in "-_ " else "_" for c in (value or "Unknown Server"))
        cleaned = "_".join(cleaned.split())
        return cleaned[:120] or "Unknown_Server"

    def _default_file_name(self, role_name: str | None = None) -> str:
        server_name = self._sanitized_name((self.guild_info or {}).get("name") or self.guild_id_var.get().strip())
        if role_name:
            role = self._sanitized_name(role_name)
            return f"{server_name}_{role}list.csv"
        return f"{server_name}_memberlist.csv"

    def _choose_save_path(self, suggested_name: str):
        result = {"path": None}
        done = threading.Event()

        def ask():
            initialdir = self.save_dir_var.get().strip() or str(DEFAULT_SAVE_DIR)
            path = filedialog.asksaveasfilename(
                title="Save CSV",
                defaultextension=".csv",
                initialdir=initialdir,
                initialfile=suggested_name,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
            result["path"] = path or None
            done.set()

        self.root.after(0, ask)
        done.wait()
        return result["path"]

    def _write_csv(self, path: str, rows):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def _member_rows(self, members):
        header = [
            "user_id",
            "username",
            "discriminator",
            "global_name",
            "nickname",
            "display_name",
            "bot",
            "joined_at",
            "highest_role",
            "role_count",
            "roles",
        ]
        rows = [header]
        for member in members:
            user = member.get("user", {})
            role_ids = [str(r) for r in member.get("roles", [])]
            role_objs = [self.role_map[rid] for rid in role_ids if rid in self.role_map]
            role_objs.sort(key=lambda r: (-int(r.get("position", 0)), r.get("name", "").lower()))
            role_names = [r.get("name", "") for r in role_objs]
            display_name = member.get("nick") or user.get("global_name") or user.get("username") or ""
            rows.append([
                str(user.get("id", "")),
                str(user.get("username", "")),
                str(user.get("discriminator", "")),
                str(user.get("global_name", "")),
                str(member.get("nick", "")),
                display_name,
                "true" if user.get("bot") else "false",
                str(member.get("joined_at", "")),
                role_names[0] if role_names else "",
                len(role_names),
                " | ".join(role_names),
            ])
        return rows

    def _ensure_roles_loaded(self, api: DiscordAPI, guild_id: str):
        if self.role_map:
            return
        roles = api.get_roles(guild_id)
        self.roles = sorted(roles, key=lambda r: (-int(r.get("position", 0)), r.get("name", "").lower()))
        self.role_map = {str(role["id"]): role for role in self.roles}
        self.root.after(0, self._refresh_role_combo)
        self.root.after(0, self._update_guild_summary)

    def _member_progress_callback(self, prefix: str):
        def callback(page: int, batch_size: int, total: int):
            self.set_progress_text(f"{prefix}: page {page}, batch {batch_size}, total collected {total}")
            self.set_status(f"{prefix} — collected {total} members so far")
        return callback

    def validate_access(self):
        def work():
            token, guild_id, _save_dir = self._require_fields()
            api = DiscordAPI(token, logger=self.log)
            self.set_progress_text("Checking bot identity...")
            bot_user = api.get_current_user()
            self.set_progress_text("Checking server access...")
            guild = api.get_guild(guild_id)
            self.set_progress_text("Loading roles...")
            roles = api.get_roles(guild_id)

            self.bot_user = bot_user
            self.guild_info = guild
            self.roles = sorted(roles, key=lambda r: (-int(r.get("position", 0)), r.get("name", "").lower()))
            self.role_map = {str(role["id"]): role for role in self.roles}

            self.root.after(0, self._refresh_role_combo)
            self.root.after(0, self._update_guild_summary)
            self._save_settings()

            self.log(f"Validated bot '{bot_user.get('username')}' against guild '{guild.get('name')}' ({guild_id}).")
            self.set_progress_text(f"Validated: {guild.get('name', guild_id)}")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Validation Successful",
                    "Bot token and server ID are valid for this server.\n\n"
                    "If member export fails later, confirm the bot has the Server Members intent enabled."
                ),
            )

        self._background("Validating bot access...", work)

    def load_roles(self):
        def work():
            token, guild_id, _save_dir = self._require_fields()
            api = DiscordAPI(token, logger=self.log)
            self.set_progress_text("Checking server access...")
            guild = api.get_guild(guild_id)
            self.set_progress_text("Loading roles...")
            roles = api.get_roles(guild_id)

            self.guild_info = guild
            self.roles = sorted(roles, key=lambda r: (-int(r.get("position", 0)), r.get("name", "").lower()))
            self.role_map = {str(role["id"]): role for role in self.roles}

            self.root.after(0, self._refresh_role_combo)
            self.root.after(0, self._update_guild_summary)
            self.log(f"Loaded {len(self.roles)} roles from '{guild.get('name')}'.")
            self.set_progress_text(f"Loaded {len(self.roles)} roles from {guild.get('name')}")

        self._background("Loading roles...", work)

    def export_all_members(self):
        def work():
            token, guild_id, _save_dir = self._require_fields()
            api = DiscordAPI(token, logger=self.log)
            self.set_progress_text("Checking server access...")
            guild = api.get_guild(guild_id)
            self.guild_info = guild
            self.root.after(0, self._update_guild_summary)
            self._ensure_roles_loaded(api, guild_id)

            self.log("Requesting full member list.")
            members = api.list_all_members(guild_id, progress_callback=self._member_progress_callback("Fetching members"))
            self.set_progress_text("Preparing save dialog...")
            path = self._choose_save_path(self._default_file_name())
            if not path:
                self.log("Export canceled.")
                self.set_progress_text("Export canceled")
                return
            self.set_progress_text("Writing CSV...")
            rows = self._member_rows(members)
            self._write_csv(path, rows)
            self.root.after(0, self._update_guild_summary)
            self.log(f"Exported {len(members)} members to {path}")
            self.set_progress_text(f"Saved {len(members)} members")
            self.root.after(
                0,
                lambda: messagebox.showinfo("Export Complete", f"Saved {len(members)} members to:\n{path}"),
            )

        self._background("Exporting all members...", work)

    def export_selected_role(self):
        def work():
            token, guild_id, _save_dir = self._require_fields()
            selected = self.role_combo.get().strip()
            if not selected:
                raise RuntimeError("Load roles and select a role first.")

            role_id = selected.rsplit("(", 1)[-1].rstrip(")")
            api = DiscordAPI(token, logger=self.log)
            self.set_progress_text("Checking server access...")
            guild = api.get_guild(guild_id)
            self.guild_info = guild
            self.root.after(0, self._update_guild_summary)
            self._ensure_roles_loaded(api, guild_id)

            role_name = self.role_map.get(role_id, {}).get("name", role_id)
            self.log(f"Requesting full member list for role filter '{role_name}'.")
            members = api.list_all_members(guild_id, progress_callback=self._member_progress_callback(f"Fetching members for {role_name}"))
            filtered = [m for m in members if role_id in [str(r) for r in m.get("roles", [])]]

            self.set_progress_text("Preparing save dialog...")
            path = self._choose_save_path(self._default_file_name(role_name=role_name))
            if not path:
                self.log("Export canceled.")
                self.set_progress_text("Export canceled")
                return

            self.set_progress_text("Writing CSV...")
            rows = self._member_rows(filtered)
            self._write_csv(path, rows)
            self.root.after(0, self._update_guild_summary)
            self.log(f"Exported {len(filtered)} members in role '{role_name}' to {path}")
            self.set_progress_text(f"Saved {len(filtered)} members for role {role_name}")
            self.root.after(
                0,
                lambda: messagebox.showinfo("Export Complete", f"Saved {len(filtered)} members to:\n{path}"),
            )

        self._background("Exporting selected role...", work)


def main():
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_readme_exists()
    root = tk.Tk()
    app = MemberExportApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._save_settings(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
