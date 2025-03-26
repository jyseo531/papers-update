import sqlite3
import datetime
import requests
import json
import arxiv
import os
import yaml
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# SQLite DB 초기화
import sqlite3

def init_db(db_name="arxiv.db"):
    # 데이터베이스 연결
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 테이블이 존재하지 않으면 새로 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            topic TEXT,
            subtopic TEXT,
            publish_date TEXT,
            title TEXT,
            authors TEXT,
            first_author TEXT,
            pdf_url TEXT,
            updated_date TEXT,
            code_url TEXT
        )  
    """)
    conn.commit()
    return conn


def db_to_md(conn, md_filename="README.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일 생성
    """
    cursor = conn.cursor()
    with open(md_filename, "w") as f:
        f.write("# arxiv-daily\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Welcome to contribute! Add your topics and keywords in [`topic.yml`](https://github.com/your-repo).\n\n")

        cursor.execute("SELECT DISTINCT topic FROM papers")
        topics = cursor.fetchall()
        for topic in topics:
            topic_name = topic[0]
            f.write(f"## {topic_name}\n\n")

            cursor.execute("SELECT DISTINCT subtopic FROM papers WHERE topic=?", (topic_name,))
            subtopics = cursor.fetchall()
            for subtopic in subtopics:
                subtopic_name = subtopic[0]
                f.write(f"\n### {subtopic_name}\n\n")

                f.write("| Publish Date | Title | Authors | PDF | Last Updated | Code |\n")
                f.write("|-------------|-------|---------|-----|-------------|------|\n")

                cursor.execute("""
                    SELECT publish_date, title, authors, pdf_url, updated_date, code_url
                    FROM papers
                    WHERE topic=? AND subtopic=?
                    ORDER BY publish_date DESC
                """, (topic_name, subtopic_name))

                papers = cursor.fetchall()
                for paper in papers:
                    publish_date, title, authors, pdf_url, updated_date, code_url = paper
                    pdf_link = f"[PDF]({pdf_url})" if pdf_url else "N/A"
                    code_link = f"[link]({code_url})" if code_url else "N/A"

                    f.write(f"| {publish_date} | **{title}** | {authors} | {pdf_link} | {updated_date} | {code_link} |\n")

                f.write("\n")

    print(f"Markdown file '{md_filename}' generated successfully.")

import sqlite3

def merge_databases(db_files, output_db="merged_arxiv.db"):
    # 새로운 데이터베이스 연결 (병합된 데이터가 저장될 곳)
    conn_out = sqlite3.connect(output_db)
    cursor_out = conn_out.cursor()

    # 첫 번째 데이터베이스의 테이블을 생성
    cursor_out.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            topic TEXT,
            subtopic TEXT,
            publish_date TEXT,
            title TEXT,
            authors TEXT,
            first_author TEXT,
            pdf_url TEXT,
            updated_date TEXT,
            code_url TEXT
        )  
    """)
    conn_out.commit()

    for db_file in db_files:
        # 각 데이터베이스 파일을 열기
        conn_in = sqlite3.connect(db_file)
        cursor_in = conn_in.cursor()

        try:
            # papers 테이블이 존재하는지 확인하고 데이터 선택
            cursor_in.execute("SELECT * FROM papers")
            rows = cursor_in.fetchall()

            # 데이터를 새로운 데이터베이스로 삽입
            cursor_out.executemany("""
                INSERT OR IGNORE INTO papers (
                    id, topic, subtopic, publish_date, title, authors, 
                    first_author, pdf_url, updated_date, code_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn_out.commit()

        except sqlite3.OperationalError as e:
            # 테이블이 없으면 오류 메시지 출력하고 계속 진행
            print(f"Skipping {db_file}: {e}")

        # 입력 데이터베이스 연결 종료
        conn_in.close()

    # 병합된 데이터베이스 연결 종료
    conn_out.close()

# 사용 예시
db_files = ["arxiv1.db", "arxiv2.db", "arxiv3.db", "arxiv4.db", "arxiv5.db"]
merge_databases(db_files)



# conn = init_db('./arxiv_star_2014.db')
# db_to_md(conn,'./arxiv_2014.md')

# conn = init_db('./arxiv_star_2015.db')
# db_to_md(conn,'./arxiv_2015.md')

# conn = init_db('./arxiv_star_2016.db')
# db_to_md(conn,'./arxiv_2016.md')

# conn = init_db('./arxiv_star_2017.db')
# db_to_md(conn,'./arxiv_2017.md')

# conn = init_db('./arxiv_star_2018.db')
# db_to_md(conn,'./arxiv_2018.md')

db_files = ["/home/cvlab/papers-update/arxiv_2014.db",
            "/home/cvlab/papers-update/arxiv_2015.db",
            "/home/cvlab/papers-update/arxiv_2016.db",
            "/home/cvlab/papers-update/arxiv_2017.db",
            "/home/cvlab/papers-update/arxiv_2018.db"]
merge_databases(db_files)