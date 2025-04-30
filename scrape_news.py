import feedparser
from supabase import create_client
import os
from dotenv import load_dotenv
import subprocess


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


tone = "a cool cybersecurity guy explaining the recent developments in a relatable and engaging way but not corny"


try:
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=cybersecurity+when:1d&hl=en-US&gl=US&ceid=US:en")
    articles = [{"title": entry.title, "link": entry.link} for entry in news_feed.entries[:5]]
    supabase.table("news").insert(articles).execute()
except Exception as e:
    print(f"Scraping error: {str(e)}")


try:
    
    combined_titles = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"""
    You are a cybersecurity expert, and your goal is to create an engaging LinkedIn post summarizing the latest cybersecurity developments like new thnigs. Write the post in the following tone:

    - Engaging, contemporary, and educational
    - Avoids overly preachy or generic language
    - Focus on sharp observations, and provide a personal perspective
    - Use clear, modern metaphors and avoid old-sounding phrases
    - Incorporate an insightful question at the end to encourage audience interaction


    Here are the latest headlines:
    {combined_titles}
    """

    
    result = subprocess.run(
    ["C:\\Users\\MAEGHAN\\AppData\\Local\\Programs\\Ollama\\ollama", "run", "mistral"],
    input=prompt.encode("utf-8"),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
    )


    
    summary = result.stdout.decode("utf-8").strip()

    
    supabase.table("summaries").insert({"content": summary, "is_approved": False}).execute()
    print("Success! Summary saved.")

except Exception as e:
    print(f"AI error: {str(e)}")
