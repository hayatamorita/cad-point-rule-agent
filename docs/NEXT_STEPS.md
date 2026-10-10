# 次回作業：実STEP対応の最小TODO

**目標**：3つのSTEPと各正解点の `#エンティティ番号` を入力し、過去のpyocc処理も参考にして、**同じ幾何・位相ルール**で3点を特定・検証できるようにする。

## 準備（社内の許可済み環境）

- [ ] [社内GitHub移行手順](INTERNAL_MIGRATION.md) に従い、社内リポジトリを別の作業コピーに用意する。
- [ ] `data/training/` に `type_a.step`, `type_b.step`, `type_c.step`, `labels.json` を置く。JSONは [見本](../data/training/labels.example.json) に従い `entity_id: 118` のように正解点を指定する。
- [ ] 過去の `.py` を `data/legacy_pyocc/` に配置する（社内版のみGit管理可）。

## 未実装：この順に開発する

1. **STEP読込（M1）**：OCCT / pythonocc（XCAF対応）で3つのSTEPを読み、Assembly / Face / Wire / Edge / Vertex と配置変換を取得する。
2. **正解点対応付け（M1）**：JSONの `#118` 等をSTEP内部の `CARTESIAN_POINT` / `VERTEX_POINT` から実際のOCCT幾何要素へ対応付ける。0件・複数件はエラー。
3. **幾何ルール化（M2）**：閉ループ、平行Edge、Face隣接、前方・左右、端点などの特徴を計算し、実STEPから使える共通ルールDSLにする。
4. **過去ロジック再利用（M2–M3）**：`cad-rule legacy-index` → `legacy-search` → `legacy-promote` で候補を探し、必要な関数だけテスト付きで `src/cad_rule_agent/geometry_primitives/` へ移植・DSL登録する（現状は目録・候補作成まで）。
5. **自律探索を実STEPへ接続（M3）**：`harness/run.sh` の仮説生成→実行→失敗分析→再生成を実STEPで回し、**独立したSTEP検証器**で3モデルすべての正解点を一意に選べるか判定する。成功ルールをJSON/Pythonで保存し、可能なら未学習の4番目のSTEPで評価する。

## 開始時の確認コマンド

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
cad-rule check-inputs
cad-rule legacy-index
bash harness/run.sh demo
```

**注意**：最後の `demo` は合成データの動作確認であり、**実STEPのPoint探索はまだできない**。実STEPを使うコマンドは、上記1〜5を実装・検証してから追加する。

## 完成条件

- 3つのSTEPで**同一ルール**を使い、各モデルの正解点を**1点だけ**特定できる。
- STEPのエンティティ番号・絶対座標・ファイル名で場合分けしない（番号は教師ラベルだけに使用）。
- 失敗理由、候補数、実行ログ、保存されたルールを確認できる。
- 実STEP対応の自動テストが通る。3例の一致だけで未知形状への一般化を保証したことにはしない。

**Codexへの最初の指示**：`AGENTS.md` とこのファイルを読んで、まずM1（STEP読込＋正解エンティティのOCCT頂点への対応付け）を、社内で利用可能なSTEPと過去pyoccコードでテストしながら実装してください。検証器の未完成部分を成功扱いしないこと。
