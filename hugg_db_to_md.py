import sqlite3
import datetime

# DB 경로 설정
pre_db_path = "./database/huggingface_model_pre.db"
main_db_path = "./database/huggingface_model.db"
md_filename = "./huggface_readme.md"

def db_to_md(pre_db_path, main_db_path, md_filename):
    """
    두 개의 SQLite DB를 조인하여 Markdown 파일 생성
    - Title은 pre_db에서 가져옴
    - Paper, GitHub URL, License, Category는 main_db에서 가져옴
    - github_url 기준으로 매칭
    """
    
    conn_pre = sqlite3.connect(pre_db_path)
    conn_main = sqlite3.connect(main_db_path)
    
    cursor_pre = conn_pre.cursor()
    cursor_main = conn_main.cursor()

    # Markdown 파일 초기화
    with open(md_filename, "w") as f:
        # Header 작성
        f.write("# Hugging Face News\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Generated from the Hugging Face database.\n\n")

        # 테이블 헤더
        f.write("| Title | Paper | GitHub URL | License | Category |\n")
        f.write("|:------|:------|:-----------|:--------|:---------|\n")

        # pre_db에서 github_url과 title 가져오기
        cursor_pre.execute("SELECT github_url, title FROM hf_news")
        pre_data = {row[0]: row[1] for row in cursor_pre.fetchall() if row[0]}  # github_url을 키로 저장

        # main_db에서 github_url 기준으로 매칭하여 데이터 가져오기
        cursor_main.execute("SELECT github_url, paper, license, category FROM hf_news")
        rows = cursor_main.fetchall()

        for github_url, paper, license, category in rows:
            title = pre_data.get(github_url, "Unknown Title")  # github_url 기준으로 title 찾기
            paper_link = f"[Paper pdf]({paper})" if paper and paper != "NULL" else "NULL"
            github_link = f"[HuggingFace]({github_url})" if github_url and github_url != "NULL" else "NULL"

            # Markdown 파일에 데이터 추가
            f.write(f"| {title} | {paper_link} | {github_link} | {license} | {category} |\n")

    print(f"✅ Markdown file '{md_filename}' generated successfully.")

    conn_pre.close()
    conn_main.close()


# 실행
db_to_md(pre_db_path, main_db_path, md_filename)
