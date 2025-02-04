from bs4 import BeautifulSoup
import requests

def scrape_emnlp_data(url):
    """Scrape paper details (title and authors) from EMNLP 2024 accepted papers page."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류가 있을 경우 예외 발생
    except requests.exceptions.RequestException as e:
        print(f"Failed to access {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    papers = []

    # 논문 제목과 저자 정보가 포함된 <p> 태그 기준으로 검색
    for p in soup.find_all("p"):
        strong_tag = p.find("strong")
        if strong_tag:
            
            title = strong_tag.get_text(strip=True)

            # 저자 정보 추출 (논문 제목 이후 <br> 태그 다음 내용)
            br_tag = strong_tag.find_next("br")
            authors = br_tag.next_sibling.strip() if br_tag and br_tag.next_sibling else "Unknown Authors"
    
            papers.append({
                'title': title,
                'authors': authors,
                'pdf_link': None,  # PDF 링크는 해당 페이지에 없음
                'code_url': None   # Code URL도 제공되지 않음
            })

    return papers
