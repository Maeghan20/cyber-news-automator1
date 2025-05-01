import feedparser
from supabase import create_client
import os
import subprocess
import platform
import sys
from shutil import which
from dotenv import load_dotenv
import requests

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Unsplash configuration
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def get_ollama_path():
    """Dynamically locate Ollama executable"""
    if platform.system() == "Windows":
        win_path = r"C:\Users\MAEGHAN\AppData\Local\Programs\Ollama\ollama.exe"
        if os.path.exists(win_path):
            return win_path
        raise FileNotFoundError(f"Ollama not found at {win_path}")
    
    # For Linux/GitHub Actions
    linux_path = which("ollama")
    if linux_path and os.access(linux_path, os.X_OK):
        return linux_path
    
    raise FileNotFoundError("Ollama not found in PATH. Install with: curl -fsSL https://ollama.com/install.sh | sh")

# Trusted cybersecurity sources
FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss.xml",
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/securityweek"
]

def fetch_unsplash_image(query="cybersecurity"):
    """Fetch an image URL from Unsplash API based on a search query"""
    url = f"https://api.unsplash.com/photos/random?client_id={UNSPLASH_ACCESS_KEY}&query={query}&orientation=landscape"
    response = requests.get(url)
    if response.status_code == 200:
        image_data = response.json()
        return image_data['urls']['regular']
    return None

try:
    # Scrape articles
    all_articles = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            all_articles.append({
                "title": entry.title,
                "link": entry.link
            })

    if not all_articles:
        print("No articles scraped.")
        sys.exit(0)

    supabase.table("news").insert(all_articles).execute()
    print(f"Inserted {len(all_articles)} articles")

    # Generate prompt
    combined_titles = "\n".join([f"- {a['title']}" for a in all_articles])
    prompt = f"""You're a cybersecurity expert writing a LinkedIn post for industry peers. 
    Summarize 3–5 of the most impactful, recent cybersecurity developments from the list below.

    Each item should:
    - Highlight a key shift (e.g., tech, breach, legislation, tactic)
    - Include a short but sharp insight (~3–5 sentences)
    - Avoid generic news tone and corny language

    The overall post should:
    - Be engaging, informative, and sound like a human who knows their field
    - Avoid emojis, fluff, or overly dramatic metaphors
    - End with a question that sparks thoughtful discussion

    News headlines:
    {combined_titles}

    Write a clean, LinkedIn-ready post that a seasoned cybersecurity professional would be proud to share."""

    # Get validated Ollama path
    ollama_path = get_ollama_path()
    
    # Run Ollama
    result = subprocess.run(
        [ollama_path, "run", "mistral"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3000
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Ollama error: {result.stderr.decode()}")

    summary = result.stdout.decode().strip()

    # Fetch an image from Unsplash
    image_url = fetch_unsplash_image("cybersecurity")  # You can change the query as needed

    # Save summary and image to Supabase
    supabase.table("summaries").insert({
        "content": summary,
        "is_approved": False,
        "posted": False,
        "image_url": image_url,
    }).execute()
    print("Summary and image saved successfully")

except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)

