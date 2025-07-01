# Discord Chatbot

An Discord chatbot built using `discord.py`, GPT-based AI models, TTS integration, and image generation features like SDXL and DALL·E. Designed for interactive conversations, dynamic commands, and full customization.

---

##  Features

- AI Chatbot with memory and internet search support
- Text-to-Speech with voice channel playback
- Image Generation (Stable Diffusion, DALL·E, SDXL, etc.)
- Dynamic presence updates
- Persona switching with instruction configs
- Slash commands with hybrid support
- Owner/admin-only command restrictions

---

## Installation

### 1. Clone the Repo

git clone https://github.com/your-username/ai-discord-chatbot.git
cd ai-discord-chatbot

### 2. Set Up Environment

Install dependencies:

`pip install -r requirements.txt`


### 3. Set Up .env File
Create a .env file in the root directory and add:

`DISCORD_TOKEN=your_discord_bot_token`<br>
`CHIMERA_GPT_KEY=your_api_key_for_ai`


### 4. Configure config.json
 
Edit bot_utilities/config_loader.py or your config.json with:

`{`<br>
  `"ALLOW_DM": true,`<br>
  `"TRIGGER": ["hey bot", "ai"],`<br>
  `"SMART_MENTION": true,`<br>
  `"PRESENCES": ["Helping users", "Generating images", "Chatting..."],`<br>
  `"DISABLE_PRESENCE": false,`<br>
  `"PRESENCES_CHANGE_DELAY": 20,`<br>
  `"GPT_MODEL": "gpt-4",`<br>
  `"MAX_HISTORY": 5,`<br>
  `"AI_NSFW_CONTENT_FILTER": true,`<br>
  `"BLACKLIST_WORDS": ["nsfw", "explicit"],`<br>
  `"INTERNET_ACCESS": true,`<br>
  `"INSTRUCTIONS": "default",`<br>
  `"Discord": "https://discord.gg/yourserver",`<br>
  `"Github": "https://github.com/your-repo"`<br>
`}`<br>

### 5. Folder Structure

 bot_utilities/
    ├─ ai_utils.py
    ├─ config_loader.py
    ├─ discord_util.py
    ├─ response_util.py
    ├─ sanitization_utils.py
    └─ replit_detector.py

 model_enum.py
 main.py
 requirements.txt
 .env

### 6. Usage
Run the bot using:

`python main.py`

**Make sure your bot has MESSAGE CONTENT INTENT, GUILD, and APPLICATION COMMANDS permissions.**


### 7. Security Notes

- Sensitive commands (like server invites) are removed from public version.
- TTS files are unique per message to avoid race conditions.
- Use command permissions wisely to prevent abuse.
