# BlindScale Configの公開

`config.json` は1系、`v2/config.json` は2.0.0以降のアプリ向けです。

編集後はリポジトリのルートで次を実行してください。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_poker_config.py
```

GitHub Pagesは `.github/workflows/pages.yml` で公開します。Pull Requestとmasterへのpushで検証し、検証成功後だけ従来と同じJekyllビルド・Pages公開へ進みます。不正なConfigは公開せず、直前の公開内容が維持されます。PagesのSourceは「GitHub Actions」を使用し、「Deploy from a branch」へ戻さないでください。

検証対象はこの製品の旧Configとv2 Configです。他製品のConfigは対象外です。

- JSONの重複キー、必須キーの欠落、未定義キー、型の誤りを拒否します。
- `allowed_versions` は空でない重複のない配列。空配列はアプリでは全許可になるため公開検証では禁止します。
- 正規表現は `^2\.0\.0$` のように3桁の数値バージョンを完全一致させる形式、または各桁に `[0-9]+` を使う形式のみ許可します。例: `^2\.0\.[0-9]+$`。任意の正規表現・部分一致・複雑な反復は許可しません。
- iOSのストアURLは `https://apps.apple.com/app/id6760666099`、Androidは登録済みの製品URLに限定します。
- `message` は日本語 `ja` と英語 `en` の空でない文字列が必須。他言語の追加は可能です。
- v2は両OSの `study_pro_product_id` と真偽値の `study_pro_purchase_enabled` が必須。製品IDは `poker.tournament.blind.floor.study_pro`・空文字・nullのみ許可します。空文字/nullによる停止と、フラグfalseによる停止は正当な設定として検証を通します。
- スキーマや製品IDを変更する場合は、アプリ側対応と検証スクリプト・テストの更新を同時に行います。

特定のリリースバージョンの許可確認:

```sh
python3 scripts/validate_poker_config.py --file products/poker-blind-tournament/config/v2/config.json --platform ios --version 2.0.0
```

TestFlightのビルド・アップロードはアプリリポジトリの `scripts/release_testflight.py` を使います。対象iOSバージョンが不足していれば既存設定を残して完全一致パターンを追加し、公開URLで許可を確認してからビルドします。Config検証・push・公開確認の失敗時はビルドもアップロードも行いません。
