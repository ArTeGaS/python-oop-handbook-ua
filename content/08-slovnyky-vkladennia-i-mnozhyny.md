# Словники, вкладені дані й множини

Список знаходить елемент за позицією: нульовий, перший, останній. Але налаштування зручніше шукати за змістом: `volume`, `language`, `difficulty`. **Словник** пов’язує ключ із відповідним значенням.

## Що зробимо

Створимо профіль гравця з налаштуваннями, досягненнями й статистикою. Побачимо, коли словник є частиною стану класу, а коли сам клас уже зайвий або, навпаки, необхідний.

:::goal
Ти зможеш безпечно читати й змінювати значення за ключем, перебирати пари, будувати вкладені дані та відрізняти словник даних від об’єкта з поведінкою.
:::

## Словник пов’язує ключ і значення

```python fragment
settings = {
    "volume": 70,
    "language": "uk",
    "show_hints": True,
}
```

Фігурні дужки позначають словник `dict`. Кожна пара має форму `key: value`.

- ключ `"volume"` веде до числа `70`;
- ключ `"language"` — до рядка `"uk"`;
- ключ `"show_hints"` — до логічного значення.

Ключі в одному словнику мають бути унікальними. Якщо записати той самий ключ повторно, пізніше значення замінить попереднє.

З Python 3.7 порядок вставлення ключів є гарантованою властивістю мови. Але звертатися до словника все одно треба за змістовним ключем, а не будувати логіку на «другій парі».

## Майстерня

Створи `player_profile.py`:

```python run file=player_profile.py expect="Мова: uk, гучність: 70, підказки: так.\nДосягнення відкрито: Перший крок.\nМова: uk, гучність: 40, підказки: так.\nДосліджено кімнат: 3."
class PlayerProfile:
    def __init__(self, name):
        self.name = name
        self.settings = {
            "volume": 70,
            "language": "uk",
            "show_hints": True,
        }
        self.statistics = {}
        self.achievements = []

    def change_setting(self, key, value):
        if key not in self.settings:
            return f"Невідоме налаштування: {key}."
        self.settings[key] = value
        return f"Налаштування {key} змінено."

    def add_stat(self, key, amount=1):
        current = self.statistics.get(key, 0)
        self.statistics[key] = current + amount

    def unlock(self, achievement):
        if achievement in self.achievements:
            return "Досягнення вже було відкрито."
        self.achievements.append(achievement)
        return f"Досягнення відкрито: {achievement}."

    def settings_text(self):
        hints = "так" if self.settings["show_hints"] else "ні"
        return (
            f"Мова: {self.settings['language']}, "
            f"гучність: {self.settings['volume']}, "
            f"підказки: {hints}."
        )


profile = PlayerProfile("Міра")
print(profile.settings_text())
print(profile.unlock("Перший крок"))

profile.change_setting("volume", 40)
profile.add_stat("rooms_explored", 3)

print(profile.settings_text())
print(f"Досліджено кімнат: {profile.statistics['rooms_explored']}.")
```

В одному об’єкті є три різні колекції:

- словник `settings` має заздалегідь відомі ключі;
- порожній словник `statistics` отримує нові категорії під час роботи;
- список `achievements` зберігає впорядковану історію досягнень.

### Читання за ключем

```python fragment
volume = self.settings["volume"]
```

Квадратні дужки повертають значення за точним ключем. Якщо ключа немає, Python показує `KeyError`.

Для необов’язкового ключа використовуй `get()`:

```python fragment
current = self.statistics.get(key, 0)
```

Якщо `key` існує, повернеться його значення. Якщо ні — запасне `0`. Без другого аргументу `get()` повертає `None`.

Не треба автоматично замінювати всі `[...]` на `.get()`. Коли ключ **зобов’язаний** існувати, `KeyError` чесно показує порушену структуру. `get()` доречний для справді необов’язкових даних або явного значення за замовчуванням.

### Додавання й заміна мають однаковий запис

```python fragment
self.statistics["steps"] = 1
self.statistics["steps"] = 2
```

Перший рядок додає нову пару, другий змінює значення наявного ключа.

Метод `update()` додає або замінює кілька пар:

```python fragment
self.settings.update({"volume": 40, "show_hints": False})
```

### Видалення

```python fragment
del self.statistics["temporary"]
```

`del` потребує наявного ключа.

```python fragment
removed = self.statistics.pop("temporary", None)
```

`pop()` видаляє ключ і повертає значення. Другий аргумент є запасним результатом, якщо ключ відсутній.

:::practice Перемкни підказки
Додай метод без аргументів:

```python fragment
def toggle_hints(self):
    self.settings["show_hints"] = not self.settings["show_hints"]
```

Виклич його двічі й перевір `settings_text()`. Чому `not` зручно описує перемикач?
:::

## Перебирання словника

### Пари через `items()`

```python run file=dict_items.py expect="health: 20\nenergy: 8"
stats = {"health": 20, "energy": 8}

for key, value in stats.items():
    print(f"{key}: {value}")
```

Кожна пара розпаковується у `key` та `value`.

### Лише ключі

```python fragment
for key in stats:
    print(key)
```

Це коротка форма `for key in stats.keys():`. Метод `keys()` корисний, коли хочеться явно підкреслити роботу з ключами.

### Лише значення

```python fragment
for value in stats.values():
    print(value)
```

Значення можуть повторюватися. Якщо потрібні лише унікальні значення, їх можна передати до `set()`.

### Визначений порядок показу

Словник пам’ятає порядок додавання, але іноді інтерфейс потребує алфавітного порядку:

```python run file=sorted_dict.py expect="energy\nhealth\nscore"
stats = {"health": 20, "score": 100, "energy": 8}

for key in sorted(stats):
    print(key)
```

`sorted(stats)` сортує ключі й повертає список.

## Вкладені структури

Значенням словника може бути список, інший словник або об’єкт.

```python run file=nested_profile.py expect="Міра: 120 очок\nМітки: дослідник, помічник"
profile_data = {
    "name": "Міра",
    "stats": {
        "score": 120,
        "level": 3,
    },
    "tags": ["дослідник", "помічник"],
}

print(f"{profile_data['name']}: {profile_data['stats']['score']} очок")
print(f"Мітки: {', '.join(profile_data['tags'])}")
```

Кожна пара дужок проходить на один рівень глибше. Надто глибоке вкладення важко читати:

```python fragment
data["players"][0]["inventory"]["tools"][2]
```

Якщо структура має власні правила й поведінку, виділи клас або хоча б проміжні імена.

### Список словників

```python run file=list_of_dicts.py expect="Датчик A: 21.5\nДатчик B: 19.0"
readings = [
    {"sensor": "A", "value": 21.5},
    {"sensor": "B", "value": 19.0},
]

for reading in readings:
    print(f"Датчик {reading['sensor']}: {reading['value']}")
```

Це зручно для простих зовнішніх даних: рядків таблиці, повідомлень API, записів JSON. Якщо кожен датчик має обчислення, перевірки й стан, об’єкти `Sensor` дадуть чіткішу модель.

### Словник об’єктів

```python run file=dict_of_objects.py expect="Робі має 10 енергії."
class Robot:
    def __init__(self, name, energy):
        self.name = name
        self.energy = energy

    def status_text(self):
        return f"{self.name} має {self.energy} енергії."


robots = {
    "worker": Robot("Робі", 10),
    "scout": Robot("Іскра", 7),
}

print(robots["worker"].status_text())
```

Словник швидко знаходить роль `"worker"`, а об’єкт зберігає поведінку конкретного робота. Колекції та ООП не конкурують — вони виконують різні роботи.

## Коли клас, а коли словник

Обирай словник, коли:

- ключі можуть з’являтися динамічно;
- дані приходять або йдуть у формат на кшталт JSON;
- потрібне просте зіставлення «ключ → значення»;
- поведінка мінімальна й живе в іншому об’єкті.

Обирай клас, коли:

- структура має обов’язкові поля;
- зміни підкоряються правилам;
- дані мають власні дії;
- важливі зрозумілі методи на кшталт `move()`, `unlock()`, `calculate_total()`.

Нормальний варіант — клас **містить** словник, як `PlayerProfile.settings`. Клас захищає правила, словник дає гнучке зберігання пар.

:::note Не перетворюй усе на класи
ООП-first не означає «клас для кожного числа». Локальний словник налаштувань може бути найпростішим рішенням. Клас виправданий, коли дає назву сутності й збирає разом її стан та поведінку.
:::

## Безпечний параметр-словник

Не використовуй порожній словник як значення параметра за замовчуванням:

```python error
class Profile:
    def __init__(self, settings={}):
        self.settings = settings
```

Цей словник створюється один раз під час визначення класу й може несподівано стати спільним для багатьох об’єктів.

Безпечний шаблон:

```python run file=safe_default_dict.py expect="{'volume': 20}\n{}"
class Profile:
    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        self.settings = settings.copy()


first = Profile()
second = Profile()

first.settings["volume"] = 20

print(first.settings)
print(second.settings)
```

`None` не змінюється. Новий словник створюється окремо для кожного виклику. `.copy()` також відділяє внутрішній словник від переданого зовнішнього словника.

Для перевірки саме `None` використовують `is None`, а не `== None`. `is` перевіряє тотожність одному спеціальному об’єкту `None`.

## Множина зберігає унікальні значення

Множина `set` не зберігає повтори:

```python run file=unique_tags.py expect="3\nTrue"
tags = {"python", "oop", "python", "practice"}

print(len(tags))
print("oop" in tags)
```

Порядок множини не слід вважати стабільним для показу. Якщо потрібен передбачуваний порядок, використовуй `sorted(tags)`.

Порожню множину створюють лише через `set()`:

```python fragment
tags = set()
```

`{}` створює порожній словник.

Основні зміни:

```python fragment
tags.add("testing")
tags.remove("oop")
tags.discard("missing")
```

`remove()` дає `KeyError`, якщо значення відсутнє; `discard()` мовчки лишає множину без змін.

Операції над множинами:

```python run file=set_operations.py expect="['loops', 'oop', 'python', 'testing']\n['python']"
learned = {"python", "oop", "loops"}
required = {"python", "testing"}

print(sorted(learned | required))
print(sorted(learned & required))
```

- `|` — об’єднання всіх значень;
- `&` — перетин спільних;
- `-` — різниця;
- `<=` — перевірка, чи є одна множина підмножиною іншої.

Множина доречна для унікальних тегів, відвіданих кімнат, дозволів або швидкої перевірки належності.

## Типова помилка

### Відсутній ключ

```python error
settings = {"volume": 70}
print(settings["language"])
```

Python покаже `KeyError: 'language'`. Виріши, що це означає для моделі:

- структура зламана — нехай помилка лишиться видимою;
- ключ необов’язковий — використай `settings.get("language", "uk")`;
- ключ треба створити раніше — виправ ініціалізацію.

### Зміна розміру словника під час перебору

```python error
for key in statistics:
    if statistics[key] == 0:
        del statistics[key]
```

Python зупиниться з `RuntimeError`, бо розмір словника змінився під час циклу. Перебирай копію ключів: `for key in list(statistics):`, або створи новий словник.

### Ключ і значення переплутані

`for key, value in data.items()` має два імені. Назви `for value, key ...` синтаксично працюватимуть, але введуть читача в оману й швидко спричинять логічну помилку.

:::mistake
Не ховай помилку структури через нескінченний ланцюжок `.get(..., {})`. Якщо поле обов’язкове, краще отримати точну помилку біля джерела, ніж `None` у далекому обчисленні.
:::

## Швидка перевірка

Визнач стан обох профілів після змін:

```python run file=profile_copy.py expect="Перший: {'theme': 'light', 'volume': 80}\nДругий: {'theme': 'dark', 'volume': 20}"
class Profile:
    def __init__(self, settings):
        self.settings = settings.copy()


defaults = {"theme": "light", "volume": 20}
first = Profile(defaults)
second = Profile(defaults)

first.settings["volume"] = 80
second.settings["theme"] = "dark"

print(f"Перший: {first.settings}")
print(f"Другий: {second.settings}")
```

:::quiz
question: Як без помилки прочитати необов’язковий ключ score і отримати 0, якщо його немає?
correct: data.get("score", 0)
option: data["score", 0]
option: data.get["score"]
explanation: Метод get() приймає ключ і запасне значення. Квадратні дужки потребують наявного точного ключа.
:::

## Самостійна робота

:::tasks
- Додай профілю налаштування `difficulty` і метод, який приймає лише значення `easy`, `normal`, `hard`, а невідоме значення відхиляє.
- Створи клас `WordCounter` зі словником частот. Метод `add(word)` має збільшувати лічильник через `.get(word, 0)`.
- Побудуй словник об’єктів `Robot`, де ключ — унікальний ідентифікатор. Додай безпечний метод пошуку, який повертає об’єкт або `None`.
- Створи список із трьох словників зовнішніх даних, перетвори кожен на об’єкт `Sensor` і порівняй, де зручніше розмістити перевірку значення.
- Перебери словник у порядку ключів і надрукуй таблицю. Потім перебери тільки унікальні значення через множину.
- Створи дві множини навичок: уже вивчені та потрібні. Знайди спільні, відсутні й повний набір.
- Відтвори проблему зі спільним словником у параметрі `settings={}`, а потім виправ її через `None` і копію.
- Навмисно зміни розмір словника під час циклу, прочитай `RuntimeError`, а потім реалізуй безпечне очищення через копію ключів або словникове включення.
:::

:::history
Назва «словник» добре описує ідею: слово веде до пояснення, а ключ — до значення. В інших мовах подібну структуру можуть називати map, hash map, associative array або object. Назви різняться, а головна модель одна: знайти значення не за позицією, а за ключем.
:::

## Підсумок

- Словник зберігає пари `ключ: значення`; ключі унікальні.
- `data[key]` потребує наявного ключа, `data.get(key, default)` підтримує необов’язкові дані.
- Присвоєння за ключем додає або змінює пару; `del` і `pop()` видаляють.
- `items()`, `keys()` і `values()` дають різні способи перебору.
- Значення можуть містити вкладені словники, списки або об’єкти, але надмірна глибина погіршує модель.
- Клас потрібен для сутності з правилами й поведінкою; словник — для гнучкого зіставлення та зовнішніх даних.
- Для змінної колекції за замовчуванням використовуй `None`, а нову колекцію створюй усередині `__init__`.
- Множина зберігає унікальні значення й підтримує об’єднання, перетин та різницю.
