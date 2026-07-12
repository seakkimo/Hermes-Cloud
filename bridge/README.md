# Hermes Bridge Agent

Connects local ROS2 / Gazebo to Hermes Cloud via WebSocket.

## Setup (WSL2)

```bash
# Install dependencies
pip3 install websockets

# Run
python3 bridge_agent.py
```

## Supported Commands

| action | description |
|--------|-------------|
| `move_forward` | Move robot forward |
| `move_backward` | Move robot backward |
| `turn_left` | Turn robot left |
| `turn_right` | Turn robot right |
| `stop` | Stop robot |

## Example command from Hermes

```json
{"action": "move_forward", "speed": 0.3}
```
