import time
import signal
import sys
import argparse
from config import WORKER_POLL_INTERVAL
from database import init_db, get_next_ready_task, add_task
from pipeline import process_task
from google_sheets import fetch_ready_rows_from_sheets

running = True

def handle_signal(sig, frame):
    global running
    print("\n[Worker] Gracefully shutting down worker...")
    running = False

def sync_from_sheets():
    """Check Google Sheets for new 'Ready' rows and enqueue them."""
    try:
        rows = fetch_ready_rows_from_sheets()
        for r in rows:
            add_task(
                product=r.get("Product", "Untitled"),
                product_photo=r.get("Product Photo", ""),
                icp=r.get("ICP", ""),
                product_features=r.get("Product Features", ""),
                video_setting=r.get("Video Setting", ""),
                model=r.get("Model", "Veo 3.1"),
                no=str(r.get("No") or r.get("_row_number")),
                status="Ready"
            )
    except Exception as e:
        print(f"[Google Sheets Sync Notice] {e}")

def run_worker(once: bool = False, poll_sheets: bool = True):
    init_db()
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print("=" * 65)
    print("      AI UGC Ads Agent Worker (Veo 3.1 & Google Sheets)      ")
    print("=" * 65)
    print(f"[*] Polling interval: {WORKER_POLL_INTERVAL} seconds.")
    if poll_sheets:
        print("[*] Google Sheets live auto-sync: ENABLED")
    print("[*] Press Ctrl+C to stop.\n")

    while running:
        try:
            if poll_sheets:
                sync_from_sheets()

            task = get_next_ready_task()
            if task:
                process_task(task)
                if once:
                    break
            else:
                if once:
                    print("[Worker] No ready tasks found.")
                    break
                time.sleep(WORKER_POLL_INTERVAL)
        except Exception as e:
            print(f"[Worker Exception] {e}")
            time.sleep(5)

    print("[Worker] Worker exited cleanly.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI UGC Worker Daemon")
    parser.add_argument("--once", action="store_true", help="Process ready tasks once and exit")
    parser.add_argument("--no-sheets", action="store_true", help="Disable automatic Google Sheets polling")
    args = parser.parse_args()
    run_worker(once=args.once, poll_sheets=not args.no_sheets)
