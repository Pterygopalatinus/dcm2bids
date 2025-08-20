"""
Главное окно GUI приложения для MRT-пайплайна
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional

from config.credentials_manager import CredentialsManager
from yandex_disk.api_client import YandexDiskClient


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MRI pipeline")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Инициализация компонентов
        self.credentials_manager = CredentialsManager()
        self.yandex_client: Optional[YandexDiskClient] = None
        self.current_path = "/"
        # Храним состояние чекбоксов
        self._item_checked = {}
        self._all_checked = False
        self._CHECKED = "☑"
        self._UNCHECKED = "☐"
        
        self._setup_ui()
        self._check_credentials()
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Панель аутентификации
        self._setup_auth_panel(main_frame)
        
        # Создаем Notebook с вкладками
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.rowconfigure(1, weight=1)

        # --- Вкладка 1: Select Files ---
        tab_files = ttk.Frame(notebook)
        tab_files.columnconfigure(0, weight=1)
        tab_files.rowconfigure(1, weight=1)  # строка с Treeview растягивается
        notebook.add(tab_files, text="Select Files")

        # Вкладки-заглушки
        notebook.add(ttk.Frame(notebook), text="Tab 2")
        notebook.add(ttk.Frame(notebook), text="Tab 3")

        # Заполняем первую вкладку
        self._setup_navigation_panel(tab_files)
        self._setup_file_list(tab_files)
        self._setup_download_controls(tab_files)

        # Статусная строка
        self._setup_status_bar(main_frame)
    
    def _setup_auth_panel(self, parent):
        """Настройка панели аутентификации"""
        auth_frame = ttk.LabelFrame(parent, text="Аутентификация", padding="5")
        auth_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Поле для токена
        ttk.Label(auth_frame, text="OAuth токен:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(auth_frame, textvariable=self.token_var, width=50, show="*")
        self.token_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Кнопки
        ttk.Button(auth_frame, text="Подключиться", command=self._connect_to_yandex).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(auth_frame, text="Сохранить токен", command=self._save_token).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(auth_frame, text="Очистить", command=self._clear_token).grid(row=0, column=4)
        
        # Настройка весов
        auth_frame.columnconfigure(1, weight=1)
    
    def _setup_navigation_panel(self, parent):
        """Настройка панели навигации"""
        nav_frame = ttk.Frame(parent)
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Кнопки навигации
        ttk.Button(nav_frame, text="← Назад", command=self._go_back).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="Обновить", command=self._refresh_files).pack(side=tk.LEFT, padx=(0, 5))
        
        # Поле пути
        ttk.Label(nav_frame, text="Путь:").pack(side=tk.LEFT, padx=(10, 5))
        self.path_var = tk.StringVar(value="/")
        path_entry = ttk.Entry(nav_frame, textvariable=self.path_var, width=40)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        path_entry.bind('<Return>', self._navigate_to_path)
        
        ttk.Button(nav_frame, text="Перейти", command=self._navigate_to_path).pack(side=tk.LEFT)
    
    def _setup_file_list(self, parent):
        """Настройка списка файлов"""
        # Фрейм для списка файлов
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Создание Treeview
        columns = ("sel", "name", "type", "size", "modified")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Колонка чекбокса
        self.file_tree.heading("sel", text=self._UNCHECKED)
        self.file_tree.column("sel", width=30, anchor=tk.CENTER, stretch=False)
        
        # Настройка колонок
        self.file_tree.heading("#0", text="")
        self.file_tree.column("#0", width=20, stretch=False)
        self.file_tree.heading("name", text="Имя")
        self.file_tree.column("name", width=300, stretch=True)
        self.file_tree.heading("type", text="Тип")
        self.file_tree.column("type", width=100, stretch=False)
        self.file_tree.heading("size", text="Размер")
        self.file_tree.column("size", width=100, stretch=False)
        self.file_tree.heading("modified", text="Изменен")
        self.file_tree.column("modified", width=150, stretch=False)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Обработчик клика для чекбоксов
        self.file_tree.bind("<Button-1>", self._on_tree_click)
        
        # Размещение элементов
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Привязка событий
        self.file_tree.bind("<Double-1>", self._on_file_double_click)
        self.file_tree.bind("<Button-3>", self._on_file_right_click)
    
    def _setup_status_bar(self, parent):
        """Настройка статусной строки"""
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def _check_credentials(self):
        """Проверка сохраненных учетных данных и переменных окружения"""
        token = self.credentials_manager.get_token()
        if token:
            self.token_var.set(token)
            self._connect_to_yandex()
    
    def _connect_to_yandex(self):
        """Подключение к Яндекс.Диску"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Ошибка", "Введите OAuth токен")
            return
        
        self.status_var.set("Подключение к Яндекс.Диску...")
        
        def connect_thread():
            try:
                self.yandex_client = YandexDiskClient(token)
                user_info = self.yandex_client.get_user_info()
                
                if user_info:
                    self.root.after(0, lambda: self._on_connection_success(user_info))
                else:
                    self.root.after(0, lambda: self._on_connection_error("Не удалось получить информацию о пользователе"))
            except Exception as e:
                self.root.after(0, lambda: self._on_connection_error(f"Ошибка подключения: {e}"))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_connection_success(self, user_info):
        """Обработка успешного подключения"""
        self.status_var.set(f"Подключено: {user_info.get('display_name', 'Пользователь')}")
        self._refresh_files()
    
    def _on_connection_error(self, error_message):
        """Обработка ошибки подключения"""
        self.status_var.set("Ошибка подключения")
        
        # Добавляем дополнительные рекомендации для ошибки 403
        if "403" in error_message or "FORBIDDEN" in error_message:
            detailed_message = f"{error_message}\n\nВозможные причины:\n" \
                             f"• Токен истек или недействителен\n" \
                             f"• Недостаточно прав в OAuth приложении\n" \
                             f"• Приложение не активировано\n\n" \
                             f"Рекомендации:\n" \
                             f"• Получите новый токен на https://oauth.yandex.ru/\n" \
                             f"• Убедитесь, что добавлены права cloud_api:disk.read"
        else:
            detailed_message = error_message
            
        messagebox.showerror("Ошибка подключения", detailed_message)
    
    def _save_token(self):
        """Сохранение токена"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Ошибка", "Введите токен для сохранения")
            return
        
        credentials = {"access_token": token}
        if self.credentials_manager.save_credentials(credentials):
            messagebox.showinfo("Успех", "Токен сохранен")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить токен")
    
    def _clear_token(self):
        """Очистка токена"""
        self.token_var.set("")
        self.credentials_manager.clear_credentials()
        self.yandex_client = None
        self.status_var.set("Токен очищен")
        self._clear_file_list()
    
    def _refresh_files(self):
        """Обновление списка файлов"""
        if not self.yandex_client:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к Яндекс.Диску")
            return
        
        self.status_var.set("Загрузка файлов...")
        
        def load_files_thread():
            try:
                files_data = self.yandex_client.list_files(self.current_path)
                self.root.after(0, lambda: self._display_files(files_data))
            except Exception as e:
                self.root.after(0, lambda: self._on_load_error(f"Ошибка загрузки файлов: {e}"))
        
        threading.Thread(target=load_files_thread, daemon=True).start()
    
    def _display_files(self, files_data):
        """Отображение файлов в списке"""
        self._clear_file_list()
        # Сброс чекбоксов
        self._item_checked.clear()
        self._all_checked = False
        if hasattr(self, 'file_tree'):
            self.file_tree.heading('sel', text=self._UNCHECKED)
        
        if not files_data:
            self.status_var.set("Нет файлов")
            return
            
        # Проверяем, есть ли items в корне или в _embedded
        if "items" in files_data:
            items = files_data["items"]
        elif "_embedded" in files_data and "items" in files_data["_embedded"]:
            items = files_data["_embedded"]["items"]
        else:
            self.status_var.set("Нет файлов")
            return
        
        for item in items:
            name = item.get("name", "")
            path = item.get("path", "")
            type_ = "Папка" if item.get("type") == "dir" else "Файл"
            size = self._format_size(item.get("size", 0))
            modified = item.get("modified", "")
            
            # Иконка не используем, вместо этого чекбокс
            item_id = self.file_tree.insert("", "end", values=(self._UNCHECKED, name, type_, size, modified), tags=(path,))
            self._item_checked[item_id] = False
        
        self.path_var.set(self.current_path)
        self.status_var.set(f"Загружено {len(items)} элементов")
    
    def _clear_file_list(self):
        """Очистка списка файлов"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
    
    def _format_size(self, size_bytes):
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _on_file_double_click(self, event):
        """Обработка двойного клика по файлу"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = self.file_tree.item(selection[0])
        path = item["tags"][0] if item["tags"] else ""
        item_type = item["values"][2] if item["values"] else ""
        
        if item_type == "Папка":
            self.current_path = path
            self._refresh_files()
    
    def _on_file_right_click(self, event):
        """Обработка правого клика по файлу"""
        # TODO: Добавить контекстное меню
        pass
    
    def _go_back(self):
        """Переход назад (к родительской папке)"""
        if self.current_path in ["/", "disk:/"]:
            return

        # Убираем последний сегмент пути
        path_trimmed = self.current_path.rstrip("/")
        segments = path_trimmed.split("/")
        if len(segments) > 1:
            parent_path = "/".join(segments[:-1])
            # Приводим к корректному виду корня
            if parent_path in ["", "disk:"]:
                parent_path = "/"
            # Убедимся, что для disk: добавлен слеш
            if parent_path.startswith("disk:") and not parent_path.startswith("disk:/"):
                parent_path = "disk:/"

            self.current_path = parent_path
            self._refresh_files()

    def _go_up(self):
        """Переход вверх по иерархии (аналогично _go_back)"""
        self._go_back()
    
    def _navigate_to_path(self, event=None):
        """Переход по указанному пути"""
        path = self.path_var.get().strip()
        if path and path != self.current_path:
            self.current_path = path
            self._refresh_files()
    
    def _on_load_error(self, error_message):
        """Обработка ошибки загрузки файлов"""
        self.status_var.set("Ошибка загрузки")
        messagebox.showerror("Ошибка", error_message)
    
    def _setup_download_controls(self, parent):
        """Панель управления скачиванием"""
        controls_frame = ttk.Frame(parent, padding="5")
        controls_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        controls_frame.columnconfigure(1, weight=1)

        # Выбор директории
        ttk.Button(controls_frame, text="Выбрать папку для скачивания", command=self._choose_download_dir).grid(row=0, column=0, padx=(0, 5))
        self.download_dir_var = tk.StringVar(value="")
        ttk.Label(controls_frame, textvariable=self.download_dir_var).grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Чекбокс разархивации
        self.decompress_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Разархивировать zip", variable=self.decompress_var).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Кнопка скачивания
        ttk.Button(controls_frame, text="Скачать выбранные", command=self._download_selected).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # Прогрессбар
        self.progress = ttk.Progressbar(controls_frame, orient=tk.HORIZONTAL, length=400, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

    def _choose_download_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.download_dir_var.set(directory)

    def _download_selected(self):
        if not self.yandex_client:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к Яндекс.Диску")
            return
        dest_dir = self.download_dir_var.get()
        if not dest_dir:
            messagebox.showwarning("Ошибка", "Сначала выберите папку для скачивания")
            return
        selected_items = [iid for iid, checked in self._item_checked.items() if checked]
        if not selected_items:
            messagebox.showinfo("Выбор", "Выберите файлы (чекбоксы) для скачивания")
            return

        self.status_var.set("Скачивание файлов...")
        decompress = self.decompress_var.get()
        # Настройка прогрессбара
        if hasattr(self, 'progress'):
            self.progress["maximum"] = len(selected_items)
            self.progress["value"] = 0

        def download_thread():
            import os, zipfile
            success_count = 0
            for item_id in selected_items:
                item = self.file_tree.item(item_id)
                remote_path = item["tags"][0] if item["tags"] else ""
                filename = item["values"][1]
                local_path = os.path.join(dest_dir, filename)
                if self.yandex_client.download_file(remote_path, local_path):
                    success_count += 1
                    if decompress and filename.lower().endswith(".zip"):
                        try:
                            with zipfile.ZipFile(local_path, 'r') as zip_ref:
                                extract_dir = os.path.join(dest_dir, os.path.splitext(filename)[0])
                                zip_ref.extractall(extract_dir)
                        except Exception as e:
                            print(f"Ошибка разархивации {filename}: {e}")
                # шаг прогресса
                if hasattr(self, 'progress'):
                    self.root.after(0, self.progress.step, 1)
            self.root.after(0, lambda: self.status_var.set(f"Скачивание завершено: {success_count} файлов"))
            if hasattr(self, 'progress'):
                self.root.after(0, lambda: self.progress.stop())

        threading.Thread(target=download_thread, daemon=True).start()
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop() 

    def _on_tree_click(self, event):
        """Обработка клика по Treeview для переключения чекбоксов"""
        region = self.file_tree.identify_region(event.x, event.y)
        column = self.file_tree.identify_column(event.x)
        handled = False
        if region == "heading" and column == "#1":  # колонка sel
            # Переключить все
            self._all_checked = not self._all_checked
            new_symbol = self._CHECKED if self._all_checked else self._UNCHECKED
            self.file_tree.heading("sel", text=new_symbol)
            for item_id in self.file_tree.get_children():
                self._item_checked[item_id] = self._all_checked
                self.file_tree.set(item_id, "sel", new_symbol)
            handled = True
        elif region == "cell" and column == "#1":
            item_id = self.file_tree.identify_row(event.y)
            if item_id:
                current = self._item_checked.get(item_id, False)
                new_state = not current
                self._item_checked[item_id] = new_state
                self.file_tree.set(item_id, "sel", self._CHECKED if new_state else self._UNCHECKED)
                # Сбросить header чекбокс если нужно
                if not new_state:
                    self._all_checked = False
                    self.file_tree.heading("sel", text=self._UNCHECKED)
                else:
                    # Проверяем все ли отмечены
                    if all(self._item_checked.values()):
                        self._all_checked = True
                        self.file_tree.heading("sel", text=self._CHECKED)
            handled = True
        # если обработали чекбокс, прервать дальнейшую обработку события Treeview
        if handled:
            return "break"
        # иначе позволяем двойному клику и выбору работать
        return None 