// SPDX-License-Identifier: MIT License
// Copyright (c) 2025 Yingwei Zheng
// This file is licensed under the MIT License.
// See the LICENSE file for more information.

#include <llvm/ADT/ScopeExit.h>
#include <llvm/ADT/StringExtras.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Config/llvm-config.h>
#include <llvm/Option/OptTable.h>
#include <llvm/Option/Option.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/Error.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/Memory.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/PrettyStackTrace.h>
#include <llvm/Support/SHA1.h>
#include <llvm/Support/raw_ostream.h>
#include <cstdlib>
#include <dlfcn.h>
#include <string>
#include <unordered_map>

#include "config.h"

using llvm::StringRef;

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
  return CLANG_I18N_TRANSLATION_DIR;
}

namespace {
class TranslationTable {
  std::unordered_map<std::string, std::string> Table;

  static void unescape(std::string &Str) {
    uint32_t Pos = 0;
    for (uint32_t I = 0; I != Str.size(); ++I) {
      if (Str[I] == '\\' && I != Str.size() - 1) {
        switch (Str[I + 1]) {
        default:
          fprintf(stderr, "Unexpected escape character: %c\n", Str[I + 1]);
          llvm_unreachable("Unexpected escape character");
        case 't':
          Str[Pos++] = '\t';
          break;
        case 'n':
          Str[Pos++] = '\n';
          break;
        case '"':
          Str[Pos++] = '\"';
          break;
        case '\'':
          Str[Pos++] = '\'';
          break;
        case '\\':
          Str[Pos++] = '\\';
          break;
        }
        ++I;
      } else {
        Str[Pos++] = Str[I];
      }
    }
    Str[Pos] = '\0';
    Str = Str.c_str();
  }

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

    SmallVector<StringRef, 0> Lines;
    (*MapFile)->getBuffer().split(Lines, '\n');
    for (auto Line : Lines) {
#if LLVM_VERSION_MAJOR > 18
      if (!Line.starts_with('H'))
#else
      if (!Line.starts_with("H"))
#endif
        continue;
      auto Key = Line.substr(1, 12);
      auto Val = Line.substr(15).drop_front().drop_back().str();
      unescape(Val);
      Table[Key.str()] = Val;
    }
  }

  StringRef replace(StringRef Src) const {
    auto It = Table.find(Hash(Src.str()));
    return It == Table.end() ? Src : It->second;
  }
};
} // namespace

static StringRef replace(StringRef Src) {
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

namespace llvm {
class ReplaceStream final : public raw_ostream {
  raw_ostream &OS;

public:
  // Turn off buffering to avoid using the fast path.
  explicit ReplaceStream(raw_ostream &OS)
      : raw_ostream(true, OS.get_kind()), OS(OS) {}

  void write_impl(const char *Ptr, size_t Size) override {
    auto Rep = ::replace(StringRef{Ptr, Size});
    OS.write(Rep.data(), Rep.size());
  }

  uint64_t current_pos() const override { return OS.tell(); }
};

class ReplaceOutStream final : public raw_fd_ostream {
public:
  // Turn off buffering to avoid using the fast path.
  explicit ReplaceOutStream()
      : raw_fd_ostream(0, false, true, outs().get_kind()) {}

  void write_impl(const char *Ptr, size_t Size) override {
    auto Rep = ::replace(StringRef{Ptr, Size});
    fwrite(Rep.data(), 1, Rep.size(), stdout);
  }
};
static_assert(sizeof(ReplaceOutStream) == sizeof(raw_fd_ostream),
              "Size mismatch");
} // namespace llvm

#ifdef CLANG_I18N_CLANG_SUPPORT
#include <clang/Basic/Diagnostic.h>
#include <clang/Basic/DiagnosticIDs.h>

namespace clang {

void Diagnostic::FormatDiagnostic(SmallVectorImpl<char> &OutStr) const {
  if (StoredDiagMessage.has_value()) {
    OutStr.append(StoredDiagMessage->begin(), StoredDiagMessage->end());
    return;
  }

  StringRef Diag =
      ::replace(getDiags()->getDiagnosticIDs()->getDescription(getID()));

  FormatDiagnostic(Diag.begin(), Diag.end(), OutStr);
}

#ifdef CLANG_I18N_LINK_DYLIB

namespace {
struct PatchFormatDiagnostic {
  PatchFormatDiagnostic() {
    const auto *FuncName = "_ZNK5clang10Diagnostic16FormatDiagnosticE"
                           "RN4llvm15SmallVectorImplIcEE";
    auto MyFunc = dlsym(RTLD_DEFAULT, FuncName);
    auto RealFunc = dlsym(RTLD_NEXT, FuncName);

#if defined(__x86_64__)
    static_assert(sizeof(MyFunc) == 8);
    uint8_t Patch[] = {// movabs rax, <MyFunc>
                       0x48, 0xb8, 0, 0, 0, 0, 0, 0, 0, 0,
                       // jmp rax
                       0xff, 0xe0};
    memcpy(Patch + 2, &MyFunc, sizeof(MyFunc));
#elif defined(__aarch64__)
    static_assert(sizeof(MyFunc) == 8);
    uint8_t Patch[] = {// ldr x16, 0x8
                       0x50, 0x00, 0x00, 0x58,
                       // br x16
                       0x00, 0x02, 0x1f, 0xd6,
                       // .quad <MyFunc>
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    static_assert(sizeof(Patch) == 16);
    memcpy(Patch + 8, &MyFunc, sizeof(MyFunc));
#elif defined(__loongarch__) && __loongarch_grlen == 64
    static_assert(sizeof(MyFunc) == 8);
    uint8_t Patch[] = {// pcaddu18i $t0, 0
                       0x0c, 0x00, 0x00, 0x1e,
                       // ld.d $t0, $t0, 12
                       0x8c, 0x31, 0xc0, 0x28,
                       // jr $t0
                       0x80, 0x01, 0x00, 0x4c,
                       // .quad <MyFunc>
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    static_assert(sizeof(Patch) == 20);
    memcpy(Patch + 12, &MyFunc, sizeof(MyFunc));
#elif defined(__riscv) && __riscv_xlen == 64
    static_assert(sizeof(MyFunc) == 8);
    uint8_t Patch[] = {// auipc t0, 0x0
                       0x97, 0x02, 0x00, 0x00,
                       // ld t0, 10(t0)
                       0x83, 0xb2, 0xa2, 0x00,
                       // c.jr t0
                       0x82, 0x82,
                       // .quad <MyFunc>
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    static_assert(sizeof(Patch) == 18);
    memcpy(Patch + 10, &MyFunc, sizeof(MyFunc));
#else
#error "Unsupported architecture"
#endif
    using namespace llvm::sys;
    MemoryBlock Mem(RealFunc, sizeof(Patch));
    [[maybe_unused]] auto Ret1 =
        Memory::protectMappedMemory(Mem, Memory::MF_RWE_MASK);
    memcpy(Mem.base(), Patch, sizeof(Patch));
    [[maybe_unused]] auto Ret2 =
        Memory::protectMappedMemory(Mem, Memory::MF_READ | Memory::MF_EXEC);
  }
};
} // namespace

static void
DummyArgToStringFn(DiagnosticsEngine::ArgumentKind AK, intptr_t QT,
                   StringRef Modifier, StringRef Argument,
                   ArrayRef<DiagnosticsEngine::ArgumentValue> PrevArgs,
                   SmallVectorImpl<char> &Output, void *Cookie,
                   ArrayRef<intptr_t> QualTypeVals) {
  StringRef Str = "<can't format argument>";
  Output.append(Str.begin(), Str.end());
}

INTERCEPTOR_ATTRIBUTE
DiagnosticsEngine::DiagnosticsEngine(
    IntrusiveRefCntPtr<DiagnosticIDs> diags,
    IntrusiveRefCntPtr<DiagnosticOptions> DiagOpts, DiagnosticConsumer *client,
    bool ShouldOwnClient)
    : Diags(std::move(diags)), DiagOpts(std::move(DiagOpts)) {
  static PatchFormatDiagnostic Patcher;
  setClient(client, ShouldOwnClient);
  ArgToStringFn = DummyArgToStringFn;

  Reset();
}

#endif

} // namespace clang
#endif

namespace llvm {

namespace opt {

INTERCEPTOR_ATTRIBUTE
void OptTable::printHelp(raw_ostream &OS, const char *Usage, const char *Title,
                         bool ShowHidden, bool ShowAllAliases,
                         Visibility VisibilityMask) const {
  ReplaceStream Wrapper{OS};
  return internalPrintHelp(
      Wrapper, Usage, Title, ShowHidden, ShowAllAliases,
      [VisibilityMask](const Info &CandidateInfo) -> bool {
        return (CandidateInfo.Visibility & VisibilityMask) == 0;
      }
#if LLVM_VERSION_MAJOR > 18
      ,
      VisibilityMask
#endif
  );
}

INTERCEPTOR_ATTRIBUTE
void OptTable::printHelp(raw_ostream &OS, const char *Usage, const char *Title,
                         unsigned FlagsToInclude, unsigned FlagsToExclude,
                         bool ShowAllAliases) const {
  ReplaceStream Wrapper{OS};
  bool ShowHidden = !(FlagsToExclude & HelpHidden);
  FlagsToExclude &= ~HelpHidden;
  return internalPrintHelp(
      Wrapper, Usage, Title, ShowHidden, ShowAllAliases,
      [FlagsToInclude, FlagsToExclude](const Info &CandidateInfo) {
        if (FlagsToInclude && !(CandidateInfo.Flags & FlagsToInclude))
          return true;
        if (CandidateInfo.Flags & FlagsToExclude)
          return true;
        return false;
      }
#if LLVM_VERSION_MAJOR > 18
      ,
      Visibility(0)
#endif
  );
}

} // namespace opt

INTERCEPTOR_ATTRIBUTE void setBugReportMsg(const char *Msg) {
  static auto RealFunc = getRealFuncAddr(&setBugReportMsg);
  return RealFunc(::replace(Msg).data());
}

INTERCEPTOR_ATTRIBUTE
bool CheckBitcodeOutputToConsole(raw_ostream &OS) {
  if (OS.is_displayed()) {
    errs() << ::replace(
        "WARNING: You're attempting to print out a bitcode file.\n"
        "This is inadvisable as it may cause display problems. If\n"
        "you REALLY want to taste LLVM bitcode first-hand, you\n"
        "can force output with the `-f' option.\n\n");
    return true;
  }
  return false;
}

INTERCEPTOR_ATTRIBUTE
void EnablePrettyStackTrace() {
  static auto RealFunc = getRealFuncAddr(&EnablePrettyStackTrace);
  setBugReportMsg(getBugReportMsg());
  return RealFunc();
}

namespace cl {
INTERCEPTOR_ATTRIBUTE bool
ParseCommandLineOptions(int argc, const char *const *argv, StringRef Overview,
                        raw_ostream *Errs, const char *EnvVar,
                        bool LongOptionsUseDoubleDash) {
  static auto RealFunc = getRealFuncAddr(&ParseCommandLineOptions);
  char Buffer[sizeof(raw_fd_ostream)];
  void *OS = &outs();
  std::memcpy(Buffer, OS, sizeof(Buffer));
  new (OS) ReplaceOutStream;
  auto Exit = llvm::make_scope_exit([&] {
    std::destroy_at(&outs());
    std::memcpy(OS, Buffer, sizeof(Buffer));
  });
  return RealFunc(argc, argv, Overview, Errs, EnvVar, LongOptionsUseDoubleDash);
}
} // namespace cl

} // namespace llvm
