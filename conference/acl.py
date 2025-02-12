import sqlite3
from bs4 import BeautifulSoup
import requests

DB_NAME = "ACL.db"
TABLE_NAME = "Conference"

def initialize_db():
    """DB 생성 및 테이블 초기화"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        Author TEXT,
        PDF_Link TEXT,
        Code_URL TEXT,
        Conference_Name TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized.")

import requests
from bs4 import BeautifulSoup

def scrape_acl_data(url):
    """ACL 2024 논문 정보 크롤링 (URL에서 직접 HTML 가져오기)"""
    
    # 웹 페이지에서 HTML 가져오기
    response = requests.get(url)
    
    # 요청 실패 처리
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch ACL data. Status code: {response.status_code}")
    
    # BeautifulSoup로 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")
    with open('acl_jounal.txt', 'w') as f :
        f.write(soup.prettify())
    papers = []

    # Long Papers & Short Papers 섹션 찾기
    for section in soup.find_all("h2"):
        if section.text.strip().lower() in ["long papers", "short papers"]:
            ul = section.find_next("ul")  # <ul> 리스트 가져오기
            if ul:
                for li in ul.find_all("li"):
                    title_tag = li.find("strong")  # 논문 제목
                    authors_tag = li.find("em")    # 저자 정보
                    
                    if title_tag and authors_tag:
                        title = title_tag.text.strip()
                        authors = authors_tag.text.strip()
                        print(title)
                        print(authors)  
                        papers.append((title, authors))

    return papers

def save_to_db(papers):
    """크롤링한 논문 데이터를 SQLite DB에 저장"""
    if not papers:
        print("❌ No papers to save! Check the scraping function.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for paper in papers:
        title, authors = paper  # 기존 데이터 (논문 제목, 저자 정보)
        pdf_link = None  # PDF 링크 없음
        code_url = None  # 코드 URL 없음
        conference_name = "ACL 2024"  # 학회명 기본값 설정

        try:
            cursor.execute(f'''
                INSERT INTO {TABLE_NAME} (Title, Author, PDF_Link, Code_URL, Conference_Name)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, authors, pdf_link, code_url, conference_name))
            print(f"✅ INSERT SUCCESS: {title}")
        except sqlite3.Error as e:
            print(f"❌ INSERT FAILED: {title}")
            print(f"SQLite Error: {e}")

    conn.commit()
    conn.close()
    print(f"✅ {len(papers)} papers saved to {DB_NAME}")



# ✅ 실행
initialize_db()  # DB 초기화
acl_url = "https://2024.aclweb.org/program/main_conference_papers/"  # ACL 2024 논문 페이지 (업데이트 필요)
papers = scrape_acl_data(acl_url)  # 논문 스크래핑
save_to_db(papers)  # DB에 저장


