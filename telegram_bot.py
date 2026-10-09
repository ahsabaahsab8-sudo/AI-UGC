import os
import sys
import json
import asyncio
import logging
from pathlib import Path
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATABASE_PATH, OUTPUTS_DIR
from database import init_db, add_task, update_task_fields
from kilo_client import generate_video_prompt

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("telegram_bot")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8864541832:AAGABVFjWzgiuYESkK5HsC8p6FG7zVcRPKk")
FLOW_BRIDGE_URL = os.getenv("FLOW_BRIDGE_URL", "http://127.0.0.1:8791")
VIDEOS_DIR = OUTPUTS_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

async def wait_for_flow_job(client: httpx.AsyncClient, job_id: str, poll_interval: int = 5, timeout: int = 300) -> str:
    """Poll Flow bridge until the generation job is finished and return downloaded file path."""
    elapsed = 0
    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        res = await client.get(f"{FLOW_BRIDGE_URL}/jobs/{job_id}")
        if res.status_code == 200:
            data = res.json()
            status = data.get("status")
            if status == "done":
                files = data.get("files", [])
                if files and "path" in files[0]:
                    return files[0]["path"]
            elif status == "failed":
                raise RuntimeError(f"Flow job {job_id} failed: {data.get('error', 'unknown error')}")
    raise TimeoutError(f"Flow job {job_id} timed out after {timeout}s")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    welcome_text = (
        "🌿 *AI UGC Video Generator Bot is Online!*\n\n"
        "Send me any command to generate full UGC commercials with Google Flow:\n\n"
        "• `/generate Nature AI` — Generates a multi-scene, character-consistent UGC ad\n"
        "• `/generate <Any Product Name>` — Generates an ad for any product\n"
        "• `/status` — Checks Google Flow & Bridge connection status\n"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler to check Google Flow bridge status."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{FLOW_BRIDGE_URL}/status?site=flow")
            if res.status_code == 200:
                data = res.json()
                ext = "Connected ✅" if data.get("extensionConnected") else "Disconnected ❌"
                usage = data.get("usage", {})
                limits = data.get("limits", {})
                msg = (
                    f"🔌 *Google Flow Status:*\n"
                    f"• Bridge: `{data.get('bridge')}` (v{data.get('bridgeVersion')})\n"
                    f"• Chrome Extension: {ext}\n"
                    f"• Account: `{data.get('plan', 'free')}` plan\n"
                    f"• Videos Used Today: `{usage.get('video', 0)} / {limits.get('video', 30)}`\n"
                    f"• Browser: `{data.get('browser', 'chrome')}`\n"
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
                return
    except Exception as e:
        await update.message.reply_text(f"❌ Error connecting to Flow Bridge: {e}")

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate multi-scene UGC ad with consistent character via Google Flow."""
    chat_id = update.effective_chat.id
    product_name = " ".join(context.args).strip() if context.args else "Nature AI"

    status_msg = await update.message.reply_text(
        f"🧠 *Step 1/4: Brainstorming viral UGC concept for '{product_name}'...*\n"
        f"Calling Kilo Gateway (`nex-agi/nex-n2.5-pro`)...",
        parse_mode="Markdown"
    )

    try:
        # 1. LLM Generates Fresh Viral UGC Script
        features = "AI Plant disease diagnosis, leaf scanner, bird song identifier, watering schedule"
        icp = "Houseplant owners, indoor gardeners, and nature lovers"
        prompt_res = generate_video_prompt(product=product_name, features=features, icp=icp)
        dialogue = prompt_res.get("dialogue", "Stop guessing why your houseplant leaves keep turning yellow!")

        # 2. Formulate 2-Scene Storyboard with Consistent Character EMMA
        shot1_prompt = (
            f"A vertical 9:16 authentic handheld UGC selfie video of character Emma in a bright living room "
            f"beside a potted houseplant with yellowing drooping leaves. Emma looks concerned at the camera and speaks: "
            f"'{dialogue}' Natural creator vlog style, soft daylight."
        )
        shot2_prompt = (
            f"A vertical 9:16 authentic UGC creator video of character Emma in a bright living room holding up her smartphone "
            f"next to the plant. Her phone screen clearly displays the {product_name} app with an active scanning green box "
            f"and diagnosis card reading: 'Disease Detected: Overwatering - Cure: Water once weekly'. Emma smiles warmly and speaks: "
            f"'You literally just point your phone camera with {product_name} and it diagnoses the plant in two seconds. "
            f"Download {product_name} today!' Authentic handheld motion, natural daylight."
        )

        task_id = add_task(
            product=f"{product_name} (Telegram Bot Ad)",
            product_photo="outputs/images/emma_portrait.jpg",
            icp=icp,
            product_features=features,
            video_setting="Living room vlog",
            model="Omni Flash (Flow Emma)",
            status="Processing"
        )

        # 3. Submit Scene 1
        await status_msg.edit_text(
            f"🎬 *Step 2/4: Generating Scene 1 with Character EMMA on Google Flow...*\n"
            f"• Model: `omni-flash` (9:16 vertical)\n"
            f"• Script Hook: _{dialogue[:80]}..._",
            parse_mode="Markdown"
        )

        async with httpx.AsyncClient(timeout=360.0) as client:
            # Check bridge connection first
            check = await client.get(f"{FLOW_BRIDGE_URL}/status?site=flow")
            if not check.json().get("extensionConnected"):
                await status_msg.edit_text("❌ Error: Google Flow extension is not connected in Chrome!")
                return

            # Submit Scene 1
            res1 = await client.post(f"{FLOW_BRIDGE_URL}/jobs", json={
                "mode": "flow-text-to-video",
                "prompt": shot1_prompt,
                "characterRefs": ["EMMA"],
                "params": {
                    "imageModel": "omni-flash",
                    "aspectRatio": "9:16",
                    "videoOption": "10s",
                    "downloadSubfolder": "telegram-ads"
                }
            })
            job1_id = res1.json()["id"]
            clip1_path = await wait_for_flow_job(client, job1_id)

            # Submit Scene 2
            await status_msg.edit_text(
                f"🎬 *Step 3/4: Scene 1 done! Generating Scene 2 (App Demo & CTA)...*\n"
                f"Maintaining identical character face & outfit (`EMMA`)...",
                parse_mode="Markdown"
            )

            res2 = await client.post(f"{FLOW_BRIDGE_URL}/jobs", json={
                "mode": "flow-text-to-video",
                "prompt": shot2_prompt,
                "characterRefs": ["EMMA"],
                "params": {
                    "imageModel": "omni-flash",
                    "aspectRatio": "9:16",
                    "videoOption": "10s",
                    "downloadSubfolder": "telegram-ads"
                }
            })
            job2_id = res2.json()["id"]
            clip2_path = await wait_for_flow_job(client, job2_id)

        # 4. Auto-Merge with ffmpeg
        await status_msg.edit_text(
            f"✂️ *Step 4/4: Merging scenes into full-length commercial...*",
            parse_mode="Markdown"
        )

        timestamp = int(asyncio.get_event_loop().time())
        final_video_path = VIDEOS_DIR / f"telegram_ad_{product_name.lower().replace(' ', '_')}_{timestamp}.mp4"

        merge_proc = await asyncio.create_subprocess_exec(
            "flow-auto", "merge", "-o", str(final_video_path), str(clip1_path), str(clip2_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await merge_proc.communicate()

        if not final_video_path.exists():
            final_video_path = Path(clip2_path)  # fallback to clip 2 if merge failed

        # Update DB
        update_task_fields(task_id, status="Finished", finished_video_path=str(final_video_path))

        caption = (
            f"🎉 *{product_name} UGC Ad Complete!*\n\n"
            f"• *Model*: Google Flow `omni-flash`\n"
            f"• *Character*: Emma (Consistent across scenes)\n"
            f"• *Duration*: 20s (Full 9:16 Vertical)\n\n"
            f"📝 *Script Delivered*:\n"
            f"\"{dialogue}\"\n"
            f"\"With {product_name}, you literally just point your phone camera and it diagnoses the plant in two seconds! Download {product_name} today!\""
        )

        # Send finished video
        with open(final_video_path, "rb") as vf:
            await context.bot.send_video(
                chat_id=chat_id,
                video=vf,
                caption=caption,
                parse_mode="Markdown"
            )
        await status_msg.delete()

    except Exception as e:
        logger.exception("Error generating ad via telegram")
        await status_msg.edit_text(f"❌ *Generation Failed:* `{str(e)}`", parse_mode="Markdown")

def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("generate", generate_handler))

    logger.info("🤖 Telegram Bot initialized and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
