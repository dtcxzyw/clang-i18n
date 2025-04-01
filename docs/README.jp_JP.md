# clang-i18n

## 簡単な説明

clang-i18n は、Clang の国際化をサポートするプラグインです。Clang ツールチェーンの診断メッセージとヘルプ情報をローカライズし、非英語圏のユーザーのニーズを満たすことを目的としています。このプロジェクトでは Clang のソースコードを修正・再ビルドする必要がなく、プラグイン形式で即座に利用可能なオンデマンド翻訳機能を提供します。

## インストール方法

現在は Linux x86_64/aarch64/loongarch64/riscv64 プラットフォームのみ対応しています。他のプラットフォームへの移植を歓迎します。  
Clang は動的リンク構築されている必要があります（Ubuntu の apt 経由でインストールした Clang/LLVM は条件を満たします）。
もし cmake が Clang/LLVM のインストールを見つけられない場合は、`sudo apt install llvm-dev libclang-dev` を実行して開発ファイルをインストールしてください。

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# 特定の Clang/LLVM バージョンを指定する場合はパスを追加します。例：
# -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DCLANG_DIR=/usr/lib/llvm-20/lib/cmake/clang
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## 使用方法

```bash
export LANG=ja_JP.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

以下の 2 つのオプション環境変数で clang-i18n の動作を制御できます：
- `CLANG_I18N_LANG`：デフォルトの言語設定（Linux では `$LANG` が使用されます）を上書きする言語コード（例: `ja_JP`）を指定します。
- `CLANG_I18N_TRANSLATION_DIR`：翻訳ファイルのディレクトリを指定（Linux でのデフォルトは `/usr/local/share/clang-i18n/i18n`）。

### VSCode の clangd 拡張機能に i18n サポートを追加
`clangd-i18n` という名前のファイルを作成し、以下の内容を記述します：

```bash
#!/usr/bin/bash
LANG=ja_JP LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
このファイルに +x 権限を付与してください：

```bash
chmod +x clangd-i18n
```
VSCode の設定で `clangd.path` をこのファイルのパスに設定します：

```json
{
    "clangd.path": <clangd-i18n のパス>
}
```

## 翻訳の貢献

新しい翻訳の追加や既存翻訳の改善、ユーモアを交えた翻訳の投稿を歓迎します。

### 翻訳フォーマット
翻訳ファイルは `.yml` 拡張子を使用し（実際は YAML 形式とは異なります）、`i18n` ディレクトリに配置します。フォーマットは以下の通りです：

```yaml
# 英文原文
Hash: 訳文
```

### 大規模言語モデルによる翻訳
OpenAI API を利用した大規模言語モデルによる翻訳に対応しています。設定方法は以下の通り：

```bash
# 依存ライブラリのインストール
pip install openai

# プロンプトファイル i18n/ja_JP.prompt を準備

# 誤訳修正ファイル i18n/ja_JP.errata を準備（フォーマット例）
# キーワード 不適切な翻訳

export LLM_ENDPOINT=<API エンドポイント>
export LLM_MODEL=<モデル名>
export LLM_TOKEN=<API キー（sk- で始まる）>

python3 translate.py corpus.txt i18n/ja_JP.prompt i18n/ja_JP.errata i18n/ja_JP.yml <バッチサイズ>
```

バッチサイズは 20 程度が適切で、大きすぎると翻訳順序が乱れる可能性があります。

## 開源ライセンス

本プロジェクトは [MIT License](LICENSE) に準拠しています。
