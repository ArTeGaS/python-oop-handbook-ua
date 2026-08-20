# JSON: збереження стану й рефакторинг

Текстовий журнал зручний для людини, але програма має окремо вгадувати, де ім’я, число чи список. JSON зберігає просту структуру даних: словники, списки, рядки, числа, логічні значення та `null`.

## Що зробимо

Збережемо профіль гравця у JSON через окремий `ProfileStore`. Сам клас `PlayerProfile` відповідатиме за правила стану, сховище — за файл, а точка запуску — за сценарій.

:::goal
Ти побачиш межу між живим об’єктом і його серіалізованими даними. Завантаження не повинно перетворювати весь код на вкладені словники.
:::

## JSON має прості типи

Вигляд файла `profile.json`:

```json
{
  "version": 1,
  "name": "Міра",
  "level": 3,
  "is_active": true,
  "skills": [
    "навігація",
    "ремонт"
  ]
}
```

Відмінності від запису Python:

- ключі JSON — рядки в подвійних лапках;
- логічні значення — `true` і `false` з малої літери;
- відсутнє значення — `null`, у Python воно стає `None`;
- коментарі й завершальні коми стандартний JSON не дозволяє.

JSON не зберігає методи класу. Він зберігає лише підтримувані дані, з яких програма може відновити новий об’єкт.

## `dumps()` і `loads()` працюють із рядком

```python run file=json_string.py expect="Міра\nTrue"
import json

data = {
    "name": "Міра",
    "skills": ["навігація", "ремонт"],
}

text = json.dumps(data, ensure_ascii=False, indent=2)
restored = json.loads(text)

print(restored["name"])
print(restored == data)
```

- `json.dumps(data)` повертає JSON-рядок; літера `s` нагадує *string*;
- `json.loads(text)` читає JSON-рядок і повертає Python-дані;
- `ensure_ascii=False` залишає українські літери читабельними;
- `indent=2` форматує файл для людини.

Без `ensure_ascii=False` дані не зіпсуються, але символи можуть виглядати як `\u041c...`.

## `dump()` і `load()` працюють із файловим об’єктом

```python run file=json_file.py expect="{'name': 'Робі', 'energy': 18}"
import json
from pathlib import Path

path = Path("robot.json")
data = {"name": "Робі", "energy": 18}

with path.open("w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

with path.open("r", encoding="utf-8") as file:
    restored = json.load(file)

print(restored)
```

`dump()` пише у відкритий файл, `load()` читає з нього. У маленькому коді також можна поєднати `Path.write_text(json.dumps(...))`.

Запис у режимі `"w"` повністю замінює попередній файл. Це має бути усвідомленою частиною методу `save()`.

## Майстерня

Створи `profile_storage.py`:

```python run file=profile_storage.py expect="Міра: рівень 4; навички: навігація, ремонт."
import json
from pathlib import Path


class ProfileDataError(ValueError):
    """JSON не відповідає контракту профілю."""


class PlayerProfile:
    def __init__(self, name, level=1, skills=None):
        if not name.strip():
            raise ValueError("Ім’я не може бути порожнім")
        if level < 1:
            raise ValueError("Рівень має бути не меншим за 1")

        self.name = name.strip()
        self.level = level
        self.skills = list(skills) if skills is not None else []

    def level_up(self):
        self.level += 1

    def learn(self, skill):
        if skill not in self.skills:
            self.skills.append(skill)

    def to_data(self):
        return {
            "version": 1,
            "name": self.name,
            "level": self.level,
            "skills": self.skills.copy(),
        }

    @classmethod
    def from_data(cls, data):
        if not isinstance(data, dict):
            raise ProfileDataError("корінь має бути об’єктом JSON")
        if data.get("version") != 1:
            raise ProfileDataError("непідтримувана версія")

        try:
            return cls(
                name=data["name"],
                level=data["level"],
                skills=data.get("skills", []),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ProfileDataError("неправильні поля профілю") from error

    def summary(self):
        skills_text = ", ".join(self.skills) if self.skills else "немає"
        return f"{self.name}: рівень {self.level}; навички: {skills_text}."


class ProfileStore:
    def __init__(self, path):
        self.path = Path(path)

    def save(self, profile):
        text = json.dumps(
            profile.to_data(),
            ensure_ascii=False,
            indent=2,
        )
        self.path.write_text(text + "\n", encoding="utf-8")

    def load(self):
        try:
            text = self.path.read_text(encoding="utf-8")
            data = json.loads(text)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as error:
            raise ProfileDataError("пошкоджений JSON") from error

        return PlayerProfile.from_data(data)


store = ProfileStore("profile.json")

profile = PlayerProfile("Міра", level=3)
profile.learn("навігація")
profile.learn("ремонт")
profile.level_up()

store.save(profile)
restored_profile = store.load()

print(restored_profile.summary())
```

### `to_data()` створює просту форму

```python fragment
def to_data(self):
    return {
        "version": 1,
        "name": self.name,
        "level": self.level,
        "skills": self.skills.copy(),
    }
```

Метод не пише файл і не імпортує `json`. Він лише перетворює стан на підтримувані прості типи. Це дозволяє використати ті самі дані для файла, мережі або перевірки.

Назви `to_dict()`/`from_dict()` теж поширені. `to_data()` підкреслює, що повернена структура є зовнішнім представленням, а не весь внутрішній світ об’єкта.

### `from_data()` відновлює об’єкт через конструктор

```python fragment
return cls(
    name=data["name"],
    level=data["level"],
    skills=data.get("skills", []),
)
```

Ми не створюємо порожній об’єкт і не вставляємо атрибути навмання. Звичайний `__init__` знову перевіряє правила.

`@classmethod` використовує `cls`, тому альтернативний конструктор лишається сумісним із похідними класами.

### Сховище не керує правилами профілю

`ProfileStore` знає `Path`, UTF-8 і JSON. Він просить профіль `to_data()` та передає прочитані дані `PlayerProfile.from_data()`.

Завдяки цьому:

- модель можна перевірити без файла;
- формат збереження можна змінити окремо;
- інтерфейс не працює з сирими словниками;
- кожна помилка має зрозумілий рівень.

:::practice Завантаж або створи
Напиши функцію сценарію:

```python fragment
def load_or_create(store, default_name):
    profile = store.load()
    if profile is not None:
        return profile
    return PlayerProfile(default_name)
```

Відсутній файл тут є нормальним першим запуском, тому `load()` повертає `None`. Пошкоджений наявний JSON — інша ситуація, її не можна мовчки замінити новим профілем.
:::

## Перевірка типів після JSON

Синтаксично правильний JSON не обов’язково відповідає моделі:

```json
{
  "version": 1,
  "name": 123,
  "level": "високий"
}
```

`json.loads()` успішно створить словник. Перевірка структури — відповідальність `from_data()` або окремого валідатора.

`isinstance()` доречний на межі зовнішніх даних:

```python fragment
if not isinstance(data.get("name"), str):
    raise ProfileDataError("name має бути рядком")
```

Не розкидай такі перевірки по всій програмі. Перетвори зовнішню структуру на надійний об’єкт один раз біля входу.

## Які Python-значення змінюються в JSON

Стандартний JSON підтримує:

- `dict` із рядковими ключами → object;
- `list` і `tuple` → array, після читання це буде `list`;
- `str` → string;
- `int`/`float` → number;
- `True`/`False` → true/false;
- `None` → null.

Кортеж після кругової подорожі стає списком:

```python run file=json_tuple.py expect="list\n[3, 5]"
import json

text = json.dumps({"position": (3, 5)})
restored = json.loads(text)

print(type(restored["position"]).__name__)
print(restored["position"])
```

Об’єкт `Path`, `date`, `set`, `Enum` або власний клас стандартний encoder напряму не знає. Перетвори їх у просту явну форму: рядок, список, значення переліку, словник.

### Ключі стають рядками

JSON object має рядкові ключі. Словник `{1: "one"}` після запису й читання повернеться як `{"1": "one"}`. Якщо тип ключа важливий, обери список записів або явне перетворення.

## Версія формату й зміна структури

Поле:

```python fragment
"version": 1
```

допомагає відрізнити формати. Коли версія 2 перейменує `level` на `rank`, старі файли не повинні дивно ламатися в далекому методі.

Стратегії:

- підтримати читання кількох версій;
- написати явну міграцію `v1 -> v2`;
- відмовити з повідомленням, що версія не підтримується;
- для необов’язкового нового поля використати безпечне значення за замовчуванням.

Не змінюй значення старого поля мовчки, якщо це може втратити дані.

```python fragment
def migrate_v1_to_v2(data):
    return {
        "version": 2,
        "name": data["name"],
        "rank": data["level"],
        "skills": data.get("skills", []),
    }
```

Міграція є чистою функцією: отримує старі дані, повертає нові, не перезаписує файл самостійно.

## Обережний запис через тимчасовий файл

Звичайний `write_text()` може лишити неповний файл, якщо процес аварійно завершиться посеред запису. Для важливого локального стану спочатку пишуть сусідній тимчасовий файл, а потім замінюють ціль:

```python fragment
def save(self, profile):
    text = json.dumps(profile.to_data(), ensure_ascii=False, indent=2) + "\n"
    temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(self.path)
```

`replace()` замінює наявний цільовий файл. Це **руйнівна дія щодо попередньої версії**, тому шлях має бути точно контрольований, а для цінних даних потрібна резервна копія або історія версій.

Гарантії атомарності залежать від файлової системи й того, чи обидва шляхи на одному томі. Для початкового локального застосунку цей шаблон зменшує ризик часткового запису, але не замінює продумане резервування.

## Рефакторинг: змінюємо будову, зберігаємо поведінку

Початкова програма часто виглядає так:

```python fragment
data = json.loads(Path("profile.json").read_text())
data["level"] += 1
Path("profile.json").write_text(json.dumps(data))
print(data["name"], data["level"])
```

Це синтаксично робочий код, а не виняток. Проблема архітектурна: читання, зміна моделі, запис і показ результату змішані. Рефакторинг розкладає їх:

```text
main -> ProfileStore.load() -> PlayerProfile.from_data()
     -> profile.level_up()
     -> ProfileStore.save(profile)
     -> profile.summary()
```

Безпечний порядок:

1. Зафіксуй поточний очікуваний результат маленькою перевіркою.
2. Виділи одну відповідальність без зміни зовнішнього результату.
3. Запусти перевірку.
4. Лише потім роби наступний крок.

Не поєднуй рефакторинг і нову функцію у величезній зміні, якщо можна розділити. Інакше важко зрозуміти причину регресії.

## JSON не є безпечним лише тому, що текстовий

`json.load()` не виконує код, що робить JSON безпечнішим за формати на кшталт `pickle` для неперевіреного джерела. Але дані все одно можуть бути:

- надто великими;
- неправильної структури;
- з небезпечними шляхами або командами як звичайним текстом;
- навмисно створеними для перевантаження логіки.

Вміст JSON — дані, не інструкції. Перевіряй межі й ніколи не виконуй рядок із файла через `eval()` або оболонку.

`pickle` може створювати довільні Python-об’єкти й **не підходить для недовірених файлів**, бо завантаження може виконати код.

## Типова помилка

### Спроба записати об’єкт напряму

```python error file=json_object.py raises=TypeError
import json


class PlayerProfile:
    pass


profile = PlayerProfile()
json.dumps(profile)
```

```output
Traceback (most recent call last):
  File "...\json_object.py", line 9, in <module>
    json.dumps(profile)
  ...
TypeError: Object of type PlayerProfile is not JSON serializable
```

Останній рядок називає тип, для якого JSON не знає формату. Перетвори об’єкт через `profile.to_data()`.

### Відсутній файл і пошкоджений файл обробляються однаково

Якщо `load()` повертає `None` і для `FileNotFoundError`, і для `JSONDecodeError`, програма може затерти пошкоджені дані новим порожнім профілем. Перший запуск — нормальний, пошкодження — проблема, яку треба показати або відновити з копії.

### Зовнішній словник стає внутрішнім станом без копії

```python run file=shared_json_list.py expect="['python', 'git']"
class Profile:
    def __init__(self, data):
        self.skills = data["skills"]


data = {"skills": ["python"]}
profile = Profile(data)
data["skills"].append("git")
print(profile.skills)
```

```output
['python', 'git']
```

`profile` ніхто не змінював напряму, але його стан уже містить `git`: список спільний із зовнішнім словником. Конструктор має зробити `list(data["skills"])` і встановити власну колекцію.

:::mistake
Не використовуй `default=str` лише для того, щоб «усе якось записалось». Він мовчки перетворить невідомі об’єкти на рядки, з яких неможливо надійно відновити тип. Визнач явний формат для кожної важливої сутності.
:::

## Швидка перевірка

Перевір кругову подорож «об’єкт → дані → JSON → дані → новий об’єкт»:

```python run file=json_round_trip.py expect="Лея: 2; ['python']"
import json


class Profile:
    def __init__(self, name, level, skills):
        self.name = name
        self.level = level
        self.skills = list(skills)

    def to_data(self):
        return {
            "name": self.name,
            "level": self.level,
            "skills": self.skills.copy(),
        }

    @classmethod
    def from_data(cls, data):
        return cls(data["name"], data["level"], data["skills"])


original = Profile("Лея", 2, ["python"])
text = json.dumps(original.to_data(), ensure_ascii=False)
restored = Profile.from_data(json.loads(text))

print(f"{restored.name}: {restored.level}; {restored.skills}")
```

:::quiz
question: Чому ProfileStore не повинен сам змінювати level профілю?
correct: Його відповідальність — зберігати й читати дані, а правила рівня належать PlayerProfile.
option: Бо JSON не підтримує числа.
option: Бо методи класу не можуть імпортувати json.
explanation: Розділення відповідальності дозволяє перевіряти модель без файла й змінювати формат сховища без перенесення правил профілю.
:::

## Самостійна робота

:::tasks
- Додай профілю поле `settings` зі словником і забезпеч копію під час створення, `to_data()` та `from_data()`.
- Створи окремі перевірки для відсутнього файла, пошкодженого JSON, відсутнього ключа й неправильного типу поля. Не повертай для всіх випадків однакове `None`.
- Реалізуй `Robot.to_data()`/`from_data()` і `RobotStore`. Методи руху й заряду мають лишитися в `Robot`, не у сховищі.
- Продемонструй, як кортеж і ключ-число змінюються після JSON round trip. Обери явне представлення, якщо початковий тип треба відновити.
- Додай `version: 1`, створи приклад старих даних і чисту функцію міграції у версію 2 без запису файла.
- Реалізуй запис через сусідній `.tmp` і `replace()` лише в окремій навчальній папці. Перед запуском надрукуй обидва абсолютні шляхи й переконайся, що вони в межах проєкту.
- Візьми монолітний скрипт зі словником і JSON та розділи на модель, сховище і `main()`. Після кожного кроку перевіряй той самий видимий результат.
- Спробуй серіалізувати `Path`, `set` або `Enum`, прочитай `TypeError`, а потім визнач явну просту форму й зворотне відновлення.
:::

:::history
JSON походить із синтаксису об’єктів JavaScript, але давно є незалежним форматом обміну. Його сила — невеликий спільний набір типів. Обмеження змушує явно вирішити, які дані справді потрібні для відновлення об’єкта.
:::

## Підсумок

- JSON зберігає прості структури, а не методи й довільні Python-об’єкти.
- `dumps()`/`loads()` працюють із рядками, `dump()`/`load()` — із файловими об’єктами.
- `ensure_ascii=False`, `indent` і UTF-8 роблять український файл читабельним.
- `to_data()` створює серіалізовану форму, `from_data()` перевіряє її й відновлює об’єкт.
- Сховище відповідає за шлях та формат; модель — за правила стану й поведінку.
- Відсутній файл, пошкоджений JSON і неправильна схема — різні ситуації.
- Версія формату та явні міграції допомагають безпечно змінювати структуру.
- Тимчасовий запис із `replace()` зменшує ризик часткового файла, але є заміною даних і потребує точного шляху.
- Рефакторинг змінює будову маленькими кроками, зберігаючи перевірену поведінку.

Офіційний орієнтир: [`json`](https://docs.python.org/3/library/json.html).
