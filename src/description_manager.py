import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from .config import Config


class DescriptionManager:
    def __init__(self, descriptions_dir: str = Config.DESCRIPTIONS_DIR, debug: bool = False):
        self.descriptions_dir = Path(descriptions_dir)
        self.debug = debug
        # Создаем папку descriptions если она не существует
        if not self.descriptions_dir.exists():
            print(f"Создаем папку описаний: {self.descriptions_dir.absolute()}")
            self.descriptions_dir.mkdir(parents=True, exist_ok=True)

        self.descriptions = self._load_all_descriptions()
        self.missing_descriptions: Dict[str, Set[str]] = {}
        self.empty_descriptions: Dict[str, Set[str]] = {}
        self.found_descriptions: Dict[str, Set[str]] = {}
        self._initialize_sets()

    def _initialize_sets(self):
        """Инициализирует множества для отсутствующих и пустых описаний"""
        for key in self.descriptions.keys():
            self.missing_descriptions[key] = set()
            self.empty_descriptions[key] = set()
            self.found_descriptions[key] = set()  # статистика по найденным описаниям

    def _load_all_descriptions(self) -> Dict[str, List[Dict]]:
        """Загружает все файлы описаний"""
        return {
            'class': self._load_description_file(Config.JSON_DESC_CLASSES),
            'method': self._load_description_file(Config.JSON_DESC_METHODS),
            'property': self._load_description_file(Config.JSON_DESC_PROPS),
            'function': self._load_description_file(Config.JSON_DESC_FUNC),
            'variable': self._load_description_file(Config.JSON_DESC_VARS),
            'constant': self._load_description_file(Config.JSON_DESC_CONST),
            'class_constant': self._load_description_file(Config.JSON_DESC_CLASS_CONST),
        }

    def _load_description_file(self, filename: str) -> List[Dict]:
        """Загружает JSON-файл с описаниями с поддержкой разных форматов"""
        file_path = self.descriptions_dir / filename
        try:
            if not file_path.exists():
                return []

            return self._load_different_file_types(file_path)

        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка загрузки файла {file_path}: {e}")
            return []

    def _load_different_file_types(self, file_path: Path) -> List[Dict]:
        """Загружает JSON-файл из конкретного пути"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Обработка разных форматов JSON
            if not data:
                return []

            # Формат 1: [{"name": "value", "desc": "description"}]
            if isinstance(data, list) and all(isinstance(item, dict) and 'name' in item for item in data):
                return data

            # Формат 2: [{"key": "description"}, {"key2": "description2"}]
            elif isinstance(data, list) and all(isinstance(item, dict) and len(item) == 1 for item in data):
                converted_data = []
                for item in data:
                    for key, value in item.items():
                        converted_data.append({'name': key, 'desc': value})
                return converted_data

            # Формат 3: {"key": "description", "key2": "description2"}
            elif isinstance(data, dict):
                converted_data = []
                for key, value in data.items():
                    converted_data.append({'name': key, 'desc': value})
                return converted_data

            return []

        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка загрузки файла {file_path}: {e}")
            return []

    def get_description(self, item_type: str, name: str, short_name: str = '',
                        exact_match: bool = True, full_names: bool = True) -> Tuple[Optional[str], bool]:
        """Получает описание для элемента"""
        descriptions = self.descriptions.get(item_type, [])
        found = False
        description = None

        if self.debug and len(descriptions) > 0:  # Теперь self.debug существует
            print(f"Поиск описания для: {item_type} '{name}' (short: '{short_name}')")
            print(f"  Доступно описаний: {len(descriptions)}")
            if len(descriptions) <= 10:  # Показываем первые 10 для отладки
                for i, desc in enumerate(descriptions[:10]):
                    print(f"    {i}: {desc.get('name', 'N/A')}")

        search_name, compare_names = self._prepare_search_names(item_type, name, short_name, full_names, exact_match)

        for item in descriptions:
            item_name = item.get('name', '')
            if not item_name:
                continue

            item_desc = item.get('desc', '')

            if self._matches(item, item_name, compare_names, exact_match):
                description = item_desc
                found = True
                break

        self._update_statistics(item_type, name, found, description)

        return description, found

    def _save_found_description(self, item_type: str, name: str, description: str):
        """Сохраняет найденное описание в файл с префиксом found_"""
        if not description.strip():
            return  # Не сохраняем пустые описания

        # Определяем файл для сохранения
        filename_map = {
            'class': 'found_classes.json',
            'method': 'found_methods.json',
            'property': 'found_properties.json',
            'function': 'found_functions.json',
            'variable': 'found_variables.json',
            'constant': 'found_constants.json',
            'class_constant': 'found_constants.json'  # Константы классов тоже в constants
        }

        filename = filename_map.get(item_type)
        if not filename:
            return

        file_path = self.descriptions_dir / filename

        #   existing_data = self._load_found_description_file(filename)
            # Загружаем существующие данные
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
        except:
            existing_data = []


        # Подготавливаем имя для сохранения
        if item_type in ['method', 'property', 'class_constant'] and '::' in name:
            # Для методов, свойств и констант классов сохраняем полное имя с классом
            save_name = name
        else:
            # Для остальных сохраняем как есть
            save_name = name

        # Проверяем, есть ли уже такое описание
        existing_names = {item['name'] for item in existing_data}

        if save_name not in existing_names:
            new_item = {'name': save_name, 'desc': description}
            updated_data = existing_data + [new_item]

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, ensure_ascii=False, indent=2)
                print(f"  Сохранено найденное описание: {item_type} '{save_name}'")
                # Здесь добавляем в статистику найденных описаний
                if item_type not in self.found_descriptions:
                    self.found_descriptions[item_type] = set()
                self.found_descriptions[item_type].add(save_name)

            except Exception as e:
                print(f"  Ошибка сохранения найденного описания: {e}")

    def _load_found_description_file(self, filename: str) -> List[Dict]:
        """Загружает файл с найденными описаниями"""
        file_path = self.descriptions_dir / filename
        try:
            if not file_path.exists():
                # Создаем пустой файл если не существует
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                return []

            return self._load_different_file_types(file_path)

        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка загрузки файла {file_path}: {e}")
            return []

    def _prepare_search_names(self, item_type: str, name: str, short_name: str,
                             full_names: bool, exact_match: bool) -> Tuple[str, List[str]]:
        """Подготавливает имена для поиска"""
        compare_names = []

        # Для методов, свойств и констант классов используем оба варианта
        if item_type in ['method', 'property', 'class_constant']:
            # Полное имя с классом (RegisterDocumentsReport::generateTemplate)
            compare_names.append(name)

            # Только имя метода/свойства/константы (generateTemplate)
            if '::' in name:
                compare_names.append(name.split('::')[-1])

            # Short name если предоставлен
            if short_name:
                compare_names.append(short_name)

        elif item_type == 'variable':
            # Нормализуем имя переменной
            normalized_name = name.lstrip(Config.VARIABLE_PREFIX)
            normalized_name = Config.VARIABLE_PREFIX + normalized_name if normalized_name else ''
            compare_names.append(normalized_name)

        else:
            # Для классов, функций, констант используем предоставленное имя
            compare_names.append(name)
            if short_name:
                compare_names.append(short_name)

        # Убираем дубликаты и пустые значения
        compare_names = list(set([cn for cn in compare_names if cn]))
        return compare_names[0] if compare_names else '', compare_names

    def _matches(self, item: Dict, item_name: str, compare_names: List[str], exact_match: bool) -> bool:
        """Проверяет совпадение имен"""
        # Если в описании указано условие 'like'
        if item.get('cond') == 'like':
            for compare_name in compare_names:
                if compare_name and compare_name.lower() in item_name.lower():
                    return True
            return False

        # Точное или неточное совпадение
        for compare_name in compare_names:
            if not compare_name:
                continue

            if exact_match:
                if item_name == compare_name:
                    return True
            else:
                if item_name.lower() == compare_name.lower():
                    return True

        return False

    def _update_statistics(self, item_type: str, name: str, found: bool, description: Optional[str]):
        """Обновляет статистику"""
        if not found:
            clean_name = name.lstrip(Config.VARIABLE_PREFIX) if item_type == 'variable' else name
            self.missing_descriptions[item_type].add(clean_name)
            print(f"  Добавлено в missing: {clean_name}")

        if not description:
            clean_name = name.lstrip(Config.VARIABLE_PREFIX) if item_type == 'variable' else name
            self.empty_descriptions[item_type].add(clean_name)
            print(f"  Добавлено в empty: {clean_name}")

    def save_empty_descriptions(self):
        """Сохраняет элементы с пустыми описаниями"""
        print("\nСохранение пустых описаний...")
        for item_type, items in self.empty_descriptions.items():
            if not items:
                continue

            print(f"  {item_type}: {len(items)} элементов")

            # Специальная обработка для множественного числа
            if item_type == 'class':
                filename = 'empty_classes.json'
            else:
                filename = f"empty_{item_type}s.json"
            file_path = self.descriptions_dir / filename
            existing_data = self._load_description_file(filename)

            existing_names = {item['name'] for item in existing_data}
            new_items = []

            for name in items:
                if name not in existing_names:
                    if item_type == 'variable' and not name.startswith(Config.VARIABLE_PREFIX):
                        name = Config.VARIABLE_PREFIX + name
                    new_items.append({'name': name, 'desc': ''})
                    print(f"    Новый: {name}")

            if new_items:
                updated_data = existing_data + new_items
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, ensure_ascii=False, indent=2)
                print(f"  Сохранено {len(new_items)} новых элементов в {file_path}")

    def print_found_statistics(self):
        """Выводит статистику найденных описаний"""
        print("\nСтатистика найденных описаний:")
        total_found = 0
        for item_type, items in self.found_descriptions.items():
            count = len(items)
            if count > 0:
                print(f"  {item_type}: {count} описаний найдено")
                total_found += count

        print(f"  Всего найдено: {total_found} описаний")