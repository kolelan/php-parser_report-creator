import csv
from pathlib import Path
from typing import List, Dict
from .config import Config

class CSVWriter:
    def __init__(self):
        self.global_row_number = 1

    def write_to_csv(self, items: List[Dict], output_path: str | Path):
        """Записывает данные в CSV файл"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            headers = self._get_headers()
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for item in sorted(items, key=lambda x: (x['relative_path'], x.get('line_number', 0))):
                row = self._prepare_row(item)
                writer.writerow(row)
                self.global_row_number += 1

    def _get_headers(self) -> List[str]:
        """Возвращает заголовки CSV"""
        headers = ['№', 'Относительный путь', '№ в классе', 'Наименование', 'Тип', 'Описание']
        if Config.INCLUDE_LINE_NUMBERS:
            headers.append('Строка')
        return headers

    def _prepare_row(self, item: Dict) -> List:
        """Подготавливает строку для CSV"""
        row = [
            self.global_row_number,
            item['relative_path'],
            item['item_number'],
            item['name'],
            item['type_ru'],
            item['description']
        ]
        if Config.INCLUDE_LINE_NUMBERS:
            row.append(item.get('line_number', ''))
        return row