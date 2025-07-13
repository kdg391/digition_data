import glob, hashlib, sys
from pathlib import Path
from typing import Dict

import pandas as pd
from tqdm import tqdm

from google import genai
from google.genai import types

IN_DIR = Path("data")
OUT_DIR = Path("filtered")
OUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

SYSTEM_PROMPT = (
    "You are a strict tweet content reviewer for a Korean security-incident study. "
    "Classify each tweet as follows:\n"
    "- If it is ANY kind of advertisement, promotion, giveaway, coupon, link farming, "
    "news-article repost (tweet that only shares a news headline or article link with no personal comment), "
    "or obviously automated real-time trend bot content, respond with EXACTLY 'BLOCK'.\n"
    "- Otherwise (genuine personal opinion, discussion, analysis, etc.) respond with EXACTLY 'KEEP'.\n"
    "Use ONLY ONE WORD ('BLOCK' or 'KEEP'). No extra characters."
)

def judge(text: str, cache: Dict[str, str]) -> str:
    h = hashlib.md5(text.encode()).hexdigest()
    if h in cache:
        return cache[h]

    try:
        response = client.models.generate_content(
            contents=[SYSTEM_PROMPT, f"Tweet: ```{text}```"],
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )

        prediction = response.text.strip().upper()
    except Exception as e:
        print(f"Gemini 오류 {e}", file=sys.stderr)
        prediction = "KEEP"

    if prediction not in ("BLOCK", "KEEP"):
        prediction = "KEEP"
    cache[h] = prediction
    return prediction

def clean_file(path: Path):
    df = pd.read_csv(path, encoding="utf-8")
    cache: Dict[str, str] = {}

    keep_mask = []
    print(f"▶ {path.name}")
    for txt in tqdm(df["text"].fillna(""), ncols=80, leave=False):
        keep_mask.append(judge(txt, cache) == "KEEP")

    df_keep = df[keep_mask].reset_index(drop=True)
    out = OUT_DIR / path.name
    df_keep.to_csv(out, index=False, encoding="utf-8")
    print(f"{len(df) - len(df_keep)}행 BLOCK, {len(df_keep)}행 저장\n")

def main():
    csvs = sorted(glob.glob(str(IN_DIR / "*.csv")))
    if not csvs:
        sys.exit("data 폴더에 CSV 없음")
    for fp in csvs:
        clean_file(Path(fp))
    print('완료')

if __name__ == "__main__":
    main()
