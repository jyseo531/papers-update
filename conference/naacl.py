import os
import requests
import sqlite3
from bs4 import BeautifulSoup

# 데이터베이스 설정
DB_DIR = "database/"
DB_NAME = os.path.join(DB_DIR, "naacl_papers.db")

def init_db():
    """SQLite 데이터베이스 초기화"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            pdf_link TEXT,
            code_link TEXT
        )
    ''')
    conn.commit()
    conn.close()

def scrape_naacl_papers(url):
    """NAACL 2024 Accepted Papers 페이지에서 논문 정보 크롤링"""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to access {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # 1️⃣ HTML 저장해서 디버깅
    with open("naacl_debug.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    papers = []

    # 2️⃣ 논문 제목과 저자 찾기
    for item in soup.find_all('li'):
        print(item.prettify())  # 디버깅: 현재 li 태그의 구조 확인

        # 논문 제목 가져오기
        title_tag = item.find('b')  # 제목은 <b> 태그 안에 존재
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # 저자 정보 가져오기 (제목을 제외한 나머지 부분)
        authors = item.get_text(separator=" ").replace(title, "").strip()

        papers.append((title, authors, "", ""))  # PDF 링크, 코드 링크는 없음

    if not papers:
        print("❌ No papers found. Check naacl_debug.html for debugging.")
    return papers

def save_to_db(papers):
    """크롤링한 논문 데이터를 SQLite DB에 저장"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for paper in papers:
        cursor.execute('''
            INSERT INTO papers (title, authors, pdf_link, code_link)
            VALUES (?, ?, ?, ?)
        ''', paper)

    conn.commit()
    conn.close()
    print(f"✅ {len(papers)} papers saved to {DB_NAME}")

if __name__ == "__main__":
    naacl_url = "https://2024.naacl.org/program/accepted_papers/"
    
    # 1. 데이터베이스 초기화
    init_db()
    
    # 2. 논문 정보 크롤링
    papers = scrape_naacl_papers(naacl_url)
    
    # 3. 데이터베이스 저장
    if papers:
        save_to_db(papers)
    else:
        print("❌ No papers found.")
