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
