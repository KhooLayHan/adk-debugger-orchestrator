import datetime
import os

import uuid
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables from .env.local
load_dotenv(dotenv_path="./.env.local")

# --- Configuration (ensure these env vars are set!) ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    # Fallback to gcloud config if .env.local is not set or is not primary
    PROJECT_ID = os.popen("gcloud config get-value project").read().strip()

    if not PROJECT_ID:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set and gcloud project config is not found.")

BIGQUERY_DATASET = "adk_traces"
BIGQUERY_TABLE = "agent_events"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID)
table_ref = bq_client.dataset(BIGQUERY_DATASET).table(BIGQUERY_TABLE)

print(f"Attempting to log to BigQuery table: {PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}")


def log_test_event(event_type, agent_id, summary):
    event_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_id": str(uuid.uuid4()),  # New unique trace_id for each test
        "event_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "event_type": event_type,
        "message_summary": summary,
        "details": f"Test run from {agent_id} at {datetime.datetime.now()}",
    }
    try:
        errors = bq_client.insert_rows_json(table_ref, [event_data])
        if errors:
            print(f"BigQuery insert errors: {errors}")
            return False
        else:
            print(f"Successfully logged event: {summary}")
            return True
    except Exception as e:
        print(f"Error logging to BigQuery: {e}")
        print("Please ensure your Google Cloud credentials are set up (`gcloud auth application-default login`)")
        print(
            f"Also check if the BigQuery API is enabled for project '{PROJECT_ID}' and the service account has 'BigQuery Data Editor' role on the dataset."
        )
        return False


if __name__ == "__main__":
    print("Running BigQuery logging test...")
    success = log_test_event("TEST_EVENT", "TestAgent", "Hello from the debugger setup!")
    if success:
        print("\nCheck your BigQuery console in the 'adk_traces.agent_events' table. You should see a new row!")
    else:
        print(
            "\nLogging failed. Please check your environment variables, BigQuery API enablement, and IAM permissions."
        )
