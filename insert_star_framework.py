import sqlite3
import requests
import base64
import time
from bs4 import BeautifulSoup
import datetime

class GitHubRepoAnalyzer:
    def __init__(self, repo_url, token=None):
        self.base_url = self.convert_to_api_url(repo_url)
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.framework_keywords = {
            "pytorch": ["torch", "torchvision"],
            "tensorflow": ["tensorflow", "tf.keras"],
        }
        self.code_extensions = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".html", ".css", ".sh", ".rb", ".php", ".ipynb"}
    
    def convert_to_api_url(self, repo_url):
        if repo_url.startswith("https://github.com/"):
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[:2]
                return f"https://api.github.com/repos/{owner}/{repo}/contents"
        raise ValueError("Invalid GitHub URL format")
    
    def analyze_repo(self):
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code != 200:
            return None
        files = response.json()
        for file in files:
            if file["type"] == "file" and file["name"].endswith(tuple(self.code_extensions)):
                file_content = requests.get(file["url"], headers=self.headers).json()
                if "content" in file_content:
                    content = base64.b64decode(file_content["content"]).decode("utf-8")
                    for framework, keywords in self.framework_keywords.items():
                        if any(keyword in content for keyword in keywords):
                            return framework
        return None

class GitHubStarCrawler:
    def __init__(self, repo_url):
        self.repo_url = repo_url
    def get_star_count(self):
        try:
            response = requests.get(self.repo_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            star_tag = soup.find('span', {'class': 'Counter js-social-count'})
            if star_tag:
                star_count = star_tag['title'].strip()
                return int(star_count.replace(',', ''))
            return 0
        except Exception:
            return 0


def update_github_info(db_file, token=None):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, code_url FROM papers WHERE code_url LIKE 'https://github.com/%'")
    rows = cursor.fetchall()
    for record_id, repo_url in rows:
        star_crawler = GitHubStarCrawler(repo_url)
        stars = star_crawler.get_star_count()
        if repo_url != "N/A":

            repo_analyzer = GitHubRepoAnalyzer(repo_url, token)
            framework = repo_analyzer.analyze_repo()
        else:
            framework = None
        cursor.execute("UPDATE papers SET star = ?, framework = ? WHERE id = ?", (stars, framework, record_id))
        conn.commit()
        print(f"Updated {repo_url}: {stars} stars, Framework: {framework}")
        time.sleep(1)
    conn.close()


import sqlite3
import datetime

def db_to_md(conn, md_filename="README.md"):
    """
    SQLite DB 데이터를 읽어 Markdown 파일 생성 (Authors, Last Updated 제외)
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

                # ✅ 헤더에서 Conference 열 추가
                f.write("| Publish Date | Title | PDF | Code | Star | Code Validity | Conference |\n")
                f.write("|-------------|-------|-----|------|------|---------|------------|\n")

                # ✅ SQL 쿼리에서 Conference 정보 포함
                cursor.execute("""
                    SELECT publish_date, title, pdf_url, code_url, star, framework, Conference
                    FROM papers
                    WHERE topic=? AND subtopic=?
                    ORDER BY star DESC, publish_date DESC
                """, (topic_name, subtopic_name))

                papers = cursor.fetchall()
                for paper in papers:
                    publish_date, title, pdf_url, code_url, star, framework, conference = paper
                    pdf_link = f"[PDF]({pdf_url})" if pdf_url else "N/A"
                    code_link = f"[link]({code_url})" if code_url else "N/A"
                    conference_text = conference if conference else "N/A"  # Conference 값이 없으면 N/A 표시

                    # ✅ Conference 열 추가하여 Markdown 테이블에 삽입
                    f.write(f"| {publish_date} | **{title}** | {pdf_link} | {code_link} | {star} | {framework} | {conference_text} |\n")

                f.write("\n")

    print(f"Markdown file '{md_filename}' generated successfully.")

if __name__ == "__main__":
    db_file = "./arxiv_star_test_2020_star_framework_0227.db"  # 데이터베이스 파일 경로
    conn = sqlite3.connect(db_file)
    
    db_to_md(conn, "./arxiv_2020_FINAL.md")  # 마크다운 생성
    conn.close()
