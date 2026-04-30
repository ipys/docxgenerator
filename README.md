# 📄 Tikrit University — Term Paper Telegram Bot

A Telegram bot that **automatically generates a professional academic term paper (.docx)**  
in the exact style of Tikrit University, powered by **Claude AI**.

---

## 📁 Project Files

```
tikrit-bot/
├── bot.py            ← Telegram bot (run this)
├── generator.py      ← Claude API + Word document builder
├── .env.example      ← Copy to .env and fill in your keys
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```

---

## ⚙️ Setup (one-time)

### Step 1 — Install Python packages
```bash
pip install -r requirements.txt
```

### Step 2 — Create a Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g. `Tikrit Paper Bot`)
4. Choose a username ending in `bot` (e.g. `tikrit_paper_bot`)
5. Copy the **token** you receive (looks like `7123456789:AAF...`)

### Step 3 — Get your Anthropic API key
1. Go to https://console.anthropic.com
2. Create an account and add a payment method
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-api03-...`)

### Step 4 — Configure your keys
```bash
cp .env.example .env
```
Open `.env` in any text editor and paste your keys:
```
TELEGRAM_BOT_TOKEN=7123456789:AAF...your_token...
ANTHROPIC_API_KEY=sk-ant-api03-...your_key...
```

### Step 5 — Run the bot
```bash
python bot.py
```
You should see: `Bot is starting — polling…`

---

## 🤖 How to Use the Bot

Open your bot on Telegram and follow these steps:

| Command | Action |
|---------|--------|
| `/start` | Welcome message |
| `/generate` | Start a new term paper |
| `/cancel` | Cancel at any time |
| `/help` | Usage instructions |

### The 7-step wizard:

```
Step 1 → University name          e.g. Tikrit University
Step 2 → College name             e.g. College of Petroleum Process Engineering  
Step 3 → Department name          e.g. Oil and Gas Refining Department
Step 4 → Grade / Year             e.g. 3rd Grade
Step 5 → Paper topic / title      e.g. Deethanizer
Step 6 → Student full name        Arabic or English
Step 7 → Send university logo     As a PHOTO (not a file)
```

After confirming, the bot generates and sends you the `.docx` file in ~30 seconds.

---

## 📄 What the Generated Paper Contains

| Section | Content |
|---------|---------|
| **Cover Page** | Ministry header (red), university logo (top-right), college/department/grade, big title, "SUBMITTED BY", author name |
| **Introduction** | 160–200 word academic introduction |
| **Section 1** | Position of topic in industrial systems + diagram placeholder |
| **Section 2** | Principle of operation + diagram placeholder |
| **Section 3** | Key parameters and control considerations |
| **Section 4** | Industrial importance and applications |
| **Conclusion** | 110–150 word summary |
| **References** | 5 APA 7th edition citations (books, journals, websites) |

---

## 🎨 Document Style (matches original template)

- Font: **Times New Roman**, 12pt
- Headings: **Bold, dark red** (same color as Tikrit University template)
- Paragraphs: **Justified**, 1.15× line spacing
- Page: **A4**, 2.54 cm margins (3 cm left)
- Cover: Exact two-column layout with logo top-right

---

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `TELEGRAM_BOT_TOKEN is not set` | Check your `.env` file |
| `401 Unauthorized` from Anthropic | Check your API key in `.env` |
| Bot doesn't respond | Make sure `python bot.py` is running |
| Logo not showing | Send the logo as a **photo**, not as a file/document |
| JSON error in logs | Re-run `/generate` — it's a transient API issue |

---

## 🔒 Security Notes

- Never share your `.env` file
- Add `.env` to your `.gitignore` if using Git:
  ```
  echo ".env" >> .gitignore
  ```

---

## 💡 Example Topics

Any engineering topic works:

```
Deethanizer / Demethanizer / Depropanizer / Debutanizer
Heat Exchangers / Distillation Column / Absorption Column
Fluid Catalytic Cracking / Hydrotreating / Reforming Unit
Natural Gas Sweetening / Pipeline Design / Reboiler Design
Crude Oil Distillation / Vacuum Distillation / Gas Compression
```

---

## 📌 Running in the Background (Linux/Server)

```bash
# Using nohup
nohup python bot.py &

# Using screen
screen -S paperbot
python bot.py
# Ctrl+A then D to detach

# Using systemd (advanced)
# Create /etc/systemd/system/paperbot.service
```
