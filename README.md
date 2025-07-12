# JCBA 及び FM++ のストリーミング受信支援スクリプト
元ネタ
https://kemasoft.net/?Stories/2022-04-04

スイッチ

**-p** には *jcba* か *fmplapla* を指定

**-s** には 一覧に記載の放送局名を指定

**-t** には必要であれば受信時間を秒単位で指定

もしくは

**-b** には 予約録音する番組名を設定

実行が始まるとストリームデータが標準出力へ送られるので、適宜再生コマンドやリダイレクトでファイル化する

```shell:みんなのあま咲き放送局 を 1 時間分 JOZZ7AI-FM.oga へ書き出す
rec_wss -p fmplapla -s amasakifm -t 3600 | ffmpeg -i - -c copy JOZZ7AI-FM.oga
rec_wss -p fmplapla -s fmnishitokyo -b "高橋勇太のロッキンジャーニー" | ffmpeg -i - -c copy 高橋勇太のロッキンジャーニー.oga
```
