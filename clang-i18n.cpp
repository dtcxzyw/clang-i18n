// SPDX-License-Identifier: MIT License
// Copyright (c) 2025 Yingwei Zheng
// This file is licensed under the MIT License.
// See the LICENSE file for more information.

#include <llvm/ADT/StringExtras.h>
#include <llvm/ADT/StringRef.h>
#include <llvm/Option/OptTable.h>
#include <llvm/Option/Option.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/Error.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/SHA1.h>
#include <clang/Basic/DiagnosticIDs.h>
#include <cstdlib>
#include <dlfcn.h>
#include <map>
#include <string>
#include <unordered_map>

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
  return "/usr/share/clang-i18n";
}

class TranslationTable {
  std::unordered_map<std::string, std::string> Table;

  static void unescape(std::string &Str) {
    uint32_t Pos = 0;
    for (uint32_t I = 0; I != Str.size(); ++I) {
      if (Str[I] == '\\' && I != Str.size() - 1) {
        switch (Str[I + 1]) {
        default:
          llvm_unreachable("Unexpected escape character");
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
      } else {
        Str[Pos++] = Str[I];
      }
    }
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
      if (!Line.starts_with('H'))
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

namespace clang {

INTERCEPTOR_ATTRIBUTE
StringRef DiagnosticIDs::getDescription(unsigned DiagID) const {
  static auto RealFunc = getRealFuncAddr(&DiagnosticIDs::getDescription);
  return replace((this->*RealFunc)(DiagID));
}

} // namespace clang

namespace llvm {

namespace opt {

namespace {
struct OptionInfo {
  std::string Name;
  StringRef HelpText;
};
} // namespace

static std::string getOptionHelpName(const OptTable &Opts, OptSpecifier Id) {
  const Option O = Opts.getOption(Id);
  std::string Name = O.getPrefixedName().str();

  // Add metavar, if used.
  switch (O.getKind()) {
  case Option::GroupClass:
  case Option::InputClass:
  case Option::UnknownClass:
    llvm_unreachable("Invalid option with help text.");

  case Option::MultiArgClass:
    if (const char *MetaVarName = Opts.getOptionMetaVar(Id)) {
      // For MultiArgs, metavar is full list of all argument names.
      Name += ' ';
      Name += MetaVarName;
    } else {
      // For MultiArgs<N>, if metavar not supplied, print <value> N times.
      for (unsigned i = 0, e = O.getNumArgs(); i < e; ++i) {
        Name += " <value>";
      }
    }
    break;

  case Option::FlagClass:
    break;

  case Option::ValuesClass:
    break;

  case Option::SeparateClass:
  case Option::JoinedOrSeparateClass:
  case Option::RemainingArgsClass:
  case Option::RemainingArgsJoinedClass:
    Name += ' ';
    [[fallthrough]];
  case Option::JoinedClass:
  case Option::CommaJoinedClass:
  case Option::JoinedAndSeparateClass:
    if (const char *MetaVarName = Opts.getOptionMetaVar(Id))
      Name += MetaVarName;
    else
      Name += "<value>";
    break;
  }

  return Name;
}

static void PrintHelpOptionList(raw_ostream &OS, StringRef Title,
                                std::vector<OptionInfo> &OptionHelp) {
  OS << ::replace(Title) << ":\n";

  // Find the maximum option length.
  unsigned OptionFieldWidth = 0;
  for (const OptionInfo &Opt : OptionHelp) {
    // Limit the amount of padding we are willing to give up for alignment.
    unsigned Length = Opt.Name.size();
    if (Length <= 23)
      OptionFieldWidth = std::max(OptionFieldWidth, Length);
  }

  const unsigned InitialPad = 2;
  for (const OptionInfo &Opt : OptionHelp) {
    const std::string &Option = Opt.Name;
    int Pad = OptionFieldWidth + InitialPad;
    int FirstLinePad = OptionFieldWidth - int(Option.size());
    OS.indent(InitialPad) << Option;

    // Break on long option names.
    if (FirstLinePad < 0) {
      OS << "\n";
      FirstLinePad = OptionFieldWidth + InitialPad;
      Pad = FirstLinePad;
    }

    SmallVector<StringRef> Lines;
    Opt.HelpText.split(Lines, '\n');
    assert(Lines.size() && "Expected at least the first line in the help text");
    auto *LinesIt = Lines.begin();
    OS.indent(FirstLinePad + 1) << *LinesIt << '\n';
    while (Lines.end() != ++LinesIt)
      OS.indent(Pad + 1) << *LinesIt << '\n';
  }
}

static StringRef getOptionHelpGroup(const OptTable &Opts, OptSpecifier Id) {
  unsigned GroupID = Opts.getOptionGroupID(Id);

  // If not in a group, return the default help group.
  if (!GroupID)
    return ::replace("OPTIONS");

  // Abuse the help text of the option groups to store the "help group"
  // name.
  //
  // FIXME: Split out option groups.
  if (const char *GroupHelp = Opts.getOptionHelpText(GroupID))
    return ::replace(GroupHelp);

  // Otherwise keep looking.
  return getOptionHelpGroup(Opts, GroupID);
}

INTERCEPTOR_ATTRIBUTE
void OptTable::internalPrintHelp(
    raw_ostream &OS, const char *Usage, const char *Title, bool ShowHidden,
    bool ShowAllAliases, std::function<bool(const Info &)> ExcludeOption,
    Visibility VisibilityMask) const {
  OS << ::replace("OVERVIEW") << ": " << ::replace(Title) << "\n\n";
  OS << ::replace("USAGE") << ": " << Usage << "\n\n";

  // Render help text into a map of group-name to a list of (option, help)
  // pairs.
  std::map<std::string, std::vector<OptionInfo>> GroupedOptionHelp;

  for (unsigned Id = 1, e = getNumOptions() + 1; Id != e; ++Id) {
    // FIXME: Split out option groups.
    if (getOptionKind(Id) == Option::GroupClass)
      continue;

    const Info &CandidateInfo = getInfo(Id);
    if (!ShowHidden && (CandidateInfo.Flags & opt::HelpHidden))
      continue;

    if (ExcludeOption(CandidateInfo))
      continue;

    // If an alias doesn't have a help text, show a help text for the aliased
    // option instead.
    const char *HelpText = getOptionHelpText(Id, VisibilityMask);
    if (!HelpText && ShowAllAliases) {
      const Option Alias = getOption(Id).getAlias();
      if (Alias.isValid())
        HelpText = getOptionHelpText(Alias.getID(), VisibilityMask);
    }

    if (HelpText && (strlen(HelpText) != 0)) {
      StringRef HelpGroup = getOptionHelpGroup(*this, Id);
      const std::string &OptName = getOptionHelpName(*this, Id);
      GroupedOptionHelp[HelpGroup.str()].push_back(
          {OptName, ::replace(HelpText)});
    }
  }

  for (auto &OptionGroup : GroupedOptionHelp) {
    if (OptionGroup.first != GroupedOptionHelp.begin()->first)
      OS << "\n";
    PrintHelpOptionList(OS, OptionGroup.first, OptionGroup.second);
  }

  OS.flush();
}

INTERCEPTOR_ATTRIBUTE
void OptTable::printHelp(raw_ostream &OS, const char *Usage, const char *Title,
                         bool ShowHidden, bool ShowAllAliases,
                         Visibility VisibilityMask) const {
  return internalPrintHelp(
      OS, Usage, Title, ShowHidden, ShowAllAliases,
      [VisibilityMask](const Info &CandidateInfo) -> bool {
        return (CandidateInfo.Visibility & VisibilityMask) == 0;
      },
      VisibilityMask);
}

INTERCEPTOR_ATTRIBUTE
void OptTable::printHelp(raw_ostream &OS, const char *Usage, const char *Title,
                         unsigned FlagsToInclude, unsigned FlagsToExclude,
                         bool ShowAllAliases) const {
  bool ShowHidden = !(FlagsToExclude & HelpHidden);
  FlagsToExclude &= ~HelpHidden;
  return internalPrintHelp(
      OS, Usage, Title, ShowHidden, ShowAllAliases,
      [FlagsToInclude, FlagsToExclude](const Info &CandidateInfo) {
        if (FlagsToInclude && !(CandidateInfo.Flags & FlagsToInclude))
          return true;
        if (CandidateInfo.Flags & FlagsToExclude)
          return true;
        return false;
      },
      Visibility(0));
}

} // namespace opt
} // namespace llvm
