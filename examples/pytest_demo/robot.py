class EnergyError(ValueError):
    """Рух неможливий через неправильну кількість енергії."""


class Robot:
    def __init__(self, name: str, energy: int = 10) -> None:
        if not name.strip():
            raise ValueError("Ім’я не може бути порожнім")
        if energy < 0:
            raise EnergyError("Енергія не може бути від’ємною")

        self.name = name.strip()
        self.energy = energy
        self.distance = 0

    def move(self, steps: int) -> int:
        if steps <= 0:
            raise ValueError("Кількість кроків має бути додатною")
        if steps > self.energy:
            raise EnergyError("Не вистачає енергії")

        self.energy -= steps
        self.distance += steps
        return self.distance

    def to_data(self) -> dict[str, object]:
        return {
            "name": self.name,
            "energy": self.energy,
            "distance": self.distance,
        }

    @classmethod
    def from_data(cls, data: dict[str, object]) -> "Robot":
        robot = cls(str(data["name"]), int(data["energy"]))
        robot.distance = int(data["distance"])
        return robot
