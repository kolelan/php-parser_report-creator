<?php

namespace App\adapters;

/**
 * Класс адаптор для условий
 */
class ConditionAdapter
{
    /**
     * Разделитель для отчёта
     */
    const DELIMETER = ':';
    /**
     * свойство апертуры
     * @var null
     */
    public $a = null;

    /**
     * корректировка данных условий
     * @var string[]
     */
    protected static $correctTable = [
        'eq' => '=',
        'ge' => '>=',
        'gt' => '>',
        'le' => '<=',
        'lt' => '<'
    ];

    public static function adapt($condition) {
        return array_key_exists($condition, static::$correctTable) ? static::$correctTable[$condition] : $condition;
    }
}
