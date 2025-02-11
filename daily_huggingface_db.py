import requests 
from bs4 import BeautifulSoup
from huggingface_script.fetch_hf_news import get_arxiv_metadata, fetch_huggingface_news
import sqlite3
from huggingface_script.insert_data import insert_model, insert_hf_news
import datetime 

def initialize_database(db_path="db/database.db"):
    """
    데이터베이스 초기화 및 필요한 테이블 생성
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 테이블 생성 (만약 테이블이 존재하지 않으면)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hf_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            paper TEXT,
            github_url TEXT,
            license TEXT,
            category TEXT
        )
    """)
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS huggingface_models (
            model_name TEXT PRIMARY KEY,
            author TEXT,
            tags TEXT,
            paper_url TEXT,
            downloads INTEGER,
            likes INTEGER
        )
    """)
    
    conn.commit()
    return conn 

def get_huggingface_models(base_url="https://huggingface.co/models"):
    """
    크롤링하여 Hugging Face 모델 메타데이터를 가져옵니다.
    
    Returns:
        dict: 모델 이름을 키로 하는 메타데이터 딕셔너리.
    """
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch Hugging Face models: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.content, "html.parser")
    models = {}

    # 모델 카드 데이터 추출
    for card in soup.find_all("div", class_="model-card"):
        try:
            model_name_element = card.find("a", class_="model-name")
            model_name = model_name_element.text.strip() if model_name_element else "Unknown Model"
            tags = [tag.text.strip() for tag in card.find_all("span", class_="tag")]
            author_element = card.find("a", class_="author")
            author_name = author_element.text.strip() if author_element else "Unknown Author"
            paper_link_element = card.find("a", class_="paper-link")
            paper_url = paper_link_element["href"].strip() if paper_link_element else None
            downloads_element = card.find("span", class_="downloads")
            downloads = int(downloads_element.text.replace(",", "")) if downloads_element else 0
            likes_element = card.find("span", class_="likes")
            likes = int(likes_element.text.replace(",", "")) if likes_element else 0

            model_data = {
                "model_name": model_name,
                "author": author_name,
                "tags": ", ".join(tags),
                "paper_url": paper_url,
                "downloads": downloads,
                "likes": likes
            }
            
            models[model_name] = model_data
        except Exception as e:
            print(f"Error parsing model card: {e}")

    return models

def save_huggingface_to_db(conn, data):
    """
    Hugging Face 모델 데이터를 SQLite 데이터베이스에 저장합니다.
    """
    cursor = conn.cursor()
    
    for model_name, model_data in data.items():
        cursor.execute("""
            INSERT OR IGNORE INTO huggingface_models
            (model_name, author, tags, paper_url, downloads, likes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (model_name, model_data["author"], model_data["tags"], model_data["paper_url"], model_data["downloads"], model_data["likes"]))

    conn.commit()

def db_to_md(conn, md_filename="./database/db_markdown/huggface_readme.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일 생성
    """
    cursor = conn.cursor()
    with open(md_filename, "w") as f:
        f.write("# Hugging Face News\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Generated from the Hugging Face database.\n\n")
        
        cursor.execute("SELECT model_name, author, tags, paper_url, downloads, likes FROM huggingface_models")
        rows = cursor.fetchall()

        f.write("| Model Name | Author | Tags | Paper URL | Downloads | Likes |\n")
        f.write("|:-----------|:-------|:-----|:----------|:----------|:------|\n")
        
        for row in rows:
            model_name, author, tags, paper_url, downloads, likes = row
            paper_link = f"[Link]({paper_url})" if paper_url else "NULL"
            f.write(f"| {model_name} | {author} | {tags} | {paper_link} | {downloads} | {likes} |\n")
    
    print(f"Markdown file '{md_filename}' generated successfully.")

if __name__ == "__main__":
    db_path = './database/huggingface_model.db'
    conn = initialize_database(db_path)

    hf_models = get_huggingface_models()
    save_huggingface_to_db(conn, hf_models)
    db_to_md(conn)
