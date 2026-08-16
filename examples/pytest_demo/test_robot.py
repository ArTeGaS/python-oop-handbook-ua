import pytest

from robot import EnergyError, Robot


@pytest.fixture
def robot() -> Robot:
    return Robot("Робі", energy=10)


def test_new_robot_has_expected_state(robot: Robot) -> None:
    assert robot.name == "Робі"
    assert robot.energy == 10
    assert robot.distance == 0


def test_move_changes_energy_and_distance(robot: Robot) -> None:
    result = robot.move(3)

    assert result == 3
    assert robot.energy == 7
    assert robot.distance == 3


def test_failed_move_preserves_state(robot: Robot) -> None:
    with pytest.raises(EnergyError, match="Не вистачає"):
        robot.move(11)

    assert robot.energy == 10
    assert robot.distance == 0


@pytest.mark.parametrize("steps", [0, -1, -20])
def test_move_rejects_nonpositive_steps(robot: Robot, steps: int) -> None:
    with pytest.raises(ValueError, match="додатною"):
        robot.move(steps)
