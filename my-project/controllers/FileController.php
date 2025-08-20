<?php

namespace App\controllers;
use Backbone\helpers\ArrayHelper;
use yii\filters\Cors;
use Yii;

/**
 * Контроллер файлов.
 */

class FileController extends \yii\rest\Controller
{
	/**
	 * Возвращает массив соотношений действий и их обработчиков.
	 * @return array
	 */

	public function actions()
	{
		return [
			'index' => 'KAPONIRAPI\controllers\actions\file\IndexAction'
		];
	}

	/**
	 * Применяет надстройки к контроллеру.
	 * @return array
	 */

	public function behaviors()
	{
		$parent = parent::behaviors();
		return ArrayHelper::merge($parent, [
			'corsFilter' => [
				'class' => Cors::className()
			]
		]);
	}

	/**
	 * Выполняет запуск действия с параметрами.
	 * @param string $id
	 * @param array $params
	 * @return mixed
	 */

	public function runAction($id, $params = array())
	{
		$post = Yii::$app->request->post();
		$data = ArrayHelper::merge($params, $post);
		return parent::runAction($id, $data);
	}

	/**
	 * Возвращает массив доступных вербов.
	 * @return array
	 */

	protected function verbs()
	{
		return [
			'create' => ['post'],
			'index' => ['get', 'head'],
			'remove' => ['delete'],
			'update' => ['put', 'patch']
		];
	}
}