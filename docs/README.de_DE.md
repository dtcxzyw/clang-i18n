# clang-i18n
Clang-Umgebung mit i18n-Unterstützung

## Einführung

Clang-i18n ist ein Plugin zur lokalisierungsoptimierten Unterstützung für die Clang-Werkzeugkette. Es ermöglicht die Lokalisierung von Diagnose- und Hilfemeldungen, um die Bedürfnisse von Nicht-Englisch-Sprechenden besser zu erfüllen. Dieses Projekt erfordert keine Änderungen am Clang-Quellcode oder Neukompilierung, sondern bietet Plug-and-Play-Übersetzungen in Form eines Plugins.

## Installation

Aktuell werden Linux-Plattformen (x86_64/aarch64/loongarch64/riscv64) unterstützt. Mitwirkungen zur Portierung auf andere Plattformen sind erwünscht. Stellen Sie sicher, dass Clang mit dynamischem Linking kompiliert wurde (Clang/LLVM via Ubuntu apt entspricht dieser Anforderung). Falls CMake die Clang/LLVM-Installation nicht findet, führen Sie `sudo apt install llvm-dev libclang-dev` aus.

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# Optional: Spezifizieren Sie Suchpfade für LLVM/Clang-Versionen mit -DLLVM_DIR und -DClang_DIR
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## Nutzung

```bash
export LANG=de_DE.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

Zwei optionale Umgebungsvariablen steuern das Verhalten:
- `CLANG_I18N_LANG`: Legt die Sprachcode fest (z.B. `de_DE`, überschreibt den Standardwert `$LANG`).
- `CLANG_I18N_TRANSLATION_DIR`: Verzeichnis für Übersetzungsdateien (Standard: `/usr/local/share/clang-i18n/i18n`).

### Clangd-Unterstützung in VSCode

Erstellen Sie eine Datei `clangd-i18n` mit folgendem Inhalt:
```bash
#!/usr/bin/bash
LANG=de_DE LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
Geben Sie Ausführungsrechte zu:
```bash
chmod +x clangd-i18n
```
Konfigurieren Sie in VSCode:
```json
{
    "clangd.path": "<Pfad/zur/clangd-i18n>"
}
```

## Mitwirkung bei Übersetzungen

Neue Übersetzungen oder Verbesserungen bestehender Übersetzungen sind willkommen. Sie können auch stilisierte Übersetzungen einreichen.

### Übersetzungsdateiformat

Übersetzungsdateien (Endung .yml) befinden sich im Verzeichnis `i18n`. Das Format:
```yaml
# Original-Englischer Text
Hash: Übersetzung
```

### Maschinenübersetzung mit LLMs

Unterstützung für LLMs mit OpenAI-kompatiblen APIs:
```bash
pip install openai
export LLM_ENDPOINT=<API-Endpunkt>
export LLM_MODEL=<Modellname>
export LLM_TOKEN=<API-Schlüssel>
python3 translate.py corpus.txt i18n/de_DE.prompt i18n/de_DE.errata i18n/de_DE.yml 20
```
Der Batch-Größenwert sollte nicht zu groß sein (empfohlen: 20).

## Lizenz

Lizenziert unter der [MIT-Lizenz](LICENSE).
```
