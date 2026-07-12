#!/usr/bin/env python3
"""
Hermes Bridge Agent
Connects local ROS2 to Hermes Cloud via WebSocket.
Run this on your local machine (WSL2).
"""
import asyncio
import json
import logging
import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import websockets

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HERMES_WS_URL = os.getenv(
    "HERMES_WS_URL",
    "wss://hermes-cloud-y1i2.onrender.com/ws/robot"
)


class RobotController(Node):
    def __init__(self):
        super().__init__("hermes_bridge")
        self.cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)
        logger.info("ROS2 node initialized")

    def move(self, linear_x: float = 0.0, angular_z: float = 0.0):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel.publish(msg)
        logger.info(f"Published cmd_vel: linear={linear_x}, angular={angular_z}")

    def stop(self):
        self.move(0.0, 0.0)


def handle_command(robot: RobotController, command: dict) -> str:
    action = command.get("action", "")
    speed = float(command.get("speed", 0.3))

    actions = {
        "move_forward":  lambda: robot.move(linear_x=speed),
        "move_backward": lambda: robot.move(linear_x=-speed),
        "turn_left":     lambda: robot.move(angular_z=speed),
        "turn_right":    lambda: robot.move(angular_z=-speed),
        "stop":          lambda: robot.stop(),
    }

    if action in actions:
        actions[action]()
        return f"OK: {action}"
    return f"Unknown action: {action}"


async def bridge(robot: RobotController):
    logger.info(f"Connecting to {HERMES_WS_URL}")
    while True:
        try:
            async with websockets.connect(HERMES_WS_URL) as ws:
                logger.info("Connected to Hermes Cloud")
                await ws.send(json.dumps({"status": "bridge_ready"}))
                async for message in ws:
                    command = json.loads(message)
                    result = handle_command(robot, command)
                    await ws.send(json.dumps({"result": result}))
        except Exception as e:
            logger.error(f"Connection error: {e}, retrying in 5s...")
            await asyncio.sleep(5)


async def main():
    rclpy.init()
    robot = RobotController()
    try:
        await bridge(robot)
    finally:
        robot.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
