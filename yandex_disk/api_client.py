"""
Клиент для работы с API Яндекс.Диска
"""

import requests
import json
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode


class YandexDiskClient:
    """Клиент для работы с API Яндекс.Диска"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о пользователе
        
        Returns:
            Dict[str, Any] или None: Информация о пользователе
        """
        try:
            response = requests.get(f"{self.base_url}/", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении информации о пользователе: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Статус код: {e.response.status_code}")
                print(f"Ответ сервера: {e.response.text}")
            return None
    
    def list_files(self, path: str = "/", limit: int = 1000, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Получает список файлов в указанной папке
        
        Args:
            path: Путь к папке (по умолчанию корневая папка)
            limit: Максимальное количество файлов
            offset: Смещение для пагинации
            
        Returns:
            Dict[str, Any] или None: Список файлов
        """
        try:
            params = {
                "path": path,
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(
                f"{self.base_url}/resources",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении списка файлов: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Статус код: {e.response.status_code}")
                print(f"Ответ сервера: {e.response.text}")
            return None
    
    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о файле
        
        Args:
            path: Путь к файлу
            
        Returns:
            Dict[str, Any] или None: Информация о файле
        """
        try:
            params = {"path": path}
            response = requests.get(
                f"{self.base_url}/resources",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении информации о файле: {e}")
            return None
    
    def create_folder(self, path: str) -> bool:
        """
        Создает папку
        
        Args:
            path: Путь к создаваемой папке
            
        Returns:
            bool: True если папка создана успешно
        """
        try:
            params = {"path": path}
            response = requests.put(
                f"{self.base_url}/resources",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при создании папки: {e}")
            return False
    
    def delete_file(self, path: str, permanently: bool = False) -> bool:
        """
        Удаляет файл или папку
        
        Args:
            path: Путь к файлу/папке
            permanently: Удалить навсегда (True) или в корзину (False)
            
        Returns:
            bool: True если удаление прошло успешно
        """
        try:
            params = {
                "path": path,
                "permanently": permanently
            }
            response = requests.delete(
                f"{self.base_url}/resources",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при удалении файла: {e}")
            return False
    
    def get_download_link(self, path: str) -> Optional[str]:
        """
        Получает ссылку для скачивания файла
        
        Args:
            path: Путь к файлу
            
        Returns:
            str или None: Ссылка для скачивания
        """
        try:
            params = {"path": path}
            response = requests.get(
                f"{self.base_url}/resources/download",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("href")
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении ссылки для скачивания: {e}")
            return None 

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Скачивает файл с Яндекс.Диска в указанный локальный путь.
        """
        try:
            href = self.get_download_link(remote_path)
            if not href:
                return False
            with requests.get(href, stream=True) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при скачивании файла {remote_path}: {e}")
            return False 