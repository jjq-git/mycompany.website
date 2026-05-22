import sqlite3
conn = sqlite3.connect('instance/app.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())
# Also check site table
try:
    cur.execute("SELECT id, slug, template_name FROM site")
    print("Sites:", cur.fetchall()[:5])
except Exception as e:
    print("Site error:", e)
# Check users
try:
    cur.execute("SELECT id, email FROM user")
    print("Users:", cur.fetchall()[:5])
except Exception as e:
    print("User error:", e)
conn.close()
