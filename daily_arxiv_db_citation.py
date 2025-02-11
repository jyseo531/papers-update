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
            citation INTEGER DEFAULT NULL
        )
    """)
    conn.commit()
    return conn

# 논문의 인용 수 가져오기
def get_citation_count(query):
    try:
        search_url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
        print(f"Requesting: {search_url}")

        # Chrome Headless 설정 (UI 없이 실행)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # GUI 없이 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # WebDriver 실행
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(search_url)

        # 페이지 로딩 대기
        time.sleep(3)

        # "인용" 관련된 첫 번째 요소 찾기
        try:
            citation_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='gs_ri']//a[contains(text(), '인용')]"))
            )

            if citation_elements:
                citation_text = citation_elements[0].text  # 예: "103회 인용"
                citation_count = int(''.join(filter(str.isdigit, citation_text)))  # 숫자만 추출
            else:
                citation_count = None
                print("Citation count not found. Google might have blocked the request.")
        except:
            citation_count = None
            print("Citation count not found. Google might have blocked the request.")

        driver.quit()
        return citation_count

    except Exception as e:
        print(f"Error fetching citation count: {e}")
        return None


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

                citation_count = get_citation_count(title)

                # Insert into database
                cursor.execute("""
                    INSERT OR IGNORE INTO papers
                    (id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, citation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, citation_count))
    conn.commit()

def get_authors(authors, first_author=False):
    return ", ".join(str(author) for author in authors) if not first_author else authors[0]

def sort_papers(papers):
    return {key: papers[key] for key in sorted(papers.keys(), reverse=True)}

def get_yaml_data(yaml_file: str):
    with open(yaml_file) as fs:
        data = yaml.load(fs, Loader=Loader)
    return data

def get_all_papers_since_2023(topic: str, query: str = "slam"):
    content = dict()
    start_date = "20230101"
    query_with_date = f"{query} AND submittedDate:[{start_date} TO 30001231]"

    search_engine = arxiv.Search(
        query=query_with_date,
        max_results=None,  # ✅ max_results 없이 모든 논문 가져오기
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    paper_list = []
    
    # ✅ arXiv API는 Generator를 사용하므로 모든 결과를 하나씩 가져올 수 있음
    for result in search_engine.results():
        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id
        code_url = base_url + paper_id
        paper_authors = get_authors(result.authors)
        publish_time = result.published.date()
        updated_time = result.updated.date()

        if publish_time.year < 2023:
            continue  # ✅ 2023년 이전 논문 제외

        # ✅ Google Scholar에서 citation 가져오기
        citation_count = get_citation_count(paper_title)

        paper_list.append({
            "id": paper_id,
            "title": paper_title,
            "authors": paper_authors,
            "publish_time": publish_time,
            "updated_time": updated_time,
            "pdf_url": paper_url,
            "citation": citation_count if citation_count is not None else 0
        })

    # ✅ 인용 수 기준으로 내림차순 정렬 후 저장
    sorted_papers = sorted(paper_list, key=lambda x: x["citation"], reverse=True)

    for paper in sorted_papers:
        content[paper["id"]] = f"|**{paper['publish_time']}**|**{paper['title']}**|{paper['authors']} et.al.|[{paper['id']}]({paper['pdf_url']})|**{paper['updated_time']}**|null|{paper['citation']}|\n"

    return {topic: content}




    
def db_to_md(conn, md_filename="./database/db_markdown/arxiv_README.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일 생성
    """
    cursor = conn.cursor()
    # Markdown 파일 초기화
    with open(md_filename, "w") as f:
        # Header 작성
        f.write("# arxiv-daily\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Welcome to contribute! Add your topics and keywords in [`topic.yml`](https://github.com/your-repo).\n\n")
        # 각 토픽별 데이터 가져오기
        cursor.execute("SELECT DISTINCT topic FROM papers")
        topics = cursor.fetchall()
        for topic in topics:
            topic_name = topic[0]
            f.write(f"## {topic_name}\n\n")
            cursor.execute("SELECT DISTINCT subtopic FROM papers WHERE topic=?", (topic_name,))
            subtopics = cursor.fetchall()
            for subtopic in subtopics:
                subtopic_name = subtopic[0]
                f.write(f"### {subtopic_name}\n\n")
                f.write("|Publish Date|Title|Authors|PDF|Last Updated|Code|Citations|\n")
                f.write("|:-----------|:-----|:------|:---|:---|:---|:---|\n")
                cursor.execute("""
                    SELECT publish_date, title, authors, pdf_url, updated_date, code_url, citation_count
                    FROM papers
                    WHERE topic=? AND subtopic=?
                    ORDER BY publish_date DESC
                """, (topic_name, subtopic_name))
                papers = cursor.fetchall()
                for paper in papers:
                    publish_date, title, authors, pdf_url, updated_date, code_url, citation = paper
                    code_link = f"[link]({code_url})" if code_url else "null"
                    citation_count = citation if citation is not None else "N/A"
                    f.write(f"|{publish_date}|**{title}**|{authors}|[PDF]({pdf_url})|{updated_date}|{code_link}|{citation_count}|\n")
                f.write("\n")
    print(f"Markdown file '{md_filename}' generated successfully.")

if __name__ == "__main__":

    # Initialize database (Arxiv)
    conn = init_db('./database/arxiv.db')
    yaml_path = os.path.join("./database", "topic.yml")
    yaml_data = get_yaml_data(yaml_path)
    data_collector = dict()

    for topic in yaml_data.keys():
        for subtopic, keyword in yaml_data[topic].items():
            print("Processing Keyword:", subtopic)
            try:
                processor=None
                data = get_all_papers_since_2023(subtopic, query=keyword)
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
    db_to_md(conn, "./database/db_markdown/arxiv_citation_all.md")
    conn.close()
    
    print("Data saved to SQLite database and Markdown file generated.")