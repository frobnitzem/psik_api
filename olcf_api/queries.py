from typing import Optional, Any

import aiohttp

async def get_json(url) -> Optional[Any]:
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return None
            #print("Content-type:", response.headers['content-type'])
            body = await response.json()
    return body
