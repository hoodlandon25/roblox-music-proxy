from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import re

app = FastAPI()

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
async def search_songs(request: SearchRequest):
    # Use a standard GET request to avoid Cloudflare AJAX/POST blocks
    url = "https://robloxsong.com/search"
    params = {"q": request.query}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://robloxsong.com/"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Cloudflare/Website blocked request (Status {response.status_code})",
                    "songs": []
                }
            html_content = response.text
        except httpx.RequestError as exc:
            return {
                "success": False,
                "error": f"Connection failed: {str(exc)}",
                "songs": []
            }

    soup = BeautifulSoup(html_content, "html.parser")
    songs = []
    
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            track_name = cols[0].get_text(separator=" ", strip=True)
            id_text = cols[1].get_text(separator=" ", strip=True)
            
            id_match = re.search(r"(\d+)", id_text)
            if id_match:
                clean_id = id_match.group(1)
                
                if track_name.lower() in ["track", "song"] or clean_id.lower() in ["roblox id", "id"]:
                    continue
                
                songs.append({
                    "track": track_name,
                    "id": clean_id
                })
                
    return {"success": True, "songs": songs}
