import sqlite3

# Connecting to sqlite ; if "hello.db" not exists, create "hello.db" file
conn = sqlite3.connect("hello.db")
print(conn)

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Inserting table new record
sql = """
INSERT INTO "HELLO" VALUES ( 'Hello World!' );"""

cursor.execute(sql)
print("Inserted successfully.")

# Commit your changes in the database
conn.commit()

# Closing the connection
conn.close()
