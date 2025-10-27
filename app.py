import streamlit as st
import pandas as pd
import plotly.express as px

latestDate="2025-10-21"

st.set_page_config(page_title="ITTF 女子排名 - 丝滑动画版", layout="wide")
st.title(f"🏓 ITTF 女子世界排名（2021–{latestDate}）")
st.markdown("拖动下方滑块或点击 ▶️ 播放，查看排名变化。孙颖莎始终高亮为红色。")


# ==============================
# 加载并预处理数据
# ==============================
@st.cache_data
def load_data():
    files = [f"data/ittf_women_{year}_rankings.csv" for year in range(2021, 2026)]
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["date"] = pd.to_datetime(
                df["date"]
            ).dt.date  # 转为 date 类型（无时分秒）
            dfs.append(df)
        except FileNotFoundError:
            continue
    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["rank"] <= 50]

    # 清洗姓名（统一为 SUN Yingsha）
    combined["clean_name"] = (
        combined["player_name"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()
    )

    # 标记是否为孙颖莎
    combined["is_sun"] = combined["clean_name"] == "SUN Yingsha"

    # 为动画排序（确保每帧按 rank 排）
    combined = combined.sort_values(["date", "rank"])

    return combined


df = load_data()

if df.empty:
    st.error("❌ 未找到数据文件！")
    st.stop()

# ==============================
# 创建动画图表（关键！）
# ==============================
# 设置颜色：孙颖莎红色，其他人浅灰
df["color"] = df["is_sun"].map({True: "SUN Yingsha", False: "Others"})

# fig = px.bar(
#     df,
#     x='rank',
#     y='points',
#     animation_frame='date',          # ⭐ 核心：按日期做动画
#     animation_group='player_name',    # 保持选手身份一致
#     text='points',
#     color='color',
#     color_discrete_map={'SUN Yingsha': 'red', 'Others': 'lightblue'},
#     hover_data={'player_name': True, 'association': True, 'date': False, 'color': False},
#     range_x=[0.5, 50.5],             # 固定 x 轴范围（避免跳动）
#     range_y=[0, df['points'].max() * 1.1],  # 固定 y 轴上限
#     title="女子世界排名动态变化（2021–2025）",
#     labels={'rank': '排名', 'points': '积分'}
# )

# # 优化动画体验
# fig.update_layout(
#     xaxis=dict(tickmode='linear', dtick=5, title='排名'),
#     yaxis_title='积分',
#     showlegend=False,
#     height=600,
#     # 关键：让动画更流畅
#     updatemenus=[dict(
#         type="buttons",
#         showactive=False,
#         buttons=[dict(
#             label="▶️ 播放",
#             method="animate",
#             args=[None, {
#                 "frame": {"duration": 800, "redraw": True},
#                 "fromcurrent": True,
#                 "transition": {"duration": 50, "easing": "cubic-in-out"}
#             }]
#         )]
#     )]
# )


# === 新增：统计孙颖莎世界第一周数 ===
sun_df = df[df['clean_name'] == 'SUN Yingsha']
weeks_as_no1 = sun_df[sun_df['rank'] == 1]['date'].nunique()

st.metric(
    label="🏆 孙颖莎保持女子世界第一的周数",
    value=f"{weeks_as_no1} 周",
    delta=f"截至{latestDate}数据",
    delta_color="off"
)


# 创建动画图表（不加 updatemenus！）
fig = px.bar(
    df,
    x="rank",
    y="points",
    animation_frame="date",
    animation_group="player_name",
    # text='points',
    color="color",
    color_discrete_map={"SUN Yingsha": "red", "Others": "lightblue"},
    hover_data={
        'player_name': True,
        'association': True,
        'points': True,      # ✅ 积分通过 hover 显示
        'date': False
    },
    range_x=[0.5, 50.5],
    range_y=[0, df["points"].max() * 1.1],
    title=f"女子世界排名动态变化（2021–{latestDate}）",
    labels={"rank": "排名", "points": "积分"},
)
# ✅ 确保 hover 显示完整信息
fig.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>协会: %{customdata[1]}<br>积分: %{y:,}<extra></extra>"
)
df['hover_name'] = df['player_name']
df['hover_assoc'] = df['association']
fig = px.bar(
    df,
    x='rank',
    y='points',
    animation_frame='date',
    animation_group='player_name',
    color='color',
    color_discrete_map={'SUN Yingsha': 'red', 'Others': 'lightblue'},
    custom_data=['hover_name', 'hover_assoc'],  # 传入自定义 hover 数据
    range_x=[0.5, 50.5],
    range_y=[0, df['points'].max() * 1.1],
    title=f"女子世界排名动态变化（2021–{latestDate}）",
    labels={'rank': '排名', 'points': '积分'}
)

fig.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>协会: %{customdata[1]}<br>积分: %{y:,}<extra></extra>"
)

# ✅ 关键：通过 layout.update 的 `animation_options` 控制速度
fig.update_layout(
    xaxis=dict(tickmode="linear", dtick=5, title="排名"),
    yaxis_title="积分",
    showlegend=False,
    height=600,
    # ⭐ 删除 updatemenus！让 Plotly 用默认控件（只有一个播放组）
)

# ✅ 设置动画速度（这才是控制快慢的关键！）
fig.layout.updatemenus[0].buttons[0].args[1]["frame"][
    "duration"
] = 100  # 每帧停留 300ms
fig.layout.updatemenus[0].buttons[0].args[1]["transition"][
    "duration"
] = 50  # 帧间过渡 100ms

# 添加孙颖莎标注（Plotly 动画中动态标注较复杂，可省略或用 hover 替代）
# 这里我们依赖颜色高亮 + hover 信息


if weeks_as_no1 > 0:
    with st.expander("📅 查看孙颖莎历次世界第一时间段"):
        no1_dates = sorted(sun_df[sun_df['rank'] == 1]['date'].unique())
        
        # 合并连续日期为时间段
        periods = []
        start = end = no1_dates[0]
        for d in no1_dates[1:]:
            if (d - end).days == 1:  # 连续
                end = d
            else:
                periods.append((start, end))
                start = end = d
        periods.append((start, end))
        
        for i, (s, e) in enumerate(periods, 1):
            if s == e:
                st.write(f"第 {i} 次：{s.strftime('%Y-%m-%d')}")
            else:
                st.write(f"第 {i} 次：{s.strftime('%Y-%m-%d')} 至 {e.strftime('%Y-%m-%d')}")
        st.write(f"**总计：{weeks_as_no1} 周**")



# ==============================
# 显示图表
# ==============================
st.plotly_chart(fig, use_container_width=True)

with st.expander("💡 使用说明"):
    st.markdown(
        """
    - 拖动底部滑块可手动切换时间
    - 点击 **▶️ 播放** 按钮自动播放动画
    - **红色柱子 = 孙颖莎**
    - 悬停查看选手详情
    """
    )
