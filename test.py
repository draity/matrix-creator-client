import asyncio
from matrix.matrix import Matrix
from matrix.config import Config, ComponentConfig

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_matrix())

async def setup_matrix():
    config = Config("192.168.178.48", [ComponentConfig(port = 20013 + 4)])
    matrix = await Matrix.create(config)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    main()