import sqlite3
from glob import glob

# :one: 병합할 DB 파일들을 찾기
db_files = glob("*.db")  # 현재 디렉토리에서 .db 확장자 파일 찾기
output_db = "final_merged_database.db"  # 병합될 최종 DB 파일명
table_name = "Conference"  # 병합할 테이블 이름 (테이블 구조가 동일해야 함)

def initialize_output_db():
    """최종 병합될 DB 생성 및 테이블 구조 복사"""
    conn_out = sqlite3.connect(output_db)
    cursor_out = conn_out.cursor()
    # 첫 번째 DB를 참조하여 테이블 구조 복사
    if db_files:
        conn_in = sqlite3.connect(db_files[0])
        cursor_in = conn_in.cursor()
        # 테이블 구조 가져오기
        cursor_in.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        create_table_sql = cursor_in.fetchone()
        if create_table_sql:
            cursor_out.execute(create_table_sql[0])  # 테이블 생성
            print(f":white_check_mark: '{table_name}' 테이블이 '{output_db}'에 생성됨.")
        conn_in.close()
    conn_out.commit()
    conn_out.close()
    
def merge_databases():
    """각 DB에서 데이터를 읽어 최종 DB로 병합 (중복 제거 없이, id 재생성)"""
    conn_out = sqlite3.connect(output_db)
    cursor_out = conn_out.cursor()
    total_records = 0  # 병합된 총 데이터 개수
    for db_file in db_files:
        if db_file == output_db:
            continue  # 출력 DB는 병합 대상에서 제외
        conn_in = sqlite3.connect(db_file)
        cursor_in = conn_in.cursor()
        # 현재 DB의 데이터 개수 확인
        cursor_in.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor_in.fetchone()[0]
        print(f":pushpin: '{db_file}'에서 가져온 데이터 개수: {row_count} 개")
        cursor_in.execute(f"SELECT * FROM {table_name};")
        rows = cursor_in.fetchall()
        for row in rows:
            cursor_out.execute(f"""
                INSERT INTO {table_name} (Title, Author, PDF_Link, Code_URL, Conference_Name)
                VALUES (?, ?, ?, ?, ?);
            """, row[1:])  # 'id' 값을 제외하고 삽입 (새로운 id 자동 생성)
        total_records += row_count  # 총 개수 업데이트
        conn_in.close()
    conn_out.commit()
    # 최종 병합된 DB 데이터 개수 확인
    cursor_out.execute(f"SELECT COUNT(*) FROM {table_name};")
    merged_count = cursor_out.fetchone()[0]
    conn_out.close()
    print(f"\n:white_check_mark: 모든 DB가 '{output_db}'로 병합 완료! (중복 제거 없음)")
    print(f":bar_chart: 병합 전 데이터 개수 합산: {total_records} 개")
    print(f":bar_chart: 병합 후 총 데이터 개수: {merged_count} 개")
# 실행
initialize_output_db()
merge_databases()