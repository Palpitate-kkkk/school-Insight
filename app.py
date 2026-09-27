import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- 页面基础设置 ----------
st.set_page_config(page_title="浙大 085400 报录比洞察", page_icon="📊", layout="wide")
FONT = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif"

# ---------- 读数据 ----------
df = pd.read_csv("data/schools.csv")
df["year"] = df["year"].astype(int)
df["year_str"] = df["year"].astype(str)   # 年份转成文字，图上才会显示成独立色块

nums = ["applicants", "admitted", "ratio", "max_score", "min_score", "avg_score", "retest_line"]
for c in nums:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# 学院简称：让图上的标签短一些、看得清
SHORT = {
    "信息与电子工程学院": "信电学院",
    "光电科学与工程学院": "光电学院",
    "控制科学与工程学院": "控制学院",
    "生物医学工程与仪器科学学院": "生仪学院",
    "计算机科学与技术学院": "计算机学院",
    "微纳电子学院": "微纳电子学院",
    "国际联合学院（海宁国际校区）": "海宁国际联合",
    "工程师学院": "工程师学院",
    "海洋学院": "海洋学院",
    "航空航天学院": "航空航天学院",
    "软件学院": "软件学院",
}
df["college_short"] = df["college"].map(SHORT).fillna(df["college"])

# ---------- 标题 ----------
st.title("浙江大学 · 085400 电子信息（专硕）报录比洞察")
st.caption("数据来源：浙江大学研究生院历年官方公布 · 覆盖 2020–2024 年")

# ---------- 侧边栏筛选 ----------
years = sorted(df["year"].unique().tolist())
colleges = sorted(df["college_short"].unique().tolist())

# 每个年份固定一个颜色，越近的年份颜色越深
PALETTE = ["#D6E4F0", "#A8C8E8", "#6FA8DC", "#3D85C6", "#1F4E79"]
YEAR_COLORS = {str(y): PALETTE[i % len(PALETTE)] for i, y in enumerate(years)}

with st.sidebar:
    st.header("筛选条件")
    sel_years = st.multiselect("年份", years, default=years)
    sel_colleges = st.multiselect("学院", colleges, default=colleges)
    st.divider()
    st.caption("数据口径：不含非全日制、推免、单独考试、强军计划、退役士兵、少数民族骨干；"
               "录取人数含本校相近专业调剂录取。")

d = df[df["year"].isin(sel_years) & df["college_short"].isin(sel_colleges)]

if d.empty:
    st.warning("当前筛选条件下没有数据，请调整左侧筛选条件。")
    st.stop()

# ---------- 核心指标卡 ----------
ap = int(d["applicants"].sum())
ad = int(d["admitted"].sum())
overall = (ap / ad) if ad else 0      # 报录比 = 报考人数 ÷ 录取人数

c1, c2, c3, c4 = st.columns(4)
c1.metric("学院数", f"{d['college_short'].nunique()} 个")
c2.metric("报考总人次", f"{ap:,}")
c3.metric("录取总人数", f"{ad:,}")
c4.metric("整体报录比", f"{overall:.2f}")

# ---------- 图 1：各学院报录比（横向） ----------
st.subheader("各学院报录比对比")
st.caption("柱子越长 = 报考的人越多、录取名额越少。越深的蓝色代表越近的年份。")

# 按五年平均报录比从高到低排，最卷的放最上面
order = d.groupby("college_short")["ratio"].mean().sort_values(ascending=False).index.tolist()

fig = px.bar(
    d, x="ratio", y="college_short", color="year_str",
    barmode="group", orientation="h",
    category_orders={"college_short": order, "year_str": [str(y) for y in sel_years]},
    color_discrete_map=YEAR_COLORS,
    labels={"ratio": "报录比", "college_short": "", "year_str": "年份"},
    height=max(420, 65 * len(order)),
)
fig.add_vline(x=overall, line_dash="dash", line_color="gray",
              annotation_text=f"所选范围整体 {overall:.2f}", annotation_position="bottom right")
fig.update_layout(font_family=FONT, legend_title_text="",
                  legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
                  margin=dict(l=10, r=10, t=60, b=10))
st.plotly_chart(fig, use_container_width=True)

# ---------- 图 2：报考 vs 录取（横向） ----------
full_years = d.dropna(subset=["applicants", "admitted"])["year"]
if not full_years.empty:
    y_latest = int(full_years.max())
    dd = d[(d["year"] == y_latest) & d["applicants"].notna()].copy()
    long = dd.melt(id_vars=["college_short"], value_vars=["applicants", "admitted"],
                   var_name="类型", value_name="人数")
    long["类型"] = long["类型"].map({"applicants": "报考", "admitted": "录取"})

    st.subheader(f"报考 vs 录取（{y_latest} 年）")
    st.caption("同一年里，大部分人倒在了录取名额之外。")

    fig2 = px.bar(
        long, x="人数", y="college_short", color="类型",
        barmode="group", orientation="h",
        color_discrete_map={"报考": "#4C78A8", "录取": "#54A24B"},
        category_orders={"college_short": order},
        labels={"college_short": ""},
        height=max(420, 65 * len(order)),
    )
    fig2.update_layout(font_family=FONT, legend_title_text="",
                       legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
                       margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("所选年份没有公布报考/录取人数，暂时无法生成这张图。")

# ---------- 分数详情 ----------
with st.expander("📋 分数详情（院线 / 最低分 / 平均分 / 最高分）"):
    cols = ["year", "college_short", "retest_line", "min_score", "avg_score", "max_score"]
    show = d[cols].sort_values(["year", "college_short"]).rename(columns={
        "year": "年份", "college_short": "学院", "retest_line": "院线",
        "min_score": "最低分", "avg_score": "平均分", "max_score": "最高分"})
    st.dataframe(show, use_container_width=True, hide_index=True)

# ---------- 完整明细 ----------
with st.expander("📄 完整数据明细"):
    st.dataframe(d.sort_values(["year", "college_short"]),
                 use_container_width=True, hide_index=True)

# ---------- 页脚 ----------
st.divider()
st.caption("数据来源：浙江大学研究生院官方公布的历年硕士报录比；2020–2021 年经中国教育在线转载。"
           "整理：Palpitate-kkkk")
