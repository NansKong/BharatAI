"""
Test Production Celery Ingestion Task Script.
Calls ingest_live_opportunities_task directly to verify background task execution.
"""

import sys

sys.path.insert(0, ".")

from app.workers.scrape_tasks import ingest_live_opportunities_task

if __name__ == "__main__":
    print("============================================================")
    print("[PRODUCTION TASK] TESTING AUTOMATED INGESTION TASK")
    print("============================================================\n")

    result = ingest_live_opportunities_task()
    print(f"Task Return Payload: {result}")
    print("\n============================================================")
