import sys
import sqlite3
from pathlib import Path
import os

def main(rebuild):
  db_path = Path(os.environ.get("PAPERS_DB_PATH", str(Path(__file__).resolve().parent / "data/papers.db")))
  db_path.parent.mkdir(parents=True, exist_ok=True)
  con = sqlite3.connect(db_path)
  cur = con.cursor()

  if rebuild:
    # Clean the whole database so that tables are re-created
    cur.execute("DROP TABLE IF EXISTS paper")

  # keywords actually contains a json structured text: '["keyword_1", ..., "keyword_n"]'
  cur.execute("""
CREATE TABLE IF NOT EXISTS paper(
  filename TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  keywords TEXT NOT NULL,
  category TEXT NOT NULL,
  reported INTEGER NOT NULL DEFAULT 0
);""")

  res = cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
  tables = res.fetchall()

  print(f"Schema created with tables: {', '.join([t[0] for t in tables])}")
  con.close()

if __name__ == '__main__':
  if ('--help' in sys.argv):
    print('Use --rebuild if you want to rebuild all tables. WARNING: It clears all data.')

  rebuild = '--rebuild' in sys.argv[1:]
  main(rebuild)