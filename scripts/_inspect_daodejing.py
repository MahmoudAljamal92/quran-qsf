"""Inspect daodejing_wangbi.txt structure."""
import sys
import re
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "corpora" / "zh" / "daodejing_wangbi.txt"

text = PATH.read_text(encoding="utf-8")
print(f"Total chars (incl. whitespace/markers): {len(text)}")
print()
print("First 600 chars (raw):")
print(text[:600])
print()
print("=" * 80)

# Check for chapter delimiter
chapter_pattern = re.compile(r"第[一二三四五六七八九十百零〇\d]+章")
matches = list(chapter_pattern.finditer(text))
print(f"\nChapter markers found: {len(matches)}")
if matches:
    print(f"First 5 markers: {[m.group(0) for m in matches[:5]]}")
    print(f"Last 5 markers: {[m.group(0) for m in matches[-5:]]}")

# Split into chapters
chapters_raw = chapter_pattern.split(text)
chapters = [c.strip() for c in chapters_raw if c.strip()]
# If first chapter is preamble before any 第X章 marker, it would still be in chapters[0]
# The split keeps content BEFORE first marker; if text starts with a marker, chapters[0] is empty

print(f"Chapters after split (non-empty): {len(chapters)}")
print()

# Check punctuation/whitespace distribution to identify "verse" boundaries within a chapter
print("Sample chapter 1 (after split):")
print(repr(chapters[0][:200]))
print()
print("Sample chapter 2:")
print(repr(chapters[1][:200]))
print()

# Identify line-final / phrase-final characters using common Chinese punctuation
# Use 。and ， as phrase-final markers
phrase_finals_per_chapter = []
for ch in chapters:
    # Strip whitespace, find characters preceding 。, ， , 、 or end-of-chapter
    finals = []
    chars = list(ch)
    for i in range(len(chars)):
        c = chars[i]
        if c in "。，；：、？！":
            # Find preceding non-whitespace, non-punct char
            j = i - 1
            while j >= 0 and chars[j] in "  \n\t":
                j -= 1
            if j >= 0 and chars[j] not in "。，；：、？！":
                finals.append(chars[j])
    # Last character of chapter (if not punct) also counts
    last_chars = ch.rstrip()
    if last_chars and last_chars[-1] not in "。，；：、？！":
        finals.append(last_chars[-1])
    phrase_finals_per_chapter.append(finals)

total_finals = sum(len(f) for f in phrase_finals_per_chapter)
print(f"Total phrase-final characters across all chapters: {total_finals}")
print(f"Average finals per chapter: {total_finals / len(chapters):.1f}")

# Build distribution
all_finals = [c for chapter_finals in phrase_finals_per_chapter for c in chapter_finals]
counter = Counter(all_finals)
print()
print(f"Distinct final characters: {len(counter)}")
print(f"Top 20 most frequent finals:")
for c, n in counter.most_common(20):
    print(f"  {c}  count={n}  freq={n/total_finals:.4f}")

# Try also using line-final (\n boundary) instead of punctuation
print()
print("=" * 80)
print("Alternative: line-final characters (split on \\n)")
all_line_finals = []
for ch in chapters:
    for line in ch.split("\n"):
        line = line.strip().rstrip("。，；：、？！ \t")
        if line:
            all_line_finals.append(line[-1])
counter_lines = Counter(all_line_finals)
print(f"Total line-finals: {len(all_line_finals)}")
print(f"Distinct line-finals: {len(counter_lines)}")
print(f"Top 20 line-finals:")
for c, n in counter_lines.most_common(20):
    print(f"  {c}  count={n}  freq={n/len(all_line_finals):.4f}")

# Chapter-final (last character of each chapter, stripping punct) — coarsest unit
print()
print("=" * 80)
print("Chapter-final characters (one per chapter, stripping trailing punct):")
chap_finals = []
for ch in chapters:
    stripped = ch.rstrip("。，；：、？！\n\t  ")
    if stripped:
        chap_finals.append(stripped[-1])
print(f"Total chapter-finals: {len(chap_finals)}")
counter_chap = Counter(chap_finals)
print(f"Distinct chapter-finals: {len(counter_chap)}")
for c, n in counter_chap.most_common(20):
    print(f"  {c}  count={n}  freq={n/len(chap_finals):.4f}")
