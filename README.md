# 📱 AI UGC Video Ad Generator 🚀 (Google Veo 3.1 & Telegram Bot)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Google Veo](https://img.shields.io/badge/Google%20Veo-3.1%20Fast-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/veo/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-2CA5E0?logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🛍️ **Autonomous AI Marketing Agent that converts static product photos and value props into ultra-realistic User-Generated Content (UGC) selfie video ads.**  
> Built as an enterprise-grade background daemon with native SQLite task queuing, Veo 3.1 video generation, and interactive Telegram Bot controls.

---

## 🌟 Key Features

- 📸 **Vision Product Analysis**: Inspects product imagery using multimodal vision models to extract design attributes, packaging typography, and color aesthetics.
- 🎬 **Google Veo 3.1 Video Engine**: Generates realistic selfie-style consumer testimonials with natural facial expressions, gestures, and product handling.
- 🤖 **Interactive Telegram Bot**: Submit new ads on the go by sending product photos and text directly in Telegram chat; receive finished videos back automatically.
- 📦 **SQLite Lightweight Queue**: No external message broker required (no Redis or RabbitMQ); zero overhead task orchestration and retry handling.
- 🔄 **CLI & Daemon Execution**: Operate via command-line interface for batch runs or launch as a self-healing background systemd service.

---

## 🏗️ Architecture & Pipeline

```
┌─────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│  Product Photo URL  │ ───>  │  Vision Analysis     │ ───>  │  Kilo Prompt Engine  │
│  & Selling Points   │       │  (Inspect Packaging) │       │  (Craft UGC Script)  │
└─────────────────────┘       └──────────────────────┘       └──────────┬───────────┘
                                                                        │
┌─────────────────────┐       ┌──────────────────────┐       ┌──────────▼───────────┐
│ Deliver to Telegram │ <───  │ Google Veo 3.1 /     │ <───  │ Nano / Flash Image    │
│ & ./outputs/videos/ │       │ Sora Video Render    │       │ Character Synthesis  │
└─────────────────────┘       └──────────────────────┘       └──────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core engine & async orchestration |
| **Video AI** | Google Veo 3.1 Fast / Sora | High-definition AI video synthesis |
| **Vision & Image** | Google Nano Pro & Gemini 2.5 Flash | Character posing and product placement generation |
| **Prompt Engineering**| Kilo Code Gateway (`nex-n2.5-pro:free`) | UGC hook & emotional script generation |
| **Task Queue** | SQLite3 (`data/ugc_ads.db`) | Durable task state machine |
| **Control Surface** | Python-Telegram-Bot | Remote mobile interface for managing generation jobs |

---

## 🔑 Environment Variables Setup (`.env`)

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

| Variable | Required | Description |
| :--- | :---: | :--- |
| `GEMINI_API_KEY` | **Yes** | Google AI Studio key for Veo 3.1 and Gemini Flash models |
| `KILO_PROMPT_API_KEY` | **Yes** | Kilo Code gateway API key for prompt engineering |
| `KILO_VISION_API_KEY` | No | Secondary vision key for high-throughput image recognition |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram Bot token from [@BotFather](https://t.me/BotFather) |
| `WORKER_POLL_INTERVAL`| No | Polling frequency in seconds (default: `10`) |
| `GOOGLE_SHEETS_API_KEY`| No | Legacy Google Sheets syncing (optional) |
| `KIE_AI_API_KEY` | No | Fallback engine for Veo/Sora generation |

---

## 🚀 Installation & Local Usage

```bash
# 1. Clone the repository
git clone https://github.com/ahsabaahsab8-sudo/AI-UGC.git
cd AI-UGC

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
nano .env

# 5. Populate sample queue item
python cli.py seed

# 6. Run the generation pipeline
python main.py
```

### 💻 CLI Commands

```bash
# Add a custom product to the generation queue
python cli.py add \
  --product "HydraGlow Daily Essence" \
  --photo "https://images.unsplash.com/photo-1608248597359-29976757b4ba?w=800" \
  --icp "Women 22-35 suffering from dry winter skin" \
  --features "Korean hyaluronic acid, glass-skin effect in 3 days" \
  --setting "Sunlit clean bathroom mirror selfie" \
  --model "Veo 3.1"

# View current task queue status
python cli.py list

# Process tasks immediately (single run)
python cli.py run

# Start Telegram Bot listener
python telegram_bot.py
```

---

## ☁️ Linux VPS 24/7 Deployment (Ubuntu / Debian)

### 1. Automated VPS Setup Script

```bash
chmod +x deploy_vps.sh
sudo ./deploy_vps.sh
```

### 2. Manual Systemd Service Configuration

Ensure continuous operation with automated restarts on failure:

```bash
# 1. Copy service configuration
sudo cp ugc-agent.service /etc/systemd/system/

# 2. Reload systemd daemon
sudo systemctl daemon-reload

# 3. Enable and start worker daemon
sudo systemctl enable --now ugc-agent

# 4. Check status and follow live logs
sudo systemctl status ugc-agent
journalctl -u ugc-agent -f
```

---

## 📂 Project Directory Structure

```
AI-UGC/
├── .env.example           # Configuration template with placeholders
├── cli.py                 # Command Line Interface for queue management
├── config.py              # Environment variable loader & settings validation
├── database.py            # SQLite schema, task states, and atomic transactions
├── deploy_vps.sh          # One-click Ubuntu/Debian deployment script
├── gemini_client.py       # Google GenAI Veo 3.1 & Flash integration
├── kilo_client.py         # Kilo Code LLM API client
├── main.py                # Background daemon worker loop
├── pipeline.py            # End-to-end multi-stage UGC synthesis pipeline
├── prompts.py             # Curated prompt engineering blueprints
├── telegram_bot.py        # Telegram Bot handler for remote submission & preview
├── ugc-agent.service      # Systemd service unit definition
└── outputs/
    ├── images/            # Intermediate product & character generations
    └── videos/            # Finished high-resolution MP4 video ads
```

---

## 🛡️ License

Released under the [MIT License](LICENSE). Contributions, feature requests, and PRs are welcome!
