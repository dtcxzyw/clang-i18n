// SPDX-License-Identifier: MIT License
// Copyright (c) 2025 Yingwei Zheng
// This file is licensed under the MIT License.
// See the LICENSE file for more information.

#include <llvm/ADT/StringExtras.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Support/Error.h>
#include <llvm/Support/SHA1.h>
#include <llvm/Support/YAMLParser.h>
#include <clang/Basic/DiagnosticIDs.h>
#include <cstdlib>
#include <dlfcn.h>
#include <string>
#include <unordered_map>

#define private public
#include <llvm/Option/OptTable.h>
#undef private

using clang::StringRef;

static StringRef getLang() {
  if (auto *Lang = std::getenv("CLANG_I18N_LANG"))
    return StringRef{Lang}.split('.').first;
  if (auto *Lang = std::getenv("LANG"))
    return StringRef{Lang}.split('.').first;
  return "";
}

static StringRef getTranslationDir() {
  if (auto *Path = std::getenv("CLANG_I18N_TRANSLATION_DIR"))
    return Path;
  return "/usr/share/clang/i18n";
}

class TranslationTable {
  std::unordered_map<std::string, std::string> Table;

public:
  static std::string Hash(StringRef Src) {
    llvm::SHA1 S;
    S.update(Src);
    auto Res = S.result();
    return llvm::toHex(Res).substr(0, 12);
  }

  TranslationTable() {
    using namespace llvm;
    auto Lang = getLang();
    if (Lang.empty() || Lang == "en_US" || Lang == "en_UK")
      return;
    auto TranslationDir = getTranslationDir();
    auto Path = TranslationDir.str() + "/" + Lang.str() + ".yml";
    auto MapFile = MemoryBuffer::getFile(Path, true);
    if (!MapFile) {
      fprintf(stderr, "Failed to open translation file: %s\n", Path.c_str());
      return;
    }
    SourceMgr SM;
    yaml::Stream YS((*MapFile)->getBuffer(), SM);
    yaml::document_iterator Doc = YS.begin();
    if (Doc == YS.end()) {
      fprintf(stderr, "Failed to parse translation file: %s\n", Path.c_str());
      return;
    }

    yaml::MappingNode *DocumentRoot =
        dyn_cast_if_present<yaml::MappingNode>(Doc->getRoot());
    if (!DocumentRoot) {
      fprintf(stderr, "Failed to parse translation file: %s\n", Path.c_str());
      return;
    }

    for (auto &Entry : *DocumentRoot) {
      if (auto *KeyStr = dyn_cast<yaml::ScalarNode>(Entry.getKey())) {
        if (auto *ValueStr = dyn_cast<yaml::ScalarNode>(Entry.getValue())) {
          SmallVector<char> Storage;
          auto KeyHex = KeyStr->getValue(Storage);
          auto Content = ValueStr->getValue(Storage);
          Table[KeyHex.str()] = Content;
        }
      }

      fprintf(stderr, "Failed to parse translation file: %s\n", Path.c_str());
      return;
    }
  }

  StringRef replace(StringRef Src) const {
    auto It = Table.find(Hash(Src.str()));
    return It == Table.end() ? Src : It->second;
  }
};

static StringRef replace(StringRef Src) {
  printf("hooked\n");
  printf("%s\n", TranslationTable::Hash("hello").c_str());
  static TranslationTable Table;
  return Table.replace(Src);
}

static void *getRealFuncAddrImpl(const char *ManagledName,
                                 void *InterceptorAddr) {
  void *RealAddr = dlsym(RTLD_NEXT, ManagledName);
  if (!RealAddr) {
    RealAddr = dlsym(RTLD_DEFAULT, ManagledName);
    if (RealAddr == InterceptorAddr)
      RealAddr = nullptr;
  }
  return RealAddr;
}

template <typename F> static F *getRealFuncAddr(F *InterceptorFunc) {
  void *InterceptorAddr;
  std::memcpy(&InterceptorAddr, &InterceptorFunc, sizeof(InterceptorAddr));
  Dl_info Info;
  dladdr(InterceptorAddr, &Info);
  void *RealFuncAddr = getRealFuncAddrImpl(Info.dli_sname, InterceptorAddr);
  assert(RealFuncAddr && "Failed to find the real function address");
  F *RealFunc;
  std::memcpy(&RealFunc, &RealFuncAddr, sizeof(RealFunc));
  return RealFunc;
}

template <typename T, typename F>
static F T::*getRealFuncAddr(F T::*InterceptorFunc) {
  void *InterceptorAddr;
  std::memcpy(&InterceptorAddr, &InterceptorFunc, sizeof(InterceptorAddr));
  Dl_info Info;
  dladdr(InterceptorAddr, &Info);
  void *RealFuncAddr = getRealFuncAddrImpl(Info.dli_sname, InterceptorAddr);
  assert(RealFuncAddr && "Failed to find the real function address");
  F T::*RealFunc;
  std::memcpy(&RealFunc, &RealFuncAddr, sizeof(RealFunc));
  return RealFunc;
}

#define INTERCEPTOR_ATTRIBUTE __attribute__((visibility("default")))

namespace clang {

INTERCEPTOR_ATTRIBUTE
StringRef DiagnosticIDs::getDescription(unsigned DiagID) const {
  static auto RealFunc = getRealFuncAddr(&DiagnosticIDs::getDescription);
  return replace((this->*RealFunc)(DiagID));
}

} // namespace clang

namespace llvm {}
