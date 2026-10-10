# 過去のpythonOCC（pyocc）コードを置く場所

**ここが、既存の点探索ロジックをまとめて保管するフォルダです。**

```text
data/
  legacy_pyocc/
    README.md                     # このファイルのみGitHubに保存
    project_01/
      old_find_point.py           # ここに自分で配置
      helper.py
    project_02/
      another_rule.py
```

- Pythonスクリプト（`.py`）をフォルダごとコピーできます。入れ子のサブフォルダも再帰探索します。
- 古い `pyocc` / `pythonocc-core` / `OCC.Core` のコードでも、**import・実行せず**AST（構文木）から関数・メソッド・使用API・名称・docstringを調べます。
- STEPファイルや旧ロジックにある `#118` 等の固定IDを再利用するのではなく、Edge/Face/Wire等の幾何条件を新しいDSL候補として再利用します。
- `.py` はこのフォルダ配下では **`.gitignore` 対象**。このリポジトリは公開なので、機密コードはGitHubにpushせずMac上でローカルに保持してください。
- Python以外のノートブック（`.ipynb`）や実行時生成コードの自動読込は現在未対応です。

## コマンド（リポジトリ直下から）

```bash
python -m pip install -e .

# 配置した昔の関数・幾何操作を自動目録化
cad-rule legacy-index

# 閉ループ、平行Edgeの探索に関係する過去関数を検索
cad-rule legacy-search --query "閉ループ 平行 エッジ"

# 使いたい関数を移植候補として「棚入れ」（レビュー用JSONを生成）
cad-rule legacy-promote --function-id 'project_01/old_find_point.py::find_parallel_edge'
```

索引は `data/legacy_catalog/index.json`、移植提案は `data/legacy_catalog/proposals/` に生成されます。**どちらもGitHubにpushしない設定です。**

**重要：現状できるのは、過去コードを静的に読み取って候補を索引・検索し、再利用のためのレビュー票を作るところまでです。** 過去のpyocc関数を自動実行したり、任意のソースコードをそのまま新しい探索DSLへ安全に自動変換したりはしません。新しい点のルール探索で本当に使用するには、候補を幾何プリミティブへ移植・レビューし、OCCT上のテストを通してDSLへ登録する必要があります（未実装のM1〜M3に含めています）。

Codexには `AGENTS.md` と `docs/LEGACY_REUSE.md` を読ませてください。

## 将来の社内GitHub移行

将来、会社内部のGitHubへ移行した場合は、その社内リポジトリの別の作業コピーでのみ `.gitignore` を変更して、`.py` ソースをGit管理できるようにします。今の個人GitHubは公開のため、この除外設定を解除しません。詳細は [移行手順](../../docs/INTERNAL_MIGRATION.md) を参照してください。
