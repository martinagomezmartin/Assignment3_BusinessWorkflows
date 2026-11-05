from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timezone

import sqlite3
import json

from pathlib import Path
from dotenv import load_dotenv
import os

from utils import pdf_to_markdown, summarize_paper

# Directory containing this Python file
BASE_DIR = Path(__file__).resolve().parent

# Load .env located in the parent directory
load_dotenv(str(BASE_DIR.parent / ".env"))

# Read all necessary env variables
DB_PATH = os.environ.get("PAPERS_DB_PATH", str(BASE_DIR.parent / "data/papers.db"))

DRIVE_DIRECTORY = os.environ.get("DRIVE_SYNC_DIR_PATH")
if not DRIVE_DIRECTORY:
  raise RuntimeError("Set DRIVE_SYNC_DIR_PATH in .env or the environment before running the DAG.")
DRIVE_DIRECTORY = Path(DRIVE_DIRECTORY).resolve()

LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gemma-4-e2b-it-qat")

def discover_new_papers_in_drive_sync_dir():
  """Find files that are not yet in the SQLite database."""

  directory = DRIVE_DIRECTORY / "papers"
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()

  cur.execute("SELECT filename FROM paper")
  processed = {row[0] for row in cur.fetchall()}

  conn.close()

  # List files in directory
  all_files = os.listdir(directory)

  # Only files not already in database
  new_files = [
      filename
      for filename in all_files 
      if (directory / filename).is_file() and filename not in processed
  ]

  return new_files

def process_new_paper(filename):
  """Process one file."""

  filepath = DRIVE_DIRECTORY / "papers" / filename

  # Call function to convert to MARKDOWN
  print(f"Calling function to convert Markdown on file: {filename}")
  markdown_contents = pdf_to_markdown(filepath)

  # Call function to extract metadata with local LLM
  print(f"Calling function to extract metadata with local LLM on file (mkdwn converted): {filename}")
  metadata_object = summarize_paper(LLM_MODEL_NAME, markdown_contents)

  # Store processed file in DB
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()

  cur.execute(
      "INSERT OR IGNORE INTO paper (filename, title, summary, keywords, category, reported) VALUES (?,?,?,?,?,?)",
      (
        filename,
        metadata_object["title"],
        metadata_object["summary"],
        json.dumps(metadata_object["keywords"]),
        metadata_object["category"],
        False,
      )
  )

  conn.commit()
  conn.close()

@dag(
  schedule="@daily",
  start_date=datetime(2025,1,1, tzinfo=timezone.utc),
  description="DAG to process new pdf papers from the library and send a summarized report through Discord.",
  tags=['INFO-H420','Group A3.3','Gómez Martín Martina','Holly i Miró Francesc','Zhao Jianli'],
  catchup=False,
  max_active_tasks=10,
)
def research_library_dag():
  # We need the reference to the task to use inside next task's .expand, so can't use the @task decorator
  scan_task = PythonOperator(
    task_id="scan_and_find_new_files",
    python_callable=discover_new_papers_in_drive_sync_dir,
  )

  process_tasks = PythonOperator.partial(
    task_id="process_file",
    python_callable=process_new_paper,
  ).expand(
    op_args=scan_task.output.map(lambda filename: [filename])
  )

  @task(trigger_rule="none_failed")
  def output_static_html_report():
    """Regenerate the static html file with all papers in the library, not just the new ones."""

    directory = DRIVE_DIRECTORY / "output"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    all_papers = cur.execute("SELECT filename, title, summary, keywords, category FROM paper")

    # TODO: Build static html library... (replace the following placeholder, apply some sorting/filtering options).
    print(f"Building static html library for all entries: {[p[0] for p in all_papers]}")
    output_html_content = """<body>
    <h1>Here should go the library for all the papers:</h1>
    <ul>
    """ + '\n'.join(['<li>' + p[0] + '</li>' for p in all_papers]) + """
    </ul>
    </body>"""

    with open(f"{directory}/index.html", "w") as output_file:
      output_file.write(output_html_content)

    conn.close()

  @task(trigger_rule="none_failed")
  def send_discord_report():
    """Report on all new files through Discord."""

    # Read all new "unreported" entries from paper DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    unreported = cur.execute("SELECT filename, title, summary, keywords, category FROM paper WHERE NOT reported")
    unreported_filenames = [e[0] for e in unreported]

    # TODO: Send new processed file list through Discord message...
    print(f"Reporting on {unreported_filenames} through Discord...")

    cur.executemany(
        "UPDATE paper SET reported = true WHERE filename = ?",
        [(filename,) for filename in unreported_filenames],
    )
  
    conn.commit()
    conn.close()

  scan_task >> process_tasks
  process_tasks >> output_static_html_report()
  process_tasks >> send_discord_report()

research_library_dag()