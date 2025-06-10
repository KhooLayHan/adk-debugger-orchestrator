import datetime
import os

import uuid
from dotenv import load_dotenv
from google.adk.llms.vertex_ai import VertexAILLM
from google.cloud import bigquery

# Load environment variables from .env.local
load_dotenv(dotenv_path="./.env.local")

# --- Configuration from environment variables ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    # Fallback to gcloud config if .env.local is not set or is not primary, else raise Error
    PROJECT_ID = os.popen("gcloud config get-value project").read().strip()
    if not PROJECT_ID:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable is not set and gcloud project config is not found."
        )

LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Ensure Vertex AI is used for GenAI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

# --- BigQuery configuration ---
BIGQUERY_DATASET = "adk_traces"
BIGQUERY_TABLE = "agent_events"

# --- Initialize BigQuery client ---
bq_client = bigquery.Client(project=PROJECT_ID)
table_ref = bq_client.dataset(BIGQUERY_DATASET).table(BIGQUERY_TABLE)


# --- Logging Utility Function ---
async def log_agent_event(
    event_type: str,
    agent_id: str,
    trace_id: str,
    message_summary: str = None,
    source_agent_id: str = None,
    target_agent_id: str = None,
    duration_ms: int = None,
    status: str = None,
    details: dict = None,
):
    """
    Logs an event to the BigQuery agent_events table.

    Args:
        event_type (str): Type of the event (e.g., "AGENT_START", "MESSAGE_SENT", "TASK_COMPLETE", "ERROR").
        agent_id (str): ID of the agent performing/receiving the event.
        trace_id (str): Unique ID for a multi-agent workflow run.
        message_summary (str, optional): A short summary of the message content or task. Defaults to None.
        source_agent_id (str, optional): ID of the sending agents (for message events). Defaults to None.
        target_agent_id (str, optional): ID of the receiving agents (for message events). Defaults to None.
        duration_ms (int, optional): Duration of the task in milliseconds. Defaults to None.
        status (str, optional): Status of an event/task. Defaults to None.
        details (dict, optional): JSON string for additional event details. Defaults to None.
    """

    event_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "event_type": event_type,
        "message_summary": message_summary,
        "source_agent_id": source_agent_id,
        "target_agent_id": target_agent_id,
        "duration_ms": duration_ms,
        "status": status,
        "details": (
            str(details) if details else None
        ),  # Store dict as string, BigQuery STRING type
    }

    try:
        errors = bq_client.insert_rows_json(table_ref, [event_data])
        if errors:
            print(f"BigQuery insert errors for {agent_id} ({event_type}): {errors}")
            # Optionally raise an exception or handle more robustly
        # else:
        #     print(f"Logged event from {agent_id}: {event_type} - {message_summary}")
    except Exception as e:
        print(f"CRITICAL ERROR logging to BigQuery for {agent_id} ({event_type}): {e}")
        # * FUTURE: Preferably use a robust error handling mechanism in production.


# --- LLM Instance Initialization ---
llm = VertexAILLM(
    project_id=PROJECT_ID,
    location=LOCATION,
    model_name="gemini-2.0-flash",  # Or "gemini-1.5-pro", "gemini-2.0-flash-001", etc.
)

print(
    f"Utils loaded. Project: {PROJECT_ID}, Location: {LOCATION}, LLM: {llm.model_name}"
)
