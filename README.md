# Local Airflow DAG to extract metadata and report on a Google Drive synced research paper library's files

This project uses Airflow **3.1.0** and Python **3.10**. For local DAG execution, use
`airflow standalone`, which also starts the scheduler, DAG processor, and
triggerer.

## Install

From the project root:

```bash
# Create a python virtual environment.
python3 -m venv .venv
```

Then: 

```bash
# Activate it and install dependencies.
source .venv/bin/activate
python -m pip install -r requirements.txt \
  --constraint https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.10.txt
python -m pip check
```

## Start the server

Set `DRIVE_SYNC_DIR_PATH` in `.env` to an existing directory containing your
papers. Relative paths are interpreted relative to the project root.

```bash
bash run_airflow.sh
```

The launcher uses the project virtual environment, initializes the
paper database, and starts all Airflow components.
It refuses to start if another launcher holds the same Airflow-home lock or
port 8080 is occupied. Always use this launcher instead of starting another
`airflow standalone` directly.
The UI is at <http://localhost:8080>. On a remote VS Code connection, forward
port 8080 using the Ports panel.

Log in as `admin` using the generated password shown in the startup terminal.
If you didn't see it, passwords are also stored locally in
`.airflow/simple_auth_manager_passwords.json.generated`, so you can find it there. 
Stop a foreground server with Ctrl+C. If ran detached you might need to send an interrupt signal to the process:

```bash
ps -a # Will list all PIDs.
kill -INT <pid> # With the correct PID.
```

Open `research_library_dag`, unpause it, and select **Trigger DAG**. The DAG
discovers new filenames, maps one processing task per file, and marks reported
papers in SQLite. Subsequent runs skip already processed files. The report task
also runs when there are no new files.
