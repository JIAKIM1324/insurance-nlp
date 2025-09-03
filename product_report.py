import re, regex
import pandas as pd
from rapidfuzz import fuzz
from tabulate import tabulate

NOISE_PATTERNS = [
    r"\(무배당\)|무배당", r"\(유배당\)|유배당",
    r"\(갱신형\)|갱신형", r"\(비갱신형\)|비갱신형",
    r"\bNEW\b|\bThe\b|\bPrime\b|\bPlus\b",
    r"특약", r"표준형", r"실속형", r"종합", r"플러스", r"라이트",
    r"무배당형|유배당형", r"II|III|IV|V", r"\d{2,4}형", r"\d{4}.\d{1,2}",
    r"[【】\[\]{}<>]", r"[-_/·|ㆍ]", r"\s+"
]

RE_KOREAN_EN = regex.compile(r"[^\p{Hangul}\p{Latin}\p{Nd}\s]")

def normalize_name(name: str) -> str:
    s = name.strip()
    s = RE_KOREAN_EN.sub(" ", s)
    for p in NOISE_PATTERNS:
        s = re.sub(p, " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def load_lexicon(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["keywords"] = df["keywords"].astype(str).apply(lambda x: [k.strip() for k in x.split(",") if k.strip()])
    return df

def match_coverages(product_name: str, lexicon_df: pd.DataFrame):
    name = normalize_name(product_name)
    name_lower = name.lower()

    results = []
    for _, row in lexicon_df.iterrows():
        ctype = row["coverage_type"]
        label = row["label"]
        kws = row["keywords"]

        hard_hits = sum(1 for kw in kws if kw.lower() in name_lower)
        hard_score = hard_hits * 40

        fuzz_scores = [fuzz.partial_ratio(kw.lower(), name_lower) for kw in kws]
        fuzz_score = max(fuzz_scores) if fuzz_scores else 0
        fuzz_weighted = int(fuzz_score * 0.6)

        score = min(100, hard_score + fuzz_weighted)

        if score >= 35:
            results.append({
                "coverage_type": ctype,
                "label": label,
                "score": score,
                "why": f"키워드:{hard_hits}, 퍼지:{fuzz_score}"
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    deduped = []
    seen = set()
    for r in results:
        if r["coverage_type"] not in seen:
            seen.add(r["coverage_type"])
            deduped.append(r)
    return deduped

def build_report(product_name: str, lexicon_df: pd.DataFrame):
    matches = match_coverages(product_name, lexicon_df)
    rows = []
    for m in matches:
        conf = "높음" if m["score"]>=80 else ("중간" if m["score"]>=55 else "낮음")
        desc = lexicon_df.loc[lexicon_df["coverage_type"]==m["coverage_type"], "desc"].values[0]
        rows.append([m["label"], m["coverage_type"], m["score"], conf, m["why"], desc])

    print("\n[입력 상품명]", product_name)
    print("[정규화된 이름]", normalize_name(product_name))
    if rows:
        print(tabulate(rows, headers=["라벨","코드","점수","신뢰도","근거","설명"], tablefmt="github"))
    else:
        print("- 매칭된 보장 항목 없음")
