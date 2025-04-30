import feedparser
from supabase import create_client
import os
from dotenv import load_dotenv
import subprocess
import platform
import sys

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom Ollama path configuration
OLLAMA_PATHS = {
    "Windows": r"C:\\Users\\MAEGHAN\\AppData\\Local\\Programs\\Ollama\\ollama.exe",
    "Linux": "ollama"
}

def get_ollama_path():
    system = platform.system()
    path = OLLAMA_PATHS.get(system)
    
    if not path or not os.path.exists(path):
        print(f"Ollama not found at configured path: {path}")
        print("Please verify Ollama installation or update the OLLAMA_PATHS dictionary")
        sys.exit(1)
        
    return path

# Scrape and process news
try:
    # Scrape Google News RSS feed
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=cybersecurity+when:1d&hl=en-US&gl=US&ceid=US:en")
    
    # Extract top 5 articles
    articles = [{"title": entry.title, "link": entry.link} for entry in news_feed.entries[:5]]
    
    if not articles:
        print("No articles found in RSS feed")
        sys.exit(0)
        
    # Save to Supabase
    supabase.table("news").insert(articles).execute()
    print(f"Inserted {len(articles)} articles into Supabase")

except Exception as e:
    print(f"Scraping error: {str(e)}")
    sys.exit(1)

try:
    # Generate LinkedIn post prompt
    combined_titles = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"""You are a cybersecurity expert creating a LinkedIn post. Use this tone:
    - Engaging, contemporary, and educational
    - Avoid corporate jargon and generic statements
    - Offer sharp insights and personal perspective
    - Use modern analogies
    - End with an engaging question
    
    Recent cybersecurity developments:
    {combined_titles}
    
    Craft a 3-paragraph post and there should be no emojis:"""

    # Get validated Ollama path
    ollama_path = get_ollama_path()

    # Generate summary with Ollama
    result = subprocess.run(
        [ollama_path, "run", "mistral"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300  # 5 minute timeout
    )

    # Handle Ollama output
    if result.returncode != 0:
        print(f"Ollama error: {result.stderr.decode('utf-8')}")
        sys.exit(1)
        
    summary = result.stdout.decode("utf-8").strip()
    
    if not summary:
        print("Received empty summary from Ollama")
        sys.exit(1)

    # Save summary to Supabase
    supabase.table("summaries").insert({
        "content": summary,
        "is_approved": False,
        "posted": False,
    }).execute()
    
    print("Successfully saved summary to Supabase")
    print("Preview:", summary[:200] + "...")

except subprocess.TimeoutExpired:
    print("Ollama response timed out after 5 minutes")
    sys.exit(1)
except Exception as e:
    print(f"AI processing error: {str(e)}")
    sys.exit(1)