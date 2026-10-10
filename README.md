# CAD Point Rule Agent

3種類の同一系統の車両部品（STEPモデル）と、各モデル上で人間が指定した正解点から、**共通の幾何・位相的Point選択ルール**を自動発見するプロジェクトです。

> **現在の実装範囲:** 合成特徴グラフで動く最小ルール合成CLI・テスト、およびSTEPのラベル用エンティティ番号検査。**Open CASCADEによるB-rep解析・実STEPの共通ルール合成・GUIクリック指定は未実装です。** 開発ロードマップに沿って実装してください。

## 目的

同一系列の車両部品がタイプ別に寸法・配置・トポロジを変えていても、各STEPで人間が指定した一つの対応点を、**同じ決定論的な探索プログラム**で選べるようにする。

典型的な選択手順: 対象部品 → 前方の面 → 内周閉ループ → 参照Edgeと平行なEdge → 左側端点。

禁止事項:
- モデル名・タイプ名・ファイル名ごとに分岐する
- 正解点の生座標をルールに記憶させる
- 変化しうるEdge/Vertex番号をモデル間の意味的IDとして使う
- 複数点に一致したとき最初の一点を黙って選ぶ
- 学習3例の成功を未知STEPにおける一般化の証明と呼ぶ

## 正解STEPとPoint指定JSONを置く場所

[`data/training/`](data/training/README.md) に `type_a.step`, `type_b.step`, `type_c.step` を置き、[`data/training/labels.example.json`](data/training/labels.example.json) を **`data/training/labels.json`** としてコピーして3つのSTEPエンティティ番号（例: `118` = `#118`）を記入してください。入力の形式を確認するには:

```bash
cad-rule check-inputs
```

`check-inputs` はSTEPのDATAセクションを読み、指定された `#番号` が `CARTESIAN_POINT` または `VERTEX_POINT` として存在することを確認します。ただし、**OCCTのB-rep上の頂点との対応付け・ルール合成は未実装**です。入力した実STEPはGitHubへpushせずローカルに置いてください（`labels.json` とSTEPはGitの追跡対象外）。

## 過去のpyoccロジックを再利用する（新機能）

過去のpyocc Pythonコードは [`data/legacy_pyocc/`](data/legacy_pyocc/README.md) にプロジェクト別に置いてください（機密保護のため **Gitには含めない** 設定です）。置いた `.py` から関数・メソッド・利用API・幾何キーワードを **実行せずに静的解析** して再利用候補を探せます。

```bash
cad-rule legacy-index
cad-rule legacy-search --query "前方 閉ループ 平行 エッジ"
cad-rule legacy-promote --function-id 'old_project/find_point.py::find_parallel_edge'
```

棚入れした候補は `data/legacy_catalog/` に索引・レビュー票として保存します。**実行可能な共通幾何ロジックへの自動変換・STEPを用いた自動採用はまだ未実装**です。移植・テスト後の幾何プリミティブは `src/cad_rule_agent/geometry_primitives/` で管理します。

詳しくは [旧pyoccロジックの再利用設計](docs/LEGACY_REUSE.md) を参照してください。

## 実行できる合成データのMVP

Python 3.11以上、実行時外部依存なし。

```bash
python -m pip install -e .
cad-rule synthesize --dataset examples/synthetic_three_variants.json --output results/rule.json
cad-rule apply --model examples/synthetic_unseen_variant.json --rule results/rule.json
python -m unittest discover -s tests -v
```

ネット接続なしの場合:
```bash
PYTHONPATH=src python -m cad_rule_agent synthesize --dataset examples/synthetic_three_variants.json --output results/rule.json
PYTHONPATH=src python -m cad_rule_agent apply --model examples/synthetic_unseen_variant.json --rule results/rule.json
PYTHONPATH=src python -m unittest discover -s tests -v
```

これらは**予め計算されたBoolean特徴からのルール合成**を実証するものであり、STEPを直接解析する実装ではありません。

## 個人GitHubから社内GitHubへの移行方針

現在のGitHubは**公開された汎用エンジン開発用**です。過去のpyoccコードはローカルでのみ扱い、社内GitHubへ移行した後、その**社内リポジトリだけ**でGit管理を有効にします。

具体的な移行方法、社内版 `.gitignore` の変更、Codexへの指示は [社内GitHub移行手順](docs/INTERNAL_MIGRATION.md) を参照してください。既存の公開リポジトリへ過去コードをpushする設定変更は行いません。

## Chen Yang方式を参考にした探索ハーネス

[harness/README.md](harness/README.md) に「仮説生成 → 検証 → 失敗記録 → 再試行」の実行環境を追加しました。

~~~bash
bash harness/run.sh demo --max-rounds 8
bash harness/verify.sh runs/harness/demo/candidates/round_04.json
~~~

自律反復の合成データ実証は動作します。Codex CLIをインストール・認証した信頼できるローカル環境では、明示的なコマンド `bash harness/run.sh codex --max-rounds 4` によるAI提案ループも利用できます。検証と記録はPythonが担当します。

**重要:** まだ実STEPの幾何ルールを自動発見する実行エンジンではありません。実STEPの独立検証器の実装は次のマイルストーンです。

## 次回の実STEP開発に向けたTODO

[**未実装箇所・実装順序をまとめた短い作業メモ**](docs/NEXT_STEPS.md) を参照してください。社内GitHub移行後にM1から着手します。

## Agentic coding への引き継ぎ

- [AGENTS.md](AGENTS.md) — 開発エージェントの厳守事項
- [PRD](docs/PRD.md) — 全要件・入出力・非目標
- [Architecture](docs/ARCHITECTURE.md) — 幾何グラフ、DSL、制約最適化、検証
- [Acceptance tests](docs/ACCEPTANCE_TESTS.md) — 品質基準・負例
- [Roadmap](docs/ROADMAP.md) — M0〜M5開発手順
- [Skill](.agents/skills/cad-rule-discovery/SKILL.md) — ルール発見の標準ワークフロー

最初のCodex指示:

> Read AGENTS.md and docs/*.md. Run the synthetic tests. Implement M1: OCCT-backed STEP/XCAF ingestion, assembly instance transforms, B-rep topology/adjacency extraction and selected Vertex labeling. Create public synthetic STEP integration fixtures. Do not claim actual STEP support until import → label → rule validation is demonstrated.

**機密保護:** 実車両部品STEPは権限確認なしにGitHub/クラウドAIにアップロードしないこと。リポジトリは公開設定です。STEPやラベル原データは.gitignoreの除外対象です。ライセンスは未設定（所有者判断）。

着想: [automatic theorem proving の探索・検証ループ](https://chenyang.co/blog/automatic-theorem-proving.html)をCADの **inductive program synthesis** に応用。ただしLeanの数学的証明ではなく、CADテストで経験的に評価します。
