"""Inspect the downloaded riwayat file format."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"data\corpora\ar\riwayat\warsh.txt", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 10:
            break
        s = line.rstrip()
        # Print first 80 chars and codepoint of first non-space char
        sample = s[:80]
        print(f"line {i}: len={len(s)}  first10cp={[hex(ord(c)) for c in s[:10]]}")
        print(f"  text: {sample}")
