import sqlite3

# Connecting to sqlite ; if "hello.db" not exists, create "hello.db" file
conn = sqlite3.connect("hello.db")
print(conn)

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Doping HELLO table if already exists.
#cursor.execute("DROP TABLE IF EXISTS HELLO")

# Creating table as per requirement
sql = """
CREATE TABLE IF NOT EXISTS "HELLO" (
	"hello_no"	INTEGER PRIMARY KEY AUTOINCREMENT
	, "world"	TEXT UNIQUE
);"""

cursor.execute(sql)
print("Table created successfully.")

sql = """INSERT OR IGNORE INTO "HELLO" ( "world" ) VALUES ( 'TEST7' ); """
cursor.execute(sql)
hello_no = cursor.lastrowid
print(f"last hello_no = {hello_no}")


sql = """
SELECT
	hello_no
FROM "HELLO"
WHERE world = 'TEST'; """
cursor.execute(sql)
row = cursor.fetchone()
print(f"{row[0]=}")


#sql = """INSERT INTO "HELLO" ( "world" ) VALUES ( 'TEST' ); """
# sqlite3.IntegrityError: UNIQUE constraint failed: HELLO.world
# sql = """INSERT OR IGNORE INTO "HELLO" ( "world" ) VALUES ( 'TEST' ); """
sql = """INSERT INTO "HELLO" ( "world" )
SELECT 'TEST'
WHERE NOT EXISTS ( SELECT 1 FROM "HELLO" WHERE world = 'TEST' ) ; """
cursor.execute(sql)
hello_no = cursor.lastrowid
print(f"last hello_no = {hello_no}")

# Commit your changes in the database
conn.commit()

# Closing the connection
conn.close()
