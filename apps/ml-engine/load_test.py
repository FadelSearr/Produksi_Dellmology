import asyncio
import aiohttp
import time

ML_BASE = 'http://localhost:8003'

async def fetch_pattern(session, symbol='BBCA'):
    url = f'{ML_BASE}/api/detect-patterns?symbol={symbol}&lookback=100&min_confidence=0.5'
    async with session.get(url) as resp:
        await resp.json()

async def fetch_screen(session, mode='DAYTRADE'):
    url = f'{ML_BASE}/api/screen?mode={mode}&min_score=0.6'
    async with session.get(url) as resp:
        await resp.json()

async def worker(name, n_requests=100):
    async with aiohttp.ClientSession() as session:
        for i in range(n_requests):
            await asyncio.gather(
                fetch_pattern(session),
                fetch_screen(session),
            )
    print(f'{name} done')

async def main():
    tasks = [worker(f'worker{i}', 50) for i in range(5)]
    start = time.time()
    await asyncio.gather(*tasks)
    print('Total time', time.time() - start)

if __name__ == '__main__':
    asyncio.run(main())
