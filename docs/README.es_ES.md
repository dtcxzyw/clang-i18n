# clang-i18n  
Wrapper de Clang con soporte para internacionalización (i18n)  

## Introducción  

clang-i18n es un plugin de soporte de internacionalización para Clang que busca proporcionar soporte de localización para las informaciones de diagnóstico y ayuda de la herramienta Clang, mejorando así la experiencia de usuarios que no usan inglés.  
Este proyecto **no requiere modificar el código fuente de Clang ni reconstruirlo**, sino que ofrece funciones de traducción bajo demanda y listas para usar mediante un plugin.  

## Instalación  

Actualmente, este proyecto es compatible con plataformas Linux x86_64/aarch64/loongarch64/riscv64. Contribuciones para portar a otras plataformas son bienvenidas.  
Asegúrese de que Clang se construyó con enlace dinámico (las versiones de Clang/LLVM instaladas desde Ubuntu apt cumplen este requisito).  
Si CMake no encuentra la instalación de Clang/LLVM, ejecute `sudo apt install llvm-dev libclang-dev` para instalar los archivos de desarrollo.  

```bash  
git clone https://github.com/dtcxzyw/clang-i18n.git  
cd clang-i18n  
mkdir -p build && cd build  
# Si necesita especificar la versión de Clang/LLVM, agregue la ruta de búsqueda a CMake.  
# Ejemplo: -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DClang_DIR=/usr/lib/llvm-20/lib/cmake/clang  
cmake .. -DCMAKE_BUILD_TYPE=Release  
cmake --build . -j  
sudo cmake --install .  
```  

## Uso  

```bash  
export LANG=es_ES.UTF-8  
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"  
clang-i18n --help  
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -  
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"  
opt-i18n --help  
```  

Además, existen dos variables de entorno opcionales para controlar el comportamiento de clang-i18n:  
- `CLANG_I18N_LANG`: Establecer el código de idioma (ej: `es_ES`) para sobrescribir la configuración predeterminada (por defecto usa `$LANG` en Linux).  
- `CLANG_I18N_TRANSLATION_DIR`: Directorio de archivos de traducción, por defecto en Linux es `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n`, es decir `/usr/local/share/clang-i18n/i18n` con la configuración predeterminada de CMake.  

### Agregar soporte i18n al complemento clangd de VSCode  

Cree un archivo llamado `clangd-i18n` con el siguiente contenido:  
```bash  
#!/usr/bin/bash  

LANG=es_ES LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@  
```  
Asegúrese de que el archivo tenga permisos ejecutables:  
```bash  
chmod +x clangd-i18n  
```  
Luego, en la configuración de VSCode, configure `clangd.path` con la ruta de este archivo:  
```json  
{  
    "clangd.path": <ruta al archivo clangd-i18n>  
}  
```  

## Contribuir con nuevas traducciones  

Las contribuciones de nuevas traducciones o mejoras en traducciones existentes son bienvenidas. También puede enviar traducciones estilizadas.  

### Formato de archivos de traducción  

Los archivos de traducción terminan con la extensión `.yml` (no son YAML estándar) y se colocan en el directorio `i18n`.  

El formato es:  
```yaml  
# Texto original en inglés  
Hash: Traducción  
```  

### Traducción automática con modelos de lenguaje grandes (LLM)  

Este proyecto soporta usar LLM con APIs compatibles con OpenAI. Método de configuración:  

```bash  
# Instalar dependencias  
pip install openai  

# Preparar el archivo de prompt i18n/es_.prompt  

# Preparar el archivo de correcciones i18n/es_ES.errata  
# Formato:  
# <Término en inglés> <Traducción incorrecta>  

export LLM_ENDPOINT=<Endpoint de la API LLM>  
export LLM_MODEL=<Nombre del modelo LLM>  
export LLM_TOKEN=<Token de API>  

python3 translate.py corpus.txt i18n/es_ES.prompt i18n/es_ES.errata i18n/es_ES.yml <Tamaño de lote>  
```  

Evite tamaños de lote demasiado grandes (recomendado: 20), de lo contrario el orden de traducciones podría alterarse.  

## Licencia  

Este proyecto está bajo la [Licencia MIT](LICENSE).
