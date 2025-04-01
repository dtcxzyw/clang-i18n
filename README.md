# clang-i18n
Clang wrapper with i18n support

[![Build](https://github.com/dtcxzyw/clang-i18n/actions/workflows/build.yml/badge.svg)](https://github.com/dtcxzyw/clang-i18n/actions/workflows/build.yml)

[简体中文](docs/README.zh_CN.md)
[繁體中文](docs/README.zh_TW.md)
[日本語](docs/README.jp_JP.md)
[Français](docs/README.fr_FR.md)
[Español](docs/README.es_ES.md)
[한국어](docs/README.ko_KR.md)
[Русский](docs/README.ru_RU.md)
[Português](docs/README.pt_BR.md)
[Deutsch](docs/README.de_DE.md)
[Türkçe](docs/README.tr_TR.md)

## Introduction

clang-i18n is a Clang i18n support plugin that aims to provide localization support for the diagnostic and help information of the Clang toolchain, in order to better meet the needs of non-English users.
This project does not require modifying the Clang source code and rebuilding it, but provides plug-and-play and on-demand translation functions in the form of a plugin.

## Installation

Currently, this project supports Linux x86_64/aarch64/loongarch64/riscv64 platforms, and contributions to port it to other platforms are welcome.
Please ensure that Clang is built with dynamic linking (Clang/LLVM installed from Ubuntu apt meets this requirement).
If cmake cannot find the Clang/LLVM installation, please run `sudo apt install llvm-dev libclang-dev` to install the development files.

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# If you need to specify the Clang/LLVM version, please add the search path to CMake.
# For example, -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DCLANG_DIR=/usr/lib/llvm-20/lib/cmake/clang
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## Usage

```bash
export LANG=zh_CN.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

In addition, there are two optional environment variables that can control the behavior of clang-i18n:
- `CLANG_I18N_LANG`: Set to the language code (e.g., zh_CN) to override the default language setting (default is `$LANG` on Linux).
- `CLANG_I18N_TRANSLATION_DIR`: Set to the directory of translation files, default value on Linux is `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, i.e. `/usr/local/share/clang-i18n/i18n` when building with the default CMake configuration.

### Add i18n support to the clangd extension on VSCode

Create a file named `clangd-i18n` with the following content:
```bash
#!/usr/bin/bash

LANG=zh_CN LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
Please ensure that this file has +x permission:
```bash
chmod +x clangd-i18n
```
Then, in the VSCode settings, set `clangd.path` to the path of this file.
```
{
    "clangd.path": <path to clangd-i18n>
}
```

## Contributing New Translations

Contributions of new translations/improvements to existing translations are welcome, and you can also submit stylized translations.

### Translation File Format

Translation files end with the .yml extension (actually not in YAML format) and are placed under the i18n directory.

The format of the translation file is as follows:

```yaml
# English original text
Hash: Translation
```

### Machine Translation with Large Language Models

This project supports using LLM with OpenAI-compatible APIs for translation, and the specific configuration method is as follows:

```bash
# Install dependencies
pip install openai

# Prepare the prompt file i18n/zh_CN.prompt

# Prepare the erratum file i18n/zh_CN.errata
# The format is as follows
# <English Term> <Wrong Translation>

export LLM_ENDPOINT=<LLM API Endpoint>
export LLM_MODEL=<LLM Model Name>
export LLM_TOKEN=<LLM API Key>

python3 translate.py corpus.txt i18n/zh_CN.prompt i18n/zh_CN.errata i18n/zh_CN.yml <Batch Size>
```

Batch size should not be too large, and it is recommended to set it to 20, otherwise the translation may be wrongly ordered.

## License

This project is licensed under the [MIT License](LICENSE).
