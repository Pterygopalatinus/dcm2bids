#!/usr/bin/env python3
"""
Главный файл для запуска MRI Pipeline приложения
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Главная функция приложения"""
    try:
        app = MainWindow()
        app.run()
    except KeyboardInterrupt:
        print("\nПриложение остановлено пользователем")
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 