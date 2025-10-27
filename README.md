# ITTF 女子世界排名动态可视化

📊 使用 Streamlit + Plotly 实现的 ITTF 女子世界排名动画，支持播放、滑动、高亮孙颖莎排名。

## 功能
- 🏓 排名随时间动态变化
- 🔴 孙颖莎始终红色高亮
- 📅 滑块控制时间
- ⏩ 播放按钮自动播放
- 📈 显示孙颖莎连续世界第一的周数

## 🚀 如何运行

1. 克隆项目：
```bash
git clone https://github.com/abby-stitch/ittf-ranking-visualization.git
cd ittf-ranking-visualization
```

2. 创建并激活 Conda 环境（推荐）：
```bash
conda create -n ittf-env python=3.10
conda activate ittf-env
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行应用：
```bash
streamlit run app.py
```

## 🛠️ 环境要求
- Python 3.11.13 
- 推荐使用 Conda 管理环境
- 依赖包见 requirements.txt

## 📂 文件说明
- **app.py** 主程序：Streamlit 动态排名动画
- **crawl_ittf_html.py** 爬取 ITTF 官网 HTML 排名数据
- **crawl_ittf_pdf.py** 爬取 ITTF PDF 排名文件
- **data/** 按年份存储的每周前五十名排名数据
- **requirements.txt** Python 依赖包列表
- **README.md** 项目说明文档

## 📊 数据来源
- [ITTF 官方网站](https://www.ittf.com)
- 包含 2021–2025 年女子单打世界排名（目前最新数据为2025.10.21）
- 数据格式：CSV，每周排名按日期记录

## 📝 说明
- 本项目仅用于学习和数据可视化展示
- 尊重 ITTF 版权，请勿用于商业用途

