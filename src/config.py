class Config:
    INCLUDE_LINE_NUMBERS = True
    VARIABLE_PREFIX = '$'
    DESCRIPTIONS_DIR = 'descriptions'
    EXACT_MATCH_FOR_CLASS_CONSTANTS = True
    CHECK_FOR_DUPLICATES = True

    # Константы файлов
    JSON_DESC_CLASSES = 'classes.json'
    JSON_DESC_METHODS = 'methods.json'
    JSON_DESC_PROPS = 'propertys.json'
    JSON_DESC_FUNC = 'functions.json'
    JSON_DESC_VARS = 'variables.json'
    JSON_DESC_CONST = 'constants.json'
    JSON_DESC_CLASS_CONST = 'class_constants.json'

    PHP_PARSER_SCRIPT = 'php_ast_parser.php'