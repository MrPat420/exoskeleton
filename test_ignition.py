import os
from datetime import datetime
from config.schemas import DS00Record, EnforcedScaffoldResponse, RCALogic
from core.ds00_state_engine import DS00Manager

print("[*] Initiating DS-00 Memory Write Test...")

try:
    # 1. Create fake test data using the rigid schemas
    test_rca = RCALogic(
        symptom="Code generated but not executed.",
        cause="Operator identified missing deployment phase.",
        action_items=["Halt GUI build", "Deploy to local disk", "Run ignition test"]
    )

    test_content = EnforcedScaffoldResponse(
        headers=["IGNITION TEST SEQUENCE"],
        rca_blocks=[test_rca],
        tables=[],
        bullet_points=["System deployed to ChromeOS successfully."]
    )

    test_record = DS00Record(
        record_id="TEST-001",
        timestamp=datetime.utcnow().isoformat() + "Z",
        origin_source="Ignition_Script",
        technical_metadata=["test_run", "environment_verification"],
        content_matrix=test_content
    )

    # 2. Write it to disk
    manager = DS00Manager(memory_dir="data/ds00_memory")
    saved_path = manager.write_record(test_record)

    print(f"[+] SUCCESS! Record written to: {saved_path}")

except Exception as e:
    print(f"[-] IGNITION FAILED. Error: {e}")
