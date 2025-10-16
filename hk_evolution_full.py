# -*- coding: utf-8 -*-
"""
hk_evolution_full.py
最終優化版：大規模整併多格式名單，來源可追溯（檔名/工作表/國家），
安全字串化、記憶體友善，並輸出清晰彙總與分類。

依賴：
  pip install -U pandas openpyxl xlrd
  pip install pyexcel-xls pyexcel-io
  （可選）pip install colorama tqdm

執行：
  python hk_evolution_full.py [資料夾路徑]

輸出：
  ./output/integrated_master.csv
  ./output/hk_in_au.csv / ./output/uncertain.csv / ./output/not_hk.csv
  ./output/email_domain_stats.csv / ./output/surname_stats.csv
  ./output/label_counts.csv / ./output/country_label_pivot.csv
  動態特徵庫：dynamic_*.txt 會在工作目錄維護/增補

備註：
- 以串流寫檔避免一次性併巨大 DataFrame 的記憶體炸裂
- .xls 優先嘗試 pandas+xlrd，不行自動改用 pyexcel-xls
- 欄名先轉字串→正規化對齊到 name/email/phone/address，再做評分
"""

import os, re, sys, glob, math, warnings
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd

# 可選套件
try:
    from tqdm import tqdm
except Exception:
    tqdm = None

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:
    class _Dummy: 
        RESET_ALL = ""
    class _C:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    Fore = _C()
    Style = _Dummy()

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------
# 可調參數
# ---------------------------
CHUNK_SIZE_CSV = 100_000       # CSV 分塊大小
MAX_REASONABLE_COLUMNS = 2000   # 拒收過寬表格（疑似解析錯誤）
OUT_DIR = Path("./output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CSV = OUT_DIR / "integrated_master.csv"
HK_IN_AU_CSV = OUT_DIR / "hk_in_au.csv"
UNCERTAIN_CSV = OUT_DIR / "uncertain.csv"
NOT_HK_CSV = OUT_DIR / "not_hk.csv"

SURNAME_STATS_CSV = OUT_DIR / "surname_stats.csv"
DOMAIN_STATS_CSV = OUT_DIR / "email_domain_stats.csv"
LABEL_COUNTS_CSV = OUT_DIR / "label_counts.csv"
COUNTRY_LABEL_PIVOT_CSV = OUT_DIR / "country_label_pivot.csv"

# 必要欄位標準名
NEEDED_COLS = ["name", "email", "phone", "address"]

# 欄位映射（常見變體 -> 標準名）
COL_MAPS = {
    # name
    "name": "name", "姓名": "name", "full name": "name", "first name": "name", "last name": "name",
    "contact name": "name", "person": "name", "user": "name", "客户": "name", "名稱": "name",
    # email
    "email": "email", "e-mail": "email", "mail": "email", "郵箱": "email", "邮箱": "email",
    "電子郵件": "email", "電子郵箱": "email",
    # phone
    "phone": "phone", "tel": "phone", "telephone": "phone", "mobile": "phone", "cell": "phone",
    "cellphone": "phone", "手機": "phone", "手机号": "phone", "電話": "phone",
    # address
    "address": "address", "addr": "address", "住址": "address", "地址": "address", "街道": "address",
    "location": "address"
}

# ---------------------------
# 基礎特徵庫（可被動態 list 疊加）
# ---------------------------
base_hk_surnames = [
    "chan","cheung","wong","lee","ho","ng","yuen","chiu","lam","kwok","leung","mak",
    "chu","tsang","chow","au","fung","kwan","ip","lo","man","tam","to","wan","yu","yip",
    "lau","poon","pang","hui","cheng","shum","shek","ngai","lok","ko","law"
]
base_cantonese_spellings = [
    "cheung","chow","tsang","chu","yuen","kwok","wai","ho","man","poon","ng"
]
base_hk_domains = [
    "hku.hk","cuhk.edu.hk","hkbu.edu.hk","polyu.edu.hk",
    "cityu.edu.hk","ln.edu.hk","eduhk.hk","ust.hk",
    "netvigator.com","yahoo.com.hk","hotmail.com.hk"
]
base_hk_suburbs = [
    "chatswood","hurstville","eastwood","burwood",
    "box hill","glen waverley","doncaster","rhodes"
]
base_hk_phones = ["+852","852"]

# ---------------------------
# 工具：顏色 log
# ---------------------------
def info(msg): print(Fore.CYAN + msg + Style.RESET_ALL)
def good(msg): print(Fore.GREEN + "✅ " + msg + Style.RESET_ALL)
def warn(msg): print(Fore.YELLOW + "⚠️ " + msg + Style.RESET_ALL)
def bad(msg):  print(Fore.RED + "❌ " + msg + Style.RESET_ALL)

# ---------------------------
# 檔名推測國別（可自行擴充）
# ---------------------------
COUNTRY_MAP = {
    # 英文縮寫
    "AU": "AU", "AUS": "AU", "Australia": "AU",
    "UK": "UK", "GB": "UK", "GBR": "UK",
    "CA": "CA", "CAN": "CA", "Canada": "CA",
    "DE": "DE", "GER": "DE", "Germany": "DE",
    "IT": "IT", "ITA": "IT", "Italy": "IT",
    "FR": "FR", "FRA": "FR", "France": "FR",
    "US": "US", "USA": "US",
    "PL": "PL", "POL": "PL",
    # 常見中文（模糊匹配）
    "澳": "AU", "英": "UK", "德": "DE", "義大利": "IT", "意大利": "IT", "法": "FR", "加": "CA", "美": "US",
}

def guess_country_code_from_filename(path: str) -> str:
    name = Path(path).name
    stem = Path(path).stem
    tokens = re.split(r"[^\w\u4e00-\u9fff]+", stem)
    candidates = []
    for t in tokens:
        if not t: 
            continue
        t_up = t.upper()
        t_cn = t
        for k, v in COUNTRY_MAP.items():
            if len(k) <= 3:  # 英文短碼
                if t_up == k or k in t_up:
                    candidates.append(v)
            else:  # 中文詞
                if k in t_cn:
                    candidates.append(v)
    if not candidates:
        # 網域線索
        if ".com.au" in name.lower() or name.lower().endswith("_au"):
            return "AU"
    return candidates[0] if candidates else ""

# ---------------------------
# 動態特徵庫
# ---------------------------
def load_dynamic_list(file, base_list):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            dynamic = [x.strip().lower() for x in f if x.strip()]
        return list(dict.fromkeys(base_list + dynamic))  # 去重保序
    return base_list

def save_new_candidates(counter: Counter, file: str, threshold: int, existing: set):
    new_items = [it for it, c in counter.items() if c >= threshold and it and it not in existing]
    if new_items:
        with open(file, "a", encoding="utf-8") as f:
            for it in new_items:
                f.write(it + "\n")
        good(f"✨ 新增 {len(new_items)} 項到 {file}")

# ---------------------------
# 欄位正規化
# ---------------------------
def to_str_series(s: pd.Series) -> pd.Series:
    # 安全字串化：NaN → "", 其他 → str
    return s.map(lambda x: "" if pd.isna(x) else (str(x).strip()))

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # 欄名一律轉字串，避免 'int' 沒有 strip()
    df.columns = [str(c) for c in df.columns]

    if df.shape[1] > MAX_REASONABLE_COLUMNS:
        df.attrs["_too_wide"] = True
        return df

    rename = {}
    for c in df.columns:
        c_norm = str(c).strip().lower()
        rename[c] = COL_MAPS.get(c_norm, c_norm)
    df = df.rename(columns=rename)

    # 缺的補齊
    for col in NEEDED_COLS:
        if col not in df.columns:
            df[col] = ""

    # 只保留必要欄位 + 其餘（維持原順序）
    ordered = NEEDED_COLS + [c for c in df.columns if c not in NEEDED_COLS]
    df = df[ordered]

    # 必要欄位強制字串化
    for col in NEEDED_COLS:
        df[col] = to_str_series(df[col])

    return df

# ---------------------------
# 各格式讀取（串流/yield DataFrame）
# ---------------------------
def iter_from_csv(file: str):
    total_rows = None
    # 嘗試估行數（不保證準確，只為進度條）
    try:
        with open(file, "rb") as f:
            total_rows = sum(1 for _ in f)
    except Exception:
        pass

    encodings_try = ["utf-8", "utf-8-sig", "latin-1"]
    for enc in encodings_try:
        try:
            it = pd.read_csv(
                file,
                dtype=str,
                on_bad_lines="skip",
                low_memory=False,
                chunksize=CHUNK_SIZE_CSV,
                encoding=enc
            )
            iterator = it
            break
        except Exception as e:
            warn(f"{file} 以 {enc} 讀取失敗：{e}")
            iterator = None
    if iterator is None:
        bad(f"{file} CSV 讀取失敗，跳過")
        return

    iterable = iterator
    if tqdm:
        iterable = tqdm(iterator, desc=f"📥 {Path(file).name}", unit="chunk")

    for chunk in iterable:
        if chunk is None or chunk.empty:
            continue
        chunk = chunk.fillna("")
        chunk = normalize_columns(chunk)
        if chunk.attrs.get("_too_wide"):
            bad(f"{file} 欄位數異常（>{MAX_REASONABLE_COLUMNS}），跳過")
            continue
        yield chunk

def iter_from_xlsx(file: str):
    try:
        xls = pd.ExcelFile(file, engine="openpyxl")
    except Exception as e:
        bad(f"{file} 讀 .xlsx 失敗：{e}")
        return

    sheets = xls.sheet_names
    iterable = sheets
    if tqdm:
        iterable = tqdm(sheets, desc=f"📗 {Path(file).name}", unit="sheet")

    for sh in iterable:
        try:
            df = pd.read_excel(file, sheet_name=sh, dtype=str, engine="openpyxl")
            if df is None or df.empty:
                continue
            df = df.fillna("")
            df = normalize_columns(df)
            if df.attrs.get("_too_wide"):
                bad(f"{file}::{sh} 欄位數異常（>{MAX_REASONABLE_COLUMNS}），跳過")
                continue
            df["sheet_name"] = sh
            yield df
        except Exception as e:
            bad(f"{file}::'{sh}' 讀取失敗：{e}")

def read_xls_via_pyexcel(file: str):
    try:
        from pyexcel_xls import get_data
    except Exception as e:
        bad(f"{file} 需要套件 pyexcel-xls：請先 `pip install pyexcel-xls pyexcel-io`；錯誤：{e}")
        return []

    try:
        data = get_data(file)  # dict: sheet_name -> rows (list[list])
    except Exception as e:
        bad(f"{file} 使用 pyexcel-xls 解析失敗：{e}")
        return []

    frames = []
    for sh, rows in data.items():
        if not rows:
            continue
        header = rows[0]
        # 若首列非字串欄名，生成通用欄名
        if any(isinstance(x, str) and x.strip() for x in header):
            cols = [str(x).strip() if x is not None else f"col{i}" for i, x in enumerate(header)]
            body = rows[1:]
        else:
            cols = [f"col{i}" for i in range(len(header))]
            body = rows
        df = pd.DataFrame(body, columns=cols)
        df = df.fillna("")
        df = normalize_columns(df)
        if df.attrs.get("_too_wide"):
            bad(f"{file}::{sh} 欄位數異常（>{MAX_REASONABLE_COLUMNS}），跳過")
            continue
        df["sheet_name"] = sh
        frames.append(df)
    return frames

def iter_from_xls(file: str):
    # 優先試 xlrd
    try:
        df = pd.read_excel(file, dtype=str, engine="xlrd")
        df = df.fillna("")
        df = normalize_columns(df)
        if not df.empty:
            df["sheet_name"] = ""
            yield df
            return
    except Exception as e1:
        warn(f"{file} xlrd 讀 .xls 失敗：{e1}；改用 pyexcel-xls")

    # fallback pyexcel-xls
    frames = read_xls_via_pyexcel(file)
    for df in frames:
        yield df

def iter_frames_from_file(file: str):
    file_l = file.lower()
    if file_l.endswith(".csv"):
        yield from iter_from_csv(file)
    elif file_l.endswith(".xlsx"):
        yield from iter_from_xlsx(file)
    elif file_l.endswith(".xls"):
        yield from iter_from_xls(file)
    elif file_l.endswith(".txt"):
        # 嘗試 tab/逗號
        for sep in ["\t", ",", ";", "|"]:
            try:
                it = pd.read_csv(file, sep=sep, dtype=str, on_bad_lines="skip", encoding="utf-8", low_memory=False)
                if it is None or it.empty:
                    continue
                it = it.fillna("")
                it = normalize_columns(it)
                if it.attrs.get("_too_wide"):
                    bad(f"{file} 欄位數異常（>{MAX_REASONABLE_COLUMNS}），跳過")
                    continue
                yield it
                break
            except Exception:
                continue
    else:
        warn(f"{file} 未支援格式，跳過")

# ---------------------------
# 評分（向量化 + 安全字串）
# ---------------------------
def build_patterns(hk_surnames, cantonese_spellings, hk_domains, hk_suburbs):
    if hk_surnames:
        pat_surname = r"\b(?:%s)\b" % "|".join(re.escape(x) for x in hk_surnames)
    else:
        pat_surname = ""
    if cantonese_spellings:
        pat_canton = r"(?:%s)" % "|".join(re.escape(x) for x in cantonese_spellings)
    else:
        pat_canton = ""
    if hk_domains:
        pat_domains = r"(?:%s)" % "|".join(re.escape(x) for x in hk_domains)
    else:
        pat_domains = ""
    if hk_suburbs:
        pat_suburbs = r"(?:%s)" % "|".join(re.escape(x) for x in hk_suburbs)
    else:
        pat_suburbs = ""
    return pat_surname, pat_canton, pat_domains, pat_suburbs

def score_block(df: pd.DataFrame,
                hk_surnames, cantonese_spellings, hk_domains, hk_suburbs, hk_phones):
    name_lc   = df["name"].astype(str).str.lower()
    email_lc  = df["email"].astype(str).str.lower()
    phone_txt = df["phone"].astype(str).str.strip()
    addr_lc   = df["address"].astype(str).str.lower()

    pat_surname, pat_canton, pat_domains, pat_suburbs = build_patterns(
        hk_surnames, cantonese_spellings, hk_domains, hk_suburbs
    )

    # 各特徵布林
    b_hk_surname   = name_lc.str.contains(pat_surname, regex=True, na=False) if pat_surname else pd.Series([False]*len(df))
    b_canton_name  = name_lc.str.contains(pat_canton, regex=True, na=False)  if pat_canton else pd.Series([False]*len(df))
    b_cjk_name     = df["name"].astype(str).str.contains(r"[\u4e00-\u9fff]", regex=True, na=False)

    b_email_domain = (
        email_lc.str.endswith(".hk", na=False) |
        (email_lc.str.contains(pat_domains, regex=True, na=False) if pat_domains else False)
    )
    b_canton_email = email_lc.str.contains(pat_canton, regex=True, na=False) if pat_canton else pd.Series([False]*len(df))

    b_hk_phone_pref = pd.Series([False]*len(df))
    if hk_phones:
        b_hk_phone_pref = phone_txt.apply(lambda x: any(x.startswith(ph) for ph in hk_phones))

    # 香港手機段（基於你原先規則：4開頭+8位）
    b_hk_mobile = phone_txt.str.match(r"^4\d{7}$", na=False)

    b_addr_suburb = addr_lc.str.contains(pat_suburbs, regex=True, na=False) if pat_suburbs else pd.Series([False]*len(df))

    # 各特徵權重
    score = (
        b_hk_surname.astype(int)   * 40 +
        b_canton_name.astype(int)  * 20 +
        b_cjk_name.astype(int)     * 20 +
        b_email_domain.astype(int) * 40 +
        b_canton_email.astype(int) * 15 +
        b_hk_phone_pref.astype(int)* 50 +
        b_hk_mobile.astype(int)    * 20 +
        b_addr_suburb.astype(int)  * 30
    )

    # 標籤
    def classify(s):
        if s >= 80:
            return "HK_in_AU"
        elif s >= 45:
            return "Uncertain"
        else:
            return "Not_HK"
    label = score.map(classify)

    # 理由（避免 ufunc 字串相加錯誤，用逐列 join）
    reasons_cols = {
        "香港常見姓氏": b_hk_surname,
        "粵語拼音（姓名）": b_canton_name,
        "中文姓名": b_cjk_name,
        "香港信箱/教育域": b_email_domain,
        "Email 粵語拼音": b_canton_email,
        "香港電話前綴": b_hk_phone_pref,
        "香港手機號段": b_hk_mobile,
        "澳洲港人常住區": b_addr_suburb,
    }
    # 先建一個 DataFrame 只放字串片段或空字串
    _reasons_df = pd.DataFrame({k: pd.Series([""]*len(df), dtype=object) for k in reasons_cols})
    for k, mask in reasons_cols.items():
        _reasons_df.loc[mask, k] = k

    reasons = _reasons_df.apply(lambda row: "; ".join([x for x in row if x]), axis=1)

    return score, label, reasons

# ---------------------------
# 串流寫檔（避免一次性併表）
# ---------------------------
def append_csv(path: Path, df: pd.DataFrame):
    header = not path.exists()
    df.to_csv(path, index=False, encoding="utf-8-sig", mode="a", header=header)

# ---------------------------
# 主流程
# ---------------------------
def process_all(base_dir: str):
    # 動態特徵庫載入
    hk_surnames = load_dynamic_list("dynamic_surnames.txt", base_hk_surnames)
    cantonese_spellings = load_dynamic_list("dynamic_spellings.txt", base_cantonese_spellings)
    hk_domains = load_dynamic_list("dynamic_domains.txt", base_hk_domains)
    hk_suburbs = load_dynamic_list("dynamic_suburbs.txt", base_hk_suburbs)
    hk_phones = load_dynamic_list("dynamic_phones.txt", base_hk_phones)

    info("🔧 特徵庫：")
    print(f"  姓氏 {len(hk_surnames)} / 粵語拼音 {len(cantonese_spellings)} / 域名 {len(hk_domains)} / 澳洲地區 {len(hk_suburbs)} / 電話前綴 {len(hk_phones)}")

    # 目標檔案
    exts = ("*.csv", "*.xlsx", "*.xls", "*.txt")
    files = []
    for ext in exts:
        files.extend(glob.glob(str(Path(base_dir) / "**" / ext), recursive=True))
    if not files:
        warn("沒有找到任何資料檔")
        return

    info(f"📂 發現 {len(files)} 個檔案")

    # 統計器（串流累計）
    label_counts = Counter()
    country_label = Counter()
    surname_counter = Counter()
    domain_counter = Counter()

    total_rows_in = 0

    # 移除舊輸出
    for p in [MASTER_CSV, HK_IN_AU_CSV, UNCERTAIN_CSV, NOT_HK_CSV,
              SURNAME_STATS_CSV, DOMAIN_STATS_CSV, LABEL_COUNTS_CSV, COUNTRY_LABEL_PIVOT_CSV]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    # 主迭代
    iterable = files
    if tqdm:
        iterable = tqdm(files, desc="🧾 Files", unit="file")

    for file in iterable:
        country_code = guess_country_code_from_filename(file)

        try:
            frame_iter = iter_frames_from_file(file)
            any_yield = False
            for df in frame_iter:
                any_yield = True
                rows_before = len(df)

                # 增補追溯欄位
                if "sheet_name" not in df.columns:
                    df["sheet_name"] = ""
                df["source_file"] = str(Path(file).as_posix())
                df["country_code"] = country_code

                # 評分 + 標籤 + 理由
                score, label, reasons = score_block(
                    df, hk_surnames, cantonese_spellings, hk_domains, hk_suburbs, hk_phones
                )
                df["score"] = score
                df["label"] = label
                df["reasons"] = reasons

                # 累計統計（避免大記憶體）
                total_rows_in += rows_before
                label_counts.update(label.tolist())
                if country_code:
                    for lb in label.tolist():
                        country_label[(country_code, lb)] += 1

                # 姓氏與網域統計（字串安全）
                first_surnames = df["name"].map(
                    lambda x: (x.strip().split()[0].lower() if isinstance(x, str) and x.strip() else "")
                )
                domains = df["email"].map(
                    lambda x: (x.split("@")[-1].strip().lower() if isinstance(x, str) and "@" in x else "")
                )
                surname_counter.update([s for s in first_surnames if s])
                domain_counter.update([d for d in domains if d])

                # 串流輸出：總表 & 三分類
                append_csv(MASTER_CSV, df[[
                    "name","email","phone","address",
                    "score","label","reasons","country_code","source_file","sheet_name"
                ]])

                append_csv(HK_IN_AU_CSV, df[df["label"]=="HK_in_AU"][[
                    "name","email","phone","address",
                    "score","reasons","country_code","source_file","sheet_name"
                ]])

                append_csv(UNCERTAIN_CSV, df[df["label"]=="Uncertain"][[
                    "name","email","phone","address",
                    "score","reasons","country_code","source_file","sheet_name"
                ]])

                append_csv(NOT_HK_CSV, df[df["label"]=="Not_HK"][[
                    "name","email","phone","address",
                    "score","reasons","country_code","source_file","sheet_name"
                ]])

            if not any_yield:
                warn(f"{file} 沒有可用資料（或格式不支援）")
        except Exception as e:
            bad(f"{file} 讀取/處理失敗：{e}")

    # ---------------------------
    # 彙總輸出
    # ---------------------------
    info("\n🧮 輸出彙總...")

    # 標籤統計
    pd.DataFrame(
        [{"label": k, "count": v} for k, v in sorted(label_counts.items(), key=lambda x: (-x[1], x[0]))]
    ).to_csv(LABEL_COUNTS_CSV, index=False, encoding="utf-8-sig")

    # 國家 × 標籤
    # 轉成透視表
    country_label_map = defaultdict(dict)
    for (cty, lb), cnt in country_label.items():
        country_label_map[cty][lb] = cnt
    rows = []
    all_labels = sorted({lb for (_, lb) in country_label.keys()})
    for cty, d in sorted(country_label_map.items()):
        row = {"country_code": cty}
        for lb in all_labels:
            row[lb] = d.get(lb, 0)
        row["total"] = sum(d.values())
        rows.append(row)
    if rows:
        pd.DataFrame(rows).to_csv(COUNTRY_LABEL_PIVOT_CSV, index=False, encoding="utf-8-sig")

    # 姓氏 / 網域 統計
    pd.Series(surname_counter).sort_values(ascending=False).to_csv(SURNAME_STATS_CSV, header=["count"], encoding="utf-8-sig")
    pd.Series(domain_counter).sort_values(ascending=False).to_csv(DOMAIN_STATS_CSV, header=["count"], encoding="utf-8-sig")

    good("\n===== 📊 分析報告 =====")
    print(f"📌 總筆數（估）：{total_rows_in}")
    print(f"🟢 高可信香港背景：{label_counts.get('HK_in_AU', 0)}")
    print(f"🟡 不確定：{label_counts.get('Uncertain', 0)}")
    print(f"🔴 非香港背景：{label_counts.get('Not_HK', 0)}")
    print("\n📑 彙總輸出：")
    print(f" - {MASTER_CSV.name}")
    print(f" - {LABEL_COUNTS_CSV.name} / {COUNTRY_LABEL_PIVOT_CSV.name}")
    print(f" - {SURNAME_STATS_CSV.name} / {DOMAIN_STATS_CSV.name}")
    print("📂 分類輸出：hk_in_au.csv / uncertain.csv / not_hk.csv")
    print("🧩 特徵庫：dynamic_surnames.txt / dynamic_domains.txt / dynamic_suburbs.txt / dynamic_phones.txt")

    # ---------------------------
    # 動態特徵庫增補
    # ---------------------------
    info("\n🧠 更新動態特徵庫候選...")
    existing_surnames = set(hk_surnames)
    existing_domains = set(hk_domains)
    save_new_candidates(surname_counter, "dynamic_surnames.txt", threshold=50, existing=existing_surnames)
    save_new_candidates(domain_counter, "dynamic_domains.txt", threshold=50, existing=existing_domains)

# ---------------------------
# 入口
# ---------------------------
if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    base = str(Path(base).resolve())
    info(f"🚀 開始處理：{base}")
    process_all(base)
