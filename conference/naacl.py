import requests
import sqlite3
from bs4 import BeautifulSoup
import os

def init_db():
    """SQLite 데이터베이스 초기화"""
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
        print(f"Failed to access {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    papers = []

    for row in soup.find_all('tr'):  # 논문 정보가 포함된 <tr> 태그 반복
        link_tag = row.find('a', href=True)
        if not link_tag:
            continue  # 링크가 없으면 스킵

        title = link_tag.text.strip()  # 논문 제목
        pdf_link = link_tag['href']  # 논문 PDF 링크
        pdf_link = f"https://2024.naacl.org{pdf_link}" if pdf_link.startswith('/') else pdf_link

        # 저자 정보
        author_div = row.find('div', {'class': 'authors'})
        authors = author_div.text.strip() if author_div else "Unknown"

        # 코드 링크 찾기 (일반적으로 PDF 아래에 코드 링크가 존재)
        code_link = ""
        code_tag = row.find('a', text="Code")  # "Code"라는 텍스트 포함하는 링크 검색
        if code_tag:
            code_link = code_tag['href']
            code_link = f"https://2024.naacl.org{code_link}" if code_link.startswith('/') else code_link

        papers.append((title, authors, pdf_link, code_link))

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
        print("No papers found.")
