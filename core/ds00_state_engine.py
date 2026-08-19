import os
import json
import yaml
import subprocess
from config.schemas import DS00Record

class DS00Manager:
    def __init__(self, memory_dir: str = "data/ds00_memory"):
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)

    def write_record(self, record: DS00Record) -> str:
        frontmatter = {
            "record_id": record.record_id,
            "timestamp": record.timestamp,
            "origin_source": record.origin_source,
            "technical_metadata": record.technical_metadata
        }
        
        lines = ["---"]
        lines.append(yaml.dump(frontmatter, default_flow_style=False).strip())
        lines.append("---\n")
        
        c_matrix = record.content_matrix
        
        for header in c_matrix.headers:
            lines.append(f"## {header}\n")
        
        if c_matrix.rca_blocks:
            lines.append("### Root Cause Analysis (RCA)")
            for rca in c_matrix.rca_blocks:
                lines.append(f"- **Symptom:** {rca.symptom}")
                lines.append(f"- **Cause:** {rca.cause}")
                lines.append("- **Action Items:**")
                for item in rca.action_items:
                    lines.append(f"  - [ ] {item}")
            lines.append("\n")
            
        if c_matrix.tables:
            for t in c_matrix.tables:
                lines.append(f"### {t.title}")
                lines.append("| " + " | ".join(t.headers) + " |")
                lines.append("|" + "|".join(["---"] * len(t.headers)) + "|")
                for row in t.rows:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("\n")
                
        if c_matrix.bullet_points:
            lines.append("### Analytical Vectors")
            for bp in c_matrix.bullet_points:
                lines.append(f"* {bp}")
            lines.append("\n")

        content = "\n".join(lines)
        file_path = os.path.join(self.memory_dir, f"{record.record_id}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return file_path

    def sync_state(self, commit_message: str = "AUTO-SYNC: DS-00 State Update") -> bool:
        try:
            # Ensure the directory is a git repository before attempting sync
            if not os.path.exists(os.path.join(self.memory_dir, ".git")):
                subprocess.run(["git", "init"], cwd=self.memory_dir, check=True, capture_output=True)
                
            subprocess.run(["git", "add", "."], cwd=self.memory_dir, check=True, capture_output=True)
            
            # Check if there are changes to commit
            status = subprocess.run(["git", "status", "--porcelain"], cwd=self.memory_dir, capture_output=True, text=True)
            if not status.stdout.strip():
                return True # Nothing to sync
                
            subprocess.run(["git", "commit", "-m", commit_message], cwd=self.memory_dir, check=True, capture_output=True)
            
            # Fails safely if no remote origin is configured yet
            subprocess.run(["git", "push"], cwd=self.memory_dir, check=True, capture_output=True)
            return True
            
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode('utf-8').strip() if e.stderr else "Unknown Git Error"
            print(f"[-] Git Sync Failed: {error_output}")
            return False
