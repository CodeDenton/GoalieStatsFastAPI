import requests
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException
from typing import List, Dict

app = FastAPI()

SEASON = "20252026"
SITUATION = "2"

def fetch_team_roster(team_abbrev: str) -> Dict:
    url = f"https://api-web.nhle.com/v1/roster/{team_abbrev}/current"
    res = requests.get(url, timeout=5)
    if res.status_code != 200:
        return {}
    return res.json()

def fetch_all_goalie_ids() -> List[int]:
    goalie_ids = set()
    teams = [
        "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET",
        "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT",
        "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
        "WPG", "WSH"
    ]
    for team in teams:
        try:
            roster = fetch_team_roster(team)
            goalies = roster.get("goalies", [])
            for goalie in goalies:
                player_id = goalie.get("id")
                if player_id:
                    goalie_ids.add(player_id)
        except:
            continue
    return sorted(list(goalie_ids))

def fetch_goalie_detail(player_id: int):
    url = f"https://api-web.nhle.com/v1/edge/goalie-detail/{player_id}/{SEASON}/{SITUATION}"
    res = requests.get(url, timeout=5)
    if res.status_code != 200:
        raise Exception("NHL API failed")
    return res.json()

async def fetch_goalie_detail_async(session, player_id: int):
    url = f"https://api-web.nhle.com/v1/edge/goalie-detail/{player_id}/{SEASON}/{SITUATION}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                return None
            return await response.json()
    except:
        return None

@app.get("/goalies")
def get_goalie_ids():
    try:
        goalie_ids = fetch_all_goalie_ids()
        return [{"id": str(gid)} for gid in goalie_ids]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch goalie IDs: {str(e)}")

@app.get("/goalies/full")
async def get_all_goalies(limit: int = None):
    goalie_ids = get_goalie_ids()
    if limit:
        goalie_ids = goalie_ids[:limit]
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_goalie_detail_async(session, int(g["id"])) for g in goalie_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for i, response in enumerate(responses):
            if response and not isinstance(response, Exception):
                results.append(response)
    return results

@app.get("/goalies/{player_id}")
def get_goalie(player_id: int):
    try:
        return fetch_goalie_detail(player_id)
    except:
        raise HTTPException(status_code=500, detail="Failed to fetch goalie")
