# clang-i18n
Wrapper do Clang com suporte a i18n

## Introdução

O clang-i18n é um plug-in de suporte a i18n para o Clang, projetado para fornecer suporte de localização para as mensagens de diagnóstico e informações de ajuda da cadeia de ferramentas Clang, visando atender melhor às necessidades de usuários que não falam inglês.
Este projeto não requer modificação do código-fonte do Clang ou recompilação, fornecendo funcionalidades de tradução sob demanda e plug-and-play por meio de um plug-in.

## Instalação

Atualmente, este projeto suporta plataformas Linux x86_64/aarch64/loongarch64/riscv64. Contribuições para portar para outras plataformas são bem-vindas.
Certifique-se de que o Clang foi compilado com vinculação dinâmica (instalações via apt do Ubuntu atendem a esse requisito).
Se o cmake não encontrar a instalação do Clang/LLVM, execute `sudo apt install llvm-dev libclang-dev` para instalar os arquivos de desenvolvimento.

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git
cd clang-i18n
mkdir -p build && cd build
# Se necessário especificar a versão do Clang/LLVM, adicione o caminho de busca ao CMake.
# Exemplo: -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DClang_DIR=/usr/lib/llvm-20/lib/cmake/clang
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
sudo cmake --install .
```

## Uso

```bash
export LANG=pt_BR.UTF-8
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"
clang-i18n --help
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"
opt-i18n --help
```

Além disso, existem duas variáveis de ambiente opcionais que controlam o comportamento do clang-i18n:
- `CLANG_I18N_LANG`: Define o código de idioma (ex.: `pt_BR`) para substituir a configuração padrão (padrão é `$LANG` no Linux).
- `CLANG_I18N_TRANSLATION_DIR`: Define o diretório de arquivos de tradução. O valor padrão no Linux é `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, ou seja, `/usr/local/share/clang-i18n/i18n` ao usar a configuração padrão do CMake.

### Adicionar suporte i18n à extensão clangd do VSCode

Crie um arquivo chamado `clangd-i18n` com o seguinte conteúdo:
```bash
#!/usr/bin/bash

LANG=pt_BR LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@
```
Certifique-se de que o arquivo tenha permissão de execução:
```bash
chmod +x clangd-i18n
```
Em seguida, nas configurações do VSCode, defina `clangd.path` como o caminho deste arquivo:
```
{
    "clangd.path": <caminho para clangd-i18n>
}
```

## Contribuindo com Novas Traduções

Contribuições de novas traduções ou melhorias em traduções existentes são bem-vindas, incluindo traduções estilizadas.

### Formato dos Arquivos de Tradução

Os arquivos de tradução têm extensão `.yml` (na verdade não estão no formato YAML) e são colocados no diretório `i18n`.

O formato do arquivo de tradução é:
```
# Texto original em inglês
Hash: Tradução
```

### Tradução Automática com Modelos de Linguagem (LLM)

Este projeto suporta o uso de LLM (Modelos de Linguagem Grandes) com APIs compatíveis com o OpenAI. Configuração específica:

```bash
# Instalar dependências
pip install openai

# Preparar o arquivo de prompt i18n/pt_BR.prompt

# Preparar o arquivo de correções i18n/pt_BR.errata
# Formato:
# <Termo em Inglês> <Tradução Incorreta>

export LLM_ENDPOINT=<Endpoint da API LLM>
export LLM_MODEL=<Nome do Modelo LLM>
export LLM_TOKEN=<Chave de Acesso da API>

python3 translate.py corpus.txt i18n/pt_BR.prompt i18n/pt_BR.errata i18n/pt_BR.yml <Tamanho do Lote>
```

O tamanho do lote não deve ser muito grande; recomenda-se 20 para evitar ordem incorreta de traduções.

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).
