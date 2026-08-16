from robot import Robot
from storage import RobotStore


def test_store_round_trip(tmp_path) -> None:
    path = tmp_path / "robot.json"
    store = RobotStore(path)
    robot = Robot("Іскра", energy=8)
    robot.move(3)

    store.save(robot)
    restored = store.load()

    assert restored.to_data() == robot.to_data()
    assert path.read_text(encoding="utf-8").endswith("\n")
