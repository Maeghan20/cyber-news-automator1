import feedparser
from supabase import create_client
import os
import subprocess
import platform
import sys
from shutil import which
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

try:
    # Scrape articles
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=cybersecurity+when:1d&hl=en-US&gl=US&ceid=US:en")
    articles = [{"title": entry.title, "link": entry.link} for entry in news_feed.entries[:5]]
    supabase.table("news").insert(articles).execute()
    print(f"Inserted {len(articles)} articles")

    # Generate prompt
    combined_titles = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"""Create a LinkedIn post with:
    - Engaging cybersecurity insights
    - Modern analogies
    - Ending question
    News: {combined_titles}"""

    # Get validated Ollama path
    ollama_path = get_ollama_path()
    
    # Run Ollama
    result = subprocess.run(
        [ollama_path, "run", "mistral"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Ollama error: {result.stderr.decode()}")

    summary = result.stdout.decode().strip()
    supabase.table("summaries").insert({"content": summary, "is_approved": False}).execute()
    print("Summary saved successfully")

except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)