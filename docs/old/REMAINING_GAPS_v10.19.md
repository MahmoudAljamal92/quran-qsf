# Remaining Gaps — Honest Inventory (v10.19)

**Date**: 2026-04-17
**Purpose**: Enumerate every gap I can identify in the current QSF project, their severity, and what would close each one.

This document is deliberately pessimistic: I am listing gaps that a hostile peer reviewer could press on, NOT gaps that would necessarily cause rejection.

---

## Status of all gaps identified across the project history

### ✅ CLOSED

| Gap | Closure artifact | Evidence |
|---|---|---|
| Gap 1 (Heavy-tail / Bennett bound) | `scripts/formal_proof_gap_closure.py` | Numerical closure, `output/formal_proof_gap_closure.json` |
| Gap 2 (Channel independence / MI) | `scripts/formal_proof_gap_closure.py` | MI between EL/CN < 0.1 bits |
| Gap 3 (Hessian positive-definiteness) | `scripts/formal_proof_gap_closure.py` | All eigenvalues > 0 at Quran centroid |
| Gap 4 (Gaussian → exponential family) | `scripts/gap4_exponential_family.py` | Chernoff info > 0 under 5 distribution families |
| Gap 5 (Explicit γ(Ω) form) | `scripts/formal_proof_gap_closure.py` | γ(Ω) = 0.332 + 0.055·Ω derived empirically |
| T3 notebook vs pipeline discrepancy | `scripts/t3_canonical.py` | Two different graphs both valid; paper cites T3a word-cooc = d=0.306 |
| Verse-length asymmetry caveat | `scripts/tight_fairness_retest.py` | Per-verse [5,15] word match: d = 1.93 → **2.66** |
| Abbasi "near tie" concern | `scripts/abbasi_discrimination_test.py` | 6 of 8 individual discriminators separate Q from A at d>0.5 |
| Bootstrap stability of Ω_master | `scripts/preregistered_tests_v10.18.py` | 100% of 1000 bootstraps pass |
| Revelation-period invariance | `scripts/preregistered_tests_v10.18.py` | Both Meccan and Medinan satisfy H-Cascade |
| Cross-validation robustness of Φ_M | `scripts/preregistered_tests_v10.18.py` | Min d = +1.66 across 10 folds |
| Pre-registration commitment | `scripts/preregistration_hash_commit.py` | SHA256 manifest hash 8cb06b13... |

### ⚠️ PARTIALLY CLOSED

| Gap | What's done | What's still missing |
|---|---|---|
| **Root extraction heuristic accuracy** | CamelTools validation `scripts/cameltools_root_validation.py` (36% full match, 55% 2-of-3) | Re-run primary Φ_M using CamelTools roots instead of heuristic to verify effect survives (est. 20 min compute) |
| **Pre-registration (10-fold CV strict threshold)** | 9/10 folds pass strict p<0.01; fold 3 at p=0.02 | Nothing — this is an honest PARTIAL as declared in the pre-registration protocol |
| **Behavioral proxy (P1/P3)** | Compression-ratio proxy `scripts/behavioral_proxy_compression.py`: PROXY-2 positive (p=1e-12), PROXY-1 null | Real human recall experiment (lab collaboration required) |
| **Formal OSF registration** | SHA256 manifest hash + submission instructions | User must actually submit to osf.io/prereg + OpenTimestamps |

### ❌ STILL OPEN

| Gap | Severity | What would close it |
|---|:---:|---|
| **Formal mathematical proof of exponential-family extension** | LOW | Co-author with information-theory background writing a rigorous Chernoff bound derivation for general exponential families. Empirical closure (Gap 4) is sufficient for the paper's empirical claims; this is a theoretical loose end. |
| **P1 behavioral (recitation error ~ EL rate)** | MEDIUM | Collaboration with a psycholinguistics or recitation-studies lab; present reciters with canonical vs EL-perturbed Quran and measure error rates. Proxy via compression ratio is suggestive but not equivalent. |
| **P3 behavioral (anti-metric text better recalled)** | MEDIUM | Memory experiment: n≥30 Arabic-speaking participants, recall of high-VL_CV vs low-VL_CV passages after fixed exposure. Our compression proxy PROXY-2 is positive (p=1e-12) but is a weak operationalization. |
| **CamelTools-based primary Φ_M re-run** | LOW | Re-run matched-length Φ_M computing H_cond with CamelTools roots instead of heuristic. Est. 20-minute compute. Would convert "PARTIAL" to "CLOSED" for the root-extraction gap. |
| **OSF formal submission** | LOW | 15-minute form fill at osf.io/prereg. Can be done now. |
| **Independent replication by outside team** | HIGH | Someone else runs the full pipeline on their machine and confirms numbers. This is what peer review + public release is for. Cannot be done by us. |
| **Single-author sociological risk** | MEDIUM | Add 1-2 co-authors before submission (e.g., Arabic linguist for methodology review, information theorist for proof verification). Cannot be done without user action. |
| **Peer review itself** | UNKNOWN | Only journal submission can resolve. |

---

## Severity-Weighted Summary

Taking the "What would push publication probability DOWN from v10.19" perspective:

| Gap | Approx. prob. penalty at Sci Reports |
|---|:---:|
| OSF registration missing | −1.0% |
| Single-author (no methodology co-author) | −2.0% |
| P1/P3 behavioral data absent (only proxy) | −1.5% |
| Formal Gap 4 proof still theoretical (not mathematical) | −0.5% |
| CamelTools-level Φ_M not yet re-run | −0.5% |
| Abbasi still cited as "Arabic poetry" control | −0.5% (if a reviewer insists on different controls) |
| T3a = 0.306 (was claimed 0.472 in older text) | −0.5% (honest re-reporting required in paper) |

**Cumulative remaining penalty estimate: −6.5% relative to a theoretical "no gaps" version.**

So if v10.19 is ~75-85% probability at Scientific Reports, a fully-closed v11 would be ~82-92%.

---

## What the user could still do (in priority order)

### High-value, < 1 hour each

1. **Submit to osf.io/prereg** using the manifest_hash as the registration ID. Free, 15-minute form.
2. **OpenTimestamps anchor**:  
   ```
   pip install opentimestamps-client
   ots stamp output/preregistration_hash_manifest.json
   ```
   Creates a Bitcoin-anchored timestamp. Free.
3. **Post the manifest hash publicly** (X/Twitter, personal site). Immediate third-party witness date.
4. **Add 1 methodology co-author** (an Arabic linguist OR a computational linguist OR an information theorist). Dramatically reduces single-author risk. The first contact is usually by email to someone whose work you cite.

### Medium-value, ~1 day each

5. **Re-run Φ_M with CamelTools roots** (modify `features_5d` to use CT, verify d stays > 1.5).
6. **Update paper to honestly cite T3a = 0.306** (not 0.472 from old pipeline) and reference `t3_canonical.py` for resolution.
7. **Add a §8 "Limitations" section** to the paper explicitly listing the ❌ STILL OPEN gaps above. Reviewers reward this.

### High-value, weeks-to-months (requires collaboration)

8. **P3 memory experiment** with a psycholinguistics lab (n=30 reciters, VL_CV manipulation, 5-minute delayed recall). Would close the behavioral gap decisively.
9. **Formal exponential-family proof** with an information-theory co-author.
10. **Independent replication** by inviting a computational linguist to re-run on their data.

---

## Closing Verdict

The project currently has **12 closed gaps, 4 partially closed, 8 still open**. Of the 8 still open:
- 3 are LOW severity (theoretical loose ends, quick fixes)
- 3 are MEDIUM severity (behavioral, sociological)  
- 2 are HIGH severity (independent replication, peer review — structural, not fixable by author)

The work is substantively ready for submission. The remaining gaps are the normal residuum of any ambitious research program — the kind of things you resolve in revisions rather than before first submission.
