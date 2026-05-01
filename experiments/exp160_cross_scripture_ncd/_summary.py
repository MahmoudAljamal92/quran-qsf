import json, sys
sys.stdout.reconfigure(encoding="utf-8")
r = json.load(open(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp160_cross_scripture_ncd\exp160_cross_scripture_ncd.json", encoding="utf-8"))
print("verdict:", r["verdict"])
print()
for p in r["results"]["thematic_pairings"]:
    if p.get("status") == "QURAN_LABEL_NOT_FOUND":
        continue
    descr = p["description"]
    rank = p["best_match_rank_0idx"]
    label = p["best_match_label"]
    print(f"-- {descr}")
    print(f"   best match (rank {rank}): {label}")
    print(f"   top-3:")
    for nbl, ncd in p["top_10_neighbours"][:3]:
        print(f"      {ncd:.4f}  {nbl}")
    print()
qab_null = r["results"]["quran_arabic_bible"]["null"]
print(f"Q-AB null min  mean/std : {qab_null['null_min_mean']:.4f} / {qab_null['null_min_std']:.4f}")
print(f"Q-AB obs  min  mean      : {qab_null['obs_min_mean']:.4f}")
print(f"Q-AB obs  mean NCD       : {r['results']['quran_arabic_bible']['obs_mean_ncd']:.4f}")
print(f"Q-NT     obs  mean NCD   : {r['results']['quran_nt']['obs_mean_ncd']:.4f}")
print(f"Q-Iliad  obs  mean NCD   : {r['results']['quran_iliad']['obs_mean_ncd']:.4f}")
print(f"Q-AB frac rows p<0.05    : {qab_null['frac_rows_p_below_05']:.3f}")
print(f"Q-AB frac rows p<0.01    : {qab_null['frac_rows_p_below_01']:.3f}")
