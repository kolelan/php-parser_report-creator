import os
import subprocess
from pathlib import Path
from typing import Dict, Any

def check_php_environment() -> bool:
    """Проверяет наличие PHP и необходимых зависимостей"""
    try:
        result = subprocess.run(['php', '-v'], capture_output=True, text=True, check=True)
        return 'PHP' in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_directory(path: str | Path) -> bool:
    """Создает директорию если не существует"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False

def normalize_variable_name(name: str, prefix: str = '$') -> str:
    """Нормализует имя переменной"""
    name = name.lstrip(prefix)
    return prefix + name if name else ''

def get_relative_path(file_path: Path, base_dir: Path) -> str:
    """Возвращает относительный путь файла"""
    try:
        return str(file_path.relative_to(base_dir))
    except ValueError:
        return str(file_path.name)