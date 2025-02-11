import requests
from bs4 import BeautifulSoup

def scrape_conference_data(url):
    """Scrape paper details from the conference website."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to access {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    papers = []
    with open('emnlp.txt', 'w') as f : 
        f.write(soup.prettify())

        
    # 논문 정보를 포함한 <tr> 태그 기준으로 검색
    for row in soup.find_all('tr'):
        # 링크와 논문 제목 추출
        link_tag = row.find('a', href=True)
        if link_tag:
            code_url = link_tag['href']  # 하이퍼링크 추출
            title = link_tag.text.strip()  # 논문 제목 추출
        else:
            continue  # 링크가 없으면 해당 <tr> 스킵

        # 저자 정보 추출
        author_div = row.find('div', {'class': 'indented'})
        authors = author_div.text.strip() if author_div else "Unknown"
        

        """
        
        Code Link, PDF_Link를 여기서 좀 나누어야 할듯 
        """


        # 디버깅용 출력
        print(f"Title: {title}, Authors: {authors}, Code URL: {code_url}")

        papers.append({
            'title': title,
            'authors': authors,
            'pdf_link': "",  # PDF 링크는 빈 문자열로 설정
            'code_url': code_url  # 하이퍼링크를 Code_URL로 설정
        })

    return papers