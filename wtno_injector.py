"""
wtno_injector.py

Reemplaza el audio de una entrada del .index por un archivo nuevo.

Estrategia:
  - Si el archivo nuevo es <= tamaño original: se sobrescribe in-place en
    el contenedor, en el mismo offset. Se actualiza el campo "size" del
    .index al nuevo tamaño (el offset no cambia).
  - Si el archivo nuevo es > tamaño original: se agrega al final del
    contenedor (append) y se actualizan tanto "offset" como "size" en el
    .index para que apunten a la nueva ubicación. El hueco viejo queda
    como desperdicio dentro del contenedor (no se recompacta), pero el
    juego solo lee lo que indica el .index, así que no afecta.

Esto evita tener que reconstruir el contenedor entero. Requiere volver a
parsear el .index después de cada inyección si vas a inyectar varias
entradas en la misma corrida (los offset_field_pos no cambian, pero el
offset/size en memoria sí, así que conviene re-parsear para tener datos
frescos).
"""

import os
import struct
from typing import Optional

from wtno_index_parser import CONTAINER_FILENAMES, WtnoEntry


def inject_entry(
    entry: WtnoEntry,
    new_file_path: str,
    index_path: str,
    containers_dir: str,
) -> WtnoEntry:
    """
    Reemplaza el audio de `entry` por el contenido de `new_file_path`.
    Modifica el contenedor de audio y el .index en disco.
    Devuelve un WtnoEntry actualizado (con el nuevo offset/size).
    """
    container_path = os.path.join(containers_dir, CONTAINER_FILENAMES[entry.language])
    if not os.path.isfile(container_path):
        raise FileNotFoundError(f"No se encontró el contenedor: {container_path}")

    with open(new_file_path, "rb") as nf:
        new_data = nf.read()
    new_size = len(new_data)

    if new_size <= entry.size:
        # in-place
        with open(container_path, "r+b") as cf:
            cf.seek(entry.offset)
            cf.write(new_data)
        new_offset = entry.offset
    else:
        # append al final
        with open(container_path, "ab") as cf:
            new_offset = cf.tell()
            cf.write(new_data)

    # patchear el .index (offset seguido de size, ambos big endian, 4 bytes c/u)
    with open(index_path, "r+b") as idx:
        idx.seek(entry.offset_field_pos)
        idx.write(struct.pack(">II", new_offset, new_size))

    return WtnoEntry(entry.name, entry.language, new_offset, new_size, entry.offset_field_pos)


if __name__ == "__main__":
    print("Este módulo se usa desde la GUI o importado; no tiene CLI standalone todavía.")
