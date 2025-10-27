import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import re

targetYear=2021


# ====== 1. 读取已有数据 ======
csv_file = f"ittf_women_{targetYear}_rankings.csv"
try:
    existing_df = pd.read_csv(csv_file)
    print(f"✅ 已加载 {len(existing_df)} 条已有数据")
except FileNotFoundError:
    existing_df = pd.DataFrame()
    print("⚠️  未找到已有 CSV，将创建新文件")

# ====== 2. 定义获取发布日期的函数 ======
def get_ranking_release_date(year, week_num):
    jan_4 = datetime(year, 1, 4)
    monday_week1 = jan_4 - timedelta(days=jan_4.weekday())
    target_monday = monday_week1 + timedelta(weeks=week_num - 1)
    return target_monday + timedelta(days=1)

def extract_association(td_element):
    """
    从 td 元素中提取协会代码（如 CHN、JPN）
    支持不同年份的 HTML 结构
    """
    # 方法1：尝试从 p 的 class 中提取（2024+ 年）
    p_tag = td_element.find('p')
    if p_tag and p_tag.get('class'):
        for cls in p_tag['class']:
            if cls.startswith('fg-'):
                return cls.split('-', 1)[1]  # 取 'fg-CHN' 中的 CHN

    # 方法2：直接从 td 文本提取（2023 年等旧结构）
    text = td_element.get_text(strip=True)
    if text and len(text) in (2, 3) and text.isalpha():
        return text

    return None  # 无法提取

# ====== 3. 只爬第1–9周 ======
new_data = []

for week in range(10, 53):  # 第1到第52周
    release_date = get_ranking_release_date(targetYear, week)
    year_dir = release_date.strftime('%Y')
    month_dir = release_date.strftime('%m')
    filename = f"{targetYear}_{week}_SEN_WS.html"
    url = f"https://www.ittf.com/wp-content/uploads/{year_dir}/{month_dir}/{filename}"

    # 检查是否已经爬过（避免重复）
    if not existing_df.empty:
        if ((existing_df['week'] == week) & (existing_df['date'] == release_date.strftime('%Y-%m-%d'))).any():
            print(f"  ⏭️  第 {week} 周已存在，跳过")
            continue

    print(f"正在爬取第 {week} 周 ({release_date.strftime('%Y-%m-%d')}) ...")

    try:
        # 礼貌请求：添加 User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️  页面不存在（状态码 {response.status_code}），跳过")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"  ⚠️  无表格，跳过")
            continue

        rows = table.find_all('tr', class_='rrow')
        if not rows:
            print(f"  ⚠️  无数据行，跳过")
            continue

        for i, row in enumerate(rows):
            if i >= 50:
                break
            cols = row.find_all('td')
            if len(cols) < 4:
                continue


            try:
                # Rank: 从第一个 td 的 text 提取数字（不是 span）
                rank_text = cols[0].text.strip()
                rank_match = re.search(r'\d+', rank_text)
                if not rank_match:
                    continue
                rank = int(rank_match.group())

                # Name
                player = cols[1].text.strip()

                # association
                association = extract_association(cols[2])

                # Points: 去除逗号、空格等非数字字符
                points_text = cols[3].text.strip()
                clean_points = re.sub(r'[^\d]', '', points_text)
                points = int(clean_points) if clean_points else None

                # 添加数据
                info = {
                    "date": release_date.strftime('%Y-%m-%d'),
                    "week": week,
                    "rank": rank,
                    "player_name": player,
                    "association": association,
                    "points": points
                }
                print(info)
                new_data.append(info)

            except Exception as e:
                print(f"  ⚠️  解析失败: {e}")
                continue

            # try:
            #     # Rank
            #     rank_span = cols[0].find('span', class_='rank')
            #     if not rank_span:
            #         continue
            #     rank_text = rank_span.text.strip()
            #     rank = int(re.findall(r'\d+', rank_text)[0])

            #     # Name
            #     player = cols[1].text.strip()

            #     # Assoc
            #     assoc_p = cols[2].find('p', class_='fg')
            #     country = assoc_p['class'][1].replace('fg-', '') if assoc_p else None

            #     # Points
            #     points_text = cols[3].text.strip()
            #     points = int(points_text.replace(',', '')) if points_text.isdigit() else None
            #     info={
            #         "date": release_date.strftime('%Y-%m-%d'),
            #         "week": week,
            #         "rank": rank,
            #         "player_name": player,
            #         "country": country,
            #         "points": points
            #     }
            #     print(info)
            #     new_data.append({
            #         "date": release_date.strftime('%Y-%m-%d'),
            #         "week": week,
            #         "rank": rank,
            #         "player_name": player,
            #         "country": country,
            #         "points": points
            #     })

            # except Exception as e:
            #     print(f"  ⚠️  解析失败: {e}")
            #     continue


        print(f"  ✅ 成功爬取 {len(rows)} 条记录")
        time.sleep(1.5)  # 礼貌等待 1.5 秒

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        time.sleep(2)
        continue

# ====== 4. 合并新旧数据 ======
print(f"new_data 长度: {len(new_data)}")

if new_data:
    new_df = pd.DataFrame(new_data)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # 可选：按 date + rank 去重（防止重复）
    combined_df.drop_duplicates(subset=['date', 'rank'], keep='first', inplace=True)

    # 按日期和排名排序（可选）
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df = combined_df.sort_values(['date', 'rank']).reset_index(drop=True)
    combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')

    # 保存回原文件
    combined_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n🎉 新增 {len(new_df)} 条记录，总记录数: {len(combined_df)}")
else:
    print("\nℹ️  没有新数据需要添加")