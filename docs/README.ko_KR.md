# clang-i18n  
국제화(i18n) 기능을 지원하는 Clang 래퍼  

## 소개  
clang-i18n은 Clang 도구체인의 진단 및 도움말 정보에 지역화(localization) 지원을 제공하여 비영어 사용자의 요구사항을 충족시키는 Clang i18n 지원 플러그인입니다.  
이 프로젝트는 Clang 소스 코드를 수정하거나 재빌드하지 않고 플러그인 형식으로 플러그 앤 플레이 및 수요에 따른 번역 기능을 제공합니다.  

## 설치  
현재 이 프로젝트는 Linux x86_64/aarch64/loongarch64/riscv64 플랫폼을 지원하며, 다른 플랫폼으로 포팅에 기여할 수 있습니다.  
Clang을 동적 링킹으로 빌드했는지 확인하십시오(예: Ubuntu apt을 통해 설치된 Clang/LLVM은 이 요구사항을 충족합니다).  
cmake가 Clang/LLVM 설치를 찾을 수 없는 경우 `sudo apt install llvm-dev libclang-dev`를 실행하여 개발 파일을 설치하십시오.  

```bash
git clone https://github.com/dtcxzyw/clang-i18n.git  
cd clang-i18n  
mkdir -p build && cd build  
# Clang/LLVM 버전을 지정하려면 CMake에 검색 경로를 추가합니다.  
# 예: -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DClang_DIR=/usr/lib/cmake/clang-20  
cmake .. -DCMAKE_BUILD_TYPE=Release  
cmake --build . -j  
sudo cmake --install .  
```  

## 사용법  
```bash  
export LANG=ko_KR.UTF-8  
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"  
clang-i18n --help  
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -  
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"  
opt-i18n --help  
```  

clang-i18n의 동작을 제어하는 두 개의 선택적 환경 변수가 있습니다:  
- `CLANG_I18N_LANG`: 기본 언어 설정을 덮어쓰는 언어 코드(예: ko_KR, 기본값은 Linux에서 `$LANG`).  
- `CLANG_I18N_TRANSLATION_DIR`: 번역 파일 디렉토리(기본값은 Linux에서 `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, CMake 기본 설정 시 `/usr/local/share/clang-i18n/i18n`).  

### VSCode의 clangd 확장에 i18n 기능 추가  
다음 내용으로 `clangd-i18n` 파일을 생성합니다:  
```bash  
#!/usr/bin/bash  

LANG=ko_KR LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@  
```  
실행 권한을 부여합니다:  
```bash  
chmod +x clangd-i18n  
```  
그리고 VSCode 설정에서 `clangd.path`를 해당 파일 경로로 설정합니다:  
```json  
{  
    "clangd.path": <clangd-i18n 파일 경로>  
}  
```  

## 새로운 번역 기여  
새 번역 또는 기존 번역 개선 기여는 환영합니다. 스타일에 맞는 번역도 제출 가능합니다.  

### 번역 파일 형식  
`.yml` 확장자로 끝나는 번역 파일(실제로 YAML 형식이 아님)은 `i18n` 디렉토리 하위에 배치됩니다.  
번역 파일 형식은 다음과 같습니다:  
```yaml  
# 영어 원문  
Hash: 번역문  
```  

### 대형 언어 모델(LLM)을 사용한 기계 번역  
OpenAI 호환 API를 지원하는 LLM으로 번역을 할 수 있으며, 구체적인 설정 방법은 다음과 같습니다:  
```bash  
# 의존성 설치  
pip install openai  

# 提示 파일(i18n/ko_KR.prompt) 준비  
# 오류 수정 파일(i18n/ko_KR.errata) 준비  
# 형식 예시:  
# <영어 용어> <잘못된 번역>  

export LLM_ENDPOINT=<LLM API 엔드포인트>  
export LLM_MODEL=<LLM 모델 이름>  
export LLM_TOKEN=<LLM API 키>  

python3 translate.py corpus.txt i18n/ko_KR.prompt i18n/ko_KR.errata i18n/ko_KR.yml <배치 크기>  
```  
배치 크기는 20 정도로 작은 값이 좋으며, 크면 번역 순서가 틀릴 수 있습니다.  

## 라이선스  
이 프로젝트는 [MIT 라이선스](LICENSE) 하에 라이선스되었습니다.
