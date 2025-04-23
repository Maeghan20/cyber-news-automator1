import feedparser
from supabase import create_client
import os
import google.generativeai as genai

# Configure API keys from environment variables
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# Initialize AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Scrape Google News
try:
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=cybersecurity+when:1d&hl=en-US&gl=US&ceid=US:en")
    articles = [{"title": entry.title, "link": entry.link} for entry in news_feed.entries[:5]]
    supabase.table("news").insert(articles).execute()
except Exception as e:
    print(f"Scraping error: {str(e)}")

# Generate LinkedIn Post
try:
    prompt = f"Create a LinkedIn post summarizing these cybersecurity articles in bullet points with emojis and hashtags: {articles}"
    response = model.generate_content(prompt)
    summary = response.text
    supabase.table("summaries").insert({"content": summary, "is_approved": False}).execute()
    print("Success! Summary saved.")
except Exception as e:
    print(f"AI error: {str(e)}")