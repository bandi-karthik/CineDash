# engine/dataframe.py
from __future__ import annotations
from typing import List, Tuple, Dict, Any, Iterable, Optional
import re

# 👇 use YOUR parser class
from engine.parser import csvreader

# ---------- core frame ----------
class MiniFrame:
    def __init__(self, name: str, columns: List[str]):
        self.name = name
        self.columns = columns
        self.col_index: Dict[str, int] = {c: i for i, c in enumerate(columns)}
        self.rows: List[tuple] = []
        self.indexes: Dict[str, Dict[Any, List[int]]] = {}

    def append(self, values: Iterable[Any]) -> None:
        t = tuple(values)
        if len(t) != len(self.columns):
            raise ValueError(f"Row width {len(t)} != schema width {len(self.columns)} for {self.name}")
        self.rows.append(t)

    def build_index(self, col: str) -> None:
        pos = self.col_index[col]
        idx: Dict[Any, List[int]] = {}
        for i, row in enumerate(self.rows):
            key = row[pos]
            idx.setdefault(key, []).append(i)
        self.indexes[col] = idx

    def get(self, row: tuple, col: str) -> Any:
        return row[self.col_index[col]]

    def iter_dicts(self):
        for r in self.rows:
            yield {c: r[self.col_index[c]] for c in self.columns}

# ---------- helpers ----------
_YEAR_RE = re.compile(r"\((\d{4})\)\s*$")

def extract_year_from_title(title: str) -> Optional[int]:
    m = _YEAR_RE.search(title)
    return int(m.group(1)) if m else None

def _to_int(s: str):
    s = s.strip()
    if s == "" or s.lower() == "null":
        return None
    return int(s)

def _to_float(s: str):
    s = s.strip()
    if s == "" or s.lower() == "null":
        return None
    return float(s)

def _split_genres(g: str):
    g = g.strip()
    if g == "" or g == "(no genres listed)":
        return []
    return g.split("|")

# ---------- loaders (MovieLens) ----------
def load_movies(path: str) -> MiniFrame:
    reader = csvreader()
    header, rows = reader.read_doc(path)  # uses YOUR parser
    pos = {name: i for i, name in enumerate(header)}
    for need in ("movieId", "title", "genres"):
        if need not in pos:
            raise ValueError(f"Missing column {need} in movies.csv header {header}")

    mf = MiniFrame("movies", ["movieId", "title", "year", "genres"])
    for raw in rows:
        movie_id = _to_int(raw[pos["movieId"]])
        title = raw[pos["title"]]
        year = extract_year_from_title(title)
        genres = _split_genres(raw[pos["genres"]])
        mf.append([movie_id, title, year, genres])
    mf.build_index("movieId")
    return mf

def load_ratings(path: str) -> MiniFrame:
    reader = csvreader()
    header, rows = reader.read_doc(path)
    pos = {name: i for i, name in enumerate(header)}
    for need in ("userId", "movieId", "rating", "timestamp"):
        if need not in pos:
            raise ValueError(f"Missing column {need} in ratings.csv header {header}")

    rf = MiniFrame("ratings", ["userId", "movieId", "rating", "timestamp"])
    for raw in rows:
        rf.append([
            _to_int(raw[pos["userId"]]),
            _to_int(raw[pos["movieId"]]),
            _to_float(raw[pos["rating"]]),
            _to_int(raw[pos["timestamp"]]),
        ])
    rf.build_index("movieId")
    return rf

def load_tags(path: str) -> MiniFrame:
    reader = csvreader()
    header, rows = reader.read_doc(path)
    pos = {name: i for i, name in enumerate(header)}
    for need in ("userId", "movieId", "tag", "timestamp"):
        if need not in pos:
            raise ValueError(f"Missing column {need} in tags.csv header {header}")

    tf = MiniFrame("tags", ["userId", "movieId", "tag", "timestamp"])
    for raw in rows:
        tf.append([
            _to_int(raw[pos["userId"]]),
            _to_int(raw[pos["movieId"]]),
            raw[pos["tag"]],
            _to_int(raw[pos["timestamp"]]),
        ])
    tf.build_index("movieId")
    return tf
