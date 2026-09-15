import asyncio
import aiohttp
import re
from typing import List, Tuple, Optional, Dict
from config import config

class ProxyManager:
    def __init__(self, db):
        self.db = db

    def parse_proxy(self, proxy_str: str) -> Optional[Dict]:
        """Parse ANY proxy format"""
        proxy_str = proxy_str.strip()

        # Remove protocol if present
        proxy_str = re.sub(r'^https?://', '', proxy_str)
        proxy_str = re.sub(r'^socks[45]?://', '', proxy_str)

        # Split by :
        parts = proxy_str.split(':')

        if len(parts) == 2:
            # Format: host:port
            host, port = parts
            return {
                'host': host,
                'port': port,
                'username': None,
                'password': None,
                'auth': False
            }

        elif len(parts) == 4:
            # Format: host:port:user:pass
            host, port, user, pwd = parts
            return {
                'host': host,
                'port': port,
                'username': user,
                'password': pwd,
                'auth': True
            }

        elif len(parts) == 3:
            # Format: host:port:auth (some providers)
            host, port, auth = parts
            # Try to split auth
            if '@' in auth:
                user, pwd = auth.split('@', 1)
                return {
                    'host': host,
                    'port': port,
                    'username': user,
                    'password': pwd,
                    'auth': True
                }

        return None

    def build_proxy_url(self, parsed: Dict, auth_type='standard') -> str:
        """Build proxy URL in different formats"""
        host = parsed['host']
        port = parsed['port']
        user = parsed.get('username')
        pwd = parsed.get('password')

        if not parsed['auth']:
            return f"http://{host}:{port}"

        if auth_type == 'standard':
            # user:pass@host:port
            return f"http://{user}:{pwd}@{host}:{port}"
        elif auth_type == 'swapped':
            # pass:user@host:port
            return f"http://{pwd}:{user}@{host}:{port}"
        elif auth_type == 'encoded':
            # URL encoded
            from urllib.parse import quote
            return f"http://{quote(user)}:{quote(pwd)}@{host}:{port}"

        return f"http://{user}:{pwd}@{host}:{port}"

    async def check_proxy(self, proxy_str: str) -> Tuple[bool, float, str]:
        """Check proxy - SIMPLE and RELIABLE"""
        parsed = self.parse_proxy(proxy_str)
        if not parsed:
            return False, 0.0, "parse_error"

        # Try different auth formats
        auth_types = ['standard', 'swapped'] if parsed['auth'] else ['none']

        for auth_type in auth_types:
            try:
                proxy_url = self.build_proxy_url(parsed, auth_type)

                timeout = aiohttp.ClientTimeout(total=20)
                start = asyncio.get_event_loop().time()

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Simple test - just check if we can reach Google
                    async with session.get(
                        'https://www.google.com/generate_204',
                        proxy=proxy_url,
                        ssl=False
                    ) as response:
                        latency = asyncio.get_event_loop().time() - start

                        if response.status == 204:
                            return True, latency, auth_type

            except asyncio.TimeoutError:
                continue
            except aiohttp.ClientProxyConnectionError:
                continue
            except aiohttp.ClientHttpProxyError as e:
                if e.status == 407:
                    # Auth failed, try next format
                    continue
                continue
            except Exception:
                continue

        return False, 0.0, "failed"

    async def import_proxies(self, proxy_data: str) -> Dict[str, int]:
        """Import and validate proxies"""
        lines = proxy_data.strip().split('\n')
        live = 0
        dead = 0
        invalid = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parsed = self.parse_proxy(line)
            if not parsed:
                invalid += 1
                continue

            # Validate
            is_live, latency, auth_type = await self.check_proxy(line)

            if is_live:
                await self.db.add_proxy(line, 'http')
                await self.db.update_proxy_status(line, 'live', latency)
                live += 1
            else:
                dead += 1

        return {"live": live, "dead": dead, "invalid": invalid}

    async def validate_all_proxies(self, status_callback=None):
        """Re-validate all proxies"""
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute("SELECT proxy_string FROM proxies")
            rows = await cursor.fetchall()

        live_count = 0
        for row in rows:
            proxy = row[0]
            is_live, latency, auth_type = await self.check_proxy(proxy)

            if is_live:
                await self.db.update_proxy_status(proxy, 'live', latency)
                live_count += 1
                if status_callback:
                    await status_callback(f"✅ {proxy[:40]}... ({latency:.2f}s)")
            else:
                await self.db.update_proxy_status(proxy, 'dead')
                if status_callback:
                    await status_callback(f"❌ {proxy[:40]}...")

        return live_count

    async def get_working_proxy(self) -> Optional[Dict]:
        """Get a working proxy"""
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                "SELECT proxy_string FROM proxies WHERE status='live' ORDER BY response_time ASC LIMIT 10"
            )
            rows = await cursor.fetchall()

        for row in rows:
            proxy_str = row[0]
            parsed = self.parse_proxy(proxy_str)
            if parsed:
                # Test each auth format
                for auth_type in ['standard', 'swapped'] if parsed['auth'] else ['none']:
                    proxy_url = self.build_proxy_url(parsed, auth_type)
                    return {
                        'server': f"http://{parsed['host']}:{parsed['port']}",
                        'username': parsed.get('username'),
                        'password': parsed.get('password'),
                        'original': proxy_str,
                        'url': proxy_url
                    }

        return None

    async def get_single_proxy(self) -> Optional[Dict]:
        return await self.get_working_proxy()

    async def report_proxy_failure(self, proxy_str: str):
        await self.db.mark_proxy_failed(proxy_str)
