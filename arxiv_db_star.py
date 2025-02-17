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

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from config import (
    SERVER_DIR_DATABASE ,
    SERVER_DIR_STORAGE,
    SERVER_PATH_README,
    SERVER_PATH_DOCS,
    SERVER_DIR_HISTORY,
    SERVER_PATH_STORAGE_MD,
    TIME_ZONE_KR,
    logger,
)
# from using_ocr import load_model, loading_pdf_image, perform_ocr, extract_link

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"


# SQLite DB 초기화
def init_db(db_name="arxiv.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS papers")
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
            code_url TEXT, 
            star INTEGER DEFAULT 0,
            framework TEXT
        )  
    """)
    conn.commit()
    return conn

def save_to_db(conn, data):
    cursor = conn.cursor()
    for topic, subtopics in data.items():
        for subtopic, papers in subtopics.items():
            for paper_id, paper_data in papers.items():
                # Parse paper_data to extract fields
                fields = paper_data.split('|')
                publish_date = fields[1].strip("**")
                title = fields[2].strip("**")
                authors = fields[3]
                first_author = authors.split(",")[0]
                pdf_url = fields[4].split("(")[-1].strip(")")
                updated_date = fields[5].strip("**")  # updated_date 추가
                code_url = fields[6].split("(")[-1].strip(")") if "link" in fields[5] else None
                star = 0
                framework = ""

                

                # Insert into database
                cursor.execute("""
                    INSERT OR IGNORE INTO papers
                    (id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, star, framework)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, star, framework))
    conn.commit()




def get_authors(authors, first_author=False):
    return ", ".join(str(author) for author in authors) if not first_author else authors[0]
"""  """
def sort_papers(papers):
    return {key: papers[key] for key in sorted(papers.keys(), reverse=True)}

def get_yaml_data(yaml_file: str):
    with open(yaml_file) as fs:
        data = yaml.load(fs, Loader=Loader)
    return data

def get_daily_papers(topic: str, query: str = "slam", start_date="20230101"):
    content = dict()
    total_results = 0
    page_size = 100  # 한 번에 불러올 논문 개수 (최대 100)
    retrieved_papers = set()  # 중복 방지

    while True:
        search_engine = arxiv.Search(
            query=f"{query} AND submittedDate:[{start_date} TO {datetime.datetime.now().strftime('%Y%m%d')}]",
            max_results=page_size,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        new_papers = list(search_engine.results())  # 검색 결과를 리스트로 변환
        if not new_papers or len(new_papers) == 0:  # 새로운 논문이 없으면 종료
            break

        for result in new_papers:
            paper_id = result.get_short_id()
            if paper_id in retrieved_papers:  # 중복 방지
                continue
            retrieved_papers.add(paper_id)

            paper_title = result.title
            paper_url = result.entry_id
            code_url = base_url + paper_id
            paper_authors = get_authors(result.authors)
            paper_first_author = get_authors(result.authors, first_author=True)
            publish_time = result.published.date()
            updated_time = result.updated.date()  # 최종 업데이트 날짜 추가
            star = 0
            framework = ""
            try:
                r = requests.get(code_url).json()
                if "official" in r and r["official"]:
                    repo_url = r["official"]["url"]
                    content[paper_id] = f"|**{publish_time}**|**{paper_title}**|{paper_authors} et.al.|[{paper_id}]({paper_url})|**{updated_time}**|**[link]({repo_url})**|**{star}**|**{framework}**|\n"

                else: 
                    content[paper_id] = f"|**{publish_time}**|**{paper_title}**|{paper_authors} et.al.|[{paper_id}]({paper_url})|**{updated_time}**|null|**{star}**|**{framework}**|\n"

            except Exception as e:
                print(f"Exception: {e} with id: {paper_id}")

        total_results += len(new_papers)
        print(f"Retrieved {total_results} papers so far...")

        # ArXiv API에는 페이지네이션 기능이 없어서, 현재 방식으로는 모든 데이터를 반복적으로 가져오는 한계가 있음.
        # 해결 방법:
        # - ArXiv 데이터셋을 직접 다운로드하여 활용하거나
        # - OpenAlex, Semantic Scholar 같은 API 활용 고려

    return {topic: content}

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

                f.write("| Publish Date | Title | Authors | PDF | Last Updated | Code | Star | Framework |\n")
                f.write("|-------------|-------|---------|-----|-------------|------|\n")

                cursor.execute("""
                    SELECT publish_date, title, authors, pdf_url, updated_date, code_url, star, framework
                    FROM papers
                    WHERE topic=? AND subtopic=?
                    ORDER BY publish_date DESC
                """, (topic_name, subtopic_name))

                papers = cursor.fetchall()
                for paper in papers:
                    publish_date, title, authors, pdf_url, updated_date, code_url = paper
                    pdf_link = f"[PDF]({pdf_url})" if pdf_url else "N/A"
                    code_link = f"[link]({code_url})" if code_url else "N/A"
                    star = 0
                    framework = ""
                    f.write(f"| {publish_date} | **{title}** | {authors} | {pdf_link} | {updated_date} | {code_link} | {star} | {framework} |\n")

                f.write("\n")

    print(f"Markdown file '{md_filename}' generated successfully.")


if __name__ == "__main__":

    # Initialize database (Arxiv)
    conn = init_db('./arxiv_star.db')
    yaml_path = os.path.join("./database", "topic.yml")
    yaml_data = get_yaml_data(yaml_path)
    data_collector = {}

    for topic in yaml_data.keys():
        for subtopic, keyword in yaml_data[topic].items():
            print("Processing Keyword:", subtopic)
            try:
                processor=None
                data = get_daily_papers(subtopic, query=keyword, start_date="20230101")
            except Exception as e:
                print(f"Error processing {subtopic}: {e}")
                data = None
            if not topic in data_collector:
                data_collector[topic] = {}
            if data:
                data_collector[topic].update(data)


    # Save collected data to SQLite database
    save_to_db(conn, data_collector)
    
    # Generate Markdown file from database
    db_to_md(conn, "./arxiv_star.md")
    conn.close()
    
    print("Data saved to SQLite database and Markdown file generated.")