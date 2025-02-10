import sqlite3
import datetime

def db_to_md(conn, md_filename="./database/db_markdown/conference_readme.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일을 생성하며, 컨퍼런스별로 그룹화하여 출력.
    """
    cursor = conn.cursor()
    
    # Markdown 파일 초기화
    with open(md_filename, "w", encoding="utf-8") as f:
        # Header 작성
        f.write("# Main AI Conference Papers\n")
        f.write(f"Updated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write("> Generated from the Conference database.\n\n")

        # 데이터 가져오기 및 컨퍼런스별 정렬
        cursor.execute("SELECT Title, Author, PDF_Link, Code_URL, Conference_Name FROM conference ORDER BY Conference_Name")
        rows = cursor.fetchall()

        # 컨퍼런스별 데이터 그룹화
        conferences = {}
        for row in rows:
            title, author, pdf_link, code_url, conference_name = row
            if conference_name not in conferences:
                conferences[conference_name] = []
            conferences[conference_name].append((title, author, pdf_link, code_url))

        # Markdown 파일에 컨퍼런스별로 정리하여 작성
        for conference, papers in conferences.items():
            f.write(f"## {conference}\n\n")
            f.write("| Title | Author | PDF | Code URL |\n")
            f.write("|:------|:------|:------|:---------|\n")

            for title, author, pdf_link, code_url in papers:
                pdf_markdown = f"[PDF]({pdf_link})" if pdf_link else "N/A"
                code_markdown = f"[Code]({code_url})" if code_url else "N/A"

                f.write(f"| {title} | {author} | {pdf_markdown} | {code_markdown} |\n")

            f.write("\n")  # 컨퍼런스 간 구분

    print(f"Markdown file '{md_filename}' generated successfully.")

# 실행
if __name__ == "__main__":
    db_path = './database/conference.db'
    conn = sqlite3.connect(db_path)
    db_to_md(conn)
