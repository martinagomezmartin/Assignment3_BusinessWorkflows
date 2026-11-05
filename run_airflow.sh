#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

export PATH="$PWD/.venv/bin:$PATH"
export AIRFLOW_HOME="${AIRFLOW_HOME:-$PWD/.airflow}"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__PARALLELISM=2
export AIRFLOW__API__HOST=127.0.0.1
export AIRFLOW__API__PORT=8080
export AIRFLOW__API__WORKERS=1

# Add a lock file to make sure you don't have two instance of airflow running that can cause issues.
mkdir -p "$AIRFLOW_HOME"
exec 9>"$AIRFLOW_HOME/standalone.lock"
if ! flock -n 9; then
  echo "Airflow is already running for AIRFLOW_HOME=$AIRFLOW_HOME. Stop it before restarting." >&2
  exit 1
fi

.venv/bin/python setup.py
exec .venv/bin/airflow standalone
