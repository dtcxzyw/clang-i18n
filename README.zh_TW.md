# clang-i18n

## 簡介

clang-i18n 是一個 Clang 的國際化支援插件，旨在為 Clang 工具鏈的診斷訊息與說明訊息提供本地化支援，以更好地滿足非英文使用者的需求。此專案無需修改 Clang 原始碼並重新建置，僅以插件形式提供即插即用、按需載入的翻譯功能。

## 安裝方式

目前此專案僅支援 Linux x86_64/aarch64/loongarch64/riscv64平台，歡迎移植至其他平台。  
請確保 Clang 為動態連結建置（透過 Ubuntu apt 安裝的 Clang/LLVM 即符合此條件）。

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# 如需指定 Clang/LLVM 版本，請新增搜尋路徑，例如：
# -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DCLANG_DIR=/usr/lib/llvm-20/lib/cmake/clang
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## 使用方式

```bash
export LANG=zh_TW.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

此外還有兩個可選環境變數可控制 clang-i18n 的行為：
- `CLANG_I18N_LANG`：設定語言代碼（例如 `zh_TW`）以覆蓋預設語言設定（Linux 平台預設使用 `$LANG`）。
- `CLANG_I18N_TRANSLATION_DIR`：設定翻譯檔案目錄，Linux 預設值為 `/usr/local/share/clang-i18n/i18n`。

### 在 VSCode 的 clangd 擴展中添加 i18n 支援
建立一個名為 `clangd-i18n` 的檔案，內容如下：

```bash
#!/usr/bin/bash
LANG=zh_TW LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
請確保該檔案具有 +x 權限：

```bash
chmod +x clangd-i18n
```
然後在 VSCode 設定中，將 `clangd.path` 設定為該檔案的路徑：

```json
{
    "clangd.path": <path to clangd-i18n>
}
```

## 貢獻新翻譯

歡迎貢獻新的翻譯或改進現有翻譯，也可提交風格化翻譯。

### 翻譯格式
翻譯檔案以 `.yml` 為擴展名（實質已非 YAML 格式），存放於 `i18n` 目錄下。格式如下：

```yaml
# 英文原文
Hash: 譯文
```

### 基於大型語言模型的翻譯
此專案支援透過 OpenAI API 等大型語言模型服務進行翻譯，配置方式如下：

```bash
# 安裝依賴套件
pip install openai

# 準備提示詞檔案 i18n/zh_CN.prompt

# 準備錯誤修正檔案 i18n/zh_CN.errata，格式如下
# 錯誤關鍵字 錯誤翻譯

export LLM_ENDPOINT=<API位址>
export LLM_MODEL=<模型名稱>
export LLM_TOKEN=<API金鑰，以 sk- 開頭>

python3 translate.py corpus.txt i18n/zh_CN.prompt i18n/zh_CN.errata i18n/zh_CN.yml <批次大小>
```

批次大小不宜過大，建議設定為 20，否則可能導致翻譯順序混亂。

## 開源協定

本專案遵循 [MIT License](LICENSE) 協定開源。
