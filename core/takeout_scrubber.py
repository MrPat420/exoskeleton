import os
import glob
import uuid
from datetime import datetime
from google import genai
from google.genai import types
from config.schemas import DS00Record
from core.ds00_state_engine import DS00Manager

class Scrubber:
    def __init__(self, raw_dir: str = "data/raw_takeout", api_key: str = None):
        self.raw_dir = raw_dir
        self.manager = DS00Manager()
        # Initializes SDK; automatically falls back to os.environ["GEMINI_API_KEY"] if None
        self.client = genai.Client(api_key=api_key)

    def chunk_content(self, content: str, max_chars: int = 500000) -> list[str]:
        return [content[i:i + max_chars] for i in range(0, len(content), max_chars)]

    def run(self):
        files = glob.glob(os.path.join(self.raw_dir, "**", "*.*"), recursive=True)
        target_files = [f for f in files if f.endswith(('.json', '.html', '.txt'))]

        for file_path in target_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self.chunk_content(content)
            
            for idx, chunk in enumerate(chunks):
                prompt = (
                    f"EXTRACT DROPPED BLUEPRINTS AND ARCHITECTURE FROM THIS RAW LOG CHUNK ({idx+1}/{len(chunks)}):\n\n"
                    f"{chunk}"
                )
                
                try:
                    response = self.client.models.generate_content(
                        model='gemini-3.7-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction="You are a data recovery scrubber. Output only structured RCA logic and blueprints.",
                            response_mime_type="application/json",
                            response_schema=DS00Record,
                            temperature=0.1
                        )
                    )
                    
                    record = DS00Record.model_validate_json(response.text)
                    
                    # Override volatile LLM fields with deterministic local state
                    record.record_id = f"TKO-{uuid.uuid4().hex[:8].upper()}"
                    record.timestamp = datetime.utcnow().isoformat() + "Z"
                    record.origin_source = os.path.basename(file_path)
                    if "chunk" not in record.technical_metadata:
                        record.technical_metadata.append(f"chunk_{idx}")
                        
                    self.manager.write_record(record)
                    
                except Exception as e:
                    print(f"[-] Scrubber Failure on {file_path} (Chunk {idx}): {str(e)}")
