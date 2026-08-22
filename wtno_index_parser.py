"""
wtno_index_parser.py

Parser del formato de indice "FDSE" usado por Wolfenstein: The New Order
(id Tech 5) para sus contenedores de audio streamed:

    streamed.resources   -> archivo 1 (MAIN_SOUND)
    english.streamed     -> archivo 2 (ENG_SOUND)
    french.streamed      -> archivo 3 (FRA_SOUND)   [deshabilitado por defecto]
    italian.streamed     -> archivo 4 (ITA_SOUND)   [deshabilitado por defecto]
    spanish.streamed     -> archivo 5 (SPA_SOUND)   [deshabilitado por defecto]

Traducido 1:1 desde el script QuickBMS del usuario. La estructura de cada
entrada del .index es:

    (little endian)
        u32 FNsize1 ; bytes FN1 (nombre interno 1, no usado para exportar)
        u32 FNsize2 ; bytes FN2 (nombre de archivo -> se exporta como .ogg)
        u32 namesize; bytes name (nombre "humano", no usado para exportar)
    (big endian)
        u32 offset
        u32 size
        u32 zsize
        u32 unksize

    Segun unksize:
        == 1  -> un solo idioma (MAIN_SOUND). Los offset/size reales estan
                 0x10 bytes mas adelante (se re-leen).
        == 4  -> cuatro idiomas (ENG, FRA, ITA, SPA), cada uno con su propio
                 offset/size, cada uno a +0x10 del anterior punto de lectura.
        else  -> bloque de datos desconocido de unksize*0x18 bytes que se
                 descarta.

    Luego, 5 bytes de padding/flags que se saltean, y si no es la ultima
    entrada, un u32 "filenumber" (big endian, seguimos igual que el bloque
    anterior).
"""

import struct
from dataclasses import dataclass
from typing import BinaryIO, Iterator, Optional

LANG_SLOTS = ["MAIN_SOUND", "ENG_SOUND", "FRA_SOUND", "ITA_SOUND", "SPA_SOUND"]

# Que contenedores estan activos por defecto (igual que el script: solo
# streamed.resources y english.streamed estan "open", el resto comentado)
DEFAULT_ACTIVE = {
    "MAIN_SOUND": True,
    "ENG_SOUND": True,
    "FRA_SOUND": False,
    "ITA_SOUND": False,
    "SPA_SOUND": False,
}

# Mapeo archivo logico -> nombre de contenedor esperado
CONTAINER_FILENAMES = {
    "MAIN_SOUND": "streamed.resources",
    "ENG_SOUND": "english.streamed",
    "FRA_SOUND": "french.streamed",
    "ITA_SOUND": "italian.streamed",
    "SPA_SOUND": "spanish.streamed",
}


@dataclass
class WtnoEntry:
    name: str  # nombre de salida, con extension .ogg
    language: str  # uno de LANG_SLOTS
    offset: int
    size: int
    offset_field_pos: int  # posicion en el .index del u32 "offset" real (size esta 4 bytes despues)


def _read_u32(f: BinaryIO, big_endian: bool) -> int:
    data = f.read(4)
    if len(data) != 4:
        raise EOFError("EOF inesperado leyendo u32")
    return struct.unpack(">I" if big_endian else "<I", data)[0]


def _read_dstring(f: BinaryIO, size: int) -> bytes:
    data = f.read(size)
    if len(data) != size:
        raise EOFError("EOF inesperado leyendo dstring")
    return data


def parse_index(path: str, active_languages: Optional[dict] = None) -> Iterator[WtnoEntry]:
    """
    Parsea un archivo .index y genera WtnoEntry para cada (nombre, idioma)
    presente y activo.

    active_languages: dict opcional {LANG_SLOT: bool} para filtrar que
    idiomas extraer (por defecto: MAIN_SOUND y ENG_SOUND, igual que el
    script original con FRA/ITA/SPA comentados).
    """
    active = dict(DEFAULT_ACTIVE)
    if active_languages:
        active.update(active_languages)

    with open(path, "rb") as f:
        f.seek(0x24)
        files = _read_u32(f, big_endian=True)
        _unk = _read_u32(f, big_endian=True)  # descartado, igual que el script

        tmp_last_index = files - 1

        for i in range(files):
            # --- little endian: nombres ---
            fnsize1 = _read_u32(f, big_endian=False)
            _fn1 = _read_dstring(f, fnsize1)

            fnsize2 = _read_u32(f, big_endian=False)
            fn2 = _read_dstring(f, fnsize2).decode("latin-1", errors="replace")

            namesize = _read_u32(f, big_endian=False)
            _name = _read_dstring(f, namesize)

            # --- big endian: offsets/tamanos ---
            _offset = _read_u32(f, big_endian=True)
            _size = _read_u32(f, big_endian=True)
            _zsize = _read_u32(f, big_endian=True)
            unksize = _read_u32(f, big_endian=True)

            out_name = fn2[:-4] + ".ogg" if fn2.lower().endswith(".wav") else fn2 + ".ogg"

            if unksize == 1:
                pos = f.tell() + 0x10
                f.seek(pos)
                field_pos = f.tell()
                real_offset = _read_u32(f, big_endian=True)
                real_size = _read_u32(f, big_endian=True)
                if active.get("MAIN_SOUND"):
                    yield WtnoEntry(out_name, "MAIN_SOUND", real_offset, real_size, field_pos)

            elif unksize == 4:
                for lang in ("ENG_SOUND", "FRA_SOUND", "ITA_SOUND", "SPA_SOUND"):
                    pos = f.tell() + 0x10
                    f.seek(pos)
                    field_pos = f.tell()
                    real_offset = _read_u32(f, big_endian=True)
                    real_size = _read_u32(f, big_endian=True)
                    if active.get(lang):
                        yield WtnoEntry(out_name, lang, real_offset, real_size, field_pos)

            else:
                skip = unksize * 0x18
                f.seek(f.tell() + skip)

            # 5 bytes de padding/flags
            f.seek(f.tell() + 5)

            if i != tmp_last_index:
                _filenumber = _read_u32(f, big_endian=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python wtno_index_parser.py archivo.index")
        sys.exit(1)

    count = 0
    for entry in parse_index(sys.argv[1]):
        print(f"[{entry.language}] {entry.name}  offset=0x{entry.offset:X}  size={entry.size}")
        count += 1
    print(f"\nTotal entradas: {count}")
