# clang-i18n

让我们说中文！

## 简介

clang-i18n是一个Clang的国际化支持插件，旨在为Clang工具链的诊断信息和帮助信息提供本地化支持，以更好地满足非英语用户的需求。
该项目不需要修改Clang源代码并重新构建，仅以插件的形式提供即插即用，按需加载的翻译功能。

## 安装方式

目前该项目仅支持Linux x86_64平台，欢迎移植到其他平台。
请确保Clang为动态链接构建（从Ubuntu apt安装的Clang/LLVM满足此要求）。

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# 如需指定Clang/LLVM版本，请添加搜索路径，例如 
# -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DCLANG_DIR=/usr/lib/llvm-20/lib/cmake/clang
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## 使用方式

```bash
export LANG=zh_CN.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

此外还有两个可选的环境变量可以控制clang-i18n的行为：
- `CLANG_I18N_LANG`：设置为语言代码（例如zh_CN）以覆盖默认的语言设置（Linux平台下默认使用`$LANG`）。
- `CLANG_I18N_TRANSLATION_DIR`：设置为翻译文件的目录，Linux下默认值为`${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`，使用 CMake 默认配置构建时即为 `/usr/local/share/clang-i18n/i18n`。

## 贡献新的翻译

欢迎贡献新的翻译/改进现有翻译，也可以提交风格化的翻译（比如来自Rustacean的嘲讽，R门！）。

### 翻译格式
翻译文件以.yml扩展名结尾（其实已经不是yaml格式），放置在i18n目录下。翻译文件的格式如下：

```yaml
# 英文原文
Hash: 译文
```

### 基于大语言模型的翻译
该项目支持使用基于OpenAI API的大模型服务进行翻译，具体配置方式如下：

```bash
# 安装依赖
pip install openai

# 准备提示词文件 i18n/zh_CN.prompt

# 准备错误纠正文件 i18n/zh_CN.errata，格式如下
# 错误关键词 错误翻译

export LLM_ENDPOINT=<API地址>
export LLM_MODEL=<模型名称>
export LLM_TOKEN=<API密钥，以sk-开头>

python3 translate.py corpus.txt i18n/zh_CN.prompt i18n/zh_CN.errata i18n/zh_CN.yml <批处理大小>
```

批处理大小不宜过大，建议设置为20，否则翻译容易乱序。

## 开源协议

本项目遵循 [MIT License](LICENSE) 开源协议。
