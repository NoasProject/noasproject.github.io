# App Store screenshots

App Store掲載用のiPhone縦向きスクリーンショット。日本語と英語を各5枚用意する。

## 掲載順

1. 機能一覧（通常トーナメント、勉強会モード、EQ計算機）
2. 通常トーナメントのブラインド・スタック管理
3. 勉強会モードのテーブルと共有状態
4. 勉強会モードのアクション記録
5. EQ計算機のハンド対レンジ計算結果

撮影用プレイヤー名には `Alex`、`Ben`、`Chris`、`Daniel`、`Emma`、`Grace`、`Liam`、`Olivia`、`Noah` を使用する。通常トーナメントでは赤・緑・青・紫・ティールのプレイヤーラベルを順に設定する。

完成画像は `ja/` と `en-US/`、アプリから取得した元画像は `source/` に保存する。完成画像は各1290×2796pxのPNG（アルファなし）で、App Store Connectの6.9インチ表示向け仕様に合わせている。

再生成:

```sh
swift scripts/generate_app_store_screenshots.swift
```
