import sqlite3
from conference.cvpr import scrape_conference_data
from conference.eccv import scrape_eccv_data
from conference.iccv import scrape_iccv_data
from conference.nips import scrape_neurips_data
from conference.emnlp import scrape_emnlp_data

DB_PATH = "database/conference.db"
CVPR_URL = "https://cvpr.thecvf.com/Conferences/2024/AcceptedPapers"
ECCV_BASE_URL = "https://eccv.ecva.net/virtual/2024/papers.html?filter=sessions&search=Poster+Session+"
ICCV_URL= "https://openaccess.thecvf.com/ICCV2023?day=all"

NEURIPS_BASE_URL_EAST = "https://neurips.cc/virtual/2024/papers.html?filter=sessions&search=Poster+Session+6+East&page="
NEURIPS_BASE_URL_WEST = "https://neurips.cc/virtual/2024/papers.html?filter=sessions&search=Poster+Session+6+West&page="

EMNLP_URL = 'https://2024.emnlp.org/program/accepted_main_conference/'

def create_database():
    """Create the database and the Conference table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Conference (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        Author TEXT NOT NULL,
        PDF_Link TEXT,
        Code_URL TEXT,
        Conference_Name TEXT NOT NULL
    )
    ''')

    print("Conference 테이블이 생성되었습니다.")
    conn.commit()
    conn.close()

def save_to_database(papers, conference_name):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()

    try:
        for paper in papers:
            # 중복 데이터 확인
            cursor.execute('''
            SELECT 1 FROM Conference WHERE Title = ? AND Author = ? AND Conference_Name = ?
            ''', (paper['title'], paper['authors'], conference_name))
            result = cursor.fetchone()

            if not result:
                cursor.execute('''
                INSERT INTO Conference (Title, Author, PDF_Link, Code_URL, Conference_Name)
                VALUES (?, ?, ?, ?, ?)
                ''', (paper['title'], paper['authors'], paper['pdf_link'], paper['code_url'], conference_name))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def main():
    create_database()

    # neurips_east_papers = scrape_neurips_data(base_url=NEURIPS_BASE_URL_EAST, session_type="East", page_count=6)
    # if neurips_east_papers:
    #     save_to_database(neurips_east_papers, "NeurIPS 2024 East")

    # neurips_west_papers = scrape_neurips_data(base_url=NEURIPS_BASE_URL_WEST, session_type="West", page_count=6)
    # if neurips_west_papers:
    #     save_to_database(neurips_west_papers, "NeurIPS 2024 West")

    # # Scrape data from CVPR aㄴnd ECCV websites and save to database
    # cvpr_papers = scrape_conference_data(url=CVPR_URL)
    # if cvpr_papers:
    #     save_to_database(cvpr_papers, "CVPR 2024")

    # eccv_papers = scrape_eccv_data(base_url=ECCV_BASE_URL, session_count=7)
    # if eccv_papers:
    #     save_to_database(eccv_papers, "ECCV 2024")


    iccv_papers = scrape_iccv_data(url=ICCV_URL)
    if iccv_papers: 
        save_to_database(iccv_papers, "ICCV 2023")

    # emnlp_papers = scrape_emnlp_data(url=EMNLP_URL) 
    # if emnlp_papers: 
    #     save_to_database(emnlp_papers, "EMNLP 2024")
    
if __name__ == "__main__":
    main()

    
