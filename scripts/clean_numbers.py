# scripts/clean_numbers.py
import argparse, os, sys, time, json
import pandas as pd
import phonenumbers as pn
from phonenumbers import PhoneNumberType as T
import requests

TYPE_MAP = {
    T.MOBILE: "mobile",
    T.FIXED_LINE: "fixed",
    T.FIXED_LINE_OR_MOBILE: "fixed_or_mobile",
    T.VOIP: "voip",
    T.TOLL_FREE: "toll_free",
    T.PREMIUM_RATE: "premium",
    T.SHARED_COST: "shared",
    T.PERSONAL_NUMBER: "personal",
    T.PAGER: "pager",
    T.UAN: "uan",
    T.UNKNOWN: "unknown",
}

def read_any(path: str) -> pd.DataFrame:
    p = path.lower()
    if p.endswith((".xlsx", ".xls")):
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, dtype=str)

def write_any(df: pd.DataFrame, path: str):
    p = path.lower()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if p.endswith((".xlsx", ".xls")):
        return df.to_excel(path, index=False)
    return df.to_csv(path, index=False)

def best_guess_column(df: pd.DataFrame, col: str | None):
    if col and col in df.columns: 
        return col
    # 嘗試常見欄名
    for k in ["phone","mobile","tel","msisdn","number","号码","手机号","電話","電話號碼"]:
        if k in df.columns: return k
    # 否則選第一欄
    return df.columns[0]

def normalize(s: str | None, default_region: str):
    if not s or str(s).strip()=="":
        return None
    try:
        n = pn.parse(str(s), default_region or None)
        if not pn.is_valid_number(n):
            return None
        e164 = pn.format_number(n, pn.PhoneNumberFormat.E164)
        region = pn.region_code_for_number(n)
        t = pn.number_type(n)
        return {"e164": e164, "region": region, "type": TYPE_MAP.get(t, "unknown")}
    except Exception:
        return None

def hlr_lookup(e164: str, vendor: str, key: str):
    # 可換你使用的供應商；下面是「通用」寫法，以 Telnyx 為例。
    try:
        if vendor == "telnyx":
            url = f"https://api.telnyx.com/v2/number_lookup/{e164}"
            r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=20)
            if r.status_code == 200:
                data = r.json().get("data", {})
                # 不同供應商字段不同，以下做通用萃取
                carrier = (data.get("carrier", {}) or {}).get("name")
                reachable = data.get("portability", {}).get("reachable")  # 有些供應商無此字段
                return {"hlr_carrier": carrier, "hlr_reachable": reachable, "hlr_raw": json.dumps(data)[:2000]}
            return {"hlr_error": f"http {r.status_code} {r.text[:200]}", "hlr_raw": r.text[:1000]}
        # 其它供應商分支可再加：twilio / vonage / neutrino ...
        return {"hlr_error": "unsupported vendor"}
    except Exception as e:
        return {"hlr_error": str(e)[:200]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="輸入 CSV/Excel 路徑")
    ap.add_argument("--out", dest="outfile", required=True, help="輸出 CSV/Excel 路徑")
    ap.add_argument("--col", default=None, help="電話欄名（可不填，自動猜）")
    ap.add_argument("--default-region", default="CN", help="預設區碼（如 CN/TW/ID 等）")
    ap.add_argument("--hlr-vendor", default=None, help="telnyx/twilio/vonage...（可不填）")
    ap.add_argument("--hlr-key", default=os.getenv("HLR_API_KEY",""), help="HLR API 金鑰（或用環境變數 HLR_API_KEY）")
    args = ap.parse_args()

    df = read_any(args.infile)
    col = best_guess_column(df, args.col)

    out_rows = []
    for _, row in df.iterrows():
        raw = str(row.get(col, "")).strip()
        norm = normalize(raw, args.default_region)
        if norm:
            out_rows.append({
                "raw": raw,
                **norm
            })
    if not out_rows:
        write_any(pd.DataFrame([], columns=["raw","e164","region","type"]), args.outfile)
        print("No valid numbers.")
        return

    out_df = pd.DataFrame(out_rows).drop_duplicates(subset=["e164"]).reset_index(drop=True)

    # 可選：HLR 檢測
    if args.hlr_vendor:
        if not args.hlr_key:
            print("HLR vendor specified but no --hlr-key or HLR_API_KEY provided.", file=sys.stderr)
        else:
            results = []
            for e164 in out_df["e164"]:
                r = hlr_lookup(e164, args.hlr_vendor, args.hlr_key)
                results.append(r)
                time.sleep(0.2)  # 禮貌限速
            hlr_df = pd.DataFrame(results)
            out_df = pd.concat([out_df, hlr_df], axis=1)

    write_any(out_df, args.outfile)
    print(f"OK -> {args.outfile}  rows={len(out_df)}")

if __name__ == "__main__":
    main()