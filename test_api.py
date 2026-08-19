import os
import uuid
from datetime import datetime, timezone
from google import genai
from google.genai import types
from config.schemas import DS00Record
from core.ds00_state_engine import DS00Manager

print("[*] Initiating Live Gemini API Hook Test...")

try:
    # 1. Initialize Client (Pulls GEMINI_API_KEY from environment)
    client = genai.Client()
    
    # 2. The Chaotic Wetware Dump (Simulating a raw thought)
    raw_thought = """
    I'm trying to SSH into the Kali box from my Spin 714 Chromebook and it's 
    throwing a connection refused error. I bet the SSH daemon crashed or didn't 
    start on boot. I need to run systemctl status ssh on Kali, and if that's up, 
    check if UFW is blocking port 22.
    """
    
    print("[*] Transmitting to Gemini 3.7 Flash. Forcing Schema Lock...")
    
    # 3. The API Call with Strict Pydantic Enforcement
    response = client.models.generate_content(
        model='gemini-3.7-flash',
        contents=f"Extract this wetware dump into our structural matrix:\n{raw_thought}",
        config=types.GenerateContentConfig(
            system_instruction="You are the Cognitive Exoskeleton. Output only structured RCA logic.",
            response_mime_type="application/json",
            response_schema=DS00Record,
            temperature=0.1
        )
    )
    
    # 4. Validate and Process the JSON Payload
    record = DS00Record.model_validate_json(response.text)
    
    # Override volatile metadata
    record.record_id = f"API-{uuid.uuid4().hex[:8].upper()}"
    record.timestamp = datetime.now(timezone.utc).isoformat()
    record.origin_source = "Live_API_Test"
    
    # 5. Write to DS-00 Memory Substrate
    manager = DS00Manager(memory_dir="data/ds00_memory")
    saved_path = manager.write_record(record)
    
    print(f"[+] API HOOK SUCCESS! Record written to: {saved_path}")

except Exception as e:
    print(f"[-] API HOOK FAILED. Error: {str(e)}")
