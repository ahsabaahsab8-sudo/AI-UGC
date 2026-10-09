# AI UGC Ads Generator (Veo 3.1 & Kilo Code)

A production-ready Python agent that converts product photos and marketing parameters into hyper-realistic UGC selfie ads. It replaces the complex n8n workflow with a lightweight, robust daemon running on SQLite.

---

## ⚡ Tech Stack & Verified APIs

- **Video Generation**: Google Veo 3.1 (`models/veo-3.1-fast-generate-preview`) via official `google-genai` SDK.
- **Image Generation / Edit**: Google Nano / Flash Image (`models/nano-banana-pro-preview` / `gemini-2.5-flash-image`).
- **Prompt Generation**: Kilo Code Gateway (`nex-agi/nex-n2.5-pro:free`) with reasoning disabled (`reasoning_effort="none"`).
- **Vision Image Analysis**: Kilo Code Gateway (`dots-studio/dots-3-note-preview:free`).
- **Queue & Storage**: Local SQLite database (`data/ugc_ads.db`) replacing Google Sheets.

---

## 🚀 Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Keys
Keys are configured in `.env`:
```env
GEMINI_API_KEY=AIzaSyBxrcLOW6l4_HP_I6IZmS5NVeZhsWBVlYY
KILO_PROMPT_API_KEY=eyJhbGci...
KILO_VISION_API_KEY=eyJhbGci...
```

### 3. Seed Demo Tasks or Add a Task
```bash
# Seed 2 sample tasks
python cli.py seed

# Or add your own product
python cli.py add \
  --product "HydroGlow Serum" \
  --photo "https://images.unsplash.com/photo-1608248597359-29976757b4ba?w=800" \
  --icp "20-30 year old skincare enthusiast" \
  --features "Deep hydration, instant dewy glass skin" \
  --setting "Sunlit bathroom vanity selfie" \
  --model "Veo 3.1"
```

### 4. Check Queue
```bash
python cli.py list
```

### 5. Start the Worker Daemon
```bash
# Run continuously in background
python main.py

# Or process a single task
python cli.py run
```

---

## ☁️ 1-Click VPS Deployment (Ubuntu / Debian)

### 1. Upload files to your VPS
```bash
scp -r * root@YOUR_VPS_IP:/root/ai-ugc/
```

### 2. Setup Virtual Environment on VPS
```bash
ssh root@YOUR_VPS_IP
cd /root/ai-ugc
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 3. Install Systemd Service
```bash
cp ugc-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ugc-agent
systemctl start ugc-agent
```

### 4. Monitor Service Logs
```bash
journalctl -u ugc-agent -f
# or
tail -f /var/log/ugc-agent.log
```

---

## 📁 Output Artifacts
- **Rendered Videos**: Saved automatically in `./outputs/videos/`
- **Generated Images**: Saved automatically in `./outputs/images/`
