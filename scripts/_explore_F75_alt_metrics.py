"""Compute V3.19 would-be CCC + RMSE + nRMSE + null-baseline-improvement on locked LOO predictions.

This script is a SANITY CHECK only — it does not constitute a pre-registration.
Its purpose is to determine whether a metric replacement (CCC for Pearson r) would
actually rehabilitate the V3.19 verdict from PARTIAL+ to STRONG, or whether it
would also fail (in which case we should not pre-register exp155).
"""
import json
import numpy as np

r = json.load(open(
    'results/experiments/exp154_F75_stretched_exp_derivation/exp154_F75_stretched_exp_derivation.json',
    encoding='utf-8'))

emp = r['results']['gap_empirical']
preds = r['results']['mode_L_LOO_primary']['predictions']

corpora = list(emp.keys())
y_emp = np.array([emp[c] for c in corpora])
y_pred = np.array([preds[c]['gap_pred'] for c in corpora])

print('Per-corpus matched data:')
print(f'{"corpus":18s} | {"empirical":>10s} | {"predicted":>10s} | {"residual":>10s}')
for c, e, p in zip(corpora, y_emp, y_pred):
    print(f'{c:18s} | {e:10.4f} | {p:10.4f} | {e-p:>+10.4f}')

print()
n = len(y_emp)
mean_e = y_emp.mean()
mean_p = y_pred.mean()
var_e = y_emp.var(ddof=1)
var_p = y_pred.var(ddof=1)
sd_e = np.sqrt(var_e)
sd_p = np.sqrt(var_p)
cov = np.cov(y_emp, y_pred, ddof=1)[0, 1]

# Pearson correlation (V3.19 reported)
r_pearson = cov / (sd_e * sd_p)

# Lin's CCC = 2 * cov / (var_e + var_p + (mean_e - mean_p)^2)
ccc = 2 * cov / (var_e + var_p + (mean_e - mean_p)**2)

# Bias correction factor (Lin's Cb)
mean_diff = mean_p - mean_e
v = sd_p / sd_e
u = mean_diff / np.sqrt(sd_e * sd_p) if (sd_e > 0 and sd_p > 0) else 0.0
Cb = 2 / (v + 1/v + u**2)

# RMSE & nRMSE
residuals = y_emp - y_pred
rmse = np.sqrt(np.mean(residuals**2))
nrmse_range = rmse / (y_emp.max() - y_emp.min())
nrmse_iqr = rmse / (np.percentile(y_emp, 75) - np.percentile(y_emp, 25))

# Mean abs residual + max abs residual
mae = np.mean(np.abs(residuals))
max_ae = np.max(np.abs(residuals))

# Null model (predict mean) baseline
null_pred = np.full_like(y_emp, mean_e)
null_mae = np.mean(np.abs(y_emp - null_pred))
null_rmse = np.sqrt(np.mean((y_emp - null_pred)**2))
r2 = 1 - np.sum(residuals**2) / np.sum((y_emp - mean_e)**2)

print(f'n_corpora              = {n}')
print(f'mean_empirical         = {mean_e:.4f}')
print(f'mean_predicted         = {mean_p:.4f}')
print(f'sd_empirical           = {sd_e:.4f}')
print(f'sd_predicted           = {sd_p:.4f}')
print(f'sd_pred / sd_emp ratio = {sd_p/sd_e:.4f}  (fit-tightness indicator: <1 = predictions too tight)')
print(f'mean diff              = {mean_diff:+.4f}')
print()
print(f'Pearson r              = {r_pearson:.4f}  (V3.19 A3 reported as 0.7475, threshold 0.85, FAIL)')
print(f'Lin CCC                = {ccc:.4f}  (Lin-McBride: <0.65 Poor; 0.65-0.80 Mod; 0.80-0.90 Subst; >=0.90 Strong)')
print(f'Bias correction Cb     = {Cb:.4f}  (=1 if no bias)')
print(f'rho * Cb               = {r_pearson * Cb:.4f}  (CCC = rho * Cb decomposition check)')
print()
print(f'RMSE                   = {rmse:.4f} bits')
print(f'nRMSE_range            = {nrmse_range:.4f}  (RMSE / data range)')
print(f'nRMSE_IQR              = {nrmse_iqr:.4f}  (RMSE / IQR)')
print(f'MAE                    = {mae:.4f} bits  (V3.19 A2 = 0.0982, ceiling 0.20, PASS)')
print(f'Max abs error          = {max_ae:.4f} bits  (V3.19 A5 ceiling 0.43, PASS)')
print()
print(f'NULL model baseline (predict empirical mean for every corpus):')
print(f'  null MAE  = {null_mae:.4f}  (model MAE / null MAE = {mae/null_mae:.4f}; <1 = better than null)')
print(f'  null RMSE = {null_rmse:.4f}  (model RMSE / null RMSE = {rmse/null_rmse:.4f})')
print(f'  R^2 (predictive)     = {r2:.4f}  (1.0 = perfect; 0 = no better than null; <0 = worse)')
print()
print('=== VERDICT BANDS ===')
print()
print(f'A3-CCC at 0.90 (Strong) ........ ' + ('PASS' if ccc >= 0.90 else 'FAIL'))
print(f'A3-CCC at 0.80 (Substantial) ... ' + ('PASS' if ccc >= 0.80 else 'FAIL'))
print(f'A3-CCC at 0.65 (Moderate) ...... ' + ('PASS' if ccc >= 0.65 else 'FAIL'))
print(f'A6-RMSE at 0.15 b .............. ' + ('PASS' if rmse <= 0.15 else 'FAIL'))
print(f'A6-RMSE at 0.20 b .............. ' + ('PASS' if rmse <= 0.20 else 'FAIL'))
print(f'A7-R^2 at 0.50 ................. ' + ('PASS' if r2 >= 0.50 else 'FAIL'))
print(f'A7-R^2 at 0.30 ................. ' + ('PASS' if r2 >= 0.30 else 'FAIL'))
print(f'A8-(model/null MAE) at 0.70 .... ' + ('PASS' if mae/null_mae <= 0.70 else 'FAIL'))
print(f'A8-(model/null MAE) at 0.85 .... ' + ('PASS' if mae/null_mae <= 0.85 else 'FAIL'))
