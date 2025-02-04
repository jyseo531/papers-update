from bs4 import BeautifulSoup
import requests 

def scrape_iccv_data(url):
    """Scrape paper details (title, authors, pdf link) from ICCV 2023 website."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to access {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    papers = []

    # 논문 정보를 포함한 <dt> 태그 기준으로 검색
    for dt in soup.find_all('dt'):
        # 논문 제목 및 PDF 링크 추출
        title_tag = dt.find('a', href=True)
        title = title_tag.text.strip() if title_tag else "Unknown Title"
        pdf_link = "https://openaccess.thecvf.com" + title_tag['href'] if title_tag else None

        # 저자 정보 추출
        dd = dt.find_next_sibling('dd')
        authors = " · ".join([a.strip() for a in dd.stripped_strings]) if dd else "Unknown Authors"
        
        # 디버깅용 출력
        print(f"Title: {title}, Authors: {authors}, PDF Link: {pdf_link}")

        papers.append({
            'title': title,
            'authors': authors,
            'pdf_link': pdf_link,
            'code_url': None  # Code URL은 ICCV 페이지에 없으므로 NULL 처리
        })

    return papers
