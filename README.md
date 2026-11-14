# food-picture-01 — Lacquered Roast Duck

A whole lacquered roast duck with glistening mahogany crispy skin, sliced
open to show juicy rosy meat, steaming on a dark platter with a single
orange wedge — photographed-style, warm golden light, the dish large and
central so it still reads delicious at small size.

## Files

- `entry.png` — the picture (JPEG bytes, 1024×1024, under 1 MiB)
- `main.py` — validates the picture (PNG/JPEG, ≤1 MiB, ≤1024 px, complete
  file) and copies it byte-for-byte to the output directory

## Run

```sh
python3 main.py
```

Writes `$MAKEFUN_OUTPUT_DIR/entry.png` (falls back to `/output/entry.png`).
Deterministic: the output is always the exact same bytes as `entry.png`.
