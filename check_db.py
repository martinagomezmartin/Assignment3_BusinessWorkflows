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

  print()
  header = ['Filename', 'Title', 'Summary', 'Keywords', 'Category']
  rows = [header] + [5*[15*'-']] + [[f, t, s, k.count('", "'), c] for (f, t, s, k, c, _) in entries]
  print('|\n'.join([''.join(['| {:16}'.format(
    str(x) if type(x) == int else
    x if len(x) < 16 
    else x[:13] + '...'
  ) for x in r]) for r in rows]) + '|')
  print()
  con.close()

if __name__ == '__main__':
  main()