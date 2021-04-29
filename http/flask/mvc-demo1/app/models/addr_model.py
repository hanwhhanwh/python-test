# addr model file
# made : hbesthee@naver.com
# date : 2021-04-26

from app.models import connect_database


""" 주소 목록을 반환합니다.
\param addr_no 시/도 고유번호 (예: 서울특별시 = 11000)

"addr_no" 매개변수가 None 이면, 시/도 목록을 반환하고,
"addr_no" 매개변수에 시/도에 대한 고유번호이면, 입력한 시/도에 대한 시/군/구 목록을 반환합니다.
"""
def get_addr(addr_no):
    qr_code_no = 1 # 세션 정보로 변경 필요함
    database = connect_database()
    if database == None:
        # 데이터베이스 연결 실패 오류 처리 필요
        return None

    connection = database.raw_connection()
    cursor = connection.cursor() # get DISPENSER_V2 mariadb cursor
    query = ""
    if addr_no == 0:
        query = f"""
INSERT INTO QR_HISTORY ( qr_code_no, reg_date, query_count, visit_count )
VALUES ( {qr_code_no}, DATE_FORMAT(NOW(), '%Y-%m-%d %H:00'), 1, 0)
ON DUPLICATE KEY UPDATE
    query_count = query_count + 1
;
        """
        print(query)
        cursor.execute(query)
        connection.commit()

    query = f"""
SELECT
    addr_no
    , addr_name
FROM ADDR_LEVEL2
WHERE 1 = 1
    AND parent_addr_no = {addr_no}
        """

    cursor.execute(query)
    rows = cursor.fetchall()
#    print(rows)

    return rows

