"""
app.py

Wolfenstein: The New Order - Audio Tool
GUI Tkinter puro (sin dependencias externas), con dos pestañas:
  - Extraer: exporta audio desde un .index + carpeta de contenedores
  - Inyectar: reemplaza el audio de una entrada puntual del .index

Uso: python3 app.py
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from wtno_index_parser import parse_index, LANG_SLOTS, DEFAULT_ACTIVE
from wtno_extractor import extract_index
from wtno_injector import inject_entry


class ExtractTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.index_path = tk.StringVar()
        self.containers_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.lang_vars = {lang: tk.BooleanVar(value=DEFAULT_ACTIVE[lang]) for lang in LANG_SLOTS}

        self._build_ui()

    def _build_ui(self):
        row = 0
        ttk.Label(self, text="Archivo .index:").grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.index_path, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text="Elegir...", command=self._pick_index).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text="Carpeta de contenedores:").grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.containers_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text="Elegir...", command=self._pick_containers).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text="Carpeta de salida:").grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text="Elegir...", command=self._pick_output).grid(row=row, column=2)
        row += 1

        lang_frame = ttk.LabelFrame(self, text="Idiomas a extraer")
        lang_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        for i, lang in enumerate(LANG_SLOTS):
            ttk.Checkbutton(lang_frame, text=lang, variable=self.lang_vars[lang]).grid(
                row=0, column=i, padx=8, pady=6
            )
        row += 1

        self.extract_btn = ttk.Button(self, text="Extraer", command=self._start_extract)
        self.extract_btn.grid(row=row, column=0, pady=8, sticky="w")

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.grid(row=row, column=1, columnspan=2, sticky="ew", pady=8)
        row += 1

        self.log = tk.Text(self, height=14, width=90, state="disabled")
        self.log.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=6)

        self.columnconfigure(1, weight=1)

    def _pick_index(self):
        path = filedialog.askopenfilename(filetypes=[("Index files", "*.index"), ("Todos", "*.*")])
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
        if not self.index_path.get() or not os.path.isfile(self.index_path.get()):
            messagebox.showerror("Error", "Elegí un archivo .index válido.")
            return
        if not self.containers_dir.get() or not os.path.isdir(self.containers_dir.get()):
            messagebox.showerror("Error", "Elegí una carpeta de contenedores válida.")
            return
        if not self.output_dir.get():
            messagebox.showerror("Error", "Elegí una carpeta de salida.")
            return

        active = {lang: var.get() for lang, var in self.lang_vars.items()}
        self.extract_btn.configure(state="disabled")
        self.progress["value"] = 0
        self._log_line("Iniciando extracción...")

        thread = threading.Thread(target=self._run_extract, args=(active,), daemon=True)
        thread.start()

    def _run_extract(self, active):
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
            self._log_line(f"\nListo. {len(results)} archivos extraídos a {self.output_dir.get()}")
        except Exception as e:
            self._log_line(f"ERROR: {e}")
        finally:
            self.extract_btn.configure(state="normal")


class InjectTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.index_path = tk.StringVar()
        self.containers_dir = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.filter_lang = tk.StringVar(value="Todos")
        self.entries = []  # lista completa de WtnoEntry cargados
        self._build_ui()

    def _build_ui(self):
        row = 0
        ttk.Label(self, text="Archivo .index:").grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.index_path, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text="Elegir...", command=self._pick_index).grid(row=row, column=2)
        row += 1

        ttk.Label(self, text="Carpeta de contenedores:").grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.containers_dir, width=55).grid(row=row, column=1, padx=6, pady=4)
        ttk.Button(self, text="Elegir...", command=self._pick_containers).grid(row=row, column=2)
        row += 1

        ttk.Button(self, text="Cargar entradas", command=self._load_entries).grid(row=row, column=0, pady=6, sticky="w")
        row += 1

        ttk.Label(self, text="Filtrar:").grid(row=row, column=0, sticky="w")
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=row, column=1, padx=6, pady=4, sticky="w")
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_text, width=35)
        filter_entry.pack(side="left")
        filter_entry.bind("<KeyRelease>", lambda e: self._refresh_table())

        ttk.Label(filter_frame, text="  Idioma:").pack(side="left")
        lang_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_lang,
            values=["Todos"] + list(LANG_SLOTS),
            state="readonly",
            width=14,
        )
        lang_combo.pack(side="left")
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())
        row += 1

        columns = ("name", "language", "offset", "size")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        for col, label, w in [
            ("name", "Nombre", 320),
            ("language", "Idioma", 100),
            ("offset", "Offset", 100),
            ("size", "Tamaño", 100),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=w)
        self.tree.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=8)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        ttk.Button(btn_frame, text="Reemplazar seleccionada...", command=self._inject_selected).pack(side="left")
        row += 1

        self.status_var = tk.StringVar(value="Sin entradas cargadas.")
        ttk.Label(self, textvariable=self.status_var).grid(row=row, column=0, columnspan=3, sticky="w", pady=6)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

    def _pick_index(self):
        path = filedialog.askopenfilename(filetypes=[("Index files", "*.index"), ("Todos", "*.*")])
        if path:
            self.index_path.set(path)
            if not self.containers_dir.get():
                self.containers_dir.set(os.path.dirname(path))

    def _pick_containers(self):
        path = filedialog.askdirectory()
        if path:
            self.containers_dir.set(path)

    def _load_entries(self):
        if not self.index_path.get() or not os.path.isfile(self.index_path.get()):
            messagebox.showerror("Error", "Elegí un archivo .index válido.")
            return
        try:
            # cargar TODOS los idiomas para poder inyectar en cualquiera
            all_active = {lang: True for lang in LANG_SLOTS}
            self.entries = list(parse_index(self.index_path.get(), active_languages=all_active))
            self._refresh_table()
            self.status_var.set(f"{len(self.entries)} entradas cargadas.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo parsear el .index:\n{e}")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        filt = self.filter_text.get().lower().strip()
        lang_filt = self.filter_lang.get()
        for idx, e in enumerate(self.entries):
            if filt and filt not in e.name.lower():
                continue
            if lang_filt != "Todos" and e.language != lang_filt:
                continue
            self.tree.insert("", "end", iid=str(idx), values=(e.name, e.language, hex(e.offset), e.size))

    def _inject_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná una entrada de la tabla.")
            return
        entry = self.entries[int(sel[0])]

        new_file = filedialog.askopenfilename(
            title=f"Elegí el archivo de reemplazo para {entry.name}",
            filetypes=[("Audio", "*.ogg *.wav"), ("Todos", "*.*")],
        )
        if not new_file:
            return

        try:
            updated = inject_entry(entry, new_file, self.index_path.get(), self.containers_dir.get())
            self.entries[int(sel[0])] = updated
            self._refresh_table()
            self.status_var.set(
                f"Reemplazado: {updated.name} ({updated.language}) -> offset={hex(updated.offset)} size={updated.size}"
            )
            messagebox.showinfo("Listo", f"{entry.name} reemplazado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo inyectar:\n{e}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wolfenstein: The New Order - Audio Tool")
        self.geometry("820x640")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        notebook.add(ExtractTab(notebook), text="Extraer")
        notebook.add(InjectTab(notebook), text="Inyectar")


if __name__ == "__main__":
    App().mainloop()
