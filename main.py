from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import re

app = FastAPI()

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
async def search_songs(request: SearchRequest):
    url = "https://srv.tunefindforfans.com/showads/track/imp.php" # Fallback if direct domains change, or target searches endpoint:
    target_url = "https://robloxsong.com/searches"
    
    # Payload format mimicking the website's search mechanism
    payload = {
        "query": request.query,
        "amount": "15"  # Limit results to keep traffic clean
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(target_url, data=payload, headers=headers, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from source site.")
            html_content = response.text
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Proxy error communicating with source: {str(exc)}")

    # Parse HTML Table rows
    soup = BeautifulSoup(html_content, "html.parser")
    songs = []
    
    # Locate all table rows in returned HTML
    rows = soup.find_all("tr")
    
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            track_name = cols[0].get_text(separator=" ", strip=True)
            id_text = cols[1].get_text(separator=" ", strip=True)
            
            # Extract only the digits representing the Roblox ID (filtering out 'Copy')
            id_match = re.search(r"(\d+)", id_text)
            if id_match:
                clean_id = id_match.group(1)
                
                # Filter out table header placeholders
                if track_name.lower() in ["track", "song"] or clean_id.lower() in ["roblox id", "id"]:
                    continue
                
                songs.append({
                    "track": track_name,
                    "id": clean_id
                })
                
    return {"success": True, "songs": songs}