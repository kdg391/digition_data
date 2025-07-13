import re, sys, html
from pathlib import Path

import pandas as pd
from tqdm import tqdm

IN_DIR  = Path("data")
OUT_DIR = Path("edit_data")
OUT_DIR.mkdir(exist_ok=True)

MENTION_PAT = re.compile(r"(?!,|\w)(@(\w+)(\s*))")

def clean_text_row(txt: str) -> str:
    txt = html.unescape(txt)
    txt = MENTION_PAT.sub("", txt)
    return txt.strip()

def process_file(fp: Path):
    df = pd.read_csv(fp, encoding="utf-8-sig")

    df["created_at"] = df["created_at"].astype(str).str.replace(r"\+00:00", "", regex=True)

    df["text"] = df["text"].astype(str).apply(clean_text_row)

    if fp.name.startswith("유심_"):
        df = df[~df["text"].str.contains("유심히", na=False)]

    df.to_csv(OUT_DIR / fp.name, index=False, encoding="utf-8")

def main():
    files = sorted(Path(IN_DIR).glob("*.csv"))
    if not files:
        print("CSV 파일 없음", file=sys.stderr)
        return

    print(f"{len(files)}개 파일 수정 중")
    for fp in tqdm(files, ncols=80):
        process_file(fp)

    print(f"\n완료")

if __name__ == "__main__":
    main()