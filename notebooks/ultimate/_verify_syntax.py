"""
Walk every code cell in QSF_ULTIMATE.ipynb and ast.parse it.
Prints cell-index and first line of any cell that fails to parse.
"""
from __future__ import annotations
import ast, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "QSF_ULTIMATE.ipynb"

def main() -> int:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    n_code = n_md = 0
    errors: list[tuple[int, str, str]] = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "markdown":
            n_md += 1
            continue
        if cell["cell_type"] != "code":
            continue
        n_code += 1
        src = "".join(cell["source"])
        first_line = src.splitlines()[0] if src.strip() else "<empty>"
        try:
            ast.parse(src)
        except SyntaxError as e:
            errors.append((i, first_line, f"{e.__class__.__name__} line {e.lineno}: {e.msg}"))
    total = len(nb["cells"])
    print(f"[verify] total cells       : {total}")
    print(f"[verify] code cells        : {n_code}")
    print(f"[verify] markdown cells    : {n_md}")
    if not errors:
        print("[verify] OK — every code cell parses")
        return 0
    print(f"[verify] FAIL — {len(errors)} cells failed:")
    for i, head, err in errors:
        print(f"  cell {i:>3d}  {head[:72]}")
        print(f"         {err}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
