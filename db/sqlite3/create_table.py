import sqlite3

# Connecting to sqlite ; if "hello.db" not exists, create "hello.db" file
conn = sqlite3.connect("hello.db")
print(conn)

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Doping HELLO table if already exists.
cursor.execute("DROP TABLE IF EXISTS HELLO")

# Creating table as per requirement
sql = """
CREATE TABLE "HELLO" (
	"world"	TEXT
);"""

cursor.execute(sql)
print("Table created successfully.")

# Commit your changes in the database
conn.commit()

# Closing the connection
conn.close()
