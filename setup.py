import sqlite3

con = sqlite3.connect("data/papers.db")
cur = con.cursor()

# keywords actually contains a json structured text: '["keyword_1", ..., "keyword_n"]'
cur.execute("""
CREATE TABLE IF NOT EXISTS paper(
  filename TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  keywords TEXT NOT NULL,
  category TEXT NOT NULL
);
""")

print("Table 'paper' created!")