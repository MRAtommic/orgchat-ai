import pandas as pd
import os
import io

class ReconciliationService:
    @staticmethod
    def process_files(marketplace_files, shipnity_files, peak_files):
        """
        Reconciles data across multiple platforms.
        marketplace_files: List of BytesIO/File objects from Shopee/Lazada
        shipnity_files: List of BytesIO/File objects from Shipnity
        peak_files: List of BytesIO/File objects from PEAK
        """
        
        # 1. Load Marketplace Data
        df_mp = pd.DataFrame()
        for f in marketplace_files:
            try:
                # Shopee/Lazada exports are usually Excel
                temp_df = pd.read_excel(f)
                
                # Detect Shopee vs Lazada
                cols = temp_df.columns.tolist()
                if 'หมายเลขคำสั่งซื้อ' in cols: # Shopee
                    temp_mp = temp_df[['หมายเลขคำสั่งซื้อ', 'สถานะการสั่งซื้อ']].copy()
                    temp_mp.columns = ['order_id', 'status_mp']
                    temp_mp['platform'] = 'Shopee'
                elif 'orderNumber' in cols: # Lazada
                    temp_mp = temp_df[['orderNumber', 'status']].copy()
                    temp_mp.columns = ['order_id', 'status_mp']
                    temp_mp['platform'] = 'Lazada'
                else:
                    continue
                
                df_mp = pd.concat([df_mp, temp_mp])
            except Exception as e:
                print(f"Error reading marketplace file: {e}")

        # 2. Load Shipnity Data
        df_shipnity = pd.DataFrame()
        for f in shipnity_files:
            try:
                temp_df = pd.read_excel(f)
                # Shipnity uses 'เลขที่บน Marketplace' as the cross-ref ID
                # We also need some status indicator. Based on PDF, they check for 'Cancelled'
                # For now, let's assume 'slip / logs' or 'tags' might have status, 
                # or we just check if it exists in shipnity vs marketplace.
                needed_cols = ['เลขที่บน Marketplace', 'เลขที่ออเดอร์', 'ยอดขาย']
                actual_cols = [c for c in needed_cols if c in temp_df.columns]
                
                temp_ship = temp_df[actual_cols].copy()
                rename_map = {
                    'เลขที่บน Marketplace': 'order_id',
                    'เลขที่ออเดอร์': 'shipnity_id',
                    'ยอดขาย': 'amount_shipnity'
                }
                temp_ship.rename(columns=rename_map, inplace=True)
                df_shipnity = pd.concat([df_shipnity, temp_ship])
            except Exception as e:
                print(f"Error reading shipnity file: {e}")

        # 3. Load Peak Data
        df_peak = pd.DataFrame()
        for f in peak_files:
            try:
                # Peak reports often have headers on row 3 or 4
                # We'll try to find the row with 'เลขที่เอกสารอ้างอิง'
                temp_df = pd.read_excel(f, header=None)
                header_row_idx = 0
                for idx, row in temp_df.iterrows():
                    if 'เลขที่เอกสารอ้างอิง' in row.values:
                        header_row_idx = idx
                        break
                
                # Reload with correct header
                temp_df = pd.read_excel(f, skiprows=header_row_idx)
                
                needed_cols = ['เลขที่เอกสารอ้างอิง', 'เลขที่ใบกำกับภาษี', 'สถานะ', 'มูลค่ารวมภาษี']
                actual_cols = [c for c in needed_cols if c in temp_df.columns]
                
                temp_peak = temp_df[actual_cols].copy()
                rename_map = {
                    'เลขที่เอกสารอ้างอิง': 'order_id',
                    'เลขที่ใบกำกับภาษี': 'peak_invoice_id',
                    'สถานะ': 'status_peak',
                    'มูลค่ารวมภาษี': 'amount_peak'
                }
                temp_peak.rename(columns=rename_map, inplace=True)
                df_peak = pd.concat([df_peak, temp_peak])
            except Exception as e:
                print(f"Error reading peak file: {e}")

        # --- RECONCILIATION LOGIC ---
        
        # Merge all data on Order ID
        # Note: Order ID might be string or int depending on excel, normalize to string
        for df in [df_mp, df_shipnity, df_peak]:
            if not df.empty and 'order_id' in df.columns:
                df['order_id'] = df['order_id'].astype(str).str.strip()

        # Master Merge
        result = pd.merge(df_mp, df_shipnity, on='order_id', how='outer')
        result = pd.merge(result, df_peak, on='order_id', how='outer')

        # Identify issues
        def identify_issue(row):
            issues = []
            
            # Case 1: Cancelled in MP but exists in PEAK
            is_cancelled_mp = str(row['status_mp']).lower() in ['cancelled', 'ยกเลิก', 'คืนเงิน/คืนสินค้า']
            if is_cancelled_mp and pd.notnull(row['peak_invoice_id']) and row['status_peak'] != 'ยกเลิก':
                issues.append("❌ ยกเลิกในระบบขายแต่ยังมีใบกำกับภาษีค้างใน PEAK (ต้องลบ)")

            # Case 2: Exists in MP but missing in Shipnity
            if pd.notnull(row['order_id']) and pd.isnull(row['shipnity_id']) and pd.notnull(row['platform']):
                issues.append("⚠️ ออเดอร์ในระบบขาย แต่ไม่พบข้อมูลใน Shipnity")

            # Case 3: Exists in Shipnity but missing in PEAK
            if pd.notnull(row['shipnity_id']) and pd.isnull(row['peak_invoice_id']) and not is_cancelled_mp:
                 issues.append("📢 มีใน Shipnity แต่ยังไม่ออกใบกำกับภาษีใน PEAK")

            return " | ".join(issues) if issues else "✅ ปกติ"

        if not result.empty:
            result['issue'] = result.apply(identify_issue, axis=1)
        
        return result

    @staticmethod
    def generate_excel_report(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reconciliation Results')
        output.seek(0)
        return output
