import argparse
import json
from database import add_task, get_all_tasks, get_next_ready_task, init_db, update_task_fields
from pipeline import process_task
from google_sheets import fetch_ready_rows_from_sheets

def cmd_add(args):
    task_id = add_task(
        product=args.product,
        product_photo=args.photo,
        icp=args.icp,
        product_features=args.features,
        video_setting=args.setting,
        model=args.model,
        no=args.no,
        status="Ready"
    )
    print(f"Task #{task_id} successfully added with status 'Ready'!")

def cmd_list(args):
    tasks = get_all_tasks(limit=args.limit)
    if not tasks:
        print("No tasks found in the database.")
        return

    print(f"\n{'ID':<5} {'Model':<15} {'Status':<12} {'Product':<25} {'Video Output'}")
    print("-" * 80)
    for t in tasks:
        vid = t.get('finished_video_path') or '-'
        if len(vid) > 30:
            vid = "..." + vid[-27:]
        print(f"{t['id']:<5} {t['model']:<15} {t['status']:<12} {t['product'][:23]:<25} {vid}")
    print()

def cmd_sync(args):
    print("[Google Sheets] Fetching 'Ready' rows from your spreadsheet...")
    rows = fetch_ready_rows_from_sheets()
    if not rows:
        print("[Google Sheets] No rows with Status='Ready' found in the sheet.")
        return

    print(f"[Google Sheets] Found {len(rows)} ready row(s). Syncing into queue:")
    for r in rows:
        tid = add_task(
            product=r.get("Product", "Untitled"),
            product_photo=r.get("Product Photo", ""),
            icp=r.get("ICP", ""),
            product_features=r.get("Product Features", ""),
            video_setting=r.get("Video Setting", ""),
            model=r.get("Model", "Veo 3.1"),
            no=str(r.get("No") or r.get("_row_number")),
            status="Ready"
        )
        print(f" -> Imported Row {r.get('_row_number')} (No: {r.get('No')}) as Task #{tid}: {r.get('Product')} [{r.get('Model')}]")
    print("[Google Sheets] Sync complete! Run 'python cli.py list' or 'python main.py' to process.")

def cmd_seed(args):
    demo_tasks = [
        {
            "product": "Nature AI - Bird Audio Scanner",
            "photo": "https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=800",
            "icp": "Outdoor hiker, backyard bird watcher, 25-45 nature enthusiast",
            "features": "Listens to audio chirps to identify bird species in 2 seconds, 10000+ species library",
            "setting": "Sunlit backyard garden patio holding phone towards trees",
            "model": "Veo 3.1",
            "no": "NATURE-1"
        },
        {
            "product": "Nature AI - Plant Disease Doctor",
            "photo": "https://images.unsplash.com/photo-1545241047-6083a3684587?w=800",
            "icp": "Houseplant lover struggling to keep potted plants alive",
            "features": "Scan leaf to detect diseases, watering guide, sunlight tracker",
            "setting": "Bright cozy living room holding monstera plant with yellow leaf",
            "model": "Nano + Veo 3.1",
            "no": "NATURE-2"
        }
    ]

    for item in demo_tasks:
        tid = add_task(
            product=item["product"],
            product_photo=item["photo"],
            icp=item["icp"],
            product_features=item["features"],
            video_setting=item["setting"],
            model=item["model"],
            no=item["no"],
            status="Ready"
        )
        print(f"Seeded Nature AI Task #{tid}: {item['product']} ({item['model']})")

def cmd_run(args):
    if args.id:
        from database import get_task_by_id
        task = get_task_by_id(args.id)
        if not task:
            print(f"Task #{args.id} not found.")
            return
    else:
        print("Looking for next ready task...")
        task = get_next_ready_task()
        if not task:
            print("No tasks with status 'Ready' found.")
            return
    process_task(task)

def main():
    init_db()
    parser = argparse.ArgumentParser(description="UGC Ads AI Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new UGC generation task")
    add_parser.add_argument("--product", required=True, help="Product name")
    add_parser.add_argument("--photo", required=True, help="URL or local path to product photo")
    add_parser.add_argument("--icp", required=True, help="Ideal customer profile / persona description")
    add_parser.add_argument("--features", required=True, help="Key product features & benefits")
    add_parser.add_argument("--setting", required=True, help="Video recording setting / environment")
    add_parser.add_argument("--model", default="Veo 3.1", choices=["Veo 3.1", "Nano + Veo 3.1", "Sora 2"], help="Model branch")
    add_parser.add_argument("--no", default=None, help="Row number or reference code")
    add_parser.set_defaults(func=cmd_add)

    # Sync from Google Sheets
    sync_parser = subparsers.add_parser("sync", help="Sync Ready rows from Google Sheet")
    sync_parser.set_defaults(func=cmd_sync)

    # List tasks
    list_parser = subparsers.add_parser("list", help="List recent tasks in database")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of tasks to show")
    list_parser.set_defaults(func=cmd_list)

    # Seed demo tasks
    seed_parser = subparsers.add_parser("seed", help="Seed Nature AI demo tasks into the database")
    seed_parser.set_defaults(func=cmd_seed)

    # Run single task
    run_parser = subparsers.add_parser("run", help="Process one ready task immediately")
    run_parser.add_argument("--id", type=int, default=None, help="Specific task ID to run")
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
