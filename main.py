import argparse
import subprocess
from pathlib import Path
from src.config import Config
from src.php_analyzer import PHPAnalyzer
from src.utils import check_php_environment

def main():
    parser = argparse.ArgumentParser(
        description='Анализатор PHP-файлов с использованием AST парсера',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('directory', help='Директория с PHP-файлами для анализа')
    parser.add_argument('--descriptions', default=Config.DESCRIPTIONS_DIR,
                        help='Директория с JSON-файлами описаний')
    parser.add_argument('--output', default='php_analysis.csv',
                        help='Имя выходного CSV-файла')
    parser.add_argument('--exact-match', action='store_true', default=True,
                        help='Сравнивать имена методов/свойств полностью')
    parser.add_argument('--partial-match', action='store_false', dest='exact_match',
                        help='Сравнивать имена методов/свойств частично')
    parser.add_argument('--full-names', action='store_true', default=True,
                        help='Показывать полные имена методов/свойств')
    parser.add_argument('--short-names', action='store_false', dest='full_names',
                        help='Показывать только имена методов/свойств без класса')
    parser.add_argument('--include-lines', action='store_true', default=Config.INCLUDE_LINE_NUMBERS,
                        help='Включать номера строк в отчет')
    parser.add_argument('--skip-composer', action='store_true',
                        help='Пропустить установку PHP-Parser')
    parser.add_argument('--debug', action='store_true',
                        help='Включить отладочный вывод')

    args = parser.parse_args()

    # Обновляем конфигурацию
    Config.INCLUDE_LINE_NUMBERS = args.include_lines
    Config.DESCRIPTIONS_DIR = args.descriptions

    # Проверяем PHP
    if not check_php_environment():
        print("Ошибка: PHP не установлен или не доступен")
        exit(1)

    # Устанавливаем PHP-Parser если нужно
    if not args.skip_composer and not Path('vendor/nikic/php-parser').exists():
        print("Установка PHP-Parser...")
        try:
            subprocess.run(['composer', 'require', 'nikic/php-parser'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при установке PHP-Parser: {e}")
            exit(1)

    # Проверяем существование директории
    directory_path = Path(args.directory)
    if not directory_path.exists():
        print(f"Ошибка: Директория {args.directory} не существует")
        exit(1)

    if args.debug:
        print(f"Анализируемая директория: {directory_path.absolute()}")
        php_files = list(directory_path.rglob('*.php'))
        print(f"Найдено PHP файлов: {len(php_files)}")
        if php_files:
            print("Первые 10 файлов:")
            for file in php_files[:10]:
                print(f"  - {file}")

    # Запускаем анализ
    analyzer = PHPAnalyzer(
        descriptions_dir=args.descriptions,
        exact_match=args.exact_match,
        full_names=args.full_names,
        debug=args.debug  # Добавляем debug флаг
    )
    analyzer.analyze_directory(args.directory, args.output)

if __name__ == "__main__":
    main()