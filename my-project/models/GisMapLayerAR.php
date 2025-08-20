<?php

namespace App\models;

class GisMapLayerAR extends \yii\db\ActiveRecord
{
    public static function tableName() {
        return '{{map.gis_map_layer}}';
    }

    public function getGisMap() {
        return $this
            ->hasOne(GisMapAR::class, ['gis_map_id' => 'gis_map_id']);
    }
}