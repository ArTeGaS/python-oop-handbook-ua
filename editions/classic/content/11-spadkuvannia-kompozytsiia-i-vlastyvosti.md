# Пов’язані об’єкти: успадкування, композиція й властивості

Класи рідко живуть окремо. Електросамокат є видом транспорту, а його батарея — окремою частиною. Перше відношення іноді описує **успадкування**, друге — **композиція**. Вибір впливає на те, наскільки легко змінювати програму.

## Що зробимо

Створимо базовий `Vehicle`, спеціалізований `ElectricScooter` і окремий об’єкт `Battery`. Потім закриємо небезпечну зміну заряду за властивістю `energy`.

:::goal
Ти зможеш перевірити відношення простими фразами: «X є різновидом Y» для успадкування та «X має Y» для композиції. Перевагу отримає простіший зв’язок, а не найбільше дерево класів.
:::

## Успадкування передає спільний опис

```python fragment
class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def move_text(self):
        return f"{self.name} рухається зі швидкістю {self.speed}."


class Bicycle(Vehicle):
    pass
```

`Bicycle(Vehicle)` означає: `Bicycle` успадковує доступні методи й атрибути, підготовлені `Vehicle`. Порожній клас із `pass` уже може створювати об’єкти:

```python run file=first_inheritance.py expect="Ластівка рухається зі швидкістю 18."
class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def move_text(self):
        return f"{self.name} рухається зі швидкістю {self.speed}."


class Bicycle(Vehicle):
    pass


bicycle = Bicycle("Ластівка", 18)
print(bicycle.move_text())
```

`Vehicle` називають базовим або батьківським класом, `Bicycle` — похідним або дочірнім.

Успадкування доречне, якщо об’єкт похідного класу справді можна використовувати всюди, де очікують базовий. Велосипед є транспортом і підтримує основні обіцянки транспорту.

## Майстерня

Створи `electric_scooter.py`:

```python run file=electric_scooter.py expect="Іскра рухається зі швидкістю 22.\nЗаряд: 30/40.\nСамокат проїхав 8 км.\nЗаряд: 22/40."
class Battery:
    def __init__(self, capacity, charge=None):
        self.capacity = capacity
        self._charge = capacity if charge is None else charge

    @property
    def charge(self):
        return self._charge

    def use(self, amount):
        if amount < 0 or amount > self._charge:
            return False
        self._charge -= amount
        return True

    def status_text(self):
        return f"Заряд: {self._charge}/{self.capacity}."


class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def move_text(self):
        return f"{self.name} рухається зі швидкістю {self.speed}."


class ElectricScooter(Vehicle):
    def __init__(self, name, speed, battery):
        super().__init__(name, speed)
        self.battery = battery
        self.distance = 0

    def ride(self, kilometers):
        if kilometers <= 0:
            return "Відстань має бути додатною."
        if not self.battery.use(kilometers):
            return "Недостатньо заряду."
        self.distance += kilometers
        return f"Самокат проїхав {kilometers} км."


battery = Battery(capacity=40, charge=30)
scooter = ElectricScooter("Іскра", speed=22, battery=battery)

print(scooter.move_text())
print(scooter.battery.status_text())
print(scooter.ride(8))
print(scooter.battery.status_text())
```

Тут обидва зв’язки мають чітку причину:

- `ElectricScooter` **є** видом `Vehicle`;
- `ElectricScooter` **має** `Battery`.

### `super()` викликає реалізацію базового класу

```python fragment
super().__init__(name, speed)
```

`super()` дає доступ до наступної реалізації в ланцюжку успадкування. Тут він просить `Vehicle` підготувати спільні атрибути `name` і `speed`.

Не дублюй:

```python fragment
self.name = name
self.speed = speed
```

у кожному похідному класі, якщо базовий уже має правильну ініціалізацію. Це не обов’язково впаде одразу, але дубльовані правила легко розійдуться.

`super()` краще за прямий виклик `Vehicle.__init__(self, ...)`, бо поважає порядок пошуку методів і підтримує складніші, хоча й рідші, схеми успадкування.

### Перевизначення методу

Похідний клас може дати власну реалізацію методу з тим самим іменем:

```python run file=override.py expect="Човен Плин рухається водою зі швидкістю 12."
class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def move_text(self):
        return f"{self.name} рухається зі швидкістю {self.speed}."


class Boat(Vehicle):
    def move_text(self):
        return f"Човен {self.name} рухається водою зі швидкістю {self.speed}."


boat = Boat("Плин", 12)
print(boat.move_text())
```

Це **перевизначення**. Виклик `boat.move_text()` знаходить найближчу реалізацію в `Boat`.

Якщо треба розширити, а не повністю замінити базовий результат:

```python fragment
def move_text(self):
    base_text = super().move_text()
    return base_text + " Двигун працює тихо."
```

Зберігай сумісний зміст: якщо базовий `move_text()` повертає рядок, похідний не повинен раптом видаляти об’єкт або повертати словник без дуже вагомої причини.

## Композиція: об’єкт складається з інших об’єктів

```python fragment
self.battery = battery
```

Самокат не успадковує батарею. Він містить посилання на окремий об’єкт і делегує йому роботу:

```python fragment
if not self.battery.use(kilometers):
    return "Недостатньо заряду."
```

Переваги:

- `Battery` можна перевірити окремо;
- ту саму модель батареї можна використати в роботі або ліхтарі;
- батарею можна замінити іншим сумісним об’єктом;
- клас самоката не розростається правилами заряджання.

:::practice Заміни батарею
Створи другу батарею більшої місткості й присвой `scooter.battery = new_battery`. Перевір, що код `ride()` не треба змінювати: він очікує поведінку `use()` і `status_text()`, а не конкретну історію об’єкта.
:::

## Підкреслення позначає внутрішню деталь

```python fragment
self._charge = capacity
```

Одне початкове підкреслення — домовленість: «це внутрішня деталь класу; зовнішньому коду краще не змінювати напряму». Python не ставить фізичний замок:

```python fragment
battery._charge = -100
```

технічно можливе. Але такий код обходить перевірки й порушує контракт.

Подвійне підкреслення `__charge` вмикає механізм зміни імені, а не абсолютну приватність. Для початкових моделей достатньо одного `_` і зрозумілих публічних методів.

## `@property` дає контрольоване читання

```python fragment
@property
def charge(self):
    return self._charge
```

Зовнішній код читає `battery.charge` без дужок, але насправді виконується метод. Властивість доречна для простого значення, яке виглядає як стан.

Без setter-властивості такий запис не дозволений:

```python error file=read_only_property.py raises=AttributeError
class Battery:
    def __init__(self, charge):
        self._charge = charge

    @property
    def charge(self):
        return self._charge


battery = Battery(80)
battery.charge = -10
```

```output
Traceback (most recent call last):
  File "...\read_only_property.py", line 11, in <module>
    battery.charge = -10
    ^^^^^^^^^^^^^^
AttributeError: property 'charge' of 'Battery' object has no setter
```

Останній рядок пояснює, що властивість доступна для читання, але не має setter-методу. Зміну треба робити через `use()` або окремий `charge_by()`, де діють правила.

Якщо пряме присвоєння справді є частиною зручного інтерфейсу, можна додати setter:

```python fragment
@charge.setter
def charge(self, value):
    if not 0 <= value <= self.capacity:
        raise ValueError("Заряд поза допустимими межами")
    self._charge = value
```

Але метод `recharge(amount)` часто краще називає дію, ніж приховане складне присвоєння.

:::note Властивість не потрібна для кожного атрибута
Публічне `self.name` — нормальний Python. Додавай `_attribute` і property, коли є справжня умова цілісності, обчислення або потреба змінити реалізацію без зміни зовнішнього інтерфейсу.
:::

## Атрибут класу спільний для всіх об’єктів

```python run file=class_attribute.py expect="2\n2"
class Robot:
    created_count = 0

    def __init__(self, name):
        self.name = name
        Robot.created_count += 1


first = Robot("Робі")
second = Robot("Іскра")

print(Robot.created_count)
print(second.created_count)
```

`created_count` належить класу й спільний. Читати його через `Robot.created_count` ясніше. Звичайні дані конкретного робота, як `name`, створюють через `self`.

Не використовуй змінний список атрибутом класу для особистих даних:

```python run file=shared_class_list.py expect="['ключ']"
class Backpack:
    items = []


first = Backpack()
second = Backpack()
first.items.append("ключ")
print(second.items)
```

```output
['ключ']
```

Ключ додали через `first`, але його видно й у `second`: усі наплічники отримали той самий список класу. Створюй `self.items = []` у `__init__`.

## `@classmethod` як альтернативний конструктор

Метод класу отримує клас у параметрі `cls`:

```python run file=class_method.py expect="Робі: 25"
class Robot:
    def __init__(self, name, energy):
        self.name = name
        self.energy = energy

    @classmethod
    def fully_charged(cls, name):
        return cls(name, energy=25)


robot = Robot.fully_charged("Робі")
print(f"{robot.name}: {robot.energy}")
```

`fully_charged()` дає назву іншому способу створення. `cls(...)` підтримує похідні класи краще, ніж жорстко записане `Robot(...)`.

`@staticmethod` створює функцію в просторі імен класу без `self` і `cls`. Використовуй її рідко: якщо функція не пов’язана зі станом чи поняттям класу, звичайний модуль часто природніший.

## Поліморфізм: одна команда для різних об’єктів

```python run file=polymorphism.py expect="Колесо котиться.\nЧовен пливе."
class WheelVehicle:
    def move_text(self):
        return "Колесо котиться."


class Boat:
    def move_text(self):
        return "Човен пливе."


vehicles = [WheelVehicle(), Boat()]

for vehicle in vehicles:
    print(vehicle.move_text())
```

Класи навіть не мають спільного базового класу, крім загального `object`. Python часто достатньо того, що об’єкт підтримує потрібний метод. Це називають **duck typing**: важлива поведінка, а не формальний ярлик.

Успадкування корисне для спільної реалізації й явного відношення, але не потрібне лише заради однакової назви методу.

Функції `isinstance(obj, Class)` і `issubclass(Child, Parent)` перевіряють формальний зв’язок. Не підмінюй ними нормальний поліморфізм великим ланцюжком перевірок типів.

## Типова помилка

### Успадкування заради повторного використання двох рядків

Якщо `Report` успадковує `Robot` лише через корисний метод форматування, твердження «звіт є роботом» хибне. Винеси функцію або окремий об’єкт форматера.

### Забутий `super().__init__()`

```python error file=missing_super.py raises=AttributeError
class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def status(self):
        print(f"{self.name}: {self.speed}")


class ElectricScooter(Vehicle):
    def __init__(self, battery):
        self.battery = battery


scooter = ElectricScooter(80)
scooter.status()
```

```output
Traceback (most recent call last):
  File "...\missing_super.py", line 16, in <module>
    scooter.status()
  File "...\missing_super.py", line 7, in status
    print(f"{self.name}: {self.speed}")
             ^^^^^^^^^
AttributeError: 'ElectricScooter' object has no attribute 'name'
```

Виклик успадкованого `status()` дійшов до читання `self.name`, якого похідний конструктор не створив. Або виклич `super().__init__(name, speed)`, або свідомо забезпеч усі обіцянки базового класу.

### Похідний клас ламає контракт

Якщо базовий `move_text()` повертає рядок, а один похідний метод повертає `None` і лише друкує, спільний цикл не зможе однаково обробити об’єкти.

:::mistake
Не створюй глибоку ієрархію наперед: `Entity -> Actor -> MovingActor -> LivingMovingActor -> Hero`. Спочатку потрібні конкретні два класи й реальна спільна поведінка. Композицію легше змінювати, тому за сумніву перевір варіант «має об’єкт».
:::

## Швидка перевірка

Визнач, де успадкування, а де композиція:

```python run file=service_robot.py expect="Сервіс-1: інструмент — ключ."
class Robot:
    def __init__(self, name):
        self.name = name


class Tool:
    def __init__(self, title):
        self.title = title


class ServiceRobot(Robot):
    def __init__(self, name, tool):
        super().__init__(name)
        self.tool = tool

    def description(self):
        return f"{self.name}: інструмент — {self.tool.title}."


robot = ServiceRobot("Сервіс-1", Tool("ключ"))
print(robot.description())
```

:::quiz
question: Який зв’язок найкраще описує фразу «самокат має батарею»?
correct: Композиція: об’єкт Battery зберігається в атрибуті самоката.
option: Успадкування: ElectricScooter повинен бути підкласом Battery.
option: Глобальна змінна battery для всіх самокатів.
explanation: Батарея є частиною самоката, але самокат не є різновидом батареї. Це відношення «має», тобто композиція.
:::

## Самостійна робота

:::tasks
- Створи базовий `Notification` із методом `message_text()` і два похідні класи, які перевизначають формат, але завжди повертають рядок.
- Створи `Flashlight`, який має об’єкт `Battery`. Нехай ліхтар делегує витрату заряду батареї, а не змінює її внутрішній атрибут напряму.
- Додай батареї метод `recharge(amount)` з межами від 0 до `capacity`. Перевір від’ємне значення, переповнення й нормальний заряд.
- Перероби прямий публічний атрибут, для якого справді потрібна перевірка, на `_attribute` з read-only property і методами зміни.
- Створи атрибут класу, який рахує кількість створених об’єктів. Поясни, чому особистий стан не можна зберігати там само.
- Додай альтернативний конструктор `from_text()` через `@classmethod`, який створює об’єкт із простого рядка відомого формату.
- Знайди у власному прикладі хибне успадкування за тестом «X є Y» і заміни його композицією або функцією.
- Створи список різних об’єктів зі спільним методом `status_text()` без спільного класу й оброби його одним циклом.
:::

:::history
Фраза «віддавай перевагу композиції перед успадкуванням» не забороняє успадкування. Вона нагадує: дерево типів важко перебудувати, а об’єкти-частини можна замінювати. Спершу перевір «має», а «є різновидом» залиш для справді стабільного відношення.
:::

## Підсумок

- Успадкування описує відношення «похідний клас є різновидом базового».
- `super()` викликає реалізацію наступного класу в ланцюжку й допомагає не дублювати ініціалізацію.
- Перевизначення дає похідному класу власну сумісну реалізацію методу.
- Композиція описує «об’єкт має інший об’єкт» і делегує йому відповідальність.
- Одне `_` позначає внутрішню деталь за домовленістю; property дає контрольоване читання або присвоєння.
- Атрибут класу спільний, атрибут `self` належить конкретному об’єкту.
- `@classmethod` зручний для альтернативного способу створення.
- Поліморфізм дозволяє однаково викликати сумісну поведінку різних об’єктів навіть без формального спільного предка.
