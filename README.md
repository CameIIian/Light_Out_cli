# Light_Out_cli

CUI で遊べる **Lights Out** 実装です。  
目的は盤面のライト (`#`) をすべて消灯 (`.`) することです。

## 実行環境

- Python 3.10+
- 標準ライブラリのみ

## 起動方法

```bash
python3 lights_out.py
```

### オプション

```bash
python3 lights_out.py --size 6
python3 lights_out.py --difficulty hard
python3 lights_out.py --seed 1234
```

- `--size N`: 盤面サイズを NxN に設定（N>=3）
- `--difficulty`: `easy(4x4)`, `normal(5x5)`, `hard(7x7)`, `lunatic(9x9)`
- `--seed`: 乱数シードを固定（デバッグ用）

## 操作

- `x y`: 指定マスと上下左右をトグル
- `q`: 終了
- `r`: 現在盤面をリスタート
- `n`: 新規盤面を生成
- `h`: ヘルプ表示
- `s`: 盤面再描画

## テスト

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
