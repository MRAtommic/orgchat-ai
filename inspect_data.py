import sys, os, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from reconciliation_service import ReconciliationService
base = r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\panha'
mp_files = [open(os.path.join(base, 'ยอดขายช่องทางต่างๆ', f), 'rb') for f in os.listdir(os.path.join(base, 'ยอดขายช่องทางต่างๆ'))]
ship_files = [open(os.path.join(base, 'Data_20-04-2026 (2).xlsx'), 'rb')]
peak_files = [open(os.path.join(base, 'PEAK ภาษี', f), 'rb') for f in os.listdir(os.path.join(base, 'PEAK ภาษี'))]
result, fin = ReconciliationService.process_files(mp_files, ship_files, peak_files)
for f in mp_files + ship_files + peak_files: f.close()

print("=== ISSUE BREAKDOWN (NEW) ===")
for issue, count in result['issue'].value_counts().items():
    print(f"  [{count}] {issue[:120]}")

# Show PEAK-only entries
print("\n=== PEAK-ONLY ENTRIES ===")
peak_only = result[result['issue'].str.contains('PEAK เท่านั้น', na=False)]
for _, r in peak_only.iterrows():
    print(f"  {r['shipnity_id']} | PEAK: {r.get('peak_invoice_id','-')} | Amt: {r.get('amount_peak',0)}")

# Show Credit Notes
print("\n=== CREDIT NOTES ===")
cn = result[result['issue'].str.contains('ใบลดหนี้', na=False)]
for _, r in cn.iterrows():
    print(f"  {r['shipnity_id']} | PEAK: {r.get('peak_invoice_id','-')} | Amt: {r.get('amount_peak',0)}")

# Show Manual Shipnity orders
print("\n=== MANUAL SHIPNITY ===")
manual = result[result['issue'].str.contains('Manual', na=False)]
for _, r in manual.iterrows():
    print(f"  {r['shipnity_id']} | Brand: {r.get('brand','-')} | Amt Ship: {r.get('amount_shipnity',0)} | PEAK: {r.get('amount_peak',0)}")
