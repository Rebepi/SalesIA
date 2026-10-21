import csv
import io
from pathlib import Path


def read_import_file(path, delimiter=None, encoding=None, column_mapping=None, corrections=None):
    raw = Path(path).read_bytes()
    if encoding:
        text = raw.decode(encoding)
        detected_encoding = encoding
    else:
        try:
            text = raw.decode("utf-8-sig")
            detected_encoding = "utf-8-sig"
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
            detected_encoding = "cp1252"
    if "\x00" in text:
        raise ValueError("El archivo contiene datos binarios. Guarda una copia como CSV.")
    if delimiter not in (None, ",", ";", "\t", "|"):
        raise ValueError("Separador no admitido.")
    if not delimiter:
        try:
            delimiter = csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter, strict=True)
    source_columns = [(name or "").strip() for name in (reader.fieldnames or [])]
    if not source_columns or len(set(source_columns)) != len(source_columns) or "" in source_columns:
        raise ValueError("Las cabeceras deben tener nombres únicos y no vacíos.")
    mapping = column_mapping or {}
    if any(source not in source_columns for source in mapping.values()):
        raise ValueError("El mapeo hace referencia a una columna que no existe en el archivo.")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Cada columna de origen puede asignarse una sola vez.")
    reader.fieldnames = source_columns
    reverse = {source: target for target, source in mapping.items()}
    rows = []
    for index, source in enumerate(reader, 1):
        if None in source:
            raise ValueError(f"La fila {index} tiene más valores que cabeceras. Revisa el separador y las comillas.")
        row = {reverse.get(key, key): (value or "").strip() for key, value in source.items()}
        row.update((corrections or {}).get(str(index), {}))
        rows.append(row)
        if len(rows) > 100000:
            raise ValueError("El archivo supera las 100000 filas permitidas.")
    columns = [reverse.get(key, key) for key in source_columns]
    if len(set(columns)) != len(columns):
        raise ValueError("El mapeo produce columnas de destino duplicadas.")
    return rows, columns, {"delimiter": delimiter, "encoding": detected_encoding, "source_columns": source_columns}
