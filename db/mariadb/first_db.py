# pip install psycopg2

import configparser
import psycopg2
import sys


user = None
password = None
host_ip = None
dbname = None
port = None
data_check_minute = 20 # 센서 데이터 수집 확인 기준 시간 (분)

# 데이터베이스 연결 정보 읽어오기
config = configparser.ConfigParser()
config.read('db/mariadb/postgres.ini', encoding="UTF-8")

data_check_minute = config.get('OPTION', 'data_check_minute', fallback = data_check_minute)

if 'DB' in config: # check 'DB' section
	# don't care : 'DB' section or db info option not exists, default value = None
	user = config.get('DB', 'user', fallback = None) 
	password = config.get('DB', 'password', fallback = None) 
	host_ip = config.get('DB', 'host_ip', fallback = None) 
	dbname = config.get('DB', 'dbname', fallback = None) 
	port = config.get('DB', 'port', fallback = None) 
else:
	print(f'Error: postgres.ini has no DB section!')
	sys.exit(1)

# 데이터베이스 연결 정보 누락 확인
if user == None or password == None or host_ip == None or dbname == None or port == None:
	print(f'Error: postgres.ini has no DB info option!')
	sys.exit(2)

connection_string = "dbname={dbname} user={user} host={host} password={password} port={port}"\
					.format(dbname=dbname,
							user=user,
							host=host_ip,
							password=password,
							port=port)    
try:
	dbconn = psycopg2.connect(connection_string)
except psycopg2.DatabaseError as e:
	print(f'Error: {e}')
	sys.exit(2)

dbcur = dbconn.cursor()

# 데이터 조회 쿼리
query = f"""
SELECT
	monitor_name, sensor_id, sensor_type
	, ( SELECT MAX(reg_dt) FROM dts_sensor_data WHERE LEFT(sensor_seq, CHAR_LENGTH(sensor_seq) - 1) = M.sensor_id )
FROM MONITOR_ITEM AS M
WHERE 1 = 1
	AND NOT EXISTS (
		SELECT
			LEFT(sensor_seq, CHAR_LENGTH(sensor_seq) - 1) AS sensor_id
			, CASE RIGHT(sensor_seq, 1) WHEN '4' THEN '4' WHEN '9' THEN '4' ELSE '0' END AS sensor_type
			, COUNT(*) AS data_count
		FROM dts_sensor_data
		WHERE 1 = 1
			AND reg_dt > CURRENT_TIMESTAMP + '-{data_check_minute} minutes'
			AND LEFT(sensor_seq, CHAR_LENGTH(sensor_seq) - 1) = M.sensor_id
			AND CASE RIGHT(sensor_seq, 1) WHEN '4' THEN '4' WHEN '9' THEN '4' ELSE '0' END = M.sensor_type
		GROUP BY LEFT(sensor_seq, CHAR_LENGTH(sensor_seq) - 1), CASE RIGHT(sensor_seq, 1) WHEN '4' THEN '4' WHEN '9' THEN '4' ELSE '0' END
	)
"""

# 쿼리 조회
dbcur.execute(query)
msg = f"최근 {data_check_minute}분 동안 수집되지 않는 센서 목록:\n\n"
count = 0
while True:
	row = dbcur.fetchone()
	if row == None:
		break

	msg += f"{row[0]} 최종 수집 시각 : {row[3]}\n"
	count += 1

if count > 1:
	print(msg)
else:
	print(f"최근 {data_check_minute}분 동안 센서 데이터 수집 정상")
	
dbconn.close()
