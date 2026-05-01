import json, sys
sys.stdout.reconfigure(encoding="utf-8")

p = r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp163_quran_geometric_shape\exp163_quran_geometric_shape.json"
r = json.load(open(p, encoding="utf-8"))
print(f"VERDICT: {r['verdict']}\n")

print("=" * 78)
print("FRAME A -- per-corpus shape descriptors (Quran has n=68)")
print("=" * 78)
descs_full = ["sphericity_log10", "isotropy", "intrinsic_dim_95pct",
              "anisotropy_westin", "linearity_westin", "planarity_westin",
              "symmetry_score", "regularity_NN_CV", "logvol"]
header = ["corpus"] + [d.replace("_westin", "") for d in descs_full]
print(("{:<16}" + "{:>12}" * len(descs_full)).format(*header))
for cn, d in r["frame_A"]["per_corpus_descriptors"].items():
    row = [cn] + [
        f"{d[k]:.3f}" if isinstance(d[k], float) else str(d[k])
        for k in descs_full
    ]
    print(("{:<16}" + "{:>12}" * len(descs_full)).format(*row))

print("\nFRAME A -- Quran p-values vs bootstrap-from-pool null (10000 draws)")
print("(seven frozen descriptors, BHL alpha=0.01 family-wise)")
print("-" * 78)
seven = ["sphericity_log10", "isotropy", "intrinsic_dim_95pct",
         "anisotropy_westin", "linearity_westin", "planarity_westin",
         "symmetry_score"]
for k in seven:
    info = r["frame_A"]["quran_vs_bootstrap_pool_null"][k]
    pv = info["p_two_sided_vs_bootstrap"]
    nm = info["null_median"]
    obs = info["observed"]
    rk = r["frame_A"]["quran_rank_in_8_corpora"][k]
    is_bhl = (k in r["frame_A"]["bhl_survivors_among_7_descriptors"])
    flag = "  <-- BHL_SIG" if is_bhl else ""
    print(f"  {k:<28}  obs={obs:8.4f}  null_med={nm:8.4f}  "
          f"p_two={pv:8.5f}  rank_low={rk['rank_low']}/{rk['out_of']}  "
          f"rank_high={rk['rank_high']}/{rk['out_of']}{flag}")

print("\n" + "=" * 78)
print("FRAME B -- 114-surah trajectory under canonical orderings")
print("=" * 78)
five = ["arc_length", "mean_curvature_rad", "curvature_variance",
        "closure_ratio_0closed_1straight", "smoothness_curvature_var"]
for ord_name in r["frame_B"]["orderings"]:
    print(f"\n[{ord_name}] (5 descriptors, perm null vs 10000 random orderings)")
    pe = r["frame_B"]["per_ordering"][ord_name]
    for k in five:
        info = pe["p_values"][k]
        is_bhl = (f"{ord_name}/{k}" in r["frame_B"]["bhl_survivors"])
        flag = "  <-- BHL_SIG" if is_bhl else ""
        print(f"  {k:<32}  obs={info['observed']:8.3f}  "
              f"null_med={info['null_median']:8.3f}  "
              f"p_two={info['p_two_sided_vs_random_orderings']:8.5f}{flag}")

print("\n" + "=" * 78)
print("FRAME C -- findings polytope (corpus z-vectors in 6D)")
print("=" * 78)
fc = r["frame_C"]
print(f"Names: {fc['names']}")
print(f"Feat: {fc['feat_names']}")
print(f"SVD var explained: {[round(v, 3) for v in fc['svd_var_explained']]}")
print(f"Quran nearest:  {fc['quran_nearest']}")
print(f"Quran farthest: {fc['quran_farthest']}")
print()
import numpy as np
D = np.array(fc["pairwise_z_distances"])
print("Pairwise z-distances:")
header = ["         "] + [f"{n[:8]:>9}" for n in fc["names"]]
print("".join(header))
for i, n in enumerate(fc["names"]):
    row = [f"{n[:8]:<9}"] + [f"{D[i,j]:>9.2f}" for j in range(len(fc["names"]))]
    print("".join(row))

print(f"\nWall-time: {r['wall_time_s']:.1f} s")
