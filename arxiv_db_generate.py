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
import datetime
import arxiv
import requests

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

def get_authors(authors, first_author=False):
    return ", ".join(str(author) for author in authors) if not first_author else authors[0]
"""  """
def sort_papers(papers):
    return {key: papers[key] for key in sorted(papers.keys(), reverse=True)}

def get_yaml_data(yaml_file: str):
    with open(yaml_file) as fs:
        data = yaml.load(fs, Loader=Loader)
    return data

def save_to_db(conn, data):
    cursor = conn.cursor()
    for topic, subtopics in data.items():
        for subtopic, papers in subtopics.items():
            for paper_id, paper_data in papers.items():
                if not isinstance(paper_data, dict):
                    print(f"⚠️ Warning: Invalid paper_data structure for {paper_id}: {paper_data}")
                    continue  # dict가 아니면 건너뛰기

                # ✅ `paper_data`에서 값 추출 (split 제거)
                publish_date = paper_data.get("publish_date", "Unknown")
                title = paper_data.get("title", "No Title")
                authors = paper_data.get("authors", "Unknown Authors")
                first_author = paper_data.get("first_author", "Unknown")
                pdf_url = paper_data.get("pdf_url", None)
                updated_date = paper_data.get("updated_date", "Unknown")
                code_url = paper_data.get("code_url", None)
                star = paper_data.get("star", 0)
                framework = paper_data.get("framework", "")

                try:
                    # ✅ 데이터베이스에 저장 (INSERT OR REPLACE로 중복 방지)
                    cursor.execute("""
                        INSERT OR REPLACE INTO papers
                        (id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, star, framework)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (paper_id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, star, framework))

                    print(f"✅ Saved to DB: {title} (ID: {paper_id})")

                except sqlite3.Error as e:
                    print(f"❌ Database Error: {e} for paper_id {paper_id}")
                    continue  # 오류 발생 시 해당 논문 건너뛰기

    conn.commit()
    print("\n✅ Data successfully saved to the database.")


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
                f.write("|-------------|-------|---------|-----|-------------|------|------|---------|\n")

                cursor.execute("""
                    SELECT publish_date, title, authors, pdf_url, updated_date, code_url, star, framework
                    FROM papers
                    WHERE topic=? AND subtopic=?
                    ORDER BY publish_date DESC
                """, (topic_name, subtopic_name))

                papers = cursor.fetchall()
                for paper in papers:
                    publish_date, title, authors, pdf_url, updated_date, code_url, star, framework = paper
                    pdf_link = f"[PDF]({pdf_url})" if pdf_url else "N/A"
                    code_link = f"[link]({code_url})" if code_url else "N/A"
                    star = 0
                    framework = ""
                    f.write(f"| {publish_date} | **{title}** | {authors} | {pdf_link} | {updated_date} | {code_link} | {star} | {framework} |\n")

                f.write("\n")

    print(f"Markdown file '{md_filename}' generated successfully.")



def get_daily_papers(topic: str, query: str = "slam", start_date="20200101"):
    """
    3개월 단위로 arXiv 논문을 가져오며, 한 번에 최대 100개씩 가져온다.
    submittedDate 기준으로 논문을 가져오되, 데이터가 없으면 lastUpdatedDate로 재검색한다.
    """
    content = dict()
    client = arxiv.Client()

    current_year = int(start_date[:4])
    current_month = int(start_date[4:6])
    #today = datetime.datetime.now().strftime("%Y%m%d")  # 오늘 날짜
    today = "20171231" # 2019년까지
    end_year = int(today[:4])  # 올해 연도

    while current_year <= end_year:
        while current_month <= 12:
            next_month = current_month + 2
            if next_month > 12:
                quarterly_start_date = f"{current_year}{current_month:02d}01"
                quarterly_end_date = f"{current_year}1231"
            else:
                quarterly_start_date = f"{current_year}{current_month:02d}01"
                quarterly_end_date = f"{current_year}{next_month-1:02d}31"

            if current_year == end_year and int(quarterly_end_date) > int(today):
                quarterly_end_date = today  # 올해인 경우, 오늘 날짜까지 검색

            print(f"\n📅 Fetching papers from {quarterly_start_date} to {quarterly_end_date}")
            print(f"🔍 Searching with query: {query}")

            all_papers = []
            last_paper_date = quarterly_start_date  # `submittedDate` 기준으로 검색

            while True:
                try:
                    # 🔥 `start` 없이 submittedDate 필터로 100개씩 가져오기 (2개월 단위)
                    search_engine = arxiv.Search(
                        query=f"{query} AND submittedDate:[{last_paper_date} TO {quarterly_end_date}]",
                        max_results=100,  # 최대 100개씩 가져오기
                        sort_by=arxiv.SortCriterion.SubmittedDate
                    )

                    new_papers = list(client.results(search_engine))

                    if not new_papers:
                        print(f"⚠️ No more papers found after {last_paper_date}. Trying lastUpdatedDate...")

                        # 🚨 submittedDate에서 데이터가 없으면 lastUpdatedDate 기준으로 재시도
                        search_engine = arxiv.Search(
                            query=f"{query} AND lastUpdatedDate:[{last_paper_date} TO {quarterly_end_date}]",
                            max_results=100,
                            sort_by=arxiv.SortCriterion.LastUpdatedDate
                        )
                        new_papers = list(client.results(search_engine))

                        if not new_papers:
                            print(f"❌ No papers found even after retrying with lastUpdatedDate. Stopping search.")
                            break

                    print(f"📌 Retrieved {len(new_papers)} papers from {current_year} (from {last_paper_date})")

                    all_papers.extend(new_papers)

                    # 📌 가장 마지막 논문의 제출 날짜를 기준으로 `submittedDate` 업데이트 (하루 뒤로 설정)
                    last_paper_date = (new_papers[-1].published + datetime.timedelta(days=1)).strftime("%Y%m%d")

                    # 논문 개수가 100개보다 작으면 더 가져올 필요 없음
                    if len(new_papers) < 100:
                        break

                    # API 요청 제한 방지
                    time.sleep(3)

                except arxiv.UnexpectedEmptyPageError:
                    print(f"⚠️ arXiv API returned an empty page at {last_paper_date}. Retrying with broader range...")
                    break  # 검색 중단 후 다음 기간으로 이동

            total_papers = len(all_papers)
            print(f"✅ Total papers retrieved for {current_year} (Month {current_month}-{next_month-1}): {total_papers}\n")

            retrieved_papers = set()  # 중복 논문 방지

            for result in all_papers:
                paper_id = result.get_short_id()
                if paper_id in retrieved_papers:  # 중복 방지
                    continue
                retrieved_papers.add(paper_id)

                paper_title = result.title
                paper_url = result.entry_id
                paper_authors = ", ".join([author.name for author in result.authors])
                publish_time = result.published.date()
                updated_time = result.updated.date()

                try:
                    r = requests.get(base_url + paper_id).json()
                    repo_url = r["official"]["url"] if "official" in r and r["official"] else None
                except Exception as e:
                    print(f"Exception: {e} with id: {paper_id}")
                    repo_url = None

                content[paper_id] = {
                    "publish_date": publish_time,
                    "title": paper_title,
                    "authors": paper_authors,
                    "first_author": paper_authors.split(",")[0] if paper_authors else "Unknown",
                    "pdf_url": paper_url,
                    "updated_date": updated_time,
                    "code_url": repo_url,
                    "star": 0,
                    "framework": "",
                }

                print(f"    ✅ {paper_title}")

            # 📌 2개월 단위 업데이트
            current_month += 2

        # 📌 연도 업데이트 및 `current_month` 초기화
        current_year += 1
        current_month = 1

    print(f"🎯 Final total papers retrieved: {len(content)}")
    return {topic: content}




# 실행 부분
if __name__ == "__main__":
    conn = init_db('./arxiv_star_2017_7.db')
    yaml_path = os.path.join("./database", "topic.yml")
    yaml_data = get_yaml_data(yaml_path)
    data_collector = {}

    for topic in yaml_data.keys():
        for subtopic, keyword in yaml_data[topic].items():
            print(f"\n🚀 Processing Keyword: {subtopic}")
            data = get_daily_papers(subtopic, query=keyword, start_date="20170101")
            if topic not in data_collector:
                data_collector[topic] = {}
            if data:
                data_collector[topic].update(data)

            save_to_db(conn, data_collector)
    # Generate Markdown file from database
    # db_to_md(conn, "./arxiv_2010_2019_star_framework.md")
    conn.close()
    
    print("\n✅ Data saved to SQLite database.")