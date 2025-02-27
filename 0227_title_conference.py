import pandas as pd
import sqlite3

# 컨퍼런스 마크다운 파일 읽기 (수동 파싱)
conference_data = []
current_conference = None

with open("./database/db_markdown/merged_conference_2020-2024_test.md", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        # 컨퍼런스 정보 파싱 (## 로 시작하는 라인)
        if line.startswith("## "):
            current_conference = line[3:].strip()  # "## " 제거 후 저장
        elif "|" in line and not line.startswith("|---"):  # 테이블 데이터 감지
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and current_conference:  # 최소한 제목이 있는지 확인
                title = parts[1]  # 테이블에서 1번째 열 (Title)
                if title.lower() != "title":  # 첫 번째 행이 헤더인지 확인
                    conference_data.append([title, current_conference])  # Title, Conference 저장

# 컨퍼런스 데이터프레임 생성
conference_df = pd.DataFrame(conference_data, columns=["Title", "Conference"])

# DB 연결
db_path = "./arxiv_star_test_2020_star_framework_0227.db"
conn = sqlite3.connect(db_path)

# 테이블 읽어오기 (테이블 이름 확인 후 변경)
table_name = "papers"  # 실제 테이블 이름으로 변경해야 함
db_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

# Conference 열 추가 (초기값 None)
db_df["Conference"] = None

# Title 기준으로 병합하여 Conference 정보 추가
db_df = db_df.merge(conference_df[["Title", "Conference"]], left_on="title", right_on="Title", how="left")

# 불필요한 Title(중복 컬럼) 삭제
db_df.drop(columns=["Title"], inplace=True)

# 결과 확인
# Conference_x 제거하고 Conference_y를 Conference로 변경
db_df.drop(columns=["Conference_x"], inplace=True)
db_df.rename(columns={"Conference_y": "Conference"}, inplace=True)

# 최종 결과 확인
print(db_df.head())

# 변경된 데이터프레임을 다시 DB에 저장 (기존 테이블 덮어쓰기)
db_df.to_sql(table_name, conn, if_exists="replace", index=False)

# 변경 사항 저장
conn.commit()
conn.close()

print("Database updated successfully.")
