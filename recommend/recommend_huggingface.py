import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import time
import datetime

# SQLite DB 경로 (올바른 경로 설정)
DB_PATH = "recommend/recommend_huggingface_models.db"
HF_URL = "https://huggingface.co/models"

# 1️⃣ DB 초기화 함수
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 모델 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS huggingface_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE,
            update_date TEXT,
            downloads TEXT,
            likes TEXT,
            link TEXT,
            category TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 초기화 완료!")

# 2️⃣ HTML 크롤링 및 파싱 함수
def fetch_and_parse_html():
    response = requests.get(HF_URL)

    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"❌ 페이지 요청 실패: {response.status_code}")
        return None

# 3️⃣ 모델 데이터 추출 함수 (각 태그 페이지에서 모델 가져오기)
def extract_huggingface_models(soup, max_models=50):
    if not soup:
        return {}

    # 태그(카테고리) 가져오기
    tag_elements = soup.select("a[href^='/models?pipeline_tag=']")

    tag_links = {}
    for tag in tag_elements:
        tag_name = tag.get_text(strip=True)
        tag_href = tag["href"]
        tag_links[tag_name] = f"https://huggingface.co{tag_href}"

    # 각 태그별 상위 모델 추출
    tag_models = {}

    for tag, tag_url in tag_links.items():
        print(f"📌 {tag} 태그 페이지 크롤링 중... ({tag_url})")

        # 태그별 개별 페이지 요청
        response = requests.get(tag_url)
        if response.status_code != 200:
            print(f"❌ {tag} 페이지 요청 실패")
            continue
        
        tag_soup = BeautifulSoup(response.text, "html.parser")
        
        models = []
        model_cards = tag_soup.select("article")[:max_models]  # 상위 50개 모델 가져오기

        for card in model_cards:
            model_name_tag = card.select_one("a")
            downloads_tag = card.select_one("span")

            if model_name_tag and downloads_tag:
                model_name = model_name_tag.get_text(strip=True)
                model_href = model_name_tag["href"]
                downloads = downloads_tag.get_text(strip=True)

                models.append({
                    "Model Name": model_name,
                    "Downloads": downloads,
                    "Link": f"https://huggingface.co{model_href}",
                    "Category": tag  
                })

        if models:
            tag_models[tag] = models
        
        time.sleep(2)  # 서버 부하 방지를 위한 딜레이

    return tag_models

# 4️⃣ 모델 데이터 정제 함수
def clean_model_data(tag_models):
    cleaned_rows = []

    for tag, models in tag_models.items():
        for model in models:
            row = {"Category": tag}
            
            raw_model_name = model["Model Name"]
            model_name_match = re.match(r"([\w\-/]+)", raw_model_name)
            model_name = model_name_match.group(1) if model_name_match else raw_model_name
            
            info_parts = raw_model_name.split("•")

            update_date = info_parts[1].strip() if len(info_parts) > 1 else "Unknown"
            downloads = info_parts[2].strip() if len(info_parts) > 2 else "Unknown"
            likes = info_parts[3].strip() if len(info_parts) > 3 else "Unknown"
            
            row.update({
                "Model Name": model_name,
                "Update Date": update_date,
                "Downloads": downloads,
                "Likes": likes,
                "Link": model["Link"]
            })

            cleaned_rows.append(row)

    return cleaned_rows

# 5️⃣ DB 저장 함수
def save_models_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for model in data:
        cursor.execute("""
            INSERT OR IGNORE INTO huggingface_models 
            (model_name, update_date, downloads, likes, link, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (model["Model Name"], model["Update Date"], model["Downloads"], model["Likes"], model["Link"], model["Category"]))
    
    conn.commit()
    conn.close()
    print("✅ 데이터가 DB에 저장되었습니다!")

# 6️⃣ Markdown 변환 함수
def db_to_md(conn, md_filename="database/db_markdown/recommend_huggingface_models.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일로 변환하여 저장하는 함수.
    """
    cursor = conn.cursor()

    # Markdown 파일 초기화
    with open(md_filename, "w", encoding="utf-8") as f:
        # Header 작성
        f.write("# Hugging Face Models\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Generated from the Hugging Face database.\n\n")

        # 데이터 가져오기 (순서 변경)
        cursor.execute("""
            SELECT category, downloads, likes, model_name, update_date, link 
            FROM huggingface_models
        """)
        rows = cursor.fetchall()

        if not rows:
            print("❌ No data found in the database. Markdown file will not be created.")
            return None

        # 테이블 헤더 작성 (사용자가 원하는 순서대로 정렬)
        f.write("| Category | Downloads | Likes | Model Name | Update Date | Link |\n")
        f.write("|:---------|:----------|:------|:-----------|:------------|:------|\n")

        # 데이터 입력
        for row in rows:
            category, downloads, likes, model_name, update_date, link = row
            link_markdown = f"[Link]({link})" if link else "N/A"
            f.write(f"| {category} | {downloads} | {likes} | {model_name} | {update_date} | {link_markdown} |\n")

    print(f"✅ Markdown file '{md_filename}' generated successfully.")
    return md_filename

# 7️⃣ 실행 함수
def main():
    initialize_database()
    
    soup = fetch_and_parse_html()
    if not soup:
        return
    
    model_data = extract_huggingface_models(soup, max_models=50)  # 상위 50개씩 크롤링
    if not model_data:
        print("❌ 모델 데이터를 찾을 수 없습니다.")
        return

    cleaned_data = clean_model_data(model_data)
    save_models_to_db(cleaned_data)

    # DB 연결 후 Markdown 변환 실행
    conn = sqlite3.connect(DB_PATH)
    markdown_file = db_to_md(conn)
    conn.close()

# 실행
if __name__ == "__main__":
    main()