"""
app.py

Wolfenstein: The New Order - Audio Tool
GUI Tkinter puro (sin dependencias externas), con dos pestañas:
  - Extraer / Extract: exporta audio desde un .index + carpeta de contenedores
  - Inyectar / Inject: reemplaza el audio de una entrada puntual del .index

Interfaz disponible en español e inglés (selector arriba a la derecha).

Uso: python3 app.py
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from wtno_index_parser import parse_index, LANG_SLOTS, DEFAULT_ACTIVE
from wtno_extractor import extract_index
from wtno_injector import inject_entry
from i18n import t


class ExtractTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent, padding=12)
        self.lang = lang
        self.index_path = tk.StringVar()
        self.containers_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.lang_vars = {lang_slot: tk.BooleanVar(value=DEFAULT_ACTIVE[lang_slot]) for lang_slot in LANG_SLOTS}

        self._build_ui()

    def _build_ui(self):
        L = self.lang
        row = 0
        ttk.Label(self, text=t("index_file", L)).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.index_path, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text=t("choose", L), command=self._pick_index).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text=t("containers_folder", L)).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.containers_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text=t("choose", L), command=self._pick_containers).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text=t("output_folder", L)).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text=t("choose", L), command=self._pick_output).grid(row=row, column=2)
        row += 1

        lang_frame = ttk.LabelFrame(self, text=t("languages_to_extract", L))
        lang_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        for i, lang_slot in enumerate(LANG_SLOTS):
            ttk.Checkbutton(lang_frame, text=lang_slot, variable=self.lang_vars[lang_slot]).grid(
                row=0, column=i, padx=8, pady=6
            )
        row += 1

        self.extract_btn = ttk.Button(self, text=t("extract_btn", L), command=self._start_extract)
        self.extract_btn.grid(row=row, column=0, pady=8, sticky="w")

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.grid(row=row, column=1, columnspan=2, sticky="ew", pady=8)
        row += 1

        self.log = tk.Text(self, height=14, width=90, state="disabled")
        self.log.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=6)

        self.columnconfigure(1, weight=1)

    def _pick_index(self):
        path = filedialog.askopenfilename(filetypes=[("Index files", "*.index"), ("*", "*.*")])
        if path:
            self.index_path.set(path)
            if not self.containers_dir.get():
                self.containers_dir.set(os.path.dirname(path))

    def _pick_containers(self):
        path = filedialog.askdirectory()
        if path:
            self.containers_dir.set(path)

    def _pick_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def _log_line(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start_extract(self):
        L = self.lang
        if not self.index_path.get() or not os.path.isfile(self.index_path.get()):
            messagebox.showerror(t("error", L), t("pick_valid_index", L))
            return
        if not self.containers_dir.get() or not os.path.isdir(self.containers_dir.get()):
            messagebox.showerror(t("error", L), t("pick_valid_containers", L))
            return
        if not self.output_dir.get():
            messagebox.showerror(t("error", L), t("pick_output_folder", L))
            return

        active = {lang_slot: var.get() for lang_slot, var in self.lang_vars.items()}
        self.extract_btn.configure(state="disabled")
        self.progress["value"] = 0
        self._log_line(t("starting_extraction", L))

        thread = threading.Thread(target=self._run_extract, args=(active,), daemon=True)
        thread.start()

    def _run_extract(self, active):
        L = self.lang
        try:
            def progress_cb(done, total, name):
                self.progress["maximum"] = total
                self.progress["value"] = done
                if done % 25 == 0 or done == total:
                    self._log_line(f"[{done}/{total}] {name}")

            results = extract_index(
                self.index_path.get(),
                self.containers_dir.get(),
                self.output_dir.get(),
                active_languages=active,
                progress_cb=progress_cb,
            )
            self._log_line("\n" + t("done_extracted", L, n=len(results), path=self.output_dir.get()))
        except Exception as e:
            self._log_line(f"ERROR: {e}")
        finally:
            self.extract_btn.configure(state="normal")


class InjectTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent, padding=12)
        self.lang = lang
        self.index_path = tk.StringVar()
        self.containers_dir = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.filter_lang = tk.StringVar(value=t("all", lang))
        self.entries = []  # lista completa de WtnoEntry cargados
        self._build_ui()

    def _build_ui(self):
        L = self.lang
        row = 0
        ttk.Label(self, text=t("index_file", L)).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.index_path, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text=t("choose", L), command=self._pick_index).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text=t("containers_folder", L)).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.containers_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text=t("choose", L), command=self._pick_containers).grid(row=row, column=2)
        row += 1

        ttk.Button(self, text=t("load_entries", L), command=self._load_entries).grid(row=row, column=0, pady=6, sticky="w")
        row += 1

        ttk.Label(self, text=t("filter_label", L)).grid(row=row, column=0, sticky="w")
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=row, column=1, padx=6, pady=4, sticky="w")
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_text, width=35)
        filter_entry.pack(side="left")
        filter_entry.bind("<KeyRelease>", lambda e: self._refresh_table())

        ttk.Label(filter_frame, text=t("language_filter_label", L)).pack(side="left")
        lang_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_lang,
            values=[t("all", L)] + list(LANG_SLOTS),
            state="readonly",
            width=14,
        )
        lang_combo.pack(side="left")
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())
        row += 1

        columns = ("name", "language", "offset", "size")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        for col, label, w in [
            ("name", t("col_name", L), 320),
            ("language", t("col_language", L), 100),
            ("offset", t("col_offset", L), 100),
            ("size", t("col_size", L), 100),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=w)
        self.tree.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=8)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        ttk.Button(btn_frame, text=t("replace_selected", L), command=self._inject_selected).pack(side="left")
        row += 1

        self.status_var = tk.StringVar(value=t("no_entries_loaded", L))
        ttk.Label(self, textvariable=self.status_var).grid(row=row, column=0, columnspan=3, sticky="w", pady=6)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

    def _pick_index(self):
        path = filedialog.askopenfilename(filetypes=[("Index files", "*.index"), ("*", "*.*")])
        if path:
            self.index_path.set(path)
            if not self.containers_dir.get():
                self.containers_dir.set(os.path.dirname(path))

    def _pick_containers(self):
        path = filedialog.askdirectory()
        if path:
            self.containers_dir.set(path)

    def _load_entries(self):
        L = self.lang
        if not self.index_path.get() or not os.path.isfile(self.index_path.get()):
            messagebox.showerror(t("error", L), t("pick_valid_index", L))
            return
        try:
            # cargar TODOS los idiomas para poder inyectar en cualquiera
            all_active = {lang_slot: True for lang_slot in LANG_SLOTS}
            self.entries = list(parse_index(self.index_path.get(), active_languages=all_active))
            self._refresh_table()
            self.status_var.set(t("n_entries_loaded", L, n=len(self.entries)))
        except Exception as e:
            messagebox.showerror(t("error", L), t("could_not_parse_index", L, err=e))

    def _refresh_table(self):
        L = self.lang
        self.tree.delete(*self.tree.get_children())
        filt = self.filter_text.get().lower().strip()
        lang_filt = self.filter_lang.get()
        for idx, e in enumerate(self.entries):
            if filt and filt not in e.name.lower():
                continue
            if lang_filt != t("all", L) and e.language != lang_filt:
                continue
            self.tree.insert("", "end", iid=str(idx), values=(e.name, e.language, hex(e.offset), e.size))

    def _inject_selected(self):
        L = self.lang
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(t("select_row_warning", L), t("select_row_msg", L))
            return
        entry = self.entries[int(sel[0])]

        new_file = filedialog.askopenfilename(
            title=t("pick_replacement_title", L, name=entry.name),
            filetypes=[("Audio", "*.ogg *.wav"), ("*", "*.*")],
        )
        if not new_file:
            return

        try:
            updated = inject_entry(entry, new_file, self.index_path.get(), self.containers_dir.get())
            self.entries[int(sel[0])] = updated
            self._refresh_table()
            self.status_var.set(
                t("replaced_status", L, name=updated.name, lang=updated.language, offset=hex(updated.offset), size=updated.size)
            )
            messagebox.showinfo(t("done", L), t("replaced_ok", L, name=entry.name))
        except Exception as e:
            messagebox.showerror(t("error", L), t("could_not_inject", L, err=e))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "es"
        self.geometry("820x680")
        self.title(t("app_title", self.lang))

        top_bar = ttk.Frame(self, padding=(12, 8, 12, 0))
        top_bar.pack(fill="x")
        self.lang_label = ttk.Label(top_bar, text=t("language_label", self.lang))
        self.lang_label.pack(side="left")
        self.lang_selector = ttk.Combobox(
            top_bar, values=["Español", "English"], state="readonly", width=12
        )
        self.lang_selector.set("Español")
        self.lang_selector.pack(side="left", padx=6)
        self.lang_selector.bind("<<ComboboxSelected>>", self._on_lang_change)

        self.notebook_container = ttk.Frame(self)
        self.notebook_container.pack(fill="both", expand=True)

        self._build_notebook()

    def _build_notebook(self):
        for widget in self.notebook_container.winfo_children():
            widget.destroy()

        notebook = ttk.Notebook(self.notebook_container)
        notebook.pack(fill="both", expand=True)

        notebook.add(ExtractTab(notebook, self.lang), text=t("tab_extract", self.lang))
        notebook.add(InjectTab(notebook, self.lang), text=t("tab_inject", self.lang))

    def _on_lang_change(self, event=None):
        selected = self.lang_selector.get()
        self.lang = "en" if selected == "English" else "es"
        self.title(t("app_title", self.lang))
        self.lang_label.configure(text=t("language_label", self.lang))
        self._build_notebook()


if __name__ == "__main__":
    App().mainloop()
