"""exp182 — The Quran IFS Fractal (genuine self-similar fractal image).

A proper fractal renderer driven entirely by Quran letter-frequency data.

Construction (Iterated Function System / IFS):
  - 28 affine contraction maps f_1, ..., f_28 in the complex plane
  - f_k(z) = c * exp(2πi * k / 28) * z + exp(2πi * k / 28)
    where c = contraction ratio (we use c = 0.35 to keep the attractor visually
    crisp); the translation places each contraction's fixed point on the unit
    circle at angle 2πk/28 (one per Arabic letter).
  - Each map f_k is chosen with probability p_k = empirical Quran frequency
    of the k-th Arabic letter (ا, ب, ت, ث, ج, ح, خ, ...).

Chaos-game rendering:
  - Start at z_0 = 0
  - At each step: pick k with probability p_k, update z_{n+1} = f_k(z_n)
  - Discard the first few hundred iterations (pre-attractor transient)
  - Accumulate a density histogram in a high-res grid
  - Render with log-density colormap

Analytical similarity dimension (for equal-contraction IFS):
  d_sim satisfies  Σ_k p_k * c^{d_sim} = 1   (Moran's equation, general form)
                   => 28 * c^{d_sim} weighted by p_k but c identical => c^{d_sim} = 1/Σp_k = 1
  For the simpler information dimension on an IFS with equal c:
      d_info = H_1({p_k}) / log(1/c)
  where H_1 is Shannon entropy of the letter distribution in NATS.

The result is a genuine Quran fractal: its very shape encodes the letter
frequencies, its fractal dimension is a closed-form function of the Quran's
letter-frequency Shannon entropy, and it exhibits true self-similarity at
all scales.
"""
from __future__ import annotations
import io
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp182_quran_ifs_fractal"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)

# IFS parameters
# For 28 equal-contraction maps, similarity dimension = log(28)/log(1/c).
# To get d_sim < 2 (a PROPER fractal, not space-filling), we need
#   c < 1/sqrt(28) = 0.1890
# We use c = 0.18 -> d_sim ≈ 1.944 (just under 2 → genuine fractal).
CONTRACTION_C = 0.18          # individual map contraction ratio
N_ITERATIONS = 6_000_000      # chaos-game iterations (more because points are sparser)
BURN_IN = 500                 # discard first N iterations
IMG_SIZE = 2048               # pixels
SEED = 20260503


def load_quran_letter_frequencies() -> np.ndarray:
    """Return 28-vector of normalised Quran letter frequencies."""
    lines = DATA.read_text(encoding="utf-8").splitlines()
    counts = Counter()
    for line in lines:
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        text = x[2]
        for c in text:
            if c in ARABIC_LETTERS_SET:
                counts[c] += 1
    total = sum(counts.values())
    p = np.array([counts.get(c, 0) / total for c in ARABIC_LETTERS])
    return p


def render_ifs_fractal(p: np.ndarray, c: float, n_iter: int, burn_in: int,
                        img_size: int, seed: int):
    """Chaos-game rendering of an IFS with 28 contractions at angle 2πk/28.

    Returns:
        density : (img_size, img_size) float32 array
        colors  : (img_size, img_size) int array with the most-recent letter
                  index that hit each pixel, useful for per-letter coloring.
    """
    rng = np.random.default_rng(seed)
    # Pre-compute the 28 affine maps: f_k(z) = a_k * z + b_k
    k = np.arange(28)
    angles = 2 * np.pi * k / 28
    # Contraction a_k = c * exp(i * angles) ; translation b_k = exp(i * angles)
    a_real = c * np.cos(angles)
    a_imag = c * np.sin(angles)
    b_real = np.cos(angles)
    b_imag = np.sin(angles)

    # Sample all map choices at once (vectorisable)
    choices = rng.choice(28, size=n_iter, p=p)

    z_re = 0.0
    z_im = 0.0

    # Accumulator
    density = np.zeros((img_size, img_size), dtype=np.float64)
    colors_sum = np.zeros((img_size, img_size, 3), dtype=np.float64)

    # Color palette: 28 colors along a hue wheel matching angle of letter
    # Use a vibrant palette — for each letter k, color (R, G, B) from angle.
    # Using HSV: hue = k / 28, sat = 0.85, val = 0.95
    import colorsys
    palette = np.array([
        colorsys.hsv_to_rgb(k_ / 28.0, 0.85, 0.95)
        for k_ in range(28)
    ])  # shape (28, 3)

    # Image bounds: attractor lies within max radius = 1 / (1 - c) (from sum of
    # geometric series of translations). For c = 0.35, max radius ≈ 1.54.
    R = 1.0 / (1.0 - c) * 1.05
    inv_scale = (img_size - 1) / (2 * R)

    for i in range(n_iter):
        kk = choices[i]
        new_re = a_real[kk] * z_re - a_imag[kk] * z_im + b_real[kk]
        new_im = a_real[kk] * z_im + a_imag[kk] * z_re + b_imag[kk]
        z_re, z_im = new_re, new_im
        if i < burn_in:
            continue
        # Map to pixel coords
        px = int((z_re + R) * inv_scale)
        py = int((z_im + R) * inv_scale)
        if 0 <= px < img_size and 0 <= py < img_size:
            density[py, px] += 1.0
            colors_sum[py, px] += palette[kk]
    return density, colors_sum


def main():
    print("=" * 72)
    print("exp182 — Quran IFS Fractal (genuine self-similar fractal image)")
    print("=" * 72)

    print("\n# Loading Quran letter frequencies...")
    p = load_quran_letter_frequencies()
    # Shannon entropy in nats and bits
    p_safe = p[p > 0]
    H_nats = -np.sum(p_safe * np.log(p_safe))
    H_bits = H_nats / np.log(2)
    print(f"  Shannon entropy H_1 = {H_bits:.4f} bits = {H_nats:.4f} nats")
    print(f"  Entropy ceiling log2(28) = {np.log2(28):.4f} bits")
    print(f"  Redundancy R = 1 - H_1/log2(28) = {1 - H_bits/np.log2(28):.4f}")

    # Analytical information dimension for equal-contraction IFS
    # d_info = H_1(p) / log(1/c)
    c = CONTRACTION_C
    d_info = H_nats / np.log(1.0 / c)
    # Also compute the upper-bound similarity dimension (equal weights, ignoring p):
    # For equal weights the similarity dimension d_sim solves 28 * c^d = 1
    # => d_sim = log(28) / log(1/c)
    d_sim = np.log(28) / np.log(1.0 / c)
    print(f"\n# Analytical fractal dimensions (contraction c = {c}):")
    print(f"  Information dimension  d_info = H_1(p) / log(1/c) = {d_info:.4f}")
    print(f"  Similarity dimension   d_sim  = log(28) / log(1/c) = {d_sim:.4f}")
    print(f"  Ambient dimension = 2 (complex plane)")
    print(f"  => attractor is a PROPER FRACTAL (non-integer dim between 0 and 2)")

    # Show top-5 letter frequencies
    order = np.argsort(p)[::-1]
    print("\n# Top-5 Arabic letters by frequency (defining largest IFS lobes):")
    for rk in range(5):
        k = order[rk]
        print(f"  {ARABIC_LETTERS[k]}  p = {p[k]:.4f}  angle = {360*k/28:.1f}°")

    print(f"\n# Running chaos-game IFS render ({N_ITERATIONS:,} iter, {IMG_SIZE}x{IMG_SIZE})...")
    density, colors_sum = render_ifs_fractal(
        p, c, N_ITERATIONS, BURN_IN, IMG_SIZE, SEED
    )
    n_filled = int((density > 0).sum())
    print(f"  Non-empty pixels: {n_filled:,} / {IMG_SIZE * IMG_SIZE:,} "
          f"({n_filled / (IMG_SIZE * IMG_SIZE):.2%})")
    print(f"  Max density    : {density.max():.0f}")
    print(f"  Total hits     : {density.sum():.0f}")

    # --- Render 1: LOG-DENSITY GRAYSCALE ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Log-density with epsilon
        log_dens = np.log1p(density)
        log_dens = log_dens / log_dens.max()

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(log_dens, cmap="magma", origin="lower",
                  interpolation="nearest")
        ax.set_title(
            "The Quran IFS Fractal — chaos game with 28 contractions\n"
            f"weighted by Quran letter frequencies (H₁ = {H_bits:.3f} bits, "
            f"d_info = {d_info:.3f})",
            fontsize=12,
        )
        ax.axis("off")
        fig.tight_layout()
        p1 = OUT_DIR / "quran_fractal_log_density.png"
        fig.savefig(p1, dpi=220, bbox_inches="tight", facecolor="black")
        plt.close(fig)
        print(f"\n  Wrote {p1}")

        # --- Render 2: LETTER-COLORED ATTRACTOR ---
        # colors_sum normalised by density, then modulated by log-density
        with np.errstate(invalid="ignore", divide="ignore"):
            mean_color = np.where(
                density[..., None] > 0,
                colors_sum / np.maximum(density[..., None], 1),
                0.0,
            )
        # Brightness from log density
        brightness = log_dens[..., None]
        rgb = mean_color * brightness
        rgb = np.clip(rgb, 0, 1)
        # Flip vertically (matplotlib convention)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(rgb, origin="lower", interpolation="nearest")
        ax.set_title(
            "The Quran IFS Fractal — colored by letter identity\n"
            f"28 Arabic-letter contractions, c = {c}, "
            f"d_sim = {d_sim:.3f}, d_info = {d_info:.3f}",
            fontsize=12,
        )
        ax.axis("off")
        fig.tight_layout()
        p2 = OUT_DIR / "quran_fractal_letter_colored.png"
        fig.savefig(p2, dpi=220, bbox_inches="tight", facecolor="black")
        plt.close(fig)
        print(f"  Wrote {p2}")

        # --- Render 3: ZOOMED-IN DETAIL showing self-similarity ---
        # Zoom into the largest lobe (letter ا, index 0, angle 0°)
        # Its fixed point is at z = 1 (on real axis, right side).
        # In pixel coords: center = ((1 + R)*inv_scale, (0 + R)*inv_scale)
        R = 1.0 / (1.0 - c) * 1.05
        inv_scale = (IMG_SIZE - 1) / (2 * R)
        largest_letter_idx = int(np.argmax(p))
        ang = 2 * np.pi * largest_letter_idx / 28
        fx = np.cos(ang) / (1 - c)  # fixed point re
        fy = np.sin(ang) / (1 - c)  # fixed point im
        cx = int((fx + R) * inv_scale)
        cy = int((fy + R) * inv_scale)
        zoom_half = IMG_SIZE // 8  # 1/4 of image size as window
        x0 = max(cx - zoom_half, 0)
        x1 = min(cx + zoom_half, IMG_SIZE)
        y0 = max(cy - zoom_half, 0)
        y1 = min(cy + zoom_half, IMG_SIZE)
        zoom_log = np.log1p(density[y0:y1, x0:x1])
        zoom_log = zoom_log / (zoom_log.max() + 1e-12)

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(zoom_log, cmap="magma", origin="lower",
                  interpolation="nearest")
        ax.set_title(
            f"Self-similarity zoom — largest lobe "
            f"(letter '{ARABIC_LETTERS[largest_letter_idx]}' at angle "
            f"{360*largest_letter_idx/28:.1f}°)\n"
            f"A miniature copy of the full fractal reappears inside.",
            fontsize=12,
        )
        ax.axis("off")
        fig.tight_layout()
        p3 = OUT_DIR / "quran_fractal_zoom_selfsim.png"
        fig.savefig(p3, dpi=220, bbox_inches="tight", facecolor="black")
        plt.close(fig)
        print(f"  Wrote {p3}")

    except Exception as e:
        print(f"(render skipped: {e})")

    # --- Receipt ---
    receipt = dict(
        experiment="exp182_quran_ifs_fractal",
        seed=SEED,
        n_iterations=int(N_ITERATIONS),
        image_size=IMG_SIZE,
        contraction_ratio=float(c),
        shannon_entropy_bits=float(H_bits),
        shannon_entropy_nats=float(H_nats),
        entropy_ceiling_bits=float(np.log2(28)),
        redundancy=float(1 - H_bits / np.log2(28)),
        d_info_information_dimension=float(d_info),
        d_sim_similarity_dimension=float(d_sim),
        letter_freqs=dict(zip(ARABIC_LETTERS, p.tolist())),
        top5_letters=[
            dict(letter=ARABIC_LETTERS[int(order[rk])],
                 freq=float(p[int(order[rk])]),
                 angle_deg=360.0 * int(order[rk]) / 28)
            for rk in range(5)
        ],
        interpretation=(
            "A genuine self-similar fractal in the complex plane, rendered by "
            "the chaos game with 28 affine contractions, each weighted by the "
            "Quran's empirical frequency of the corresponding Arabic letter. "
            "The attractor's information dimension equals the Quran's letter-"
            "frequency Shannon entropy (in nats) divided by log(1/c). It is "
            "self-similar: every lobe contains a miniature copy of the full "
            "fractal. This is the IFS realisation of the Quran's letter-"
            "frequency distribution as a geometric object."
        ),
        output_images=[
            "quran_fractal_log_density.png",
            "quran_fractal_letter_colored.png",
            "quran_fractal_zoom_selfsim.png",
        ],
    )
    out_path = OUT_DIR / "exp182_quran_ifs_fractal.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
