import requests
import pdfplumber
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import time

# ==============================
# 配置
# ==============================
targetYear = 2021
csv_file = f"ittf_women_{targetYear}_7_rankings.csv"

# ==============================
# 工具函数：计算发布日期
# ==============================
def get_ranking_release_date(year, week_num):
    jan_4 = datetime(year, 1, 4)
    monday_week1 = jan_4 - timedelta(days=jan_4.weekday())
    target_monday = monday_week1 + timedelta(weeks=week_num - 1)
    return target_monday + timedelta(days=1)

# ==============================
# 加载已有数据
# ==============================
try:
    existing_df = pd.read_csv(csv_file)
    print(f"✅ 已加载 {len(existing_df)} 条已有数据")
except FileNotFoundError:
    existing_df = pd.DataFrame()
    print("⚠️ 未找到已有 CSV，将创建新文件")

# ==============================
# 主循环：爬取第1–52周
# ==============================
new_data = []

for week in range(7, 8):
    release_date = get_ranking_release_date(targetYear, week)
    year_dir = release_date.strftime('%Y')
    month_dir = release_date.strftime('%m')
    filename = f"WS-WR-{targetYear}.W{week}-v2.pdf"
    url = f"https://www.ittf.com/wp-content/uploads/{year_dir}/{month_dir}/{filename}"

    # 跳过已存在
    if not existing_df.empty:
        if ((existing_df['week'] == week) & 
            (existing_df['date'] == release_date.strftime('%Y-%m-%d'))).any():
            print(f"  ⏭️ 第 {week} 周已存在，跳过")
            continue

    print(f"正在爬取第 {week} 周 ({release_date.strftime('%Y-%m-%d')}) ...")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️ 页面不存在（状态码 {response.status_code}），跳过")
            continue

        # # 用 BytesIO 包装
        # pdf_bytes = BytesIO(response.content)
        # with pdfplumber.open(pdf_bytes) as pdf:
        #     page = pdf.pages[0]
        #     text_lines = page.extract_text().split('\n')

        #     # 过滤掉标题、空白行
        #     data_lines = []
        #     for line in text_lines:
        #         line = line.strip()
        #         if not line or line.startswith('Rank') or line.startswith('WOMEN'):
        #             continue
        #         if len(line.split()) < 3:  # 至少有 Rank, Name, Assoc.
        #             continue
        #         data_lines.append(line)

        #     # 手动解析每一行
        #     for line in data_lines:
        #         parts = line.split()
        #         if len(parts) < 4:
        #             continue

        #         # 推测结构：[Rank] [Name...] [Assoc.] [Points]
        #         rank_str = parts[0]
        #         name_parts = parts[1:-2]  # 中间名字部分
        #         assoc = parts[-2]
        #         points_str = parts[-1]

        #         # 清理
        #         rank = int(rank_str)
        #         name = ' '.join(name_parts)
        #         points = int(points_str.replace(',', ''))

        #         info = {
        #             "date": release_date.strftime('%Y-%m-%d'),
        #             "week": week,
        #             "rank": rank,
        #             "player_name": name,
        #             "association": assoc,
        #             "points": points
        #         }
        #         new_data.append(info)
        #         print(f"  ✅ 添加: {name} ({assoc}) - {points}分")

        # 用 BytesIO 包装
        pdf_bytes = BytesIO(response.content)
        parsed_count = 0  # 已解析的有效记录数

        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                if parsed_count >= 50:
                    break
                text = page.extract_text()
                if not text:
                    continue
                text_lines = text.split('\n')

                # 过滤掉标题、空白行
                data_lines = []
                for line in text_lines:
                    line = line.strip()
                    if not line or line.startswith(('Rank', 'WOMEN', 'World', 'ITTF', 'Page')):
                        continue
                    if len(line.split()) < 3:  # 至少有 Rank, Name, Assoc.
                        continue
                    data_lines.append(line)

                # 手动解析每一行
                for line in data_lines:
                    if parsed_count >= 50:
                        break

                    parts = line.split()
                    if len(parts) < 4:
                        continue

                    # 推测结构：[Rank] [Name...] [Assoc.] [Points]
                    try:
                        rank = int(parts[0])
                        if rank > 50:  # 安全兜底：跳过 rank > 50 的行
                            continue
                        name = ' '.join(parts[1:-2])
                        assoc = parts[-2]
                        points = int(parts[-1].replace(',', ''))
                    except (ValueError, IndexError):
                        continue

                    info = {
                        "date": release_date.strftime('%Y-%m-%d'),
                        "week": week,
                        "rank": rank,
                        "player_name": name,
                        "association": assoc,
                        "points": points
                    }
                    new_data.append(info)
                    parsed_count += 1
                    print(f"  ✅ 添加: {name} ({assoc}) - {points}分")

                print(f"  ✅ 成功解析第 {week} 周")
                time.sleep(2)

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        time.sleep(3)
        continue

# ==============================
# 保存结果
# ==============================
if new_data:
    new_df = pd.DataFrame(new_data)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # 去重 + 排序
    combined_df.drop_duplicates(subset=['date', 'rank'], keep='first', inplace=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df = combined_df.sort_values(['date', 'rank']).reset_index(drop=True)
    combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')

    # 保存
    combined_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n🎉 新增 {len(new_df)} 条记录，总记录数: {len(combined_df)}")
else:
    print("\nℹ️ 没有新数据需要添加")