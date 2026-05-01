"""
expP15_riwayat_invariance/run.py
================================
Riwayat invariance test: does T² and EL survive Warsh / Qalun / Duri?

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP15_riwayat_invariance/expP15_riwayat_invariance.json
        data/corpora/ar/riwayat/<warsh|qalun|duri>.txt (downloaded)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
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

EXP = "expP15_riwayat_invariance"
SEED = 42
SVM_C = 1.0
MIN_VERSES = 2
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Candidate download URLs per riwayat (try in order; first success wins).
# Source: github.com/IshakiSmaili/QuranJSON (MIT licensed; provides 5 riwayat
# plus Hafs as plain UTF-8 text in the standard `surah|verse|text` format).
RIWAYAT_URLS: dict[str, list[str]] = {
    "warsh": [
        "https://raw.githubusercontent.com/IshakiSmaili/QuranJSON/main/data/Warsh.txt",
    ],
    "qalun": [
        "https://raw.githubusercontent.com/IshakiSmaili/QuranJSON/main/data/Qaloun.txt",
    ],
    "duri": [
        "https://raw.githubusercontent.com/IshakiSmaili/QuranJSON/main/data/Douri.txt",
    ],
    "shuba": [
        "https://raw.githubusercontent.com/IshakiSmaili/QuranJSON/main/data/Shuba.txt",
    ],
    "sousi": [
        "https://raw.githubusercontent.com/IshakiSmaili/QuranJSON/main/data/Sousi.txt",
    ],
}

# AUDIT FIX F4 (2026-04-26): pin SHA-256 of each riwayat input.
# The IshakiSmaili/QuranJSON repository is mutable upstream (issues, fixes,
# diacritic normalisations can land at any time). Without a pin, a
# silent upstream change would alter every downstream result on the next
# fresh download. Each value below was captured on 2026-04-26 from the
# locally cached files at data/corpora/ar/riwayat/<name>.txt that drove
# the previously locked verdict. Any future deviation triggers a
# `SHA_MISMATCH` skip (same severity as `DOWNLOAD_FAILED`).
#
# To intentionally re-pin (e.g. after vetting an upstream fix), update
# the value below AND record the rationale in PREREG.md.
RIWAYAT_PINNED_SHA256: dict[str, str] = {
    "warsh": "b5a8ad018e68a2c641a1acc08fa1c1bb9b0828ed136fbbbe19a89b6ca2828b7f",
    "qalun": "183c0a6c82ef14e2950ac0200baaedfb0c41c7522fd004f34aa95369b0413a84",
    "duri":  "4cae9123aa739310f38a8c9399d737755242a353476675989fe5f77e179e07c8",
    "shuba": "c64677fcbdfb239cb854f1d514020a8970833805c56951c40696bb9e1d82b8a5",
    "sousi": "045ded25e270ca5f333a588ffc79db43fbe514551185765b32dfc708567e5985",
}

USER_AGENT = "QSF-research/v7.9-cand (educational; respect tanzil.net license)"


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _download(url: str, dest: Path, timeout: int = 30) -> bool:
    """Try to download `url` to `dest`. Return True on success."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 100_000:  # Quran text is at least ~700 KB
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"      [download fail {e!r}]")
        return False


def _sha256_of(path: Path) -> str:
    """Stream-compute SHA-256 of a file (memory-bounded for ~1.4 MB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _verify_pin(name: str, path: Path) -> tuple[bool, str, str | None]:
    """F4: verify on-disk SHA-256 matches the pinned expectation.

    Returns ``(ok, observed_sha, expected_sha_or_None)``. ``ok`` is
    ``True`` only when both an expected pin exists for ``name`` AND the
    observed hash equals it. If no pin is registered for ``name``
    (which should never happen for the canonical 5 riwayat) the
    function returns ``ok=False`` so the run skips the riwayat rather
    than silently trusting an unpinned file.
    """
    observed = _sha256_of(path)
    expected = RIWAYAT_PINNED_SHA256.get(name)
    return (expected is not None and observed == expected, observed, expected)


def _parse_tanzil(text: str) -> list[list[str]]:
    """Parse the IshakiSmaili/QuranJSON format:
       <surah header in Arabic, e.g. "سُورَةُ اُ۬لْفَاتِحَةِ">
       <blank line>
       <surah text with verses delimited by Arabic-Indic numerals ١٢٣...>
       <blank line>
       (next surah header)
    Returns list of 114 lists of verse strings.
    """
    # Arabic-Indic digit range U+0660 .. U+0669
    AR_DIGITS = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
    # Surah header detector: must contain سُورَة (with diacritics it can be سُورَةُ ...)
    header_re = re.compile(r"^\s*س[ُ]?و[رَ]?[ةَ]")

    # Split file into surah blocks on header lines
    lines = text.splitlines()
    surah_blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if header_re.match(line):
            if current:
                surah_blocks.append(current)
            current = []
        else:
            current.append(line)
    if current:
        surah_blocks.append(current)

    if len(surah_blocks) < 100:
        # Fallback: maybe headers are formatted differently; try splitting on
        # double-blank-line as surah separator.
        full = "\n".join(lines)
        surah_blocks = [b.splitlines() for b in re.split(r"\n\s*\n\s*\n+", full)]

    surahs: list[list[str]] = []
    # Verse splitter: any single Arabic-Indic numeral (one or more digits) acts
    # as the separator. We may also see ASCII digits; cover both.
    verse_split_re = re.compile(rf"[{AR_DIGITS}\d]+")
    for block in surah_blocks:
        joined = " ".join(b.strip() for b in block if b.strip())
        if not joined:
            continue
        parts = verse_split_re.split(joined)
        verses = [p.strip() for p in parts if p.strip() and len(p.split()) >= 1]
        if len(verses) >= 1:
            surahs.append(verses)

    return surahs


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

    # --- Download riwayat (F4: every load path verifies the pinned SHA) ---
    riwayat_dir = _ROOT / "data" / "corpora" / "ar" / "riwayat"
    riwayat_dir.mkdir(parents=True, exist_ok=True)
    download_log: dict[str, dict] = {}
    for name, urls in RIWAYAT_URLS.items():
        dest = riwayat_dir / f"{name}.txt"
        expected = RIWAYAT_PINNED_SHA256.get(name)

        # Branch 1: file is already on disk.
        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"[{EXP}] Riwayat '{name}' cached ({dest.stat().st_size} bytes)")
            ok, observed, _ = _verify_pin(name, dest)
            if ok:
                download_log[name] = {
                    "status": "cached",
                    "url": None,
                    "size": dest.stat().st_size,
                    "sha256": observed,
                    "sha256_expected": expected,
                    "sha256_match": True,
                }
            else:
                print(f"   [F4 SHA_MISMATCH] {name}: observed {observed[:12]}.. "
                      f"!= pinned {(expected or 'NONE')[:12]}.. -> SKIPPING")
                download_log[name] = {
                    "status": "SHA_MISMATCH",
                    "url": None,
                    "size": dest.stat().st_size,
                    "sha256": observed,
                    "sha256_expected": expected,
                    "sha256_match": False,
                }
            continue

        # Branch 2: file missing -> download.
        print(f"[{EXP}] Downloading riwayat '{name}' ...")
        ok_url = None
        for url in urls:
            print(f"   trying {url}")
            if _download(url, dest):
                ok_url = url
                break
        if not ok_url:
            download_log[name] = {
                "status": "FAILED", "url": None,
                "size": 0, "sha256": None,
                "sha256_expected": expected, "sha256_match": False,
            }
            continue

        # Branch 2b: download succeeded -> verify the pin.
        ok, observed, _ = _verify_pin(name, dest)
        if ok:
            download_log[name] = {
                "status": "downloaded",
                "url": ok_url,
                "size": dest.stat().st_size,
                "sha256": observed,
                "sha256_expected": expected,
                "sha256_match": True,
            }
            print(f"   OK ({dest.stat().st_size} bytes)  sha={observed[:12]}.. PINNED")
        else:
            # Reject the freshly-downloaded file so it cannot poison a
            # subsequent run via the cache branch.
            try:
                dest.unlink()
            except OSError:
                pass
            download_log[name] = {
                "status": "SHA_MISMATCH",
                "url": ok_url,
                "size": 0,
                "sha256": observed,
                "sha256_expected": expected,
                "sha256_match": False,
            }
            print(f"   [F4 SHA_MISMATCH] {name}: downloaded SHA {observed[:12]}.. "
                  f"!= pinned {(expected or 'NONE')[:12]}.. -> file deleted, skipping")

    # --- Compute ctrl features (load from existing pickle) ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Locked control pool
    Xc = []
    for cn in ARABIC_CTRL:
        for u in CORPORA.get(cn, []):
            if len(u.verses) >= MIN_VERSES:
                Xc.append(features_5d(list(u.verses)))
    Xc = np.array(Xc, dtype=float)
    Xc = Xc[np.isfinite(Xc).all(axis=1)]
    n_c = Xc.shape[0]
    el_c = []
    for cn in ARABIC_CTRL:
        for u in CORPORA.get(cn, []):
            if len(u.verses) >= MIN_VERSES:
                el_c.append(el_rate(list(u.verses)))
    el_c = np.array(el_c, dtype=float)

    # Hafs baseline
    Xq_hafs = []
    el_q_hafs = []
    for u in CORPORA.get("quran", []):
        if len(u.verses) >= MIN_VERSES:
            Xq_hafs.append(features_5d(list(u.verses)))
            el_q_hafs.append(el_rate(list(u.verses)))
    Xq_hafs = np.array(Xq_hafs, dtype=float)
    Xq_hafs = Xq_hafs[np.isfinite(Xq_hafs).all(axis=1)]
    el_q_hafs = np.array(el_q_hafs, dtype=float)
    n_q_hafs = Xq_hafs.shape[0]
    T2_hafs = _hotelling_t2(Xq_hafs, Xc)
    EL_hafs = float(el_q_hafs.mean())
    print(f"[{EXP}] Hafs baseline: T² = {T2_hafs:.2f}, EL_q = {EL_hafs:.4f}, n_q = {n_q_hafs}")

    # --- Process each riwayat ---
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score

    rows: dict[str, dict] = {}
    for name in RIWAYAT_URLS.keys():
        info = download_log.get(name, {})
        # F4: only proceed when both download AND pinned-SHA check passed.
        if info.get("status") not in ("downloaded", "cached") or not info.get("sha256_match"):
            reason = info.get("status", "UNKNOWN")
            rows[name] = {
                "status": "DOWNLOAD_FAILED" if reason != "SHA_MISMATCH" else "SHA_MISMATCH",
                "sha256_match": bool(info.get("sha256_match")),
                "sha256_observed": info.get("sha256"),
                "sha256_expected": info.get("sha256_expected"),
            }
            print(f"[{EXP}] {name}: skipped ({reason})")
            continue
        path = riwayat_dir / f"{name}.txt"
        text = path.read_text(encoding="utf-8", errors="ignore")
        surahs = _parse_tanzil(text)
        if not surahs or len(surahs) < 100:
            rows[name] = {"status": "PARSE_FAILED",
                          "n_surahs_parsed": len(surahs)}
            print(f"[{EXP}] {name}: parsed only {len(surahs)} surahs (need 114); skipping")
            continue
        Xq = []
        el_q = []
        for verses in surahs:
            if len(verses) >= MIN_VERSES:
                Xq.append(features_5d(verses))
                el_q.append(el_rate(verses))
        Xq = np.array(Xq, dtype=float)
        Xq = Xq[np.isfinite(Xq).all(axis=1)]
        el_q = np.array(el_q, dtype=float)
        n_q = Xq.shape[0]
        if n_q < 50:
            rows[name] = {"status": "TOO_FEW_SURAHS", "n_surahs": n_q}
            print(f"[{EXP}] {name}: only {n_q} parseable surahs; skipping")
            continue
        T2 = _hotelling_t2(Xq, Xc)
        EL_mean = float(el_q.mean())
        # AUC EL
        Xt = np.concatenate([el_q, el_c]).reshape(-1, 1)
        yt = np.concatenate([np.ones(n_q), np.zeros(n_c)])
        svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced", random_state=SEED)
        svm.fit(Xt, yt)
        auc = float(roc_auc_score(yt, svm.decision_function(Xt)))

        rel_T2 = (T2 - T2_hafs) / T2_hafs
        rel_EL = (EL_mean - EL_hafs) / EL_hafs
        cond_T2 = abs(rel_T2) < 0.05
        cond_EL = abs(rel_EL) < 0.02
        cond_AUC = auc >= 0.97
        rows[name] = {
            "status": "OK",
            "n_surahs": n_q,
            "T2": T2, "rel_T2_drift": rel_T2,
            "EL_mean": EL_mean, "rel_EL_drift": rel_EL,
            "auc_el": auc,
            "cond_T2": cond_T2, "cond_EL": cond_EL, "cond_AUC": cond_AUC,
            "n_conditions_met": int(cond_T2) + int(cond_EL) + int(cond_AUC),
        }
        print(f"[{EXP}] {name}: T² = {T2:.2f} (Δ {rel_T2:+.3f}), "
              f"EL = {EL_mean:.4f} (Δ {rel_EL:+.4f}), "
              f"AUC = {auc:.4f}  -> {rows[name]['n_conditions_met']}/3")

    # --- Verdict ---
    ok_riwayat = [r for r in rows.values() if r.get("status") == "OK"]
    if not ok_riwayat:
        verdict = "INSUFFICIENT_DATA"
    elif all(r["n_conditions_met"] == 3 for r in ok_riwayat):
        verdict = "INVARIANT"
    elif all(r["n_conditions_met"] >= 2 for r in ok_riwayat):
        verdict = "NEAR_INVARIANT"
    else:
        verdict = "RIWAYAT_DEPENDENT"

    print(f"[{EXP}] Verdict: {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "download_log": download_log,
        "hafs_baseline": {
            "T2": T2_hafs, "EL_mean": EL_hafs, "n_q": n_q_hafs, "n_c": n_c,
        },
        "rows": rows,
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
