# micropython-sgp30

Sensirion SGP30 (eCO2 / TVOC) 室内空気品質センサーを、MicroPython環境で利用するためのシンプルなドライバです。

## 🛠️ 対応デバイス

* MicroPythonが動作するマイコンボード（例：ESP32, Raspberry Pi Picoなど）
* Sensirion SGP30 室内空気品質センサー

## 📥 インストール方法

1.  このリポジトリの `sgp30.py` ファイルをダウンロードします。
2.  MicroPython開発環境（例: Thonny）を使用し、`sgp30.py`をマイコンボードのルートディレクトリにアップロードします。

## 🚀 使い方 (使用例)

以下のコードを `main.py` などとして実行することで、eCO2 (等価二酸化炭素) と TVOC (総揮発性有機化合物) の測定を開始できます。

測定開始後、センサーの調整のため、最初の15秒間は固定値（eCO2: 400ppm, TVOC: 0ppb）が返されます。

```python
from machine import I2C, Pin
import time
from sgp30 import SGP30

# I2Cのセットアップ例 (お使いのボードに合わせてピン番号を変更してください)
# 例: Seeed Studio Xiao ESP32C6 の場合
# i2c = I2C(0, scl=Pin(23), sda=Pin(22)) 
# 例: Picoの場合
# i2c = I2C(0, scl=Pin(1), sda=Pin(0)) 

# ここにI2Cオブジェクトの初期化コードを記述してください
i2c = I2C(...) 

# SGP30ドライバの初期化
sgp = SGP30(i2c)
sgp.init_air_quality()

print("SGP30センサー初期化完了。15秒間、センサー調整中...")

# センサーが安定するまで待機
time.sleep(15) 
print("測定開始")

while True:
    # IAQ測定コマンドを送信し、結果を取得
    reading = sgp.measure_iaq()
    
    # 結果の表示
    print("-" * 20)
    print(f"eCO2 (等価二酸化炭素): {reading.equivalent_co2} ppm")
    print(f"TVOC (総揮発性有機化合物): {reading.total_voc} ppb")
    
    # SGP30の仕様により、測定間隔は最低1秒必要
    time.sleep(1)
```

## 📝 主なメソッド

* **`sgp.init_air_quality()`** : IAQ（室内空気品質）測定を開始するための**初期化**を行います。
* **`sgp.measure_iaq()`** : eCO2とTVOCの最新の測定値を取得します。
* **`sgp.get_iaq_baseline()`** : センサーの**ベースライン値**を読み出します。（精度維持のため推奨）
* **`sgp.set_iaq_baseline(TVOC, eCO2)`** : 以前保存したベースライン値をセンサーに書き込みます。
* **`sgp.set_absolute_humidity(grams_per_m3)`** : 外部の温湿度センサーで得た**絶対湿度**を設定し、測定精度を向上させます。

## 🔗 参考資料

[Sensirion SGP30 製品ページ/データシート](https://sensirion.com/media/documents/984E0DD5/61644B8B/Sensirion_Gas_Sensors_Datasheet_SGP30.pdf)