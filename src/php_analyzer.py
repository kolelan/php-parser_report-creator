from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from .config import Config
from .description_manager import DescriptionManager
from .php_parser import PHPParser
from .csv_writer import CSVWriter
from .utils import get_relative_path


class PHPAnalyzer:
    TYPE_MAPPING = {
        'class': 'Класс',
        'method': 'Метод',
        'property': 'Свойство',
        'function': 'Функция',
        'variable': 'Переменная',
        'constant': 'Константа',
        'class_constant': 'Константа класса'
    }

    CLASS_ITEMS = {'class', 'method', 'property', 'class_constant'}

    def __init__(self, descriptions_dir: str = Config.DESCRIPTIONS_DIR,
                 exact_match: bool = True, full_names: bool = True, debug: bool = False):
        self.descriptions_dir = descriptions_dir
        self.exact_match = exact_match
        self.full_names = full_names
        self.debug = debug

        self.description_manager = DescriptionManager(descriptions_dir, debug=debug)
        self.php_parser = PHPParser(debug=debug)
        self.csv_writer = CSVWriter()

        self.base_dir = Path()
        self.current_class = ""
        self.current_class_items = 0

        self.stats = self._initialize_stats()

    def _initialize_stats(self) -> Dict[str, defaultdict]:
        """Инициализирует статистику"""
        return {
            'found': defaultdict(int),
            'missing': defaultdict(int),
            'empty': defaultdict(int),
            'total': defaultdict(int)
        }

    def analyze_directory(self, directory: str | Path, output_csv: str | Path) -> None:
        """Анализирует директорию с PHP файлами"""
        self.base_dir = Path(directory)
        all_items = []
        duplicates = defaultdict(list)

        print(f"Поиск PHP файлов в: {self.base_dir.absolute()}")

        php_files = list(self.base_dir.rglob('*.php'))
        print(f"Найдено PHP файлов: {len(php_files)}")

        if not php_files:
            print("Предупреждение: PHP файлы не найдены!")
            # Покажем структуру директории для диагностики
            print("Содержимое директории:")
            for item in self.base_dir.rglob('*'):
                print(f"  - {item}")
            return

        for file_path in php_files:
            if self.debug:
                print(f"Обработка файла: {file_path}")
            file_items = self._process_file(file_path)

            if self.debug and file_items:
                print(f"  Извлечено элементов: {len(file_items)}")

            for item in file_items:
                self._check_duplicates(item, duplicates)
                all_items.append(item)

        if all_items:
            self._write_results(all_items, output_csv, duplicates)
            self._print_statistics()
        else:
            print("PHP-файлы не найдены или не содержат анализируемых элементов.")
            if self.debug:
                # Протестируем парсинг на одном файле с максимальной отладкой
                test_file = php_files[0]
                print(f"\nТестовый парсинг файла: {test_file}")
                self._test_parse_file(test_file)

    def _process_file(self, file_path: Path) -> List[Dict]:
        """Обрабатывает один файл"""
        elements = self.php_parser.parse_file(file_path)
        items = []
        relative_path = get_relative_path(file_path, self.base_dir)

        for element in elements:
            item = self._process_element(element, relative_path)
            if item:
                items.append(item)

        return items

    def _process_element(self, element: Dict, relative_path: str) -> Optional[Dict]:
        """Обрабатывает один элемент"""
        item_type = element['type']
        self.stats['total'][item_type] += 1

        name = element['name']
        short_name = element.get('short_name', '')
        desc = element['desc']  # Описание из PHP DocBlock
        line_number = element.get('startLine', 0)

        # Ищем описание в JSON файлах
        json_description, found = self.description_manager.get_description(
            item_type, name, short_name, self.exact_match, self.full_names
        )

        if found:
            self.stats['found'][item_type] += 1
            desc = json_description or desc  # Используем описание из JSON если найдено
        else:
            self.stats['missing'][item_type] += 1

        # ВАЖНО: Сохраняем описание из PHP DocBlock в found_ файлы ТОЛЬКО если не нашли в JSON
        if desc.strip() and not found:  # Если есть описание из DocBlock И не нашли в JSON
            self.description_manager._save_found_description(item_type, name, desc)

        # Обновляем статистику пустых описаний
        if not desc.strip():
            self.stats['empty'][item_type] += 1

        display_name = self._get_display_name(name, short_name)
        item_number = self._get_item_number(item_type, name)

        item_data = self._build_item_data(
            relative_path, display_name, item_type, desc, item_number, line_number
        )

        return item_data

    def _get_display_name(self, name: str, short_name: str) -> str:
        """Возвращает отображаемое имя"""
        return short_name if (not self.full_names and short_name) else name

    def _get_item_number(self, item_type: str, name: str) -> int:
        """Определяет номер элемента"""
        if item_type in self.CLASS_ITEMS:
            if item_type == 'class':
                self.current_class = name
                self.current_class_items = 1
                return 1
            else:
                item_number = self.current_class_items
                self.current_class_items += 1
                return item_number
        return 1

    def _build_item_data(self, relative_path: str, name: str, item_type: str,
                         description: str, item_number: int, line_number: int) -> Dict:
        """Создает данные элемента"""
        item_data = {
            'relative_path': relative_path,
            'name': name,
            'type': item_type,
            'type_ru': self.TYPE_MAPPING.get(item_type, item_type),
            'description': description,
            'item_number': item_number
        }

        if Config.INCLUDE_LINE_NUMBERS:
            item_data['line_number'] = line_number

        return item_data

    def _check_duplicates(self, item: Dict, duplicates: Dict):
        """Проверяет дубликаты"""
        if not Config.CHECK_FOR_DUPLICATES:
            return

        if item['type'] in ['method', 'property', 'class_constant', 'function', 'variable']:
            key = self._get_duplicate_key(item)
            duplicates[key].append({
                'file': item['relative_path'],
                'line': item.get('line_number', 0)
            })

    def _get_duplicate_key(self, item: Dict) -> tuple:
        """Возвращает ключ для проверки дубликатов"""
        if item['type'] in ['method', 'property', 'class_constant']:
            return (item['name'].split('::')[-1], item['type'])
        return (item['name'], item['type'])

    def _write_results(self, items: List[Dict], output_csv: str | Path, duplicates: Dict):
        """Записывает результаты"""
        self.csv_writer.write_to_csv(items, output_csv)
        self.description_manager.save_empty_descriptions()
        print(f"Результаты сохранены в {output_csv}")

    def _print_statistics(self):
        """Выводит статистику"""
        print("\nСтатистика анализа:")
        print("{:<15} {:<10} {:<10} {:<10} {:<10}".format(
            "Тип", "Всего", "Найдено", "Нет опис.", "Пустые"))

        for item_type, ru_name in self.TYPE_MAPPING.items():
            print("{:<15} {:<10} {:<10} {:<10} {:<10}".format(
                ru_name,
                self.stats['total'].get(item_type, 0),
                self.stats['found'].get(item_type, 0),
                self.stats['missing'].get(item_type, 0),
                self.stats['empty'].get(item_type, 0)
            ))
        # Выводим статистику найденных описаний
        self.description_manager.print_found_statistics()

    def _test_parse_file(self, file_path: Path):
        """Тестовый парсинг файла для диагностики"""
        try:
            # Прочитаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Размер файла: {len(content)} символов")
            print(f"Первые 200 символов: {content[:200]}...")

            # Запустим PHP парсер вручную для отладки
            result = subprocess.run(
                ['php', Config.PHP_PARSER_SCRIPT, str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            print(f"PHP stdout: {result.stdout[:500]}...")
            if result.stderr:
                print(f"PHP stderr: {result.stderr}")

        except Exception as e:
            print(f"Ошибка тестового парсинга: {e}")