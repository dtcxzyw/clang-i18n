# clang-i18n  
Clang оболочка с поддержкой локализации  

## Введение  

clang-i18n — это плагин Clang для поддержки локализации, который旨在 предоставлять локализацию диагностических сообщений и справочной информации Clang, чтобы лучше удовлетворять потребности носителей языков, отличных от английского.  
Этот проект не требует модификации исходного кода Clang и пересборки, а вместо этого предлагает готовые к использованию и динамические переводы в виде плагина.  

## Установка  

В настоящее время проект поддерживает платформы Linux x86_64/aarch64/loongarch64/riscv64. Порты на другие платформы приветствуются.  
Убедитесь, что Clang собран с динамической связкой (пакеты, установленные через Ubuntu apt, соответствуют этому требованию).  
Если CMake не находит установку Clang/LLVM, выполните `sudo apt install llvm-dev libclang-dev` для установки файлов разработчика.  

```bash  
git clone https://github.com/dtcxzyw/clang-i18n.git  
cd clang-i18n  
mkdir -p build && cd build  
# Если нужно указать версию Clang/LLVM, добавьте пути поиска в CMake.  
# Пример: -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DCLANG_DIR=/usr/lib/llvm-20/lib/cmake/clang  
cmake .. -DCMAKE_BUILD_TYPE=Release  
cmake --build . -j  
sudo cmake --install .  
```  

## Использование  

```bash  
export LANG=ru_RU.UTF-8  
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"  
clang-i18n --help  
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -  
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"  
opt-i18n --help  
```  

Кроме того, есть два опциональных окружения, которые управляют поведением clang-i18n:  
- `CLANG_I18N_LANG`: Устанавливает код языка (например, ru_RU) для переопределения настроек по умолчанию (по умолчанию — `$LANG` в Linux).  
- `CLANG_I18N_TRANSLATION_DIR`: Указывает каталог с переводами. По умолчанию в Linux: `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, то есть `/usr/local/share/clang-i18n/i18n` при сборке с настройками по умолчанию CMake.  

### Добавление поддержки локализации для clangd в VSCode  

Создайте файл `clangd-i18n` со следующим содержимым:  
```bash  
#!/usr/bin/bash  

LANG=ru_RU LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@  
```  
Убедитесь, что файл имеет права на выполнение:  
```bash  
chmod +x clangd-i18n  
```  
Затем в настройках VSCode установите `clangd.path` как путь к этому файлу:  
```json  
{  
    "clangd.path": <путь к clangd-i18n>  
}  
```  

## Вклад в переводы  

Приветствуются новые переводы или улучшения существующих. Также принимаются стилизованные переводы.  

### Формат файлов перевода  

Файлы перевода имеют расширение .yml (на самом деле не в формате YAML) и размещаются в директории i18n.  

Формат файла перевода:  
```yaml  
# Исходный английский текст  
Хэш: Перевод  
```  

### Машинный перевод с помощью LLM  

Проект поддерживает использование моделей с API совместимыми с OpenAI. Конфигурация:  
```bash  
# Установка зависимостей  
pip install openai  

# Подготовка файла подсказок i18n/ru_RU.prompt  

# Подготовка файла исправлений i18n/ru_RU.errata  
# Формат:  
# <Английский термин> <Неверный перевод>  

export LLM_ENDPOINT=<LLM API Endpoint>  
export LLM_MODEL=<LLM Model Name>  
export LLM_TOKEN=<LLM API Key>  

python3 translate.py corpus.txt i18n/ru_RU.prompt i18n/ru_RU.errata i18n/ru_RU.yml <Batch Size>  
```  

Рекомендуется использовать размер пакета 20, иначе порядок переводов может быть нарушен.  

## Лицензия  

Проект распространяется под лицензией [MIT](LICENSE).
