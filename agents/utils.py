import datetime
import os

import uuid
from dotenv import load_dotenv
from google import genai
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
        event_type (str): The type of the event (e.g., "AGENT_START", "MESSAGE_SEND", "TASK_COMPLETE", "ERROR").
        agent_id (str): The unique identifier of the agent logging the event.
        trace_id (str): A unique ID for the entire multi-agent workflow session.
        message_summary (str, optional): A brief summary of the event or message. Defaults to None.
        source_agent_id (str, optional): The ID of the agent that initiated the message/event. Defaults to None.
        target_agent_id (str, optional): The ID of the agent that is the recipient of the message/event. Defaults to None.
        duration_ms (int, optional): The duration of an operation in milliseconds. Defaults to None.
        status (str, optional): The status of a event or task (e.g. "SUCCESS", "FAILURE"). Defaults to None.
        details (dict, optional): A dictionary of additional structured details for the event. Defaults to None.
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
        ),  # Store dict as string for BigQuery STRING type
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
# Initialize the GenAI client, specifying Vertex AI usage with project and location
# This client abstracts the model interaction
try:
    # Use Vertex AI specific client initialization
    genai_client = genai.Client(project=PROJECT_ID, location=LOCATION, vertexai=True)

    # Get the GenerativeModel instance via the client's model attribute
    llm_model = genai_client.models.get("gemini-2.0-pro")

    print(
        f"Utils loaded. Project: {PROJECT_ID}, Location: {LOCATION}, LLM: {llm_model.name}"
    )
except Exception as e:
    print(f"Error: Could not initialize google-genai client or model: {e}")
    print(
        "Ensure GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are correctly set, and that the service account used has 'Vertex AI User' role."
    )

    llm_model = None  # Set to None so agents will fail gracefully or be handled
