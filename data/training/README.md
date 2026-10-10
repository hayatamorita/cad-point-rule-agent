# 実際のSTEPと正解点を入れる場所

**このフォルダに次の4ファイルを置きます。**

```text
data/training/
├── README.md               # この説明（GitHubに保存）
├── labels.example.json     # 記入見本（GitHubに保存）
├── type_a.step             # AタイプのSTEP（自分で置く／Gitには含めない）
├── type_b.step             # BタイプのSTEP（自分で置く／Gitには含めない）
├── type_c.step             # CタイプのSTEP（自分で置く／Gitには含めない）
└── labels.json             # 3つの正解点（自分で作る／Gitには含めない）
```

## 設定手順

1. STEPのファイル名を **type_a.step**, **type_b.step**, **type_c.step** に揃えて、このフォルダに置く（`.stp` は `.step` にリネーム）。ファイル内容は編集しない。
2. `labels.example.json` を同じフォルダに **`labels.json`** という名前でコピーする。
3. `labels.json` 内の各 `target_point.xyz_mm` の `[null, null, null]` を、それぞれのSTEPで指定した正解点の **[X, Y, Z] (mm)** に置き換える。
4. 保存後、リポジトリのルートで `cad-rule check-inputs` を実行する（`pip install -e .` でコマンドを導入）。

例：`"xyz_mm": [123.45, 67.89, 10.0]`。**これは単なる書式例であり、正解点ではありません。** 位置はSTEPアセンブリの**ルート座標系 (step_global)** で指定してください。各部品単体のローカル座標系と異なる場合があります。

座標だけで複数頂点に一致する場合に備えて `occurrence_path` を予約しています。現状の `check-inputs` はこの項目の型だけ検査し、該当頂点へのスナップは**まだ実装されていません**。

`vehicle_axes` は今後「前方・左側・上方」を定義するための追加設定です。方向条件を使う段階で明示的な座標軸の定義が必要になります。`null` はまだ指定していない意味です。

## 現在動くこと／未実装のこと

- ✅ `cad-rule check-inputs` で3ファイルの存在・空でないこと・JSON構造・座標と公差をチェック
- ❌ STEPのB-rep読込、正解点が実際にVertexかどうかの判定、3つのSTEPからのルール自動発見（今後のM1/M2で実装）

**機密保護:** このリポジトリは公開リポジトリです。`.gitignore` により、STEPと `labels.json` は標準ではGitへ追加されません。機密データをCodex Cloudや別の外部サービスに渡す場合は、組織の許可も確認してください。`git add -f` は使用しないでください。
