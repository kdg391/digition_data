import glob, sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from transformers import pipeline

DATA_DIR = Path("data")
OUT_DIR = Path("data_with_sentiment")
OUT_DIR.mkdir(exist_ok=True)

MODEL_NAME = "sangrimlee/bert-base-multilingual-cased-nsmc"
BATCH_SIZE = 32

sent_pipe = pipeline("text-classification", model=MODEL_NAME, batch_size=BATCH_SIZE)

def annotate_df(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    texts = df["text"].fillna("").tolist()
    for batch_start in tqdm(range(0, len(texts), BATCH_SIZE), ncols=80, leave=False):
        batch = texts[batch_start : batch_start + BATCH_SIZE]
        batch_out = sent_pipe(batch)
        results.extend(batch_out)

    df_out = df.copy()
    df_out["sentiment"] = [r["label"] for r in results]
    df_out = df_out.drop(columns=["like_count"], errors="ignore")
    return df_out

def main():
    csv_files = sorted(glob.glob(str(DATA_DIR / "*.csv")))
    if not csv_files:
        print("data/에 CSV 파일 없음", file=sys.stderr)
        return

    print(f"총 {len(csv_files)}개 파일 처리 시작")
    for fp in csv_files:
        name = Path(fp).name
        print(f" ㄴ {name}")
        df = pd.read_csv(fp, encoding="utf-8-sig")
        df = annotate_df(df)
        out_path = OUT_DIR / name
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n완료 {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
