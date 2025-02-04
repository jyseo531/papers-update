import requests 
from bs4 import BeautifulSoup 

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_filename(url):
    """Replace characters in the URL to create a valid file name."""
    return url.replace("/", "_").replace(":", "_").replace("?", "_").replace("&", "_")


def scrape_project_page(project_url):
    """Scrape details from the project page, including Paper Link and Code URL."""
    try:
        response = requests.get(project_url, verify=False)
        if response.status_code != 200:
            print(f"Failed to access project page: {project_url}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for project page: {project_url}, Error: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Paper Link and Code URL 추출
    paper_link = None
    code_url = None

    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'paper' in href.lower() or 'arxiv' in href.lower():
            print(href)
            paper_link = href if href.startswith("http") else f"https://neurips.cc{href}"
        if 'github' in href.lower() or 'code' in href.lower():
            print(href)
            code_url = href if href.startswith("http") else f"https://neurips.cc{href}"

    return paper_link, code_url


def scrape_poster_page(poster_url):
    """Scrape the project page link from the poster page."""
    base_url = "https://neurips.cc"
    full_url = base_url + poster_url if poster_url.startswith("/") else poster_url

    try:
        response = requests.get(full_url, verify=False)
        if response.status_code != 200:
            print(f"Failed to access poster page: {full_url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for poster page: {full_url}, Error: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Project Page 링크 추출
    project_link_tag = soup.find('a', text=lambda t: t and 'Project Page' in t)
    if project_link_tag:
        project_link = project_link_tag['href']
        # 절대 경로인지 확인 후 변환
        if not project_link.startswith("http"):
            project_link = base_url + project_link
        return project_link

    print(f"No Project Page link found on {full_url}")
    return None


def scrape_neurips_data(base_url, session_type, page_count):
    """Scrape paper details (title, authors, pdf link, code link) from NeurIPS sessions."""
    all_papers = []

    for page in range(1, page_count + 1):
        url = f"{base_url}{page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to access {url}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"Scraping {session_type} page {page}...")
        # with open(f"debug_neurips_{session_type}_page_{page}.txt", "w", encoding="utf-8") as file:
        #     file.write(soup.prettify())
            
        # 논문 정보를 포함한 <li> 태그 기준으로 검색
        for li in soup.find_all('li'):
            # 논문 제목 및 포스터 페이지 링크 추출
            link_tag = li.find('a', href=True)
            title = link_tag.text.strip() if link_tag else "Unknown Title"
            poster_url = link_tag['href'] if link_tag and link_tag['href'].startswith("/virtual/2024/poster") else None
            
            # Poster URL은 정상적으로 작동함.
            if not poster_url:
                continue

            # 포스터 페이지에서 Project Page 링크 추출
            project_url = scrape_poster_page(poster_url)

            # Project Page에서 Paper Link와 Code URL 추출
            # paper_link, code_url = scrape_project_page(project_url) if project_url else (None, None)

            # 저자 정보가 없으므로 기본값 설정
            authors = "Unknown Authors"
            paper_link, code_url = project_url, None
            # 디버깅용 출력
            print(f"Title: {title}, Authors: {authors}, Poster URL: {poster_url}, Paper Link: {paper_link}, Code URL: {code_url}")

            all_papers.append({
                'title': title,
                'authors': authors,
                'pdf_link': paper_link,
                'code_url': code_url
            })


    return all_papers