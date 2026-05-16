import pandas as pd
import os
import io


class ReconciliationService:
    @staticmethod
    def process_files(marketplace_files, shipnity_files, peak_files):
        """
        Reconciles data across Shopee/Lazada ↔ Shipnity ↔ PEAK.
        
        Matching chain:
        Marketplace 'Order ID' → Shipnity 'เลขที่บน Marketplace'
        Shipnity 'เลขที่ออเดอร์' → PEAK 'เลขที่เอกสารอ้างอิง'
        
        Returns: (df_result, financial_summary)
        """

        # ═══════════════════════════════════════
        # 1. Load Marketplace Data (Shopee / Lazada)
        # ═══════════════════════════════════════
        mp_rows = []
        for f in marketplace_files:
            try:
                temp_df = pd.read_excel(f)
                cols = temp_df.columns.tolist()

                if 'หมายเลขคำสั่งซื้อ' in cols:  # Shopee
                    status_col = None
                    for c in ['สถานะคำสั่งซื้อ', 'สถานะการสั่งซื้อ', 'Order Status']:
                        if c in cols:
                            status_col = c
                            break
                    if not status_col:
                        status_col = cols[1]

                    # Find amount column
                    amount_col = None
                    for c in ['จำนวนเงินรวมที่ผู้ซื้อต้องชำระ', 'ราคารวม', 'ยอดรวม', 'ยอดคำสั่งซื้อ']:
                        if c in cols:
                            amount_col = c
                            break

                    for _, row in temp_df.iterrows():
                        mp_rows.append({
                            'mp_order_id': str(row['หมายเลขคำสั่งซื้อ']).strip(),
                            'status_mp': str(row[status_col]).strip(),
                            'platform': 'Shopee',
                            'amount_mp': float(row[amount_col]) if amount_col and pd.notnull(row.get(amount_col)) else 0
                        })

                elif 'orderNumber' in cols:  # Lazada
                    for _, row in temp_df.iterrows():
                        mp_rows.append({
                            'mp_order_id': str(row['orderNumber']).strip(),
                            'status_mp': str(row.get('status', '')).strip(),
                            'platform': 'Lazada',
                            'amount_mp': float(row.get('paidPrice', 0)) if pd.notnull(row.get('paidPrice')) else 0
                        })
            except Exception as e:
                print(f"[RECON] Error reading marketplace file: {e}")

        df_mp = pd.DataFrame(mp_rows)
        if not df_mp.empty:
            df_mp = df_mp.drop_duplicates(subset='mp_order_id', keep='first')
        print(f"[RECON] Marketplace orders loaded: {len(df_mp)}")

        # ═══════════════════════════════════════
        # 2. Load Shipnity Data
        # ═══════════════════════════════════════
        ship_rows = []
        for f in shipnity_files:
            try:
                temp_df = pd.read_excel(f)
                for _, row in temp_df.iterrows():
                    mp_ref = str(row.get('เลขที่บน Marketplace', '')).strip()
                    ship_id = str(row.get('เลขที่ออเดอร์', '')).strip()
                    invoice = str(row.get('เลขที่ใบกำกับภาษี', '')).strip()
                    sales = row.get('ยอดขาย', 0)
                    channel = str(row.get('ช่องทางติดต่อ', '')).strip()

                    try:
                        sales_float = float(sales) if pd.notnull(sales) else 0
                    except (ValueError, TypeError):
                        sales_float = 0

                    ship_rows.append({
                        'mp_order_id': mp_ref if mp_ref and mp_ref != '-' and mp_ref != 'nan' else '',
                        'shipnity_id': ship_id,
                        'shipnity_invoice': invoice,
                        'amount_shipnity': sales_float,
                        'channel': channel
                    })
            except Exception as e:
                print(f"[RECON] Error reading shipnity file: {e}")

        df_ship = pd.DataFrame(ship_rows)
        print(f"[RECON] Shipnity orders loaded: {len(df_ship)}")

        # ═══════════════════════════════════════
        # 3. Load PEAK Data (header at row 5)
        # ═══════════════════════════════════════
        peak_rows = []
        for f in peak_files:
            try:
                raw = pd.read_excel(f, header=None)
                header_idx = 0
                for idx, row in raw.iterrows():
                    row_vals = [str(v) for v in row.values if pd.notnull(v)]
                    if any('เลขที่เอกสารอ้างอิง' in v for v in row_vals):
                        header_idx = idx
                        break

                f.seek(0)
                df_peak_raw = pd.read_excel(f, header=header_idx)
                df_peak_raw = df_peak_raw.dropna(subset=['เลขที่เอกสารอ้างอิง'])

                for _, row in df_peak_raw.iterrows():
                    ref_id = str(row.get('เลขที่เอกสารอ้างอิง', '')).strip()
                    invoice_id = str(row.get('เลขที่ใบกำกับภาษี', '')).strip()
                    status = str(row.get('สถานะ', '')).strip()
                    
                    try:
                        amount = float(row.get('มูลค่ารวมภาษี', 0)) if pd.notnull(row.get('มูลค่ารวมภาษี')) else 0
                    except (ValueError, TypeError):
                        amount = 0
                    
                    try:
                        tax = float(row.get('ภาษีมูลค่าเพิ่ม', 0)) if pd.notnull(row.get('ภาษีมูลค่าเพิ่ม')) else 0
                    except (ValueError, TypeError):
                        tax = 0

                    if ref_id and ref_id != 'nan':
                        peak_rows.append({
                            'shipnity_id': ref_id,
                            'peak_invoice_id': invoice_id,
                            'status_peak': status,
                            'amount_peak': amount,
                            'tax_amount': tax
                        })
            except Exception as e:
                print(f"[RECON] Error reading PEAK file: {e}")
                import traceback
                traceback.print_exc()

        df_peak = pd.DataFrame(peak_rows)
        print(f"[RECON] PEAK invoices loaded: {len(df_peak)}")

        # ═══════════════════════════════════════
        # 4. RECONCILIATION: Chain matching
        # ═══════════════════════════════════════
        if df_mp.empty:
            result = pd.DataFrame()
        elif df_ship.empty:
            result = df_mp.copy()
            result['shipnity_id'] = ''
            result['shipnity_invoice'] = ''
            result['amount_shipnity'] = 0
        else:
            result = pd.merge(
                df_mp,
                df_ship[df_ship['mp_order_id'] != ''],
                on='mp_order_id',
                how='left'
            )

        if not result.empty and not df_peak.empty and 'shipnity_id' in result.columns:
            result = pd.merge(result, df_peak, on='shipnity_id', how='left')
        
        # Orphaned PEAK entries
        if not df_peak.empty and not df_ship.empty:
            all_ship_ids = set(df_ship['shipnity_id'].tolist())
            orphan_peak = df_peak[~df_peak['shipnity_id'].isin(all_ship_ids)].copy()
            if not orphan_peak.empty:
                orphan_peak['mp_order_id'] = ''
                orphan_peak['status_mp'] = ''
                orphan_peak['platform'] = ''
                orphan_peak['shipnity_invoice'] = ''
                orphan_peak['amount_shipnity'] = 0
                orphan_peak['amount_mp'] = 0
                result = pd.concat([result, orphan_peak], ignore_index=True)

        # ═══════════════════════════════════════
        # 5. Identify Issues
        # ═══════════════════════════════════════
        AMOUNT_TOLERANCE = 5.0  # ±5 baht tolerance

        def identify_issue(row):
            issues = []
            status_mp = str(row.get('status_mp', '')).strip().lower()
            
            peak_inv = str(row.get('peak_invoice_id', '')).strip()
            has_peak = bool(peak_inv and peak_inv not in ['', 'nan', 'None'])
            
            ship_id = str(row.get('shipnity_id', '')).strip()
            has_shipnity = bool(ship_id and ship_id not in ['', 'nan', 'None'])
            
            mp_id = str(row.get('mp_order_id', '')).strip()
            has_mp = bool(mp_id and mp_id not in ['', 'nan', 'None'])
            
            status_peak = str(row.get('status_peak', '')).strip()
            amt_peak = float(row.get('amount_peak', 0) or 0)
            amt_ship = float(row.get('amount_shipnity', 0) or 0)

            is_cancelled = status_mp in ['ยกเลิกแล้ว', 'ยกเลิก', 'cancelled', 'canceled', 'คืนเงิน/คืนสินค้า', 'returned']
            
            # Detect PEAK-only entries (shipnity_id is actually a PEAK reference, not a real Shipnity order)
            is_peak_ref = ship_id.upper().startswith(('RT-', 'CNT-', 'IV-', 'TIV-'))
            is_credit_note = ship_id.upper().startswith('CNT-') or amt_peak < 0
            
            # Case 0: Credit Note (ใบลดหนี้) from PEAK
            if is_credit_note:
                issues.append(f"📋 ใบลดหนี้ (Credit Note) ยอด: {amt_peak:,.0f}")
                return " | ".join(issues)

            # Case 1: Cancelled in marketplace but tax invoice still exists in PEAK
            if is_cancelled and has_peak and 'ยกเลิก' not in status_peak.lower():
                issues.append("❌ ยกเลิกในระบบขาย แต่ยังมีใบกำกับภาษีใน PEAK (ต้องยกเลิก/ออกใบลดหนี้)")

            # Case 2: Order in marketplace but not found in Shipnity
            if has_mp and not has_shipnity and not is_cancelled:
                issues.append("⚠️ มีในระบบขาย แต่ไม่พบใน Shipnity")

            # Case 3: In Shipnity but no tax invoice in PEAK (real Shipnity order only)
            if has_shipnity and not is_peak_ref and not has_peak and not is_cancelled:
                issues.append("📢 มีใน Shipnity แต่ยังไม่ออกใบกำกับภาษีใน PEAK")

            # Case 4: PEAK-only entry (no marketplace order, PEAK reference as shipnity_id)
            if not has_mp and is_peak_ref:
                issues.append("🔍 รายการใน PEAK เท่านั้น (ไม่มีต้นทางจาก Marketplace)")

            # Case 5: Has Shipnity ID but no marketplace order (manual Shipnity order)
            if not has_mp and has_shipnity and not is_peak_ref:
                issues.append("📦 รายการ Manual จาก Shipnity (ไม่ผ่าน Marketplace)")

            # Case 6: Amount mismatch between Shipnity and PEAK
            if has_shipnity and not is_peak_ref and has_peak and not is_cancelled:
                if amt_ship > 0 and amt_peak > 0 and abs(amt_ship - amt_peak) > AMOUNT_TOLERANCE:
                    diff = amt_ship - amt_peak
                    issues.append(f"💰 ยอดเงินไม่ตรง (Shipnity: {amt_ship:,.0f} / PEAK: {amt_peak:,.0f} / ต่าง: {diff:+,.0f})")

            return " | ".join(issues) if issues else "✅ ปกติ"

        if not result.empty:
            result['issue'] = result.apply(identify_issue, axis=1)

            # Detect brand from Shipnity ID prefix
            def detect_brand(row):
                sid = str(row.get('shipnity_id', '')).strip().upper()
                if sid.startswith('DUIT'):
                    return 'DUIT'
                elif sid.startswith('TT'):
                    return 'Thumb Toe'
                elif sid.startswith('BT'):
                    return 'Bytuneller'
                return ''
            result['brand'] = result.apply(detect_brand, axis=1)

            # Reorder columns
            desired_cols = ['mp_order_id', 'platform', 'brand', 'status_mp', 'shipnity_id',
                           'shipnity_invoice', 'amount_shipnity',
                           'peak_invoice_id', 'status_peak', 'amount_peak', 'tax_amount', 'issue']
            existing_cols = [c for c in desired_cols if c in result.columns]
            result = result[existing_cols]

        # ═══════════════════════════════════════
        # 6. Financial Summary
        # ═══════════════════════════════════════
        financial = {
            'total_shipnity_sales': 0,
            'total_peak_amount': 0,
            'total_peak_tax': 0,
            'amount_diff': 0,
            'mp_total_orders': len(df_mp),
            'ship_total_orders': len(df_ship),
            'peak_total_invoices': len(df_peak),
            'mp_cancelled': 0,
            'mp_completed': 0
        }

        if not df_ship.empty and 'amount_shipnity' in df_ship.columns:
            financial['total_shipnity_sales'] = float(df_ship['amount_shipnity'].sum())

        if not df_peak.empty:
            if 'amount_peak' in df_peak.columns:
                financial['total_peak_amount'] = float(df_peak['amount_peak'].sum())
            if 'tax_amount' in df_peak.columns:
                financial['total_peak_tax'] = float(df_peak['tax_amount'].sum())

        financial['amount_diff'] = financial['total_shipnity_sales'] - financial['total_peak_amount']

        if not df_mp.empty:
            cancelled_statuses = ['ยกเลิกแล้ว', 'ยกเลิก', 'cancelled', 'canceled', 'returned']
            financial['mp_cancelled'] = int(df_mp[df_mp['status_mp'].str.lower().isin(cancelled_statuses)].shape[0])
            financial['mp_completed'] = int(len(df_mp) - financial['mp_cancelled'])

        issue_count = len(result[result['issue'] != '✅ ปกติ']) if not result.empty else 0
        print(f"[RECON] Final result rows: {len(result)}, Issues: {issue_count}")

        return result, financial

    @staticmethod
    def generate_excel_report(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reconciliation Results')
        output.seek(0)
        return output
