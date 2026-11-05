import sys
import sqlite3
from pathlib import Path
import os

def main():
  db_path = Path(os.environ.get("PAPERS_DB_PATH", str(Path(__file__).resolve().parent / "data/papers.db")))
  db_path.parent.mkdir(parents=True, exist_ok=True)
  con = sqlite3.connect(db_path)
  cur = con.cursor()

  res = cur.execute("SELECT * FROM paper;")
  entries = res.fetchall()
  print(f"Entires: {entries}")
  con.close()

if __name__ == '__main__':
  main()