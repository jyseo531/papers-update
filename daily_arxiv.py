#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   daily_arxiv.py
@Time    :   2021-10-29 22:34:09
@Author  :   Bingjie Yan
@Email   :   bj.yan.pa@qq.com
@License :   Apache License 2.0
"""


import datetime
import requests
import json
import arxiv
import os
import shutil
import yaml
import time
import random
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from config import (
    SERVER_PATH_TOPIC,
    SERVER_DIR_STORAGE,
    SERVER_PATH_README,
    SERVER_PATH_DOCS,
    SERVER_DIR_HISTORY,
    SERVER_PATH_STORAGE_MD,
    TIME_ZONE_KR,
    logger,
)

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


def get_yaml_data(yaml_file: str):
    fs = open(yaml_file)
    data = yaml.load(fs, Loader=Loader)
    print(data)
    return data


def get_daily_papers(topic: str, query: str = "slam", max_results=2):
    # output
    content = dict()

    # content
    output = dict()

    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    cnt = 0

    for result in search_engine.results():

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id

        code_url = base_url + paper_id
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()

        print("Time = ", publish_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        try:
            r = requests.get(code_url).json()
            # source code link
            if "official" in r and r["official"]:
                cnt += 1
                repo_url = r["official"]["url"]
                content[
                    paper_key] = f"|**{publish_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|**[link]({repo_url})**|\n"
            else:
                content[
                    paper_key] = f"|**{publish_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|null|\n"

        except Exception as e:
            print(f"exception: {e} with id: {paper_key}")

    data = {topic: content}
    return data


def update_json_file(filename, data):
    with open(filename, "r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)

    json_data = m.copy()

    # update papers in each keywords
    for topic in data.keys():
        if not topic in json_data.keys():
            json_data[topic] = {}
        for subtopic in data[topic].keys():
            papers = data[topic][subtopic]

            if subtopic in json_data[topic].keys():
                json_data[topic][subtopic].update(papers)
            else:
                json_data[topic][subtopic] = papers

    with open(filename, "w") as f:
        json.dump(json_data, f)


# 2025-02-20 test
import os
import json
import shutil
import datetime
def json_to_md(filename, to_web=False):
    """
    JSON 데이터를 Markdown 파일로 변환하여 저장
    """

    DateNow = datetime.date.today().strftime("%Y.%m.%d")

    # arxiv-daily 폴더 생성
    arxiv_daily_path = os.path.join("docs", "arxiv-daily")
    os.makedirs(arxiv_daily_path, exist_ok=True)

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
        data = json.loads(content) if content else {}

    if not to_web:
        md_filename = os.path.join(arxiv_daily_path, "README.md")

        # clean README.md if it already exists
        with open(md_filename, "w+", encoding="utf-8") as f:
            f.write(f"## Updated on {DateNow}\n\n")
            f.write("> Welcome to contribute! Add your topics and keywords in `topic.yml`\n\n")

            for topic, subtopics in data.items():
                f.write(f"## {topic}\n\n")
                for subtopic, papers in subtopics.items():
                    if not papers:
                        continue

                    f.write(f"### {subtopic}\n\n")
                    f.write("| Publish Date | Title | Authors | PDF | Code |\n")
                    f.write("|-------------|----------------|-------------|------|------|\n")

                    sorted_papers = sort_papers(papers)

                    for _, v in sorted_papers.items():
                        if isinstance(v, dict):  # Markdown 형식으로 변환
                            publish_date = v.get("publish_date", "N/A")
                            title = v.get("title", "N/A")
                            authors = ", ".join(v.get("authors", [])) if isinstance(v.get("authors"), list) else v.get("authors", "N/A")
                            pdf_link = f"[PDF]({v.get('pdf', '#')})" if v.get("pdf") else "N/A"
                            code_link = f"[Code]({v.get('code', '#')})" if v.get("code") else "N/A"

                            f.write(f"| {publish_date} | {title} | {authors} | {pdf_link} | {code_link} |\n")
                        elif isinstance(v, str):
                            f.write(v)

                    f.write("\n")

    else:
        # 기존 docs/arxiv-daily 폴더 삭제 후 다시 생성
        if os.path.exists(arxiv_daily_path):
            shutil.rmtree(arxiv_daily_path)
        os.makedirs(arxiv_daily_path, exist_ok=True)

        md_indexname = os.path.join(arxiv_daily_path, "index.md")
        with open(md_indexname, "w+", encoding="utf-8") as f_index:
            f_index.write("# arxiv-daily\n\n")

            for topic, subtopics in data.items():
                topic_path = os.path.join(arxiv_daily_path, topic)
                os.makedirs(topic_path, exist_ok=True)  # topic 폴더 생성

                topic_indexname = os.path.join(topic_path, "index.md")
                with open(topic_indexname, "w+", encoding="utf-8") as f_topic_index:
                    f_topic_index.write(f"# {topic}\n\n")

                # index.md에 topic 추가
                f_index.write(f"- [{topic}](./{topic}/index.md)\n")

                for subtopic, papers in subtopics.items():
                    if not papers:
                        continue

                    md_filename = os.path.join(topic_path, f"{subtopic}.md")

                    with open(md_filename, "w+", encoding="utf-8") as f:
                        f.write(f"# {subtopic}\n\n")
                        f.write("| Publish Date | Title | Authors | PDF | Code |\n")
                        f.write("|-------------|----------------|-------------|------|------|\n")

                        sorted_papers = sort_papers(papers)

                        for _, v in sorted_papers.items():
                            if isinstance(v, dict):
                                publish_date = v.get("publish_date", "N/A")
                                title = v.get("title", "N/A")
                                authors = ", ".join(v.get("authors", [])) if isinstance(v.get("authors"), list) else v.get("authors", "N/A")
                                pdf_link = f"[PDF]({v.get('pdf', '#')})" if v.get("pdf") else "N/A"
                                code_link = f"[Code]({v.get('code', '#')})" if v.get("code") else "N/A"

                                f.write(f"| {publish_date} | {title} | {authors} | {pdf_link} | {code_link} |\n")
                            elif isinstance(v, str):
                                f.write(v)

                        f.write("\n")

                    # topic index에 subtopic 추가
                    with open(topic_indexname, "a+", encoding="utf-8") as f_topic_index:
                        f_topic_index.write(f"- [{subtopic}](./{subtopic}.md)\n")

    print("Markdown file generation finished.")



if __name__ == "__main__":

    data_collector = dict()

    yaml_path = "./database/topic.yml"
    yaml_data = get_yaml_data(yaml_path)

    # print(yaml_data)

    keywords = dict(yaml_data)

    for topic in keywords.keys():
        for subtopic, keyword in dict(keywords[topic]).items():

            # topic = keyword.replace("\"","")
            print("Keyword: " + subtopic)
            try:
                data = get_daily_papers(
                    subtopic, query=keyword, max_results=10)
            except:
                print(f'CANNOT get {subtopic} data from arxiv')
                data = None
            # time.sleep(random.randint(2, 10))

            if not topic in data_collector.keys():
                data_collector[topic] = {}

            if data:
                data_collector[topic].update(data)

            print(data)
            # print(data_collector)

            print("\n")

    print(data_collector)
    # update README.md file
    json_file = "arxiv-daily.json"
    
 #1️⃣ 파일이 없으면 생성하고 빈 JSON 구조로 초기화
if not os.path.exists(json_file):
    with open(json_file, "w") as f:
        json.dump({}, f)  # 빈 JSON 객체 저장
    print(f"📂 {json_file} 파일을 새로 생성했습니다.")

    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file)

    # json data to markdown
    json_to_md(json_file, to_web=True)

