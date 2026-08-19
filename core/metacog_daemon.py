import os
import json
import glob
import shutil
import uuid
from datetime import datetime
from google import genai
from google.genai import types

from config.schemas import DS00Record, EnforcedScaffoldResponse, MarkdownTable, RCALogic
from core.ds00_state_engine import DS00Manager

class MetacogDaemon:
    def __init__(self, api_key: str = None):
        """Initializes the Sleep-State Metacognitive Engine."""
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.manager = DS00Manager()
        
        self.inbox_dir = "data/ds00_memory/inbox"
        self.l2_dir = "data/ds00_memory/l2_episodic"
        self.wiki_dir = "data/wiki_llm"
        self.graph_path = "data/ds00_memory/temporal_graph.json"
        
        # Ensure architectural substrate exists
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.l2_dir, exist_ok=True)
        os.makedirs(self.wiki_dir, exist_ok=True)
        
        if not os.path.exists(self.graph_path):
            with open(self.graph_path, "w", encoding="utf-8") as f:
                json.dump({"edges": []}, f)

    def _get_temporal_graph_schema(self) -> dict:
        """Strict JSON Schema to prevent Pydantic $ref validation crashes."""
        return {
            "type": "OBJECT",
            "properties": {
                "edges": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "source_node_id": {"type": "STRING", "description": "L1 Record ID"},
                            "target_entity": {"type": "STRING", "description": "WikiLLM concept/node"},
                            "relationship": {"type": "STRING", "description": "SUPERSEDES, EXTENDS, CONTRADICTS"},
                            "valid_from": {"type": "STRING", "description": "ISO-8601 timestamp"},
                            "superseded_by": {"type": "STRING", "nullable": True}
                        },
                        "required": ["source_node_id", "target_entity", "relationship", "valid_from"]
                    }
                }
            },
            "required": ["edges"]
        }

    def _get_reflexion_audit_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "contradictions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "unverified_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "synthesized_axioms": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["contradictions", "unverified_actions", "synthesized_axioms"]
        }

    def run_nightly_cycle(self):
        """Executes the 4-Phase Autonomous Sleep Cycle."""
        print("[*] INITIATING METACOGNITIVE SLEEP CYCLE...")

        # ==========================================
        # PHASE 1: THE SWEEP (INGEST L1 VOLATILE STATE)
        # ==========================================
        l1_files = glob.glob(os.path.join(self.inbox_dir, "*.md"))
        if not l1_files:
            print("[*] Phase 1: Zero L1 volatility detected. Returning to sleep.")
            return

        combined_l1_payload = ""
        for fpath in l1_files:
            with open(fpath, "r", encoding="utf-8") as f:
                combined_l1_payload += f"\n--- [FILE: {os.path.basename(fpath)}] ---\n{f.read()}\n"

        print(f"[*] Phase 1: Swept {len(l1_files)} volatile L1 nodes.")

        # ==========================================
        # PHASE 2: TEMPORAL GRAPH LINKER (GEMINI 3.1 PRO)
        # ==========================================
        print("[*] Phase 2: Engaging Gemini 3.1 Pro (Macro-Architecture Linker)...")
        graph_prompt = (
            "Analyze these daily DS-00 records against standard engineering principles and historical assumptions. "
            "Extract semantic relationships (edges) between these new nodes and broader architectural concepts. "
            f"Use the current timestamp ({datetime.utcnow().isoformat() + 'Z'}) for the valid_from fields.\n\n"
            f"{combined_l1_payload}"
        )
        
        graph_response = self.client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=graph_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a Temporal GraphRAG daemon. Link short-term episodic memory to long-term semantic structures.",
                response_mime_type="application/json",
                response_schema=self._get_temporal_graph_schema(),
                temperature=0.0
            )
        )
        
        new_edges = json.loads(graph_response.text).get("edges", [])
        
        with open(self.graph_path, "r+", encoding="utf-8") as f:
            current_graph = json.load(f)
            current_graph["edges"].extend(new_edges)
            f.seek(0)
            json.dump(current_graph, f, indent=2)
            f.truncate()

        # ==========================================
        # PHASE 3: REFLEXION AUDIT LOOP
        # ==========================================
        print("[*] Phase 3: Engaging Adversarial Reflexion Audit...")
        reflexion_prompt = (
            "Act as an adversarial Red Team. Audit today's L1 records. "
            "Identify logical flaws, unverified assumptions, and extract hardened axioms.\n\n"
            f"{combined_l1_payload}"
        )
        
        audit_response = self.client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=reflexion_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a strict metacognitive auditor.",
                response_mime_type="application/json",
                response_schema=self._get_reflexion_audit_schema(),
                temperature=0.1
            )
        )
        
        audit_data = json.loads(audit_response.text)

        # ==========================================
        # PHASE 4: STATE COMPRESSION & GIT SYNC
        # ==========================================
        print("[*] Phase 4: State Compression & Substrate Synchronization...")
        
        # 4A. Archive L1 to L2
        for fpath in l1_files:
            shutil.move(fpath, os.path.join(self.l2_dir, os.path.basename(fpath)))

        # 4B. Write Reflexion Audit as a new DS-00 Record
        audit_matrix = EnforcedScaffoldResponse(
            headers=["NIGHTLY METACOGNITIVE AUDIT", "SYSTEM AXIOMS"],
            rca_blocks=[],
            tables=[
                MarkdownTable(
                    title="Detected Contradictions & Unverified Actions",
                    headers=["Type", "Finding"],
                    rows=[["Contradiction", c] for c in audit_data.get("contradictions", [])] +
                         [["Unverified Action", u] for u in audit_data.get("unverified_actions", [])]
                )
            ],
            bullet_points=audit_data.get("synthesized_axioms", [])
        )
        
        audit_record = DS00Record(
            record_id=f"AUDIT-{datetime.utcnow().strftime('%Y%m%d')}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            origin_source="metacog.service",
            technical_metadata=[f"processed_files_{len(l1_files)}", "model_gemini_3.1_pro"],
            content_matrix=audit_matrix
        )
        
        self.manager.write_record(audit_record)
        self.manager.sync_state(commit_message=f"AUTO-SYNC: Metacognitive Sleep Cycle {audit_record.record_id}")
        
        print("[*] CYCLE COMPLETE. Awaiting Waking State I/O.")

if __name__ == "__main__":
    daemon = MetacogDaemon()
    daemon.run_nightly_cycle()
