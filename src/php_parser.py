import json
import subprocess
from pathlib import Path
from typing import Dict, List
from .config import Config


class PHPParser:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self._create_php_parser_script()

    def _create_php_parser_script(self):
        """Создает PHP-скрипт для анализа AST"""
        php_script = r"""<?php
require 'vendor/autoload.php';

use PhpParser\Error;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node;
use PhpParser\ParserFactory;

class ElementVisitor extends NodeVisitorAbstract {
    public $elements = [];
    private $currentClass = null;
    private $inFunction = false;

    public function enterNode(Node $node) {
        if ($node instanceof Node\Stmt\Class_) {
            $this->currentClass = $node->name->toString();
            $this->elements[] = [
                'type' => 'class',
                'name' => $this->currentClass,
                'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                'startLine' => $node->getStartLine()
            ];
        }
        elseif ($node instanceof Node\Stmt\ClassMethod && $this->currentClass) {
            $this->elements[] = [
                'type' => 'method',
                'name' => $this->currentClass . '::' . $node->name->toString(),
                'short_name' => $node->name->toString(),
                'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                'startLine' => $node->getStartLine()
            ];
            $this->inFunction = true;
        }
        elseif ($node instanceof Node\Stmt\Property && $this->currentClass) {
            foreach ($node->props as $prop) {
                $this->elements[] = [
                    'type' => 'property',
                    'name' => $this->currentClass . '::$' . $prop->name->toString(),
                    'short_name' => $prop->name->toString(),
                    'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                    'startLine' => $node->getStartLine()
                ];
            }
        }
        elseif ($node instanceof Node\Stmt\ClassConst && $this->currentClass) {
            foreach ($node->consts as $const) {
                $this->elements[] = [
                    'type' => 'class_constant',
                    'name' => $this->currentClass . '::' . $const->name->toString(),
                    'short_name' => $const->name->toString(),
                    'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                    'startLine' => $node->getStartLine()
                ];
            }
        }
        elseif ($node instanceof Node\Stmt\Function_ && !$this->currentClass && !$this->inFunction) {
            $this->elements[] = [
                'type' => 'function',
                'name' => $node->name->toString(),
                'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                'startLine' => $node->getStartLine()
            ];
            $this->inFunction = true;
        }
        elseif ($node instanceof Node\Expr\Assign && $node->var instanceof Node\Expr\Variable && !$this->currentClass && !$this->inFunction) {
            $varName = is_string($node->var->name) ? $node->var->name : '';
            if ($varName) {
                $this->elements[] = [
                    'type' => 'variable',
                    'name' => '$' . $varName,
                    'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                    'startLine' => $node->getStartLine()
                ];
            }
        }
        elseif ($node instanceof Node\Stmt\Const_ && !$this->currentClass && !$this->inFunction) {
            foreach ($node->consts as $const) {
                $this->elements[] = [
                    'type' => 'constant',
                    'name' => $const->name->toString(),
                    'desc' => $node->getDocComment() ? $this->cleanComment($node->getDocComment()->getText()) : '',
                    'startLine' => $node->getStartLine()
                ];
            }
        }
    }

    public function leaveNode(Node $node) {
        if ($node instanceof Node\Stmt\Class_) {
            $this->currentClass = null;
        }
        elseif ($node instanceof Node\Stmt\ClassMethod || $node instanceof Node\Stmt\Function_) {
            $this->inFunction = false;
        }
    }

    private function cleanComment(string $comment): string {
        // Удаляем открывающие и закрывающие теги комментариев PHP
        $comment = preg_replace('/^\/\*\*|\*\/$/', '', $comment);
        
        $lines = explode("\n", $comment);
        $result = [];
        
        foreach ($lines as $line) {
            $line = trim($line);
            
            // Удаляем начальные звездочки и пробелы
            if (str_starts_with($line, '*')) {
                $line = substr($line, 1);
            }
            
            $line = trim($line);
            
            // Пропускаем пустые строки и аннотации
            if (!$line || str_starts_with($line, '@')) {
                continue;
            }
            
            $result[] = $line;
        }
        
        $cleanText = implode(' ', $result);
        
        // Проверяем, содержит ли текст латинские символы
        if (preg_match('/[a-zA-Z]/', $cleanText)) {
            // Ищем первую точку в тексте
            $firstDotPos = strpos($cleanText, '.');
            
            if ($firstDotPos !== false) {
                // Обрезаем до первой точки (включая саму точку)
                $cleanText = substr($cleanText, 0, $firstDotPos + 1);
            } else {
                // Если точки нет, ограничиваем 10 словами
                $words = preg_split('/\s+/', $cleanText);
                if (count($words) > 10) {
                    $cleanText = implode(' ', array_slice($words, 0, 10)) . '...';
                }
            }
        }
        
        return trim($cleanText);
    }
}

$code = file_get_contents($argv[1]);
$parser = (new ParserFactory())->createForHostVersion();
$traverser = new NodeTraverser();
$visitor = new ElementVisitor();
$traverser->addVisitor($visitor);

try {
    $stmts = $parser->parse($code);
    if ($stmts !== null) {
        $traverser->traverse($stmts);
    }
    echo json_encode($visitor->elements);
} catch (Error $error) {
    file_put_contents('php://stderr', "Parse error in {$argv[1]}: {$error->getMessage()}\n");
    echo '[]';
}
"""
        with open(Config.PHP_PARSER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(php_script)

    def parse_file(self, file_path: Path) -> List[Dict]:
        """Парсит PHP-файл и возвращает элементы"""
        try:
            if self.debug:
                print(f"  Парсинг файла: {file_path}")

            result = subprocess.run(
                ['php', Config.PHP_PARSER_SCRIPT, str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stderr:
                print(f"  Предупреждение: {result.stderr.strip()}")

            elements = json.loads(result.stdout) if result.stdout else []

            if self.debug:
                print(f"  Найдено элементов: {len(elements)}")
                for element in elements:
                    print(f"    - {element['type']}: {element['name']}")

            return elements

        except subprocess.CalledProcessError as e:
            print(f"  Ошибка парсинга: {e.stderr}")
            return []
        except json.JSONDecodeError as e:
            print(f"  Ошибка декодирования JSON: {e}")
            print(f"  Raw output: {result.stdout[:200]}...")
            return []