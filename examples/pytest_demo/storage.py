import json
from pathlib import Path

from robot import Robot


class RobotStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def save(self, robot: Robot) -> None:
        text = json.dumps(robot.to_data(), ensure_ascii=False, indent=2)
        self.path.write_text(text + "\n", encoding="utf-8")

    def load(self) -> Robot:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return Robot.from_data(data)
