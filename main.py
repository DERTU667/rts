import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.graphics import Ellipse, Rectangle, Color, Triangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import random
import math
import time  # Для отслеживания времени между кликами

# Установка размера окна для тестирования
Window.size = (1000, 600)

# Определение типов юнитов
class UnitType:
    CAVALRY = 'cavalry'
    PIKEMAN = 'pikeman'
    SWORDSMAN = 'swordsman'

# Класс базы
class Base:
    def __init__(self, x, y, color, canvas, name):
        self.x = x
        self.y = y
        self.hp = 250
        self.coins = 100
        self.income = 1
        self.color = color
        self.radius = 50  # Радиус базы
        self.inner_radius = 30  # Внутренний радиус
        self.name = name  # "player" или "computer"
        self.canvas = canvas
        self.draw()

    def draw(self):
        with self.canvas:
            # Внешний круг
            Color(*self.color)
            self.outer_circle = Ellipse(pos=(self.x - self.radius, self.y - self.radius),
                                        size=(self.radius*2, self.radius*2))
            # Внутренний круг более тёмного оттенка
            Color(*self.get_inner_color())
            self.inner_circle = Ellipse(pos=(self.x - self.inner_radius, self.y - self.inner_radius),
                                        size=(self.inner_radius*2, self.inner_radius*2))

    def get_inner_color(self):
        return tuple(max(c - 0.3, 0) for c in self.color)

    def update(self, dt):
        self.coins += self.income * dt

    def take_damage(self, damage):
        self.hp -= damage
        print(f"{self.name.capitalize()} Base получил {damage:.2f} урона! HP: {self.hp:.2f}")

# Класс юнита
class Unit:
    def __init__(self, unit_type, x, y, owner, canvas):
        self.type = unit_type
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.owner = owner  # "player" или "computer"
        self.hp = 5
        self.damage = 0.1  # Урон за секунду (уменьшен в 10 раз)
        self.speed = 100  # пикселей в секунду
        self.size = 20  # Размер юнита (диаметр)
        self.color = (1, 0, 0) if self.owner == "player" else (0, 0, 1)
        self.canvas = canvas
        self.shape = self.get_shape()
        self.selected = False  # Флаг выбора юнита
        self.selection_border = None  # Ссылка на обводку выделения
        self.draw()

    def get_shape(self):
        if self.type == UnitType.CAVALRY:
            return 'square'
        elif self.type == UnitType.PIKEMAN:
            return 'triangle'
        elif self.type == UnitType.SWORDSMAN:
            return 'circle'

    def draw(self):
        with self.canvas:
            Color(*self.color)
            if self.shape == 'square':
                self.graphic = Rectangle(pos=(self.x - self.size/2, self.y - self.size/2),
                                         size=(self.size, self.size))
            elif self.shape == 'triangle':
                self.graphic = Triangle(points=[
                    self.x, self.y + self.size/2,
                    self.x - self.size/2, self.y - self.size/2,
                    self.x + self.size/2, self.y - self.size/2
                ])
            elif self.shape == 'circle':
                self.graphic = Ellipse(pos=(self.x - self.size/2, self.y - self.size/2),
                                       size=(self.size, self.size))

    def update_graphic_position(self):
        if self.shape == 'square':
            self.graphic.pos = (self.x - self.size/2, self.y - self.size/2)
        elif self.shape == 'triangle':
            self.graphic.points = [
                self.x, self.y + self.size/2,
                self.x - self.size/2, self.y - self.size/2,
                self.x + self.size/2, self.y - self.size/2
            ]
        elif self.shape == 'circle':
            self.graphic.pos = (self.x - self.size/2, self.y - self.size/2)
        if self.selected and self.selection_border:
            self.selection_border.circle = (self.x, self.y, self.size)

    def update_position(self, dt, all_units, enemy_units, boundaries):
        old_x, old_y = self.x, self.y
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance_to_target = math.hypot(dx, dy)

        if distance_to_target > 5:
            # Нормализуем направление
            dx /= distance_to_target
            dy /= distance_to_target
            # Вычисляем потенциальное новое положение
            new_x = self.x + dx * self.speed * dt
            new_y = self.y + dy * self.speed * dt

            # Проверяем столкновение с границами экрана
            min_x, max_x, min_y, max_y = boundaries
            half_size = self.size / 2

            # Ограничиваем координаты новыми границами
            new_x = max(min_x + half_size, min(new_x, max_x - half_size))
            new_y = max(min_y + half_size, min(new_y, max_y - half_size))

            self.x = new_x
            self.y = new_y
            self.update_graphic_position()

        # Избежание наложения с союзными юнитами
        for other in all_units:
            if other is not self and other.owner == self.owner:
                dist = math.hypot(self.x - other.x, self.y - other.y)
                min_dist = (self.size + other.size) / 2
                if dist < min_dist and dist != 0:
                    overlap = min_dist - dist
                    # Вычисление направления от другого юнита
                    ox = (self.x - other.x) / dist
                    oy = (self.y - other.y) / dist
                    # Сдвиг текущего юнита
                    self.x += ox * overlap / 2
                    self.y += oy * overlap / 2
                    self.update_graphic_position()

    def distance_to_base(self, base):
        return math.hypot(self.x - base.x, self.y - base.y)

    def select(self):
        if not self.selected:
            self.selected = True
            with self.canvas:
                Color(1, 1, 0)  # Жёлтый цвет для выделения
                self.selection_border = Line(circle=(self.x, self.y, self.size), width=2)

    def deselect(self):
        if self.selected:
            self.selected = False
            if self.selection_border:
                self.canvas.remove(self.selection_border)
                self.selection_border = None

# Класс игры
class RTSGame(FloatLayout):
    def __init__(self, **kwargs):
        super(RTSGame, self).__init__(**kwargs)
        self.state = 'menu'
        self.selected_units = []  # Список выбранных юнитов
        self.player_base = Base(100, Window.height/2, (1, 0, 0), self.canvas, "player")  # Красный
        self.computer_base = Base(Window.width - 100, Window.height/2, (0, 0, 1), self.canvas, "computer")  # Синий
        self.player_units = []
        self.computer_units = []
        self.computer_hire_timer = 0
        self.computer_attack_timer = 0
        self.hire_cost = 10
        self.init_menu()
        
        # Добавление переменных для отслеживания двойного клика
        self.last_touch_time = 0
        self.double_click_time = 0.3  # Максимальное время между кликами для двойного клика
        self.last_touched_unit = None

    def init_menu(self):
        # Создание кнопки "Играть"
        self.play_button = Button(text="Играть",
                                  size_hint=(None, None),
                                  size=(200, 60),
                                  pos_hint={'center_x':0.5, 'center_y':0.5})
        self.play_button.bind(on_release=self.start_game)
        self.add_widget(self.play_button)

    def start_game(self, instance):
        print("Кнопка 'Играть' нажата")  # Отладочное сообщение
        self.state = 'playing'
        self.remove_widget(self.play_button)
        # Запуск таймеров
        Clock.schedule_interval(self.update_game, 1/60.)
        # Создание начальных юнитов компьютера
        self.create_computer_initial_units()
        Clock.schedule_once(self.send_computer_initial_units, 5)
        # Инициализация кнопок найма
        self.init_hire_buttons()

    def init_hire_buttons(self):
        # Создание панели найма юнитов
        hire_panel = BoxLayout(orientation='horizontal',
                               size_hint=(1, 0.1),
                               pos=(0, 0))
        # Коница
        hire_cavalry = Button(text="Коница",
                               size_hint=(0.33, 1))
        with hire_cavalry.canvas.before:
            Color(1, 0, 0)
            self.cavalry_icon = Rectangle(pos=(hire_cavalry.x + 35, hire_cavalry.y + 10),
                                          size=(30, 30))
        hire_cavalry.bind(on_release=lambda x: self.hire_unit(UnitType.CAVALRY))
        # Пикинер
        hire_pikeman = Button(text="Пикинер",
                               size_hint=(0.33, 1))
        with hire_pikeman.canvas.before:
            Color(0, 1, 0)
            self.pikeman_icon = Triangle(points=[
                hire_pikeman.x + 50, hire_pikeman.y + 40,
                hire_pikeman.x + 35, hire_pikeman.y + 10,
                hire_pikeman.x + 65, hire_pikeman.y + 10
            ])
        hire_pikeman.bind(on_release=lambda x: self.hire_unit(UnitType.PIKEMAN))
        # Мечник
        hire_swordsman = Button(text="Мечник",
                                 size_hint=(0.33, 1))
        with hire_swordsman.canvas.before:
            Color(0, 0, 1)
            self.swordsman_icon = Ellipse(pos=(hire_swordsman.x + 35, hire_swordsman.y + 10),
                                         size=(30, 30))
        hire_swordsman.bind(on_release=lambda x: self.hire_unit(UnitType.SWORDSMAN))
        # Добавление кнопок в панель
        hire_panel.add_widget(hire_cavalry)
        hire_panel.add_widget(hire_pikeman)
        hire_panel.add_widget(hire_swordsman)
        self.add_widget(hire_panel)

    def hire_unit(self, unit_type):
        if self.player_base.coins >= self.hire_cost:
            self.player_base.coins -= self.hire_cost
            # Определение случайного смещения вокруг базы для распределения юнитов
            spread_radius = 30  # Радиус распределения
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, spread_radius)
            offset_x = math.cos(angle) * distance
            offset_y = math.sin(angle) * distance
            spawn_x = self.player_base.x + offset_x
            spawn_y = self.player_base.y + offset_y
            # Создание юнита на базе игрока с распределённой позицией
            unit = Unit(unit_type, spawn_x, spawn_y, "player", self.canvas)
            self.player_units.append(unit)
            print(f"Нанимается юнит: {unit_type} на позиции ({spawn_x:.2f}, {spawn_y:.2f})")  # Отладочное сообщение
        else:
            print("Недостаточно монет для найма юнита.")  # Отладочное сообщение

    def create_computer_initial_units(self):
        for unit_type in [UnitType.CAVALRY, UnitType.PIKEMAN, UnitType.SWORDSMAN]:
            for _ in range(2):
                if self.computer_base.coins >= self.hire_cost:
                    self.computer_base.coins -= self.hire_cost
                    # Определение случайного смещения вокруг базы компьютера
                    spread_radius = 30
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(0, spread_radius)
                    offset_x = math.cos(angle) * distance
                    offset_y = math.sin(angle) * distance
                    spawn_x = self.computer_base.x + offset_x
                    spawn_y = self.computer_base.y + offset_y
                    unit = Unit(unit_type, spawn_x, spawn_y,
                                "computer", self.canvas)
                    self.computer_units.append(unit)
                    print(f"ИИ нанимает {unit_type} на позиции ({spawn_x:.2f}, {spawn_y:.2f})")  # Отладочное сообщение

    def send_computer_initial_units(self, dt):
        for unit in self.computer_units:
            unit.target_x = self.player_base.x
            unit.target_y = self.player_base.y

    def update_game(self, dt):
        if self.state != 'playing':
            return
        # Обновление баз
        self.player_base.update(dt)
        self.computer_base.update(dt)

        # Определение границ экрана (без панели найма)
        button_panel_height = Window.height * 0.1
        boundaries = (
            0,  # min_x
            Window.width,  # max_x
            button_panel_height,  # min_y
            Window.height  # max_y
        )

        # Обновление юнитов
        all_units = self.player_units + self.computer_units
        for unit in self.player_units:
            unit.update_position(dt, all_units, self.computer_units, boundaries)
        for unit in self.computer_units:
            unit.update_position(dt, all_units, self.player_units, boundaries)

        # Проверка столкновений и нанесение урона
        self.handle_collisions(dt)

        # Обновление таймеров компьютера
        self.computer_hire_timer += dt
        self.computer_attack_timer += dt

        # Нанимать юниты компьютера каждые 15 секунд
        if self.computer_hire_timer >= 15:
            self.computer_hire_timer = 0
            self.computer_hire_units()

        # Решать нападать каждые 30 секунд
        if self.computer_attack_timer >= 30:
            self.computer_attack_timer = 0
            if random.random() > 0.5:
                self.computer_send_attack()

        # Проверка победы/поражения
        if self.player_base.hp <= 0 or self.computer_base.hp <= 0:
            self.end_game()

    def handle_collisions(self, dt):
        # Столкновения между вражескими юнитами (игрок vs компьютер)
        for p_unit in self.player_units.copy():
            for c_unit in self.computer_units.copy():
                distance = math.hypot(p_unit.x - c_unit.x, p_unit.y - c_unit.y)
                min_dist = (p_unit.size + c_unit.size) / 2
                if distance <= min_dist:
                    # Наносим урон друг другу (уменьшенный в 10 раз)
                    damage_to_computer = p_unit.damage
                    damage_to_player = c_unit.damage
                    c_unit.hp -= damage_to_computer
                    p_unit.hp -= damage_to_player
                    print(f"Урон: {p_unit.type} наносит {damage_to_computer:.2f} урона {c_unit.type}")
                    print(f"Урон: {c_unit.type} наносит {damage_to_player:.2f} урона {p_unit.type}")

                    # Отталкивание юнитов друг от друга
                    if distance != 0:
                        ox = (p_unit.x - c_unit.x) / distance
                        oy = (p_unit.y - c_unit.y) / distance
                    else:
                        ox, oy = 1, 0  # Если совпадают позиции, отталкиваем вправо

                    overlap = min_dist - distance + 1
                    p_unit.x += ox * (overlap / 2)
                    p_unit.y += oy * (overlap / 2)
                    c_unit.x -= ox * (overlap / 2)
                    c_unit.y -= oy * (overlap / 2)
                    p_unit.update_graphic_position()
                    c_unit.update_graphic_position()

                    # Проверка уничтожения
                    if p_unit.hp <= 0:
                        if p_unit in self.player_units:
                            self.player_units.remove(p_unit)
                            try:
                                self.canvas.remove(p_unit.graphic)
                                if p_unit.selected:
                                    self.selected_units.remove(p_unit)
                                    p_unit.deselect()
                                print(f"{p_unit.type} игрока уничтожен.")
                            except:
                                pass
                    if c_unit.hp <= 0:
                        if c_unit in self.computer_units:
                            self.computer_units.remove(c_unit)
                            try:
                                self.canvas.remove(c_unit.graphic)
                                print(f"{c_unit.type} компьютера уничтожен.")
                            except:
                                pass

        # Столкновения с базами
        # Юниты игрока атакуют базу компьютера
        for unit in self.player_units.copy():
            distance = math.hypot(unit.x - self.computer_base.x, unit.y - self.computer_base.y)
            min_dist = (unit.size / 2) + self.computer_base.radius
            if distance <= min_dist:
                # Нанесение урона базе (уменьшенный в 10 раз)
                damage = unit.damage
                self.computer_base.take_damage(damage)
                print(f"{unit.type} игрока атакует базу компьютера и наносит {damage:.2f} урона.")

                # Отталкивание юнита от базы
                if distance != 0:
                    ox = (unit.x - self.computer_base.x) / distance
                    oy = (unit.y - self.computer_base.y) / distance
                else:
                    ox, oy = 1, 0  # Если совпадают позиции, отталкиваем вправо

                overlap = min_dist - distance + 1
                unit.x += ox * overlap
                unit.y += oy * overlap
                unit.update_graphic_position()

        # Юниты компьютера атакуют базу игрока
        for unit in self.computer_units.copy():
            distance = math.hypot(unit.x - self.player_base.x, unit.y - self.player_base.y)
            min_dist = (unit.size / 2) + self.player_base.radius
            if distance <= min_dist:
                # Нанесение урона базе (уменьшенный в 10 раз)
                damage = unit.damage
                self.player_base.take_damage(damage)
                print(f"{unit.type} компьютера атакует базу игрока и наносит {damage:.2f} урона.")

                # Отталкивание юнита от базы
                if distance != 0:
                    ox = (unit.x - self.player_base.x) / distance
                    oy = (unit.y - self.player_base.y) / distance
                else:
                    ox, oy = 1, 0  # Если совпадают позиции, отталкиваем вправо

                overlap = min_dist - distance + 1
                unit.x += ox * overlap
                unit.y += oy * overlap
                unit.update_graphic_position()

    def computer_hire_units(self):
        # Подсчёт типов юнитов игрока
        counts = {UnitType.CAVALRY:0, UnitType.PIKEMAN:0, UnitType.SWORDSMAN:0}
        for unit in self.player_units:
            counts[unit.type] +=1
        # Определяем наиболее многочисленный тип у игрока
        if counts[UnitType.CAVALRY] >= counts[UnitType.PIKEMAN] and counts[UnitType.CAVALRY] >= counts[UnitType.SWORDSMAN]:
            counter_type = UnitType.PIKEMAN
        elif counts[UnitType.PIKEMAN] >= counts[UnitType.CAVALRY] and counts[UnitType.PIKEMAN] >= counts[UnitType.SWORDSMAN]:
            counter_type = UnitType.SWORDSMAN
        else:
            counter_type = UnitType.CAVALRY

        # Нанимать 5 юнитов типа counter_type
        for _ in range(5):
            if self.computer_base.coins >= self.hire_cost:
                self.computer_base.coins -= self.hire_cost
                spread_radius = 30
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, spread_radius)
                offset_x = math.cos(angle) * distance
                offset_y = math.sin(angle) * distance
                spawn_x = self.computer_base.x + offset_x
                spawn_y = self.computer_base.y + offset_y
                unit = Unit(counter_type, spawn_x, spawn_y, "computer", self.canvas)
                self.computer_units.append(unit)
                print(f"ИИ нанимает {counter_type} на позиции ({spawn_x:.2f}, {spawn_y:.2f})")  # Отладочное сообщение

    def computer_send_attack(self):
        # Приказ всем компьютерам атаковать базу игрока
        for unit in self.computer_units:
            unit.target_x = self.player_base.x
            unit.target_y = self.player_base.y
        print("ИИ отправляет войска на атаку!")

    def end_game(self):
        self.state = 'game_over'
        Clock.unschedule(self.update_game)
        # Удаление всех юнитов
        for unit in self.player_units.copy():
            try:
                self.canvas.remove(unit.graphic)
                if unit.selected:
                    self.selected_units.remove(unit)
                    unit.deselect()
                self.player_units.remove(unit)
            except:
                pass
        for unit in self.computer_units.copy():
            try:
                self.canvas.remove(unit.graphic)
                self.computer_units.remove(unit)
            except:
                pass
        # Показать результат
        if self.player_base.hp > 0:
            result_text = "Победа!"
        else:
            result_text = "Поражение!"
        self.result_label = Label(text=result_text,
                                  font_size=50,
                                  color=(1,1,1,1),
                                  size_hint=(None, None),
                                  size=(300, 100),
                                  pos=(Window.width/2 - 150, Window.height/2 + 50))
        self.add_widget(self.result_label)
        # Добавление кнопки перезапуска
        self.restart_button = Button(text="Перезапустить",
                                     size_hint=(None, None),
                                     size=(200, 60),
                                     pos_hint={'center_x':0.5, 'center_y':0.3})
        self.restart_button.bind(on_release=self.restart_game)
        self.add_widget(self.restart_button)

    def restart_game(self, instance):
        # Удаление результатов и кнопки перезапуска
        if hasattr(self, 'result_label') and self.result_label in self.children:
            self.remove_widget(self.result_label)
        if hasattr(self, 'restart_button') and self.restart_button in self.children:
            self.remove_widget(self.restart_button)
        # Сброс состояния
        self.player_base.hp = 250
        self.player_base.coins = 100
        self.computer_base.hp = 250
        self.computer_base.coins = 100
        self.computer_hire_timer = 0
        self.computer_attack_timer = 0
        self.state = 'playing'
        self.selected_units = []
        # Создание начальных юнитов компьютера
        self.create_computer_initial_units()
        Clock.schedule_once(self.send_computer_initial_units, 5)
        # Запуск таймеров
        Clock.schedule_interval(self.update_game, 1/60.)
        # Инициализация кнопок найма
        self.init_hire_buttons()

    def on_touch_down(self, touch):
        if self.state == 'playing':
            # Проверяем, нажата ли кнопка найма
            for child in self.children:
                if isinstance(child, BoxLayout):
                    for button in child.children:
                        if button.collide_point(*touch.pos):
                            return super(RTSGame, self).on_touch_down(touch)

            # Проверяем, нажата ли свой юнит
            for unit in self.player_units:
                if (unit.x - unit.size/2 <= touch.x <= unit.x + unit.size/2 and
                        unit.y - unit.size/2 <= touch.y <= unit.y + unit.size/2):
                    current_time = time.time()
                    # Проверяем, был ли предыдущий клик на том же юните и в пределах двойного клика
                    if (self.last_touched_unit == unit and
                        (current_time - self.last_touch_time) <= self.double_click_time):
                        # Это двойной клик - выбираем все юниты того же типа
                        self.select_all_units_of_type(unit.type)
                        self.last_touched_unit = None
                        self.last_touch_time = 0
                    else:
                        # Это первый клик - сохраняем информацию для возможного двойного клика
                        self.last_touched_unit = unit
                        self.last_touch_time = current_time
                        # Запускаем таймер для сброса двойного клика
                        Clock.schedule_once(lambda dt: self.reset_last_touch(), self.double_click_time)
                        # Обрабатываем одиночный клик как обычно
                        if unit in self.selected_units:
                            unit.deselect()
                            self.selected_units.remove(unit)
                        else:
                            unit.select()
                            self.selected_units.append(unit)
                    return True
            # Проверяем, нажата ли вражеская юнита (можно добавить аналогичную логику для вражеских юнитов, если необходимо)
            for unit in self.computer_units:
                if (unit.x - unit.size/2 <= touch.x <= unit.x + unit.size/2 and
                        unit.y - unit.size/2 <= touch.y <= unit.y + unit.size/2):
                    # Можно добавить действия при клике на вражеский юнит, если требуется
                    return super(RTSGame, self).on_touch_down(touch)

            # Если клик вне юнитов и кнопок, приказать переместиться выбранным юнитам
            if self.selected_units:
                target_x, target_y = touch.x, touch.y
                # Ограничиваем целевые позиции границами экрана
                button_panel_height = Window.height * 0.1
                target_x = max(unit.size/2, min(target_x, Window.width - unit.size/2))
                target_y = max(button_panel_height + unit.size/2, min(target_y, Window.height - unit.size/2))
                for unit in self.selected_units:
                    unit.target_x = target_x
                    unit.target_y = target_y
            return True
        return super(RTSGame, self).on_touch_down(touch)

    def reset_last_touch(self):
        self.last_touched_unit = None
        self.last_touch_time = 0

    def select_all_units_of_type(self, unit_type):
        # Сначала снимаем выделение со всех юнитов
        for unit in self.selected_units.copy():
            unit.deselect()
            self.selected_units.remove(unit)
        # Затем выделяем все юниты определённого типа
        for unit in self.player_units:
            if unit.type == unit_type:
                unit.select()
                self.selected_units.append(unit)
        print(f"Выбраны все союзные юниты типа: {unit_type}")  # Отладочное сообщение

# Основной класс приложения
class RTSApp(App):
    def build(self):
        game = RTSGame()
        return game

# Запуск приложения
if __name__ == '__main__':
    RTSApp().run()