"""Quick read of exp122 receipt to find F75 label + per-corpus values."""
import json

d = json.load(open('results/experiments/exp122_zipf_equation_hunt/exp122_zipf_equation_hunt.json', encoding='utf-8'))
r = d['results']

for key in ('top_pass', 'top_partial_outlier', 'top_partial_tightness'):
    if key not in r or not r[key]:
        continue
    items = r[key] if isinstance(r[key], list) else [r[key]]
    print(f'=== {key} ({len(items)} entries) ===')
    for cand in items[:5]:
        label = cand.get('label')
        print(f'  label: {label}')
        print(f'    cv_others={cand.get("cv_others"):.4f}  abs_z_quran={cand.get("abs_z_quran"):.4f}  z_quran={cand.get("z_quran"):+.4f}  max_other_abs_z={cand.get("max_other_abs_z"):.4f}')
        for kk in cand:
            if kk in ('label', 'cv_others', 'abs_z_quran', 'z_quran', 'max_other_abs_z', 'classification'):
                continue
            v = cand[kk]
            if isinstance(v, (list, dict)):
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    print(f'    {kk} (first 3 of {len(v)}):')
                    for x in v[:3]:
                        print(f'      {x}')
                else:
                    print(f'    {kk}: {v}')
            else:
                print(f'    {kk}: {v}')
        print()
