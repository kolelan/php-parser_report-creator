<?php

set_time_limit(0);

// Переменные окружения Kerberos
if (isset($_SERVER['KRB5CCNAME'])) {
    @putenv("KRB5CCNAME={$_SERVER['KRB5CCNAME']}");
} elseif (isset($_SERVER['REDIRECT_KRB5CCNAME'])) {
    @putenv("KRB5CCNAME={$_SERVER['REDIRECT_KRB5CCNAME']}");
}

use Backbone\components\Env;
defined('YII_DEBUG') or define('YII_DEBUG', true);
defined('YII_ENV') or define('YII_ENV', 'dev');
require_once sprintf('%s/../../vendor/autoload.php', __DIR__);
require_once sprintf('%s/../../vendor/yiisoft/yii2-p516/Yii.php', __DIR__);

$defaults = require_once sprintf('%s/../config/web.php', __DIR__);
$config = Env::instance()->readIniConfig($defaults);
$application = new yii\web\Application($config);
$application->run();