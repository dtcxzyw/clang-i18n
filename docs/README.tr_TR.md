# clang-i18n  
i18n desteğiyle Clang sarmalayıcısı  

## Giriş  

Clang-i18n, Clang araç zincirinin tanılama ve yardım bilgilerinin yerelleştirilmiş destek sunarak, İngilizce olmayan kullanıcıların ihtiyaçlarını daha iyi karşılamayı amaçlayan bir Clang i18n desteği eklentisidir.  
Bu proje Clang kaynak kodunu değiştirip yeniden derlemeyi gerektirmez, ancak eklenti formunda "plug-and-play" ve talebe dayalı çeviri fonksiyonları sunar.

## Kurulum  

Şu anda bu proje Linux x86_64/aarch64/loongarch64/riscv64 platformlarını desteklemektedir ve diğer platformlara taşınması için katkılar kabul edilmektedir.  
Clang'ın dinamik bağlantı ile derlendiğinden emin olun (Ubuntu apt üzerinden yüklenmiş Clang/LLVM bu gerekiyi karşılar).  
CMake Clang/LLVM kurulumunu bulamıyorsa `sudo apt install llvm-dev libclang-dev` komutunu çalıştırarak geliştirme dosyalarını yükleyin.  

```bash  
git clone https://github.com/dtcxzyw/clang-i18n.git  
cd clang-i18n  
mkdir -p build && cd build  
# Clang/LLVM sürümü belirtmek isterseniz, CMake için arama yolu ekleyin.  
# Örnek: -DLLVM_DIR=/usr/lib/llvm-20/lib/cmake/llvm -DClang_DIR=/usr/lib/cmake/clang-20  
cmake .. -DCMAKE_BUILD_TYPE=Release  
cmake --build . -j  
sudo cmake --install .  
```

## Kullanım  

```bash  
export LANG=tr_TR.UTF-8  
alias clang-i18n="LD_PRELOAD=/usr/local/lib/libclang-i18n.so clang"  
clang-i18n --help  
echo "float main() { return 0; }" | clang-i18n -fsyntax-only -x c++ -  
alias opt-i18n="LD_PRELOAD=/usr/local/lib/libllvm-i18n.so opt"  
opt-i18n --help  
```  

Ayrıca clang-i18n davranışını kontrol edebilecek iki isteğe bağlı ortam değişkeni mevcuttur:  
- `CLANG_I18N_LANG`: Varsayılan dili geçersiz kılmak için dil kodu belirtin (örneğin `tr_TR`, varsayılan Linux'ta `$LANG`).  
- `CLANG_I18N_TRANSLATION_DIR`: Çeviri dosyalarının dizinini belirtin, varsayılan Linux yol ise `${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/clang-i18n/i18n` (varsayılan CMake yapılandırması ile `/usr/local/share/clang-i18n/i18n`).  

### VSCode'da clangd Eklentisine i18n Destek Ekleme  

Aşağıdaki içeriği içeren bir `clangd-i18n` dosyası oluşturun:  
```bash  
#!/usr/bin/bash  

LANG=tr_TR LD_PRELOAD=/usr/local/lib/libclang-i18n.so /usr/bin/clangd $@  
```  
Dosyanın +x iznine sahip olduğundan emin olun:  
```bash  
chmod +x clangd-i18n  
```  
Sonra VSCode ayarlarında `clangd.path` yolunu bu dosyanın yolu olarak ayarlayın:  
```  
{  
    "clangd.path": <clangd-i18n dosyasının yolu>  
}  
```  

---

## Yeni Çeviriler Ekleme  

Yeni çeviriler veya mevcut çevirilerin geliştirilmesi için katkı kabul edilmektedir ve stilize çevirilerde sunulabilir.  

### Çeviri Dosya Biçimi  

`.yml` uzantılı çeviri dosyaları (gerçekte YAML değil) `i18n` dizini altında yer alır.  

Çeviri dosyası biçimi şöyledir:  
```yaml  
# İngilizce orijinal metin  
Hash: Çeviri  
```  

### Büyük Dil Modelleri ile Makine Çeviri  

Bu proje, OpenAI uyumlu API'leri ile LLM'lerden çeviri yapmaya destek vermektedir. Yapılandırma adımları:  
```bash  
# Bağımlılıkları yükleyin  
pip install openai  

# İstek dosyası i18n/tr_TR.prompt'u hazırlayın  

# Hata dosyası i18n/tr_TR.errata'yı hazırlayın  
# Biçimi şöyledir  
# <İngilizce Terim> <Yanlış Çeviri>  

export LLM_ENDPOINT=<LLM API Sonucu>  
export LLM_MODEL=<LLM Model Adı>  
export LLM_TOKEN=<LLM API Anahtarı>  

python3 translate.py corpus.txt i18n/tr_TR.prompt i18n/tr_TR.errata i18n/tr_TR.yml <Batch Boyutu>  
```  
Batch boyutu çok büyük olmamalıdır, 20'ye ayarlanması tavsiye edilir, aksi halde çeviri sıralaması hatalı olabilir.  

---

## Lisans  

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
