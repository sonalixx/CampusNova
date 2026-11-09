# 🏫 CampusNova

A mobile-first smart campus web app for Alliance University, built with Streamlit and Supabase.

**Design Project 1 (E1CSA313)** · Faculty Mentor: Dr. Vinita Nair
**Team:** Bhavishya Raj M.H, Vidhyasri R, Samriddhi Singh, R. Dharshini

## Features

| Tab | What it does |
|---|---|
| 🔐 Login / Sign up | Supabase Auth. Student details are stored in the database. Sessions survive a page refresh. |
| 🏠 Home | Editable student profile with photo, university link, admin notices, light/dark theme. |
| 🧭 Map | Walking routes built from the campus GPX files (Dijkstra), with OSM buildings as background. |
| 🤖 Chat | Campus assistant. Answers from the campus knowledge base and falls back to general knowledge (Groq LLM). Points to the Map for location questions. |
| 🚨 SOS | One-tap emergency alert with a live popup for other users, plus helpline buttons. |
| 🛠 Admin | Admins post notices and edit the chatbot knowledge base. |

## Tech stack

Python · Streamlit · Supabase (Auth, Postgres, Storage) · Folium · Groq API

## Project structure

```
CampusNova/
├── app.py              # entry point: login gate, nav bar, theme, SOS popup
├── auth.py             # login and signup
├── db.py               # Supabase client
├── home_page.py        # profile, notices
├── nav_page.py         # GPX routing and map
├── chat_page.py        # AI assistant
├── kb.py               # starter knowledge base
├── sos_page.py         # emergency alerts
├── admin_page.py       # notices and KB editor
├── supabase_setup.sql  # database setup
├── requirements.txt
├── gpx/                # campus .gpx path files and one .osm file
└── .streamlit/
    ├── config.toml
    └── secrets.toml    # not committed
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 1. Supabase

1. Create a project at supabase.com.
2. Open **SQL Editor**, paste the contents of `supabase_setup.sql` and run it.
3. Go to **Authentication → Sign In / Providers → Email** and turn **Confirm email** off while testing.

### 2. Secrets

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-or-publishable-key"
GROQ_API_KEY = "gsk_..."
```

Use the anon/publishable key only, never the service_role key. Get a free Groq key at console.groq.com/keys.

### 3. GPX files

Put the `.gpx` files in `gpx/`. Each file is one walkable path, and its name gives the place names: `Library to ATM.gpx` creates the places "Library" and "ATM". Paths that come within 12 m of each other are joined automatically.

## Making someone an admin

Sign up in the app first, then run in the Supabase SQL Editor:

```sql
update students set is_admin = true
where id = (select id from auth.users where email = 'person@example.com');
```

They must log out and back in. A **🛠 Admin** tab then appears.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (private is fine). Make sure `secrets.toml` is not committed.
2. At share.streamlit.io choose **Create app**, pick the repo, branch `main`, main file `app.py`.
3. In **Advanced settings → Secrets**, paste the three secrets above.
4. Deploy. The HTTPS link is needed for GPS location to work on phones.
5. In Supabase **Authentication → URL Configuration**, set **Site URL** to the app link.

## Notes and limitations

- Dark mode uses a CSS colour inversion, which is quick but not pixel-perfect.
- The SOS popup checks for new alerts every 10 seconds (polling, not push).
- Location sharing needs HTTPS and the user's permission.
- The free Groq tier has rate limits.