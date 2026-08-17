# Методи: параметри, аргументи й `return`

Об’єкт уже вміє зберігати стан. Тепер навчимо його приймати команди з додатковими даними, перевіряти результат своєї роботи та повертати значення тому коду, який викликав метод.

## Що зробимо

Створимо героя, який отримує лікування й витрачає енергію на удар. Одні методи змінюватимуть стан, інші — обчислюватимуть і **повертатимуть** результат без друку.

:::goal
Після розділу ти зможеш простежити шлях значення: від аргументу у виклику — до параметра методу — до нового стану або результату `return`.
:::

## Команді часто потрібні додаткові дані

Метод `robot.move()` може завжди рухати робота на однакову відстань. Але команда `hero.heal(15)` повинна знати, скільки саме здоров’я відновити.

```python fragment
class Hero:
    def heal(self, amount):
        self.health += amount
```

`amount` у визначенні методу — **параметр**. Він позначає місце для майбутнього значення.

```python fragment
hero.heal(15)
```

`15` у виклику — **аргумент**, тобто конкретне значення, передане параметру.

Коротко:

- параметр живе у загальному описі методу;
- аргумент з’являється під час конкретного виклику;
- `self` теж параметр, але об’єкт для нього Python підставляє автоматично.

## Майстерня

Створи файл `hero_actions.py`:

```python run file=hero_actions.py expect="Міра: 70 здоров’я, 25 енергії.\nУдар завдав 12 шкоди.\nМіра: 85 здоров’я, 17 енергії."
class Hero:
    def __init__(self, name, health=100, energy=30):
        self.name = name
        self.health = health
        self.energy = energy

    def heal(self, amount):
        self.health += amount

    def strike(self, damage, energy_cost=8):
        self.energy -= energy_cost
        return damage

    def status_text(self):
        return f"{self.name}: {self.health} здоров’я, {self.energy} енергії."


hero = Hero("Міра", health=70, energy=25)

print(hero.status_text())
hero.heal(15)
dealt_damage = hero.strike(12)

print(f"Удар завдав {dealt_damage} шкоди.")
print(hero.status_text())
```

Тут є три різні види роботи:

- `heal()` змінює стан;
- `strike()` змінює стан і повертає число;
- `status_text()` не змінює стан, а складає й повертає текст.

### Значення за замовчуванням

У заголовку `__init__` два параметри мають готові значення:

```python fragment
def __init__(self, name, health=100, energy=30):
```

Тому всі ці виклики правильні:

```python fragment
first = Hero("Міра")
second = Hero("Орест", 80)
third = Hero("Лея", 70, 50)
```

- `first` отримає `health=100`, `energy=30`;
- `second` отримає `health=80`, `energy=30`;
- `third` отримає всі передані значення.

Обов’язкові параметри ставлять перед параметрами зі значенням за замовчуванням. Такий заголовок був би помилковим: `def __init__(self, health=100, name):`.

:::note Стабільне значення за замовчуванням
Для числа, рядка, `True`, `False` або `None` значення за замовчуванням безпечне. Змінні списки й словники потребують іншого прийому; ми розберемо його після знайомства з колекціями.
:::

### Позиційні й іменовані аргументи

У виклику `Hero("Міра", 70, 25)` Python зіставляє значення з параметрами за позицією. Це **позиційні аргументи**.

```python fragment
hero = Hero("Міра", health=70, energy=25)
```

`health=70` та `energy=25` — **іменовані аргументи**. Вони довші, але не дають переплутати два схожих числа.

Позиційні аргументи мають стояти перед іменованими:

```python fragment
hero = Hero("Міра", energy=25, health=70)
```

Порядок двох іменованих аргументів уже не важливий.

:::practice Перевір різні виклики
Створи трьох героїв:

```python run file=hero_defaults.py expect="Ада: 100/30\nБор: 60/30\nВіра: 90/45"
class Hero:
    def __init__(self, name, health=100, energy=30):
        self.name = name
        self.health = health
        self.energy = energy

    def short_status(self):
        return f"{self.name}: {self.health}/{self.energy}"


first = Hero("Ада")
second = Hero("Бор", 60)
third = Hero("Віра", energy=45, health=90)

print(first.short_status())
print(second.short_status())
print(third.short_status())
```

Поясни, звідки взялося кожне число: з аргументу чи зі значення за замовчуванням.
:::

## `return` передає результат назовні

Порівняй два методи:

```python fragment
def print_status(self):
    print(f"Здоров’я: {self.health}")

def status_text(self):
    return f"Здоров’я: {self.health}"
```

Перший сам вирішує, що результат треба показати в терміналі. Другий лише готує текст і віддає його виклику. Тому з `status_text()` можна зробити більше:

```python fragment
message = hero.status_text()
print(message)
save_later = message
```

Пізніше цей текст можна буде показати у графічному інтерфейсі, записати у файл або перевірити тестом. Метод не прив’язаний до одного способу використання.

Рядок із `return` одразу завершує метод:

```python fragment
def double(self, number):
    return number * 2
    print("Цей рядок не виконається.")
```

Код після виконаного `return` у тому самому блоці недосяжний.

### Метод без явного `return` повертає `None`

```python run file=none_result.py expect="Лікування завершено.\nNone"
class Hero:
    def heal(self, amount):
        print("Лікування завершено.")


hero = Hero()
result = hero.heal(10)
print(result)
```

`None` означає «корисного значення тут немає». Це окремий об’єкт Python, а не нуль, не порожній рядок і не `False`.

Не треба додавати `return None` наприкінці кожного методу: Python робить це неявно. Явний `return` потрібен, коли ми справді хочемо передати результат або достроково завершити роботу.

### Обчислення краще відділяти від виведення

```python run file=travel_cost.py expect="Подорож коштує 36 монет."
class Journey:
    def __init__(self, price_per_step):
        self.price_per_step = price_per_step

    def calculate_cost(self, steps):
        return self.price_per_step * steps


journey = Journey(price_per_step=3)
cost = journey.calculate_cost(12)
print(f"Подорож коштує {cost} монет.")
```

Метод рахує, а зовнішній код вирішує, як використати число. Це простий приклад **поділу відповідальності**: кожна частина має одну зрозумілу роботу.

## Передавання об’єкта методу

Аргументом може бути не лише число або рядок, а й інший об’єкт.

```python run file=training.py expect="Тренування: Ніка -> Рей.\nРей отримує 3 досвіду."
class Hero:
    def __init__(self, name):
        self.name = name
        self.experience = 0

    def train(self, student, points):
        student.experience += points
        return f"Тренування: {self.name} -> {student.name}."

    def experience_text(self):
        return f"{self.name} отримує {self.experience} досвіду."


mentor = Hero("Ніка")
student = Hero("Рей")

print(mentor.train(student, 3))
print(student.experience_text())
```

Усередині `train()` параметр `student` посилається на той самий об’єкт, що й зовнішнє ім’я `student`. Тому зміна `student.experience` зберігається після завершення методу.

Це потужна можливість, але користуйся нею зрозуміло: назва методу має підказувати, що стан іншого об’єкта зміниться.

## Типова помилка

### Виклик не відповідає параметрам

```python error file=missing_argument.py raises=TypeError
class Hero:
    def heal(self, amount):
        print(f"Відновлено: {amount}")


hero = Hero()
hero.heal()
```

```output
Traceback (most recent call last):
  File "...\missing_argument.py", line 7, in <module>
    hero.heal()
TypeError: Hero.heal() missing 1 required positional argument: 'amount'
```

Останній рядок називає метод і параметр `amount`, для якого не передали значення.

```python error file=too_many_arguments.py raises=TypeError
class Hero:
    def heal(self, amount):
        print(f"Відновлено: {amount}")


hero = Hero()
hero.heal(10, 20)
```

```output
Traceback (most recent call last):
  File "...\too_many_arguments.py", line 7, in <module>
    hero.heal(10, 20)
TypeError: Hero.heal() takes 2 positional arguments but 3 were given
```

У повідомленні враховано й прихований для виклику `self`: метод має два параметри `self` та `amount`, але отримав об’єкт плюс два числа — разом три аргументи.

### Результат надруковано двічі

```python run file=printed_none.py expect="Герой готовий.\nNone"
class Hero:
    def status_text(self):
        print("Герой готовий.")


hero = Hero()
print(hero.status_text())
```

```output
Герой готовий.
None
```

Метод спочатку друкує повідомлення, а потім неявно повертає `None`; зовнішній `print()` показує саме це повернене значення. Якщо зовнішній код має друкувати результат, метод повинен **повертати** рядок:

```python fragment
def status_text(self):
    return "Герой готовий."
```

:::mistake
Не пиши `return print(...)`, коли хочеш повернути текст. `print()` показує значення й повертає `None`. Спочатку склади рядок, поверни його через `return`, а друкуй у місці виклику.
:::

## Швидка перевірка

Спочатку визнач, які значення потраплять у параметри `minutes` і `intensity`, і лише тоді запускай:

```python run file=music_player.py expect="18\nЗалишилося 42 хв."
class MusicPlayer:
    def __init__(self, battery=60):
        self.battery = battery

    def play(self, minutes, intensity=1):
        used = minutes * intensity
        self.battery -= used
        return used

    def battery_text(self):
        return f"Залишилося {self.battery} хв."


player = MusicPlayer()
spent = player.play(minutes=9, intensity=2)

print(spent)
print(player.battery_text())
```

:::quiz
question: Навіщо метод status_text() повертає рядок, а не одразу друкує його?
correct: Щоб код, який викликав метод, сам вирішив, як використати готовий текст.
option: Бо методи класу не можуть використовувати print().
option: Щоб атрибути об’єкта стали глобальними змінними.
explanation: return віддає значення назовні. Його можна надрукувати, зберегти, записати у файл або перевірити тестом.
:::

## Самостійна робота

:::tasks
- Додай герою метод `rest(minutes)`, який відновлює по 2 одиниці енергії за хвилину й повертає фактично додану кількість.
- Створи клас `Calculator` з методами `add(a, b)`, `subtract(a, b)` і `square(number)`. Усі методи мають повертати значення, а друк зроби поза класом.
- Створи клас `Ticket` з обов’язковою назвою події та ціною за замовчуванням 100. Створи три квитки різними поєднаннями позиційних та іменованих аргументів.
- Перероби метод, який одночасно рахує і друкує вартість, на два кроки: метод повертає число, зовнішній код формує повідомлення.
- Створи два об’єкти `Pet`. Нехай метод одного об’єкта `share_food(other, amount)` зменшує його запас їжі й збільшує запас іншого.
- Навмисно виклич метод без обов’язкового аргументу. Знайди в останньому рядку traceback назву методу та опис відсутнього параметра, після чого виправ виклик.
:::

:::history
Слово `return` буквально означає «повернути». Значення ніби проходить усередину методу через аргументи, опрацьовується, а потім повертається до місця виклику. Ця схема існувала в мовах задовго до Python і лишається одним з головних способів складати великі програми з малих частин.
:::

## Підсумок

- Параметр описує місце для значення, аргумент передає конкретне значення під час виклику.
- `self` Python передає автоматично, решту обов’язкових аргументів передає програміст.
- Значення за замовчуванням робить аргумент необов’язковим.
- Іменовані аргументи пояснюють зміст і не залежать від взаємного порядку.
- `return` передає результат коду, який викликав метод, і завершує метод.
- Метод без явного `return` повертає `None`.
- Обчислення, зміна стану й показ результату — різні відповідальності; їх корисно бачити окремо.
- Аргументом може бути інший об’єкт, і метод може взаємодіяти з його станом.
