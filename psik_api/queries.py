from typing import Optional, Any
import re
import logging
_logger = logging.getLogger(__name__)

import aiohttp

async def get_http(url, json=False) -> Optional[Any]:
    headers = {}
    if json:
        headers['Accept'] = 'application/json'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return None
            #print("Content-type:", response.headers['content-type'])
            if json:
                return await response.json()
            return await response.text()

#web_status = re.compile(r'<div class="system-status" data-system="([^"]*)">.*?<div class="current-status">\s*<div class="([^"]*)">', re.DOTALL)
web_status = re.compile(r'<div class="system-status" data-system="([^"]*)">.*?<div class="current-status">\s*<div class="([^"]*)">.*?</div>\s*(<p>)?\s*([^<]+)</div>', re.DOTALL)
# TODO: also parse <i check></i> Operational <p>Up since Jun 20, 2023 </div>
async def fetch_current_status():
    text = await get_http("https://www.olcf.ornl.gov/for-users/center-status")
    if text is None:
        _logger.error("Error fetching OLCF status web-API")
        return

    stat = {}
    for m in web_status.finditer(text):
        since = " ".join(m.group(4).split())
        stat[m.group(1)] = (m.group(2), since)
    if len(stat) == 0:
        _logger.error("Invalid response from OLCF status web-API")
        return
    else:
        _logger.info("Parsed response from OLCF status web-API:", stat)
    return stat
