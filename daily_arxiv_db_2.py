import sqlite3
import datetime
import requests
import json
import arxiv
import os
import yaml
import time
import random

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# Semantic Scholar API URL
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/v1/paper/arXiv:"

# SQLite DB 초기화 및 citation 열 추가
def init_db(db_name="arxiv.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 기존 papers 테이블이 있으면 삭제하고 새로 생성 (테스트용)
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
def get_citation_count(arxiv_id):
    try:
        response = requests.get(f"{SEMANTIC_SCHOLAR_API}{arxiv_id}")
        if response.status_code == 200:
            data = response.json()
            return data.get("citationCount", None)  # 인용 수 반환 (없으면 None)
        else:
            print(f"Semantic Scholar API 요청 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching citation count for {arxiv_id}: {e}")
        return None

# 데이터 저장 함수 (인용 수 추가됨)
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
                updated_date = fields[5].strip("**")
                code_url = fields[6].split("(")[-1].strip(")") if "link" in fields[6] else None
                
                # Semantic Scholar API로 citation count 가져오기
                citation_count = get_citation_count(paper_id)

                # Insert into database
                cursor.execute("""
                    INSERT OR IGNORE INTO papers
                    (id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, citation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, topic, subtopic, publish_date, title, authors, first_author, pdf_url, updated_date, code_url, citation_count))
    conn.commit()

# 논문 데이터 가져오기 (arXiv API)
def get_daily_papers(topic: str, query: str = "slam", max_results=2):
    content = dict()
    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    for result in search_engine.results():
        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id
        code_url = f"https://arxiv.paperswithcode.com/api/v0/papers/{paper_id}"
        paper_authors = ", ".join([str(a) for a in result.authors])
        paper_first_author = result.authors[0]
        publish_time = result.published.date()
        updated_time = result.updated.date()  # 최종 업데이트 날짜 추가 
        
        try:
            r = requests.get(code_url).json()
            if "official" in r and r["official"]:
                repo_url = r["official"]["url"]
                content[paper_id] = f"|**{publish_time}**|**{paper_title}**|{paper_authors} et.al.|[{paper_id}]({paper_url})|**{updated_time}**|**[link]({repo_url})**|\n"
            else:
                content[paper_id] = f"|**{publish_time}**|**{paper_title}**|{paper_authors} et.al.|[{paper_id}]({paper_url})|**{updated_time}**|null|\n"
        
        except Exception as e:
            print(f"Exception: {e} with id: {paper_id}")
    return {topic: content}

# SQLite DB 데이터를 Markdown 파일로 변환 (인용 수 추가)
def db_to_md(conn, md_filename="README.md"):
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
                f.write(f"### {subtopic_name}\n\n")
                f.write("|Publish Date|Title|Authors|PDF|Last Updated|Code|Citations|\n")
                f.write("|:-----------|:-----|:------|:---|:---|:---|:---|\n")
                cursor.execute("""
                    SELECT publish_date, title, authors, pdf_url, updated_date, code_url, citation
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

# 메인 실행 부분
if __name__ == "__main__":
    conn = init_db('./database/arxiv.db')
    yaml_path = os.path.join("./database", "topic.yml")
    yaml_data = get_yaml_data(yaml_path)
    data_collector = dict()

    for topic in yaml_data.keys():
        for subtopic, keyword in yaml_data[topic].items():
            print("Processing Keyword:", subtopic)
            try:
                data = get_daily_papers(subtopic, query=keyword, max_results=10)
            except Exception as e:
                print(f"Error processing {subtopic}: {e}")
                data = None
            if topic not in data_collector:
                data_collector[topic] = {}
            if data:
                data_collector[topic].update(data)

    save_to_db(conn, data_collector)
    db_to_md(conn, 'database/db_markdown/readme.md')
    conn.close()
    print("Data saved to SQLite database and Markdown file generated.")
