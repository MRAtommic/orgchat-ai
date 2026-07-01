# -*- coding: utf-8 -*-
"""ทดสอบ WHT inference logic"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

test_cases = [
    # (vendor_name, tax_id, net_amount, expected_wht)
    ("บริษัท ชิปนิตี้ จำกัด",        "0105560071446", 19900,   "3%"),
    ("บริษัท เอ็น.ซี.ซี. จำกัด",     "0105534007639", 55750,   "3%"),
    ("บริษัท อิมแพ็ค จำกัด",          "0125542006506", 10000,   "3%"),
    ("บริษัท บอกบุญ 888 จำกัด",       "0105565077582", 13976,   "3%"),
    ("Gogoprint (Thailand) Co. Ltd.", "0105558155905", 1225,    "3%"),
    ("SPX Express (Thailand) Co.",    "0105565099047", 106.54,  "0"),   # marketplace
    ("บริษัท ทำถูก จำกัด",            "0105558065078", 14346,   "3%"),
    ("บุคคลทั่วไป",                   "1234567890123", 5000,    "0"),   # ไม่ใช่นิติบุคคล
    ("บริษัท ราคาต่ำ จำกัด",          "0105000000001", 500,     "0"),   # ยอดต่ำกว่า 1000
]

def infer_wht(vendor_name, tax_id, net_amount):
    tax_digits = ''.join(c for c in tax_id if c.isdigit())
    is_company = len(tax_digits) == 13 and tax_digits.startswith('0')
    if not is_company:
        for kw in ['บริษัท', 'บจก', 'หจก', 'จำกัด', ' co.', ' ltd', 'corp', 'มหาชน']:
            if kw.lower() in vendor_name.lower():
                is_company = True
                break

    no_wht = ['shopee', 'lazada', 'spx', 'shippop', 'ชิปป๊อป', 'kerry', 'flash', 'j&t', 'dhl', 'ไปรษณีย์']
    is_marketplace = any(kw in vendor_name.lower() for kw in no_wht)

    if is_company and net_amount >= 1000 and not is_marketplace:
        return "3%"
    return "0"

print(f"{'Vendor':<35} {'Tax ID':<15} {'Amount':>8}  {'Expected':<10} {'Got':<10} {'Pass'}")
print("-" * 90)
all_pass = True
for vendor, tax_id, amount, expected in test_cases:
    result = infer_wht(vendor, tax_id, amount)
    ok = "✅" if result == expected else "❌"
    if result != expected:
        all_pass = False
    print(f"{vendor:<35} {tax_id:<15} {amount:>8,.0f}  {expected:<10} {result:<10} {ok}")

print()
print("✅ ทุก test ผ่าน!" if all_pass else "❌ มีบาง test ไม่ผ่าน")
