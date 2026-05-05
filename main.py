import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
import os
from datetime import datetime


class PasswordGeneratorApp:
    def __init__(self, root):
        """Инициализация главного окна приложения."""
        self.root = root
        self.root.title("Random Password Generator")  # заголовок окна
        self.root.geometry("600x500")                  # размер окна

        # файл для хранения истории паролей
        self.history_file = "password_history.json"
        # загружаем историю из файла (или пустой список, если файла нет)
        self.history = self.load_history()

        # создаём интерфейс
        self.setup_ui()
        # показываем пример пароля сразу при запуске
        self.update_preview()

    def setup_ui(self):
        """Создание всех элементов интерфейса."""
        # группа параметров пароля
        frame_opts = ttk.LabelFrame(self.root, text="Параметры пароля")
        frame_opts.pack(fill="x", padx=10, pady=5)

        # Ползунок длины пароля
        ttk.Label(frame_opts, text="Длина пароля:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.length_var = tk.IntVar(value=12)  # текущее значение длины
        length_slider = ttk.Scale(
            frame_opts,
            from_=6,                    # минимум 6 символов
            to=32,                      # максимум 32 символа
            variable=self.length_var,   # связываем с переменной
            orient="horizontal",        # горизонтальный ползунок
            command=lambda _: self.update_preview(),  # при изменении обновляем пример
        )
        length_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.length_label = ttk.Label(frame_opts, text="12")  # метка с числом
        self.length_label.grid(row=0, column=2, padx=5, pady=5)

        # настройка столбца так, чтобы слайдер растягивался
        frame_opts.grid_columnconfigure(1, weight=1)

        # Чекбоксы для выбора наборов символов
        self.use_digits = tk.BooleanVar(value=True)    # цифры 0–9
        self.use_lower  = tk.BooleanVar(value=True)    # строчные буквы
        self.use_upper  = tk.BooleanVar(value=True)    # прописные буквы
        self.use_special = tk.BooleanVar(value=True)   # спецсимволы

        ttk.Checkbutton(
            frame_opts,
            text="Цифры 0-9",
            variable=self.use_digits,
            command=self.update_preview,  # при изменении обновляем пример
        ).grid(row=1, column=0, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(
            frame_opts,
            text="Строчные a-z",
            variable=self.use_lower,
            command=self.update_preview,
        ).grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(
            frame_opts,
            text="Прописные A-Z",
            variable=self.use_upper,
            command=self.update_preview,
        ).grid(row=2, column=0, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(
            frame_opts,
            text="Спецсимволы (!@#$%^&*)",
            variable=self.use_special,
            command=self.update_preview,
        ).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        # Кнопка генерации пароля
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        self.generate_btn = ttk.Button(
            btn_frame,
            text="Сгенерировать",
            command=self.generate_password,  # при нажатии вызывается метод
        )
        self.generate_btn.pack(side="left", padx=5, pady=5)

        # Поле‑превью пароля (только для чтения)
        ttk.Label(self.root, text="Пример пароля:").pack(anchor="w", padx=10)
        self.preview_var = tk.StringVar(value="")  # строковая переменная для виджета
        ttk.Entry(
            self.root,
            textvariable=self.preview_var,
            state="readonly",  # поле нельзя редактировать
        ).pack(fill="x", padx=10, pady=2)

        # Таблица истории паролей
        history_frame = ttk.LabelFrame(self.root, text="История паролей")
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("length", "chars", "password", "timestamp")
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",  # показывают только заголовки столбцов
            height=8,
        )
        self.history_tree.heading("length", text="Длина")
        self.history_tree.heading("chars", text="Символы")
        self.history_tree.heading("password", text="Пароль")
        self.history_tree.heading("timestamp", text="Дата/время")
        self.history_tree.pack(fill="both", expand=True, padx=2, pady=2)

        # Вертикальный скроллбар для таблицы
        vsb = ttk.Scrollbar(self.history_tree, orient="vertical", command=self.history_tree.yview)
        vsb.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=vsb.set)

        # Заполняем таблицу текущей историей
        self.refresh_history()

    def update_preview(self, *_):
        """Обновляет текст примера пароля в поле‑превью при изменении длины или чекбоксов."""
        length = self.length_var.get()  # текущая длина из ползунка
        self.length_label.config(text=str(length))  # показываем число

        try:
            pw = self._generate_password_preview(length)
            self.preview_var.set(pw)
        except ValueError:
            self.preview_var.set("Ошибка: недостаточно символов")

    def _generate_password_preview(self, length):
        """
        Внутренний метод: генерирует пример пароля заданной длины
        без добавления записи в историю.
        Параметры:
            length — желаемая длина пароля.
        Возвращает строку пароля.
        Выбрасывает ValueError, если выбрано 0 наборов символов.
        """
        chars = ""  # строка всех доступных символов
        if self.use_digits.get():
            chars += "0123456789"
        if self.use_lower.get():
            chars += "abcdefghijklmnopqrstuvwxyz"
        if self.use_upper.get():
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.use_special.get():
            chars += "!@#$%^&*"

        # если нет ни одного набора символов — ошибка
        if not chars:
            raise ValueError("Нет ни одного набора символов")

        # собираем пароль случайным выбором символов
        return "".join(random.choice(chars) for _ in range(length))

    def generate_password(self):
        """Основной метод генерации пароля и добавления его в историю."""
        length = self.length_var.get()

        # проверка на минимальную и максимальную длину
        if length < 6 or length > 32:
            messagebox.showwarning(
                "Ошибка",
                "Длина пароля должна быть от 6 до 32 символов."
            )
            return

        # генерируем пароль, при ошибке показываем сообщение
        try:
            password = self._generate_password_preview(length)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        # собираем строку‑описание используемых символов
        char_desc = []
        if self.use_digits.get():  char_desc.append("цифры")
        if self.use_lower.get():   char_desc.append("a-z")
        if self.use_upper.get():   char_desc.append("A-Z")
        if self.use_special.get(): char_desc.append("спецсим")

        # объект для записи в историю
        record = {
            "length": length,               # длина пароля
            "chars": ", ".join(char_desc),  # используемые наборы
            "password": password,           # сам пароль
            "timestamp": datetime.now().isoformat(),  # дата/время в строчном формате
        }

        self.history.insert(0, record)   # добавляем в начало списка (свежий пароль сверху)
        self.save_history()             # сохраняем историю в JSON‑файл
        self.refresh_history()          # обновляем таблицу в интерфейсе
        self.update_preview()           # обновляем пример пароля

    def refresh_history(self):
        """Очищает таблицу и заполняет её данными из self.history."""
        # удаляем все строки из таблицы
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        # добавляем каждую запись в таблицу
        for record in self.history:
            self.history_tree.insert(
                "",  # вставка в корень
                "end",  # в конец
                values=(
                    record["length"],
                    record["chars"],
                    record["password"],
                    record["timestamp"][:19],  # обрезаем до читаемой части времени
                ),
            )

    def load_history(self):
        """Считывает историю из password_history.json или возвращает пустой список."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):  # проверяем, что это список записей
                        return data
            except (json.JSONDecodeError, OSError):
                # если файл битый или ошибка чтения — игнорируем
                pass
        return []  # пустая история при старте

    def save_history(self):
        """Сохраняет текущий список истории в JSON‑файл."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()  # создаём главное окно Tkinter
    app = PasswordGeneratorApp(root)  # создаём объект приложения
    root.mainloop()  # запускаем главный цикл обработки событий GUI