import asyncio
from matrix.matrix import Matrix
from matrix.config import Config, ComponentConfig

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_matrix())

async def setup_matrix():
    config = Config(
        "192.168.178.48", 
        [
            # ComponentConfig(name = "imu", port = 20013),
            # ComponentConfig(name = "humidity", port = 20013 + 4),
            # ComponentConfig(name = "everloop", port = 20013 + (4 * 2)),
            # ComponentConfig(name = "pressure", port = 20013 + (4 * 3)),
            # ComponentConfig(name = "uv", port = 20013 + (4 * 4)),
            ComponentConfig(name = "zigbee", port = 40000 + 1)
        ]
    )
    matrix = await Matrix.create(config)

    for c in matrix.components:
        print(c.name)

    # everloop = next(c for c in matrix.components if c.name == "everloop")
    # everloop.set_uniform_color(0,150,150,0)

    zigbee = next(c for c in matrix.components if c.name == "zigbee")
    loop = asyncio.get_event_loop()
    loop.create_task(zigbee.services.checkGatewayActive())

    toggledOnce = False

    while True:
        if len(zigbee.devices) > 0 and not toggledOnce:
            zigbee.devices[0].toggle()
            toggledOnce = True
        await asyncio.sleep(1)

if __name__ == "__main__":
    main()