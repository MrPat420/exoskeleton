import os
import sys

# FORCE ROOT: This moves the script into the exoskeleton directory immediately
os.chdir(os.path.expanduser("~/exoskeleton"))

import uuid
from datetime import datetime, timezone
from google import genai
from google.genai import types
from config.schemas import DS00Record
from core.ds00_state_engine import DS00Manager

def ingest_cli_thought(raw_text: str):
    print("[*] Processing Local CLI Ingress...")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    manager = DS00Manager()

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=f"Extract this technical thought into strict RCA schemas:\n{raw_text}",
        config=types.GenerateContentConfig(
            system_instruction="Extract core engineering logic into strict RCA JSON schemas.",
            response_mime_type="application/json",
            response_schema=DS00Record,
            temperature=0.1
        )
    )

    record = DS00Record.model_validate_json(response.text)
    record.record_id = f"CLI-{uuid.uuid4().hex[:8].upper()}"
    record.timestamp = datetime.now(timezone.utc).isoformat()
    record.origin_source = "Local_CLI_Ingress"
    
    filepath = manager.write_record(record)
    manager.sync_state(f"AUTO-SYNC: CLI Ingress {record.record_id}")
    print(f"[+] SUCCESS. Committed to: {filepath}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        thought = " ".join(sys.argv[1:])
        ingest_cli_thought(thought)
