import pandas as pd
import streamlit as st
from product_report import load_lexicon, build_report, normalize_name, match_coverages

st.set_page_config(page_title="보험명 → 보장 리포트", page_icon="📄")

st.title("보험명 → 보장 리포트 (MVP)")
lex = load_lexicon("coverage_lexicon.csv")

name = st.text_input("보험 상품명을 입력하세요", "무배당 삼성화재 NEW 실손의료비(갱신형)")
if st.button("분석"):
    st.write("입력 상품명:", name)
    st.write("정규화된 이름:", normalize_name(name))

    matches = match_coverages(name, lex)
    if matches:
        df = pd.DataFrame([{
            "라벨": m["label"],
            "코드": m["coverage_type"],
            "점수": m["score"],
            "신뢰도": "높음" if m["score"]>=80 else ("중간" if m["score"]>=55 else "낮음"),
            "근거": m["why"],
            "설명": lex.loc[lex["coverage_type"]==m["coverage_type"], "desc"].values[0]
        } for m in matches])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("매칭된 보장 항목이 없습니다. 키워드 사전을 보강해보세요.")
