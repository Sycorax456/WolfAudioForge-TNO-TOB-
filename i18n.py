"""
i18n.py

Diccionario simple de traducciones para la GUI (español / inglés).
Uso: t("key", lang) -> texto en el idioma pedido.
"""

STRINGS = {
    "app_title": {"es": "Wolfenstein: The New Order - Audio Tool", "en": "Wolfenstein: The New Order - Audio Tool"},
    "tab_extract": {"es": "Extraer", "en": "Extract"},
    "tab_inject": {"es": "Inyectar", "en": "Inject"},
    "language_label": {"es": "Idioma de la interfaz:", "en": "Interface language:"},

    "index_file": {"es": "Archivo .index:", "en": ".index file:"},
    "containers_folder": {"es": "Carpeta de contenedores:", "en": "Containers folder:"},
    "output_folder": {"es": "Carpeta de salida:", "en": "Output folder:"},
    "choose": {"es": "Elegir...", "en": "Browse..."},
    "languages_to_extract": {"es": "Idiomas a extraer", "en": "Languages to extract"},
    "extract_btn": {"es": "Extraer", "en": "Extract"},
    "starting_extraction": {"es": "Iniciando extracción...", "en": "Starting extraction..."},
    "done_extracted": {"es": "Listo. {n} archivos extraídos a {path}", "en": "Done. {n} files extracted to {path}"},
    "error": {"es": "Error", "en": "Error"},
    "pick_valid_index": {"es": "Elegí un archivo .index válido.", "en": "Pick a valid .index file."},
    "pick_valid_containers": {"es": "Elegí una carpeta de contenedores válida.", "en": "Pick a valid containers folder."},
    "pick_output_folder": {"es": "Elegí una carpeta de salida.", "en": "Pick an output folder."},

    "load_entries": {"es": "Cargar entradas", "en": "Load entries"},
    "filter_label": {"es": "Filtrar:", "en": "Filter:"},
    "language_filter_label": {"es": "  Idioma:", "en": "  Language:"},
    "all": {"es": "Todos", "en": "All"},
    "col_name": {"es": "Nombre", "en": "Name"},
    "col_language": {"es": "Idioma", "en": "Language"},
    "col_offset": {"es": "Offset", "en": "Offset"},
    "col_size": {"es": "Tamaño", "en": "Size"},
    "replace_selected": {"es": "Reemplazar seleccionada...", "en": "Replace selected..."},
    "no_entries_loaded": {"es": "Sin entradas cargadas.", "en": "No entries loaded."},
    "n_entries_loaded": {"es": "{n} entradas cargadas.", "en": "{n} entries loaded."},
    "could_not_parse_index": {"es": "No se pudo parsear el .index:\n{err}", "en": "Could not parse the .index:\n{err}"},
    "select_row_warning": {"es": "Atención", "en": "Attention"},
    "select_row_msg": {"es": "Seleccioná una entrada de la tabla.", "en": "Select an entry from the table."},
    "pick_replacement_title": {"es": "Elegí el archivo de reemplazo para {name}", "en": "Pick the replacement file for {name}"},
    "replaced_status": {
        "es": "Reemplazado: {name} ({lang}) -> offset={offset} size={size}",
        "en": "Replaced: {name} ({lang}) -> offset={offset} size={size}",
    },
    "done": {"es": "Listo", "en": "Done"},
    "replaced_ok": {"es": "{name} reemplazado correctamente.", "en": "{name} replaced successfully."},
    "could_not_inject": {"es": "No se pudo inyectar:\n{err}", "en": "Could not inject:\n{err}"},
}


def t(key: str, lang: str, **kwargs) -> str:
    text = STRINGS.get(key, {}).get(lang, key)
    if kwargs:
        return text.format(**kwargs)
    return text
