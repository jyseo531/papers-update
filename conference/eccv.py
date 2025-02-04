import requests
from bs4 import BeautifulSoup

def scrape_eccv_data(base_url, session_count):
    """Scrape paper details (title, authors) from multiple ECCV session pages."""
    all_papers = []

    for session in range(1, session_count + 1):
        url = f"{base_url}{session}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to access {url}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"Scraping session {session}...")

        # 논문 정보를 포함한 <li> 태그 기준으로 검색
        for li in soup.find_all('li'):
            # 논문 제목 추출
            link_tag = li.find('a', href=True)
            title = link_tag.text.strip() if link_tag else "Unknown Title"

            # 저자 정보가 없으므로 기본값 설정
            authors = "Unknown Authors"

            # 디버깅용 출력
            print(f"Title: {title}, Authors: {authors}")

            all_papers.append({
                'title': title,
                'authors': authors,
                'pdf_link': None,  # PDF 링크는 NULL 처리
                'code_url': None   # Code URL은 NULL 처리
            })

    return all_papers