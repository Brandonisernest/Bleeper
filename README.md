# 🎙️ Podcast Bleeper
A personal tool that automatically finds and removes curse words from podcast MP3 files using AI transcription.

---

## 📁 Files in this folder
- **bleep.py** — the main script that does all the work
- **detective.py** — debugging tool to see what Whisper heard at a specific timestamp
- **wordlist.txt** — your master list of words to bleep
- **README.md** — this file!

---

## 🚀 How to use it

### Step 1: Make sure your wordlist is up to date
Open `wordlist.txt` in any text editor and add or remove words as needed. One word per line. Lines starting with `#` are ignored (they're just comments).

### Step 2: Open Terminal
Press **Cmd + Space**, type **Terminal**, hit Enter.

### Step 3: Navigate to this folder
Type `cd ` (with a space after it), then drag the Bleeper folder into the Terminal window. Hit Enter.

### Step 4: Run the script
Type `python3 bleep.py ` (with a space after it), then drag your podcast MP3 into the Terminal window. Hit Enter.

**With bleep tone (default):**
```
python3 bleep.py yourpodcast.mp3
```

**With silence instead of bleep tone:**
```
python3 bleep.py yourpodcast.mp3 --mode silence
```

**With a more accurate (but slower) model:**
```
python3 bleep.py yourpodcast.mp3 --model medium
```

**Combining options:**
```
python3 bleep.py yourpodcast.mp3 --mode silence --model small
```

### Step 5: Wait for it to finish
A 2+ hour podcast takes roughly 20-40 minutes. Terminal will print each word it finds as it goes. Don't close Terminal while it's running!

### Step 6: Find your clean file
When it's done, a new file called `yourpodcast_clean.mp3` will appear in the same folder as your original file.

---

## ▶️ Playing the clean file
Always open the clean file with **QuickTime Player** or **VLC** — right click the file → Open With → QuickTime Player.

⚠️ **Don't open it by double-clicking** as it may open in Apple Music which caches files and might play an old version instead.

---

## ✏️ Updating your word list
Just open `wordlist.txt` in any text editor (TextEdit works fine) and add or remove words. Changes take effect immediately next time you run the script. Remember to include variations of words (-ing, -er, -ed etc.)!

---

## ⚙️ Settings (inside bleep.py)
If you open `bleep.py` you'll see these settings near the top that you can tweak:

| Setting | Default | What it does |
|---|---|---|
| `PADDING_MS` | `80` | Extra milliseconds muted on each side of a word |
| `BLEEP_FREQ_HZ` | `1000` | The frequency (pitch) of the bleep tone |

The Whisper model is now set via `--model` on the command line instead!

---

## 🛠️ Requirements
These need to be installed on your Mac (you already did this!):
- Python 3
- Homebrew
- ffmpeg
- openai-whisper
- pydub

---

## 🔍 Debugging missed words (detective.py)
If the script missed a word, use the inspector to see exactly what Whisper heard at that timestamp:

**Using mm:ss format:**
```
python3 detective.py yourpodcast.mp3 35:46
```

**Using seconds:**
```
python3 detective.py yourpodcast.mp3 2146
```

**Show a wider window around the timestamp (default is 30 seconds each side):**
```
python3 detective.py yourpodcast.mp3 35:46 --window 60
```

**Use a more accurate model for inspection:**
```
python3 detective.py yourpodcast.mp3 35:46 --model medium
```

It'll print every word Whisper heard around that moment. If Whisper misheared the word, just add what it *actually* transcribed to your wordlist instead!

---

## 💡 Tips
- Test on a short clip first (use QuickTime Player → Edit → Trim to make one)
- The script never modifies your original file — it always creates a new `_clean` version
- If Whisper mishears a word, try upgrading to `small` or `medium` model in settings
- Run it in the background while doing other things — it'll beep when done if your Mac notifications are on

---

*Built with OpenAI Whisper + pydub. Runs entirely on your Mac — no internet needed after setup.*
