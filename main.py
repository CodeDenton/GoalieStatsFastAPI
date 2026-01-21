import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException
from typing import List, Dict

app = FastAPI()

SEASON = "20252026"
SITUATION = "2"

TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
    "WPG", "WSH"
]

async def fetch_json(session, url: str):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as res:
            if res.status != 200:
                return None
            return await res.json()
    except:
        return None

@app.get("/goalies")
async def get_goalie_ids():
    goalie_ids = set()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_json(session, f"https://api-web.nhle.com/v1/roster/{team}/current") for team in TEAMS]
        rosters = await asyncio.gather(*tasks)
        for roster in rosters:
            if not roster:
                continue
            for goalie in roster.get("goalies", []):
                player_id = goalie.get("id")
                if player_id:
                    goalie_ids.add(player_id)
    return [{"id": str(gid)} for gid in sorted(list(goalie_ids))]

@app.get("/goalies/full")
async def get_all_goalies(limit: int = None):
    goalie_list = await get_goalie_ids()
    if limit:
        goalie_list = goalie_list[:limit]

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_json(session, f"https://api-web.nhle.com/v1/edge/goalie-detail/{int(g['id'])}/{SEASON}/{SITUATION}")
            for g in goalie_list
        ]
        results = await asyncio.gather(*tasks)
    # filter out None responses
    return [r for r in results if r]

@app.get("/goalies/{player_id}")
async def get_goalie(player_id: int):
    async with aiohttp.ClientSession() as session:
        result = await fetch_json(session, f"https://api-web.nhle.com/v1/edge/goalie-detail/{player_id}/{SEASON}/{SITUATION}")
        if not result:
            raise HTTPException(status_code=500, detail="Failed to fetch goalie")
        return result
