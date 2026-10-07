# 🧾 Receipt & Expense Tracker

An AI-powered chat app that turns a photo of a receipt (or a plain text description) into a clean expense record — merchant, date, items, total, and category — and can text you a running summary on WhatsApp.

Built with **Streamlit**, **Gemini** (chat + vision), and **Twilio** (WhatsApp). No OpenCV, no OCR library, no model training required.

## Features

- 💬 Chat interface — type an expense or attach a receipt photo
- 📸 Vision-based receipt reading via Gemini
- 🏷️ Auto-categorization (Food, Transport, Shopping, Bills, Health, Entertainment, Other)
- 📤 One-click summary sent straight to WhatsApp via Twilio
- 🔒 Secrets kept out of version control

## Project Structure

```
receipt-tracker/
├── app.py                        # the app itself
├── prompts.py                    # the AI's personality, kept separate
├── requirements.txt              # dependencies
├── .gitignore                    # keeps secrets.toml out of GitHub
└── .streamlit/
    └── secrets.toml.example      # template - copy to secrets.toml and fill in
```

## Prerequisites

- Python 3.9 or newer
- A free [Google AI Studio](https://aistudio.google.com) account (for a Gemini API key)
- A free [Twilio](https://www.twilio.com/try-twilio) account (for the WhatsApp sandbox)

## Setup

1. **Clone and enter the project folder**
   ```bash
   git clone <your-repo-url>
   cd receipt-tracker
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS/Linux
   .\venv\Scripts\Activate.ps1     # Windows PowerShell
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get a Gemini API key**
   Go to aistudio.google.com → **Get API key**.

5. **Set up Twilio WhatsApp**
   - Sign up at twilio.com/try-twilio, copy your **Account SID** and **Auth Token**.
   - Under **Messaging → Try it out → Send a WhatsApp message**, note the sandbox number and join code.
   - From your test WhatsApp number, send the join message (e.g. `join happy-tiger`) to the sandbox number. This opt-in expires after ~72 hours of inactivity.
   - Under **Messaging → Content Template Builder**, create a Text template with two variables, e.g.:
     `Hi {{1}}, here's your expense summary:\n\n{{2}}`
     Note its **Content SID** (starts with `HX...`).

6. **Configure secrets**
   Copy the template and fill in your real values:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Then edit `.streamlit/secrets.toml` with your Gemini key, Twilio SID/token, WhatsApp sandbox number, and Content SID.

## Running Locally

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Onboard with the WhatsApp number that joined your sandbox, try a typed expense, try a receipt photo, then click **Send to WhatsApp**.

## Deploying to Streamlit Community Cloud

1. Push the project to GitHub — do **not** commit `.streamlit/secrets.toml`.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select the repo, branch, and `app.py` as the entry point.
4. In **Settings → Secrets**, paste the same contents as your local `secrets.toml`.
5. Deploy — you'll get a public URL.

## Notes

- WhatsApp requires an approved Content Template for messages your app sends on its own initiative (like the summary button), since free-form replies only work within a 24-hour window opened by the user.
- If the WhatsApp summary stops sending, your sandbox opt-in may have expired — just re-send the join message.

## Future Ideas

- Monthly budget limits with overspend warnings
- Store expenses in a table and export to CSV
- Structured JSON output from Gemini for category charts

## License

MIT (or your choice)
