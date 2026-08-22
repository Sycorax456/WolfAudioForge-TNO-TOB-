"""
wtno_extractor.py

Usa wtno_index_parser para leer un .index y extraer el audio real desde
los contenedores .streamed / .resources correspondientes (copia directa
de bytes en offset..offset+size, igual que el comando 'log' de QuickBMS).
"""

import os
from typing import Callable, Optional

from wtno_index_parser import CONTAINER_FILENAMES, parse_index


def extract_index(
    index_path: str,
    containers_dir: str,
    output_dir: str,
    active_languages: Optional[dict] = None,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> list:
    """
    index_path: ruta al archivo .index
    containers_dir: carpeta donde estan streamed.resources / english.streamed / etc.
    output_dir: carpeta de salida para los .ogg extraidos
    active_languages: ver wtno_index_parser.parse_index
    progress_cb: callback opcional(done, total, nombre_actual)

    Devuelve una lista de (nombre_salida, idioma, ruta_salida) exitosos.
    Los idiomas cuyo contenedor no se encuentra en containers_dir se
    saltean con un aviso (no rompen la extraccion completa).
    """
    entries = list(parse_index(index_path, active_languages))
    total = len(entries)

    # cache de handles abiertos por idioma
    open_containers = {}
    missing_warned = set()
    results = []

    os.makedirs(output_dir, exist_ok=True)

    try:
        for i, entry in enumerate(entries):
            container_name = CONTAINER_FILENAMES[entry.language]
            container_path = os.path.join(containers_dir, container_name)

            if entry.language not in open_containers:
                if not os.path.isfile(container_path):
                    if entry.language not in missing_warned:
                        missing_warned.add(entry.language)
                    open_containers[entry.language] = None
                else:
                    open_containers[entry.language] = open(container_path, "rb")

            fh = open_containers[entry.language]
            if fh is None:
                continue  # contenedor faltante, se saltea esta entrada

            fh.seek(entry.offset)
            data = fh.read(entry.size)

            # subcarpeta por idioma para evitar colisiones de nombre entre MAIN/ENG/etc.
            lang_dir = os.path.join(output_dir, entry.language)
            os.makedirs(lang_dir, exist_ok=True)
            out_path = os.path.join(lang_dir, entry.name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            with open(out_path, "wb") as out_f:
                out_f.write(data)

            results.append((entry.name, entry.language, out_path))

            if progress_cb:
                progress_cb(i + 1, total, entry.name)

    finally:
        for fh in open_containers.values():
            if fh is not None:
                fh.close()

    if missing_warned:
        print("Aviso: no se encontraron estos contenedores (se saltearon sus entradas):")
        for lang in missing_warned:
            print(f"  - {CONTAINER_FILENAMES[lang]} ({lang})")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Uso: python wtno_extractor.py archivo.index carpeta_contenedores carpeta_salida")
        sys.exit(1)

    idx, containers, out = sys.argv[1], sys.argv[2], sys.argv[3]
    res = extract_index(idx, containers, out)
    print(f"Extraidas {len(res)} entradas a {out}")
