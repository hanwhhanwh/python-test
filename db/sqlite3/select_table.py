import sqlite3

# Connecting to sqlite ; if "hello.db" not exists, create "hello.db" file
conn = sqlite3.connect("hello.db")
print(conn)

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

sql = """
SELECT * FROM "HELLO";"""

# Retrieving data
cursor.execute(sql)

# Fetching 1st row from the table
result = cursor.fetchone()
print(result)

cursor.execute(sql)
# Fetching ALL rows from the table
result = cursor.fetchall()
print(result)

# Closing the connection
conn.close()
