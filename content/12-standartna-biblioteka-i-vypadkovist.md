# Стандартна бібліотека й керована випадковість

Python постачається не лише із синтаксисом, а й із великою **стандартною бібліотекою**. Вона вже містить генератори випадкових чисел, статистику, дати, лічильники, переліки станів і багато інших перевірених інструментів.

## Що зробимо

Створимо генератор тренувальних місій. Він використовуватиме окремий об’єкт випадковості, а перевірка зможе передати фіксоване зерно й отримати повторюваний результат.

:::goal
Випадковість залишиться залежністю, якою керує об’єкт, а не магією, розкиданою по методах. Ти навчишся відрізняти стандартний модуль, сторонній пакет і власний модуль.
:::

## Три джерела імпортів

```python fragment
import random
from statistics import mean

from mission import Mission
```

У типовому файлі імпорти групують так:

1. стандартна бібліотека Python;
2. сторонні пакети, встановлені в середовище;
3. власні локальні модулі.

Між групами залишають порожній рядок. Це допомагає одразу побачити, що потребує `pip`, а що приходить разом із Python.

Стандартні `random`, `statistics`, `collections`, `datetime`, `enum`, `json`, `pathlib`, `math` окремо не встановлюють.

## Майстерня

Створи `mission_generator.py`:

```python run file=mission_generator.py expect="Однаковий результат: True"
import random


class Mission:
    def __init__(self, start, destination, difficulty):
        self.start = start
        self.destination = destination
        self.difficulty = difficulty

    def description(self):
        return (
            f"Маршрут: {self.start} -> {self.destination}, "
            f"складність {self.difficulty}."
        )


class MissionGenerator:
    def __init__(self, places, random_source=None):
        self.places = places.copy()
        self.random_source = random_source or random.Random()

    def create(self):
        start, destination = self.random_source.sample(self.places, k=2)
        difficulty = self.random_source.randint(1, 5)
        return Mission(start, destination, difficulty)


places = ["Маяк", "Ліс", "Порт", "Вежа"]

first_generator = MissionGenerator(places, random.Random(7))
second_generator = MissionGenerator(places, random.Random(7))

first_description = first_generator.create().description()
second_description = second_generator.create().description()

print(first_description)
print(second_description)
print(f"Однаковий результат: {first_description == second_description}")
```

Два різні об’єкти `Random` отримали однакове зерно `7`, тому створили однакову послідовність рішень. У звичайному запуску `random_source` не передається й використовується нове непередбачуване для користувача джерело.

### Залежність передано в конструктор

```python fragment
def __init__(self, places, random_source=None):
    self.places = places.copy()
    self.random_source = random_source or random.Random()
```

Генератор не звертається до глобального `random.choice()` у випадкових місцях. Він зберігає один сумісний об’єкт. Це **впровадження залежності** (*dependency injection*): потрібний інструмент можна передати ззовні.

Назва звучить складно, але дія проста: не створюй незамінний інструмент глибоко всередині кожного методу, якщо перевірці або іншому сценарію може знадобитися контрольована версія.

## Основні інструменти `random`

### Випадковий елемент

```python run file=random_choice.py expect="Обрано відомий напрямок: True"
import random

rng = random.Random(3)
directions = ["північ", "південь", "схід", "захід"]
direction = rng.choice(directions)

print(f"Обрано: {direction}")
print(f"Обрано відомий напрямок: {direction in directions}")
```

`choice(sequence)` потребує непорожню послідовність і повертає один елемент.

### Ціле число з обома межами

```python run file=random_int.py expect="Число в межах кубика: True"
import random

rng = random.Random(5)
roll = rng.randint(1, 6)

print(f"Випало: {roll}")
print(f"Число в межах кубика: {1 <= roll <= 6}")
```

`randint(1, 6)` може повернути і 1, і 6. Це відрізняється від `range()`, де права межа не включається.

Еквівалент через `randrange()`:

```python fragment
rng.randrange(1, 7)
```

`randrange()` працює за правилами `range` й не включає `stop`.

### Кілька різних елементів

```python run file=random_sample.py expect="Кількість: 2\nУсі різні: True"
import random

rng = random.Random(2)
picked = rng.sample(["A", "B", "C", "D"], k=2)

print(picked)
print(f"Кількість: {len(picked)}")
print(f"Усі різні: {len(set(picked)) == len(picked)}")
```

`sample()` повертає новий список без повторного вибору того самого елемента. `k` не може бути більшим за кількість доступних значень.

Для вибору з можливими повторами є `choices(..., k=...)`.

### Перемішування на місці

```python run file=random_shuffle.py expect="Ті самі карти: True"
import random

cards = [1, 2, 3, 4]
original = cards.copy()
rng = random.Random(4)
rng.shuffle(cards)

print(cards)
print(f"Ті самі карти: {sorted(cards) == sorted(original)}")
```

`shuffle()` змінює список і повертає `None`, як `list.sort()`. Якщо початковий порядок треба зберегти, перемішуй копію.

### Дробове число

```python fragment
rng.random()
rng.uniform(1.5, 3.5)
```

`random()` дає `float` від 0 включно до 1 не включно. `uniform(a, b)` — дробове число між межами; точна поведінка крайньої межі залежить від округлення, тому не будуй на ній логіку точного включення.

## Зерно не робить результат випадковішим

Псевдовипадковий генератор створює довгу послідовність за алгоритмом. Однаковий початковий стан — **seed**, або зерно — дає однакову послідовність.

Це корисно для:

- повторюваних тестів;
- відтворення помилки;
- однакової генерації навчального прикладу;
- збереження процедурного світу за кодом зерна.

Не став постійне зерно у звичайній програмі, якщо користувач очікує новий результат кожного запуску. Передавай його лише в перевірці або як усвідомлену функцію продукту.

:::warning Не для паролів і токенів
Модуль `random` не призначений для секретів. Його послідовність відтворювана. Для паролів, токенів і кодів безпеки використовують стандартний модуль `secrets`, наприклад `secrets.choice()` або `secrets.token_urlsafe()`.
:::

## Керована перевірка без вгадування

Можна передати не справжній генератор, а маленький передбачуваний об’єкт із потрібними методами:

```python run file=fake_random.py expect="Маршрут: Ліс -> Порт, складність 4."
class FixedRandom:
    def sample(self, values, k):
        return ["Ліс", "Порт"]

    def randint(self, start, stop):
        return 4


class Mission:
    def __init__(self, start, destination, difficulty):
        self.start = start
        self.destination = destination
        self.difficulty = difficulty

    def description(self):
        return (
            f"Маршрут: {self.start} -> {self.destination}, "
            f"складність {self.difficulty}."
        )


class MissionGenerator:
    def __init__(self, places, random_source):
        self.places = places
        self.random_source = random_source

    def create(self):
        start, destination = self.random_source.sample(self.places, k=2)
        difficulty = self.random_source.randint(1, 5)
        return Mission(start, destination, difficulty)


generator = MissionGenerator(["Ліс", "Порт"], FixedRandom())
print(generator.create().description())
```

`MissionGenerator` не питає, якого класу `random_source`. Йому потрібні сумісні методи `sample()` і `randint()`. Це практичний поліморфізм і основа майбутніх тестових підмін.

## `statistics`: готові обчислення

```python run file=statistics_example.py expect="Середнє: 4\nМедіана: 4\nНайчастіше: 4"
from statistics import mean, median, mode

scores = [2, 4, 4, 6]

print(f"Середнє: {mean(scores):g}")
print(f"Медіана: {median(scores):g}")
print(f"Найчастіше: {mode(scores):g}")
```

- `mean()` — арифметичне середнє;
- `median()` — середнє позиційне значення після впорядкування;
- `mode()` — найчастіше значення.

Порожні дані або неоднозначні припущення треба обробляти відповідно до задачі. Читай документацію функції, а не вгадуй поведінку за назвою.

## `collections.Counter`: словник частот

```python run file=counter_example.py expect="python: 3\nloops: 1"
from collections import Counter

topics = ["python", "oop", "python", "loops", "python"]
counts = Counter(topics)

print(f"python: {counts['python']}")
print(f"loops: {counts['loops']}")
```

`Counter` поводиться як спеціалізований словник лічильників. Для відсутнього ключа повертає 0. Він також має `most_common()`:

```python fragment
top_two = counts.most_common(2)
```

Використання готового типу зменшує власний код, але варто розуміти базову словникову модель, яку він розширює.

## `Enum`: названий набір станів

Рядки `"new"`, `"active"`, `"done"` легко написати з помилкою. Перелік `Enum` дає стани з автодоповненням:

```python run file=enum_status.py expect="Завдання виконується."
from enum import Enum, auto


class TaskStatus(Enum):
    NEW = auto()
    ACTIVE = auto()
    DONE = auto()


class Task:
    def __init__(self, title):
        self.title = title
        self.status = TaskStatus.NEW

    def start(self):
        self.status = TaskStatus.ACTIVE

    def status_text(self):
        if self.status is TaskStatus.ACTIVE:
            return "Завдання виконується."
        if self.status is TaskStatus.DONE:
            return "Завдання завершено."
        return "Завдання нове."


task = Task("Практика")
task.start()
print(task.status_text())
```

Члени переліку порівнюють через `is` або `==`. `auto()` створює внутрішні значення, бо конкретні числа тут не важливі.

Не створюй `Enum` для двох станів, які природно виражає `bool`, наприклад `is_open`. Перелік корисний для трьох і більше взаємовиключних названих станів.

## Дата й час

```python run file=date_example.py expect="2026-08-16\n2026"
from datetime import date

lesson_day = date(2026, 8, 16)

print(lesson_day.isoformat())
print(lesson_day.year)
```

Об’єкти `date` краще за ручні рядки, коли треба порівнювати дні або додавати проміжки. Для поточної дати є `date.today()`, але приклади й тести з фіксованою датою повторюваніші.

Часові пояси — окрема важлива тема. Для реальних моментів часу не змішуй наївні `datetime` з даними різних поясів; використовуй timezone-aware об’єкти й чітко фіксуй зону.

## Як читати документацію модуля

Не треба запам’ятовувати всю бібліотеку. Для нового інструмента перевір:

1. Чи модуль входить до стандартної бібліотеки потрібної версії Python?
2. Які типи приймає функція?
3. Що повертає і чи змінює аргумент?
4. Які винятки можливі?
5. Чи є приклад мінімального використання?
6. Чи підходить інструмент для безпеки й точності конкретної задачі?

У VS Code наведи курсор на ім’я або використай **Go to Definition**. Для повного контракту переходь до офіційної документації Python.

## Сторонній пакет: коли він справді потрібен

Сторонній пакет не входить до стандартного Python. Перед додаванням:

- сформулюй проблему, яку він розв’язує;
- перевір, що пакет підтримується й має документацію;
- використовуй активну `.venv`;
- зафіксуй залежність;
- не підключай експериментальний інструмент до базового навчального матеріалу без причини.

Встановлення стабільного пакета в активне середовище:

```powershell
python -m pip install package_name
```

Після цього імпорт зазвичай має іншу назву, яку треба взяти з документації пакета, а не вгадувати.

## Типова помилка

### Глобальне `random.seed()` змінює весь модуль

```python fragment
import random

random.seed(7)
```

Це змінює глобальний генератор модуля, яким можуть користуватися інші частини програми. Для ізольованого компонента краще `rng = random.Random(7)` і передавання `rng` об’єкту.

### Змішано `choice()` і `sample()`

Два окремі виклики `choice()` можуть вибрати те саме місце двічі. Якщо старт і фініш мають різнитися, `sample(places, k=2)` прямо виражає правило.

### Встановлено назву стандартного модуля

Не запускай `pip install random` або `pip install statistics` для звичайного Python. Спершу спробуй імпорт у чистому файлі й перевір офіційну документацію.

:::mistake
Не перевіряй випадковий код твердженням «результат має бути саме 4», якщо джерело не зафіксоване. Передай seeded `Random` або контрольовану підміну, тоді очікування стає частиною контракту.
:::

## Швидка перевірка

Два генератори з різними зернами повинні мати незалежний стан:

```python run file=independent_random.py expect="[1, 3, 1]\n[1, 1, 1]"
import random

first = random.Random(1)
second = random.Random(2)

print([first.randint(1, 3) for _ in range(3)])
print([second.randint(1, 3) for _ in range(3)])
```

:::quiz
question: Навіщо передавати MissionGenerator окремий random_source?
correct: Щоб звичайний запуск мав випадковість, а перевірка могла підставити повторюване джерело.
option: Щоб модуль random став стороннім пакетом.
option: Щоб кожна місія завжди була однаковою для користувача.
explanation: Явна залежність дозволяє керувати випадковістю без зміни логіки генератора.
:::

## Самостійна робота

:::tasks
- Створи генератор кидків кубика з переданим `random.Random`. Перевір однакові серії для однакових зерен і різні — для різних.
- Згенеруй випадкову команду з трьох різних імен через `sample()`. Оброби випадок, коли доступних імен менше трьох.
- Зроби об’єкт `Deck`, який зберігає карти, перемішує копію й роздає через `pop()`. Початковий список зовні не повинен змінюватися.
- Порахуй частоти слів через звичайний словник, а потім через `Counter`. Порівняй обсяг коду й структуру результату.
- Створи `Enum` для станів замовлення `NEW`, `PAID`, `SENT`, `DELIVERED`. Методи мають дозволяти лише логічні переходи.
- Передай генератору маленький `FixedRandom`, який повертає заготовлені значення. Перевір поведінку без справжньої випадковості.
- Знайди в офіційній документації один стандартний модуль для власної задачі. Запиши його вхід, результат, можливу помилку й мінімальний приклад.
- Поясни, чому `random` не підходить для коду відновлення пароля, і створи окремий безпечний приклад із `secrets.token_urlsafe()` без публікації отриманого токена.
:::

:::history
Псевдовипадкова послідовність детермінована, але для людини виглядає хаотично. Саме повторюваність робить її корисною в моделюванні й тестах. Криптографічна випадковість має іншу мету й суворіші вимоги, тому Python розділяє `random` і `secrets`.
:::

## Підсумок

- Стандартна бібліотека постачається з Python; сторонні пакети встановлюють окремо у віртуальне середовище.
- `Random` можна створити як незалежний об’єкт і передати компоненту.
- Однакове зерно дає повторювану послідовність, що корисно для перевірок і відтворення помилок.
- `choice()`, `randint()`, `sample()`, `shuffle()` і `random()` мають різні контракти.
- `random` не підходить для секретів; для них існує `secrets`.
- `statistics`, `Counter`, `Enum` і `datetime` розв’язують поширені задачі без власного повторного винаходу.
- Перед додаванням залежності перевір призначення, підтримку, документацію й спосіб відтворення середовища.
- Випадкову залежність краще передавати явно, щоб об’єкт лишався керованим і тестованим.

Офіційні орієнтири: [`random`](https://docs.python.org/3/library/random.html), [`secrets`](https://docs.python.org/3/library/secrets.html), [`statistics`](https://docs.python.org/3/library/statistics.html), [`collections.Counter`](https://docs.python.org/3/library/collections.html#collections.Counter), [`enum`](https://docs.python.org/3/library/enum.html).
