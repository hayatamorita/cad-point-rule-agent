# 正解STEPとSTEPエンティティ番号の指定

3つのSTEPファイルをこのフォルダに置き、各ファイルの正解を **#エンティティ番号** で指定します。点のXYZ座標を手で書く必要はありません。

```text
data/training/
├── README.md
├── labels.example.json   # GitHubに保存済みのテンプレート
├── type_a.step           # 手元で追加するSTEP（gitignore対象）
├── type_b.step
├── type_c.step
└── labels.json           # テンプレートをコピー・編集（gitignore対象）
```

## 使い方

1. 使用許可のあるSTEPのファイル名を `type_a.step`, `type_b.step`, `type_c.step` に揃えて、このフォルダへ配置します。
2. `labels.example.json` を同じ場所の `labels.json` にコピーします。
3. 各 `target_point.entity_id` に、**そのSTEPファイルの実際のエンティティID**を入れてください。例：`118` または `"#118"`（JSONでは文字列の `"#118"` も受理）。
4. リポジトリルートで `python -m pip install -e .` の後に `cad-rule check-inputs` を実行します。

JSONの例:

```json
{
  "schema_version": 2,
  "training_cases": [
    { "variant": "a", "step_file": "type_a.step", "target_point": { "entity_id": 118 } },
    { "variant": "b", "step_file": "type_b.step", "target_point": { "entity_id": 245 } },
    { "variant": "c", "step_file": "type_c.step", "target_point": { "entity_id": 361 } }
  ]
}
```

これは架空の番号です。実際のSTEP内の番号と一致させてください。

## CARTESIAN_POINT と VERTEX_POINT の違い

STEPは一般に、以下のように**幾何座標と位相的頂点を別エンティティとして表現**します。

```step
#118 = CARTESIAN_POINT('',(120.0,35.0,20.0));
#119 = VERTEX_POINT('',#118);
```

上の例では `entity_id: 118` と `entity_id: 119` のどちらでもラベルを指定できます。

- `CARTESIAN_POINT` : 座標を保持する点です。**CADの頂点（Vertex）として使われているとは限りません**。ゼロ個または複数の `VERTEX_POINT` から参照されることがあります。
- `VERTEX_POINT` : 位相的頂点で、参照先の幾何点を持ちます。**実STEPのVertexを指定したいならこちらがより明確**です。

`check-inputs` はSTEPのDATAセクション内に指定IDが実在するか、上記2種類の点かを検査し、`VERTEX_POINT` なら参照する `CARTESIAN_POINT` も追跡します。**Open CASCADEのTopoDS_Vertexへの対応・assembly occurrenceの区別・ルール自動合成は未実装**です。将来、複数の実体Vertex/Occurrenceに対応する場合は一意性チェックを追加します。

## 注意点

STEP内の `#118` は**ファイルごとに固有の番号**です。別タイプのSTEPでは番号が変わります。この番号は教師用ラベルにのみ使い、未知モデル向けの共通選択ルールには使いません。

STEPと `labels.json` はGitにコミットされない設定です。公開GitHubやクラウドへの生CADアップロードは所有者/組織の許可を確認してください。
