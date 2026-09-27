import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="目标院校数据洞察", page_icon="📊", layout="wide")

FONT = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif"



def load_data():
    path = Path(__file__).parent / "data" / "schools.csv"
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(str)
    num_cols = ["applicants", "admitted", "ratio",
                "min_score", "avg_score", "max_score", "retest_line"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


df = load_data()

st.title("📊 目标院校数据洞察")
st.caption("浙江大学 · 085400 电子信息（专硕）· 数据来自研究生院官方公布")

with st.sidebar:
    st.header("🎛 筛选条件")
    years = st.multiselect("年份", sorted(df["year"].unique()), default=sorted(df["year"].unique()))
    colleges = st.multiselect("学院", sorted(df["college"].unique()), default=sorted(df["college"].unique()))
    st.divider()
    st.caption("**数据口径**：不含非全日制、推免、单独考试、强军计划、退役士兵、少民骨干；录取人数含本校相近专业调剂录取。")

f = df[df["year"].isin(years) & df["college"].isin(colleges)].copy()

if f.empty:
    st.warning("当前筛选条件下没有数据，请在左侧放宽筛选范围。")
    st.stop()

total_app = f["applicants"].sum()
total_adm = f["admitted"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("学院数", f"{f['college'].nunique()} 个")
c2.metric("报考总人次", f"{int(total_app):,}" if total_app else "—")
c3.metric("录取总人数", f"{int(total_adm):,}" if total_adm else "—")
c4.metric("整体报录比", f"{total_app / total_adm:.2f}" if total_adm else "—")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("各学院报录比对比")
    fig = px.bar(
        f,
        x="college",
        y="ratio",
        color="year",
        barmode="group",
        labels={"ratio": "报录比", "college": "", "year": "年份"},
    )
    fig.update_layout(font=dict(family=FONT), legend_title_text="", margin=dict(t=10, b=80))
    fig.update_xaxes(tickangle=-40)
    st.plotly_chart(fig)

with right:
    valid = f.dropna(subset=["applicants", "admitted"])
    if valid.empty:
        st.subheader("报考 vs 录取")
        st.info("当前数据里缺少「报考人数 / 录取人数」，这张图暂时画不出来。")
    else:
        latest = max(valid["year"].unique())
        st.subheader(f"报考 vs 录取（{latest} 年）")
        fy = valid[valid["year"] == latest]
        m = fy.melt(
            id_vars=["college"],
            value_vars=["applicants", "admitted"],
            var_name="类型",
            value_name="人数",
        )
        m["类型"] = m["类型"].map({"applicants": "报考", "admitted": "录取"})
        fig2 = px.bar(
            m,
            x="college",
            y="人数",
            color="类型",
            barmode="group",
            color_discrete_map={"报考": "#5B8FF9", "录取": "#61DDDA"},
            labels={"college": ""},
        )
        fig2.update_layout(font=dict(family=FONT), legend_title_text="", margin=dict(t=10, b=80))
        fig2.update_xaxes(tickangle=-40)
        st.plotly_chart(fig2)

with st.expander("📈 分数详情（院线 / 最低分 / 平均分 / 最高分）"):
    score_cols = ["college", "year", "retest_line", "min_score", "avg_score", "max_score"]
    st.dataframe(f[score_cols].sort_values(["college", "year"]), hide_index=True)

st.subheader("🧾 数据明细")
detail_cols = [
    "year", "school", "college", "major_code", "major_name",
    "applicants", "admitted", "ratio", "min_score", "avg_score", "source_url",
]
st.dataframe(f[detail_cols], hide_index=True)

st.divider()
st.caption("数据来源：浙江大学研究生院《硕士各专业报录比及平均分》。如有出入，以官方原始文件为准。")
