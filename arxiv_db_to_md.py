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