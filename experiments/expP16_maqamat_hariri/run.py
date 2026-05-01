"""
expP16_maqamat_hariri/run.py
============================
Maqamat al-Hariri (50 maqāmāt, classical Arabic saj‛) test of the EL law.

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP16_maqamat_hariri/expP16_maqamat_hariri.json
        data/corpora/ar/maqamat/maqamat_hariri.txt (downloaded)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import features_5d, el_rate  # noqa: E402

EXP = "expP16_maqamat_hariri"
SEED = 42
SVM_C = 1.0
MIN_VERSES = 2
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Candidate Maqamat URLs (try in order; first success wins).
# Verified via `https://archive.org/metadata/<id>` lookups.
MAQAMAT_URLS = [
    # Internet Archive: al-Hariri 50 maqamat (502 KB Arabic plain text)
    ("text", "https://archive.org/download/maqamateharirialmaqlatalbeeriya/54_djvu.txt"),
    # Backup: alternate Maqamat-genre item (al-Hamadhani — saj' rhymed prose,
    # equally valid as a saj' control even though not al-Hariri specifically)
    ("text", "https://archive.org/download/maqamatalhariri/%D9%85%D9%82%D8%A7%D9%85%D8%A7%D8%AA%20%D8%A8%D8%AF%D9%8A%D8%B9%20%D8%A7%D9%84%D8%B2%D9%85%D8%A7%D9%86%20%D8%A7%D9%84%D9%87%D9%85%D8%B0%D8%A7%D9%86%D9%8A_djvu.txt"),
    # Backup: Sharaha (commentary) volume 1 — contains original Maqamat text inline
    ("text", "https://archive.org/download/sharaha-maqamat-al-hareeri-4_202011/Sharaha%20Maqamat%20Al%20Hareeri%201_djvu.txt"),
    # Wikisource fallback (URL-encoded Arabic title)
    ("html", "https://ar.wikisource.org/wiki/%D9%85%D9%82%D8%A7%D9%85%D8%A7%D8%AA_%D8%A7%D9%84%D8%AD%D8%B1%D9%8A%D8%B1%D9%8A"),
]
USER_AGENT = "QSF-research/v7.9-cand (educational; respect upstream license)"

# Combining-mark / punctuation set used to determine verse boundaries.
NON_ALPHA_PUNCT = set(".,;:!?\"'()[]{}-—–…॥।。、，；：！？「」『』〈〉«»‹›")


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _http_get(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"      [http_get fail {e!r}]")
        return None


def _strip_html(html: str) -> str:
    """Best-effort HTML strip — preserves Arabic content. We don't need
    perfect; we just need enough text to compute features."""
    # Remove scripts / styles
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block tags with newlines so we keep paragraph structure
    html = re.sub(r"<(p|br|div|li|h[1-6])[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Drop remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
    return html


def _arabic_only(text: str) -> str:
    """Keep Arabic letters + diacritics + spaces + Arabic punctuation."""
    out_chars = []
    for c in text:
        cp = ord(c)
        # Arabic block U+0600-U+06FF + Arabic supplement U+0750-U+077F + Arabic ext-A U+08A0-U+08FF
        # + Arabic presentation forms U+FB50-U+FDFF + U+FE70-U+FEFF
        if (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF) \
                or (0xFB50 <= cp <= 0xFDFF) or (0xFE70 <= cp <= 0xFEFF):
            out_chars.append(c)
        elif c in (" ", "\n", "\t", ".", ",", "؟", "،", "؛", "!", "?"):
            out_chars.append(c)
    return "".join(out_chars)


def _split_verses(arabic_text: str, min_words: int = 3) -> list[str]:
    """Split Maqamat text into verses on rhyme-line boundaries.
    For saj‛ the natural verse delimiter is the period or semicolon; we
    additionally split on Arabic full-stop (U+06D4) and Arabic comma (U+060C)
    when followed by line break. We require at least `min_words` per verse."""
    text = re.sub(r"[\r]+", "", arabic_text)
    # Replace Arabic full-stop with ASCII '.'
    text = text.replace("\u06D4", ".")
    # Split on common saj‛ delimiters: ., ؟, !, newline+newline
    parts = re.split(r"[.؟!]+|\n\s*\n", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p.split()) >= min_words:
            out.append(p)
    return out


def _terminal_natural_letter(verse: str) -> str | None:
    for c in reversed(verse.strip()):
        cat = unicodedata.category(c)
        if cat.startswith("M"):
            continue
        if c in NON_ALPHA_PUNCT or c.isspace():
            continue
        if c.isalpha():
            return c
    return None


def _hotelling_t2(X_quran: np.ndarray, X_ctrl: np.ndarray) -> float:
    nq, p = X_quran.shape
    nc = X_ctrl.shape[0]
    mu_q = X_quran.mean(axis=0)
    mu_c = X_ctrl.mean(axis=0)
    Sq = np.cov(X_quran, rowvar=False, ddof=1) if nq > 1 else np.zeros((p, p))
    Sc = np.cov(X_ctrl, rowvar=False, ddof=1) if nc > 1 else np.zeros((p, p))
    Spool = ((nq - 1) * Sq + (nc - 1) * Sc) / max(nq + nc - 2, 1)
    Sinv = np.linalg.pinv(Spool)
    diff = mu_q - mu_c
    return float((nq * nc / (nq + nc)) * (diff @ Sinv @ diff))


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Download Maqamat ---
    maqamat_dir = _ROOT / "data" / "corpora" / "ar" / "maqamat"
    maqamat_dir.mkdir(parents=True, exist_ok=True)
    dest = maqamat_dir / "maqamat_hariri.txt"

    download_log: dict = {"attempts": [], "final": None}
    if dest.exists() and dest.stat().st_size > 50_000:
        print(f"[{EXP}] Maqamat already downloaded ({dest.stat().st_size} bytes)")
        download_log["final"] = {"status": "cached", "size": dest.stat().st_size}
    else:
        print(f"[{EXP}] Downloading Maqamat al-Hariri ...")
        ok = False
        for kind, url in MAQAMAT_URLS:
            print(f"   [{kind}] {url}")
            data = _http_get(url, timeout=45)
            attempt = {"kind": kind, "url": url, "got_bytes": len(data) if data else 0}
            if data is None or len(data) < 5_000:
                download_log["attempts"].append({**attempt, "status": "FAILED"})
                continue
            text = data.decode("utf-8", errors="ignore")
            if kind == "html":
                text = _strip_html(text)
            arabic = _arabic_only(text)
            n_arabic_chars = sum(1 for c in arabic if c.isalpha())
            attempt["arabic_chars"] = n_arabic_chars
            if n_arabic_chars < 50_000:  # Maqamat is ~200 KB of Arabic text
                download_log["attempts"].append({**attempt, "status": "TOO_SHORT"})
                continue
            with open(dest, "w", encoding="utf-8") as f:
                f.write(arabic)
            sha = hashlib.sha256(arabic.encode("utf-8")).hexdigest()
            download_log["attempts"].append({**attempt, "status": "OK", "sha256": sha})
            download_log["final"] = {"status": "downloaded", "url": url,
                                      "kind": kind, "size": dest.stat().st_size,
                                      "sha256": sha}
            print(f"   OK ({n_arabic_chars} Arabic chars, sha={sha[:12]}...)")
            ok = True
            break
        if not ok:
            print(f"[{EXP}] All download attempts failed; cannot run Maqamat test.")
            record = {
                "experiment": EXP, "prereg_sha256": _prereg_hash(),
                "download_log": download_log,
                "verdict": "DOWNLOAD_FAILED",
                "wall_time_s": time.time() - t0,
            }
            with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            self_check_end(pre, EXP)
            return 0

    # --- Parse to "surahs" (we treat each maqāmā as a unit; if we cannot
    # split into 50 maqāmāt cleanly, we fall back to chunking by ~200-word
    # groups so we have many units for the classifier).
    raw = dest.read_text(encoding="utf-8", errors="ignore")
    verses = _split_verses(raw, min_words=3)
    print(f"[{EXP}] Total verses parsed: {len(verses)}")
    if len(verses) < 100:
        # Fallback: split on whitespace, group into 30-verse chunks (proxy for
        # one short maqāmā each)
        words = raw.split()
        verses = []
        chunk_size = 30
        cur = []
        for w in words:
            cur.append(w)
            if len(cur) >= chunk_size and (w.endswith(".") or w.endswith("؟") or w.endswith("!")):
                verses.append(" ".join(cur))
                cur = []
        if cur:
            verses.append(" ".join(cur))
        print(f"[{EXP}] Fallback chunking: {len(verses)} verses")

    # Group verses into "units" of ~50 verses each (proxy for maqāmāt)
    UNIT_SIZE = 50
    units: list[list[str]] = []
    for i in range(0, len(verses), UNIT_SIZE):
        chunk = verses[i:i + UNIT_SIZE]
        if len(chunk) >= MIN_VERSES:
            units.append(chunk)
    print(f"[{EXP}] Built {len(units)} Maqamat units of ~{UNIT_SIZE} verses each")

    # --- Compute EL, ن-rate, 5-D ---
    Xm = []
    el_m = []
    finals = []
    for u in units:
        feat = features_5d(u)
        if np.isfinite(feat).all():
            Xm.append(feat)
            el_m.append(el_rate(u))
        for v in u:
            ch = _terminal_natural_letter(v)
            if ch:
                finals.append(ch)
    Xm = np.array(Xm, dtype=float)
    el_m = np.array(el_m, dtype=float)
    cnt = Counter(finals)
    tot = sum(cnt.values())
    p_noon = cnt.get("\u0646", 0) / tot if tot > 0 else 0.0
    top_letter, top_count = cnt.most_common(1)[0] if cnt else ("", 0)
    p_max = top_count / tot if tot > 0 else 0.0
    print(f"[{EXP}] Maqamat: n_units={len(units)}, n_verses_total={tot}")
    print(f"[{EXP}]   EL mean = {el_m.mean():.4f}  EL std = {el_m.std(ddof=1):.4f}")
    print(f"[{EXP}]   p(ن) = {p_noon:.4f}  top_letter = {top_letter} (p_max = {p_max:.4f})")

    # --- Classify Maqamat vs Quran via EL ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl for Quran ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    el_q = []
    for u in CORPORA.get("quran", []):
        if len(u.verses) >= MIN_VERSES:
            el_q.append(el_rate(list(u.verses)))
    el_q = np.array(el_q, dtype=float)
    n_q = len(el_q)
    n_m = len(el_m)

    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    from scipy.stats import mannwhitneyu

    Xt = np.concatenate([el_q, el_m]).reshape(-1, 1)
    yt = np.concatenate([np.ones(n_q), np.zeros(n_m)])
    svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced", random_state=SEED)
    svm.fit(Xt, yt)
    auc_qm = float(roc_auc_score(yt, svm.decision_function(Xt)))
    mw = mannwhitneyu(el_q, el_m, alternative="greater")
    mw_p = float(mw.pvalue)

    # --- Verdict ---
    cond_EL = el_m.mean() < 0.40
    cond_noon = p_noon < 0.20
    cond_AUC = auc_qm >= 0.95
    if auc_qm < 0.85:
        verdict = "EL_LAW_FAILS_VS_SAJ"
    elif cond_EL and cond_noon and cond_AUC:
        verdict = "QURAN_DISTINCT_FROM_SAJ"
    else:
        verdict = "SAJ_PARTIALLY_OVERLAPS"

    print(f"[{EXP}] AUC(Quran vs Maqamat) = {auc_qm:.4f}  MW p = {mw_p:.4e}")
    print(f"[{EXP}] Verdict: {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "download_log": download_log,
        "n_units": len(units),
        "n_verses_total": tot,
        "el_quran_mean": float(el_q.mean()),
        "el_maqamat_mean": float(el_m.mean()),
        "el_maqamat_std": float(el_m.std(ddof=1)),
        "p_noon_maqamat": p_noon,
        "p_max_maqamat": p_max,
        "top_letter_maqamat": top_letter,
        "auc_quran_vs_maqamat": auc_qm,
        "mw_p_quran_gt_maqamat": mw_p,
        "cond_EL_lt_040": bool(cond_EL),
        "cond_noon_lt_020": bool(cond_noon),
        "cond_AUC_geq_095": bool(cond_AUC),
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
