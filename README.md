# Decode-by-Quaarrd-
Snap a photo, pick a mode, get an instant AI answer — bill splitting, code debugging, or recipe ideas
# 🔎 Decode — by Quaarrd

**One photo. Pick a mode. Get a real, honest answer.**

🔗 **Live app:** https://pudvhqhuxp8pexavqjfhgp.streamlit.app/

Built for **STEMist Hacks IV** (August 2026).

---

## What is Decode?

Decode is a single AI tool for four everyday situations that all start the same way — you're staring at something and need help understanding it:

- 🧾 **Split It** — Photo of a receipt/bill → a fair, itemized split of who owes what
- 🐛 **Fix It** — Photo/screenshot of a code error → a plain-English explanation and fix
- 🍳 **Cook It** — Photo of your fridge/pantry/a food package → a recipe from what you actually have
- 🎯 **Anything Else** — Any photo → ask it literally anything

Instead of building four separate apps, Decode uses **one shared pipeline**: a vision model reads your photo, an optional web search grounds the answer in real facts, and a reasoning model gives you a clear final answer — tailored per mode.

## Why it's different

Most "AI reads your photo" tools just guess. Decode is built to **verify, not hallucinate**:

- When it identifies a specific product/brand, it searches the live web (via Tavily) for real, current information instead of relying on the model's training data alone.
- If the web search doesn't find a relevant answer, **Decode says so explicitly** rather than inventing a source, URL, or fact. Every claim in the final answer is grounded in what was actually found — or clearly flagged as unverified.
- You can also just type your own question directly, and it becomes the search query — no rigid categories.

## How it works

1. Upload one or more photos (or use your camera)
2. Pick a mode
3. The vision model (Groq) reads and describes the photo(s)
4. If relevant, Decode searches the web (Tavily) using a targeted query built from what was identified in the photo
5. A reasoning model (Groq) combines the photo analysis + real search results into a final, honest answer

## Tech stack

- **Frontend/hosting:** Streamlit (Streamlit Community Cloud)
- **Vision + reasoning:** Groq API (`qwen/qwen3.6-27b` for vision, `openai/gpt-oss-120b` for reasoning)
- **Real-time web search:** Tavily API
- **Language:** Python

## Try it yourself

No login required — just open the live app and upload a photo:

👉 https://pudvhqhuxp8pexavqjfhgp.streamlit.app/

**Good things to try:**
- A restaurant receipt, then tell it who ordered what
- A screenshot of a code error
- A photo of a packaged food product, and ask what's actually in it

## Setup (run locally)

```bash
git clone https://github.com/quaarrd-cmyk/Decode-by-Quaarrd-.git
cd Decode-by-Quaarrd-
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your-groq-key"
TAVILY_API_KEY = "your-tavily-key"
```

Run:
```bash
streamlit run app.py
```

## About

Built solo by **YRY**, founder of **Quaarrd**, for STEMist Hacks IV — built in a single evening, mobile-only, entirely from a phone.

## License

MIT
