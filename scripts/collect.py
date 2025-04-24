# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import sys
import os
import subprocess
import ast

llvm_src_path = sys.argv[1]
llvm_build_path = sys.argv[2]
output_path = sys.argv[3]
strings = []

diagnostic_extractor = """
#define DIAG(ENUM, CLASS, DEFAULT_SEVERITY, DESC, GROUP, SFINAE, NOWERROR, SHOWINSYSHEADER, SHOWINSYSMACRO, DEFERRABLE, CATEGORY) DESC
#include "clang/Basic/DiagnosticCommonKinds.inc"
#include "clang/Basic/DiagnosticDriverKinds.inc"
#include "clang/Basic/DiagnosticFrontendKinds.inc"
#include "clang/Basic/DiagnosticSerializationKinds.inc"
#include "clang/Basic/DiagnosticLexKinds.inc"
#include "clang/Basic/DiagnosticParseKinds.inc"
#include "clang/Basic/DiagnosticASTKinds.inc"
#include "clang/Basic/DiagnosticCommentKinds.inc"
#include "clang/Basic/DiagnosticCrossTUKinds.inc"
#include "clang/Basic/DiagnosticSemaKinds.inc"
#include "clang/Basic/DiagnosticAnalysisKinds.inc"
#include "clang/Basic/DiagnosticRefactoringKinds.inc"
#include "clang/Basic/DiagnosticInstallAPIKinds.inc"
"""

diagnostic_strings = (
    subprocess.check_output(
        [
            "cc",
            "-E",
            "-P",
            "-I",
            os.path.join(llvm_build_path, "tools/clang/include"),
            "-",
        ],
        input=diagnostic_extractor.encode(),
    )
    .decode()
    .splitlines()
)
print("Diagnostic:", len(diagnostic_strings))
for line in diagnostic_strings:
    strings.append(ast.literal_eval(line))


def get_custom_messages(
    path, keyword, suffix=False, trunc_for_suffix=False, max_len=10000000
):
    count = 0
    global strings

    for r, ds, fs in os.walk(os.path.join(llvm_src_path, path)):
        for f in fs:
            if (
                not f.endswith(".cpp")
                and not f.endswith(".h")
                and not (f.startswith("__") and "." not in f)
            ):
                continue
            if "test" in r:
                continue
            with open(os.path.join(r, f)) as src:
                srcstr = src.read()
            if keyword not in srcstr:
                continue
            pos = 0
            while True:
                pos = srcstr.find(keyword, pos + 1)
                if pos == -1:
                    break
                beg = srcstr.find('"', pos)
                if beg == -1:
                    break
                depth = 0
                while True:
                    ch = srcstr[pos]
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    if pos == len(srcstr) - 1:
                        break
                    pos += 1
                expr = srcstr[beg:pos]
                if srcstr[beg - 1 : beg + 2] != 'R"(':
                    expr = expr.replace("\n", "")
                else:
                    expr = '""' + expr + '""'
                if len(expr) == 0:
                    continue
                if trunc_for_suffix:
                    npos = expr.rfind('"')
                    if npos != -1:
                        expr = expr[: npos + 1]
                substr = None
                try:
                    substr = ast.literal_eval(expr)
                except Exception:
                    pass
                if not isinstance(substr, str):
                    substr = None
                if substr is None:
                    for i in range(1, len(expr)):
                        try:
                            if suffix:
                                substr = ast.literal_eval(expr[i:].replace("\n", ""))
                            else:
                                substr = ast.literal_eval(expr[:-i].replace("\n", ""))
                            if not isinstance(substr, str):
                                substr = None
                                continue
                            if substr is not None:
                                break
                        except Exception:
                            pass
                if substr is None:
                    continue
                while substr.startswith("(") and substr.endswith(")"):
                    substr = substr[1:-1]
                if (
                    len(substr) != 0
                    and not (
                        ("-" in substr) and (" " not in substr) and ("<" not in substr)
                    )
                    and len(substr) < max_len
                ):
                    strings.append(substr)
                    count += 1
    return count


custom_diagnostic_strings_count = 0
custom_diagnostic_strings_count += get_custom_messages("clang/lib", ".getCustomDiagID(")
custom_diagnostic_strings_count += get_custom_messages(
    "libcxx/include", "_LIBCPP_DIAGNOSE_WARNING("
)
print("Custom Diagnostic:", custom_diagnostic_strings_count)

option_extractor = """
#define OPTION(PREFIXES_OFFSET, PREFIXED_NAME_OFFSET, ID, KIND, GROUP, ALIAS, ALIASARGS, FLAGS, VISIBILITY, PARAM, HELPTEXT, HELPTEXTSFORVARIANTS, METAVAR, VALUES) HELPTEXT
#include "clang/Driver/Options.inc"
#undef OPTION
#define OPTION(PREFIXES_OFFSET, PREFIXED_NAME_OFFSET, ID, KIND, GROUP, ALIAS, ALIASARGS, FLAGS, VISIBILITY, PARAM, HELPTEXT, HELPTEXTSFORVARIANTS, METAVAR, VALUES) HELPTEXTSFORVARIANTS
#include "clang/Driver/Options.inc"
"""
option_strings = (
    subprocess.check_output(
        [
            "cc",
            "-E",
            "-P",
            "-I",
            os.path.join(llvm_build_path, "tools/clang/include"),
            "-",
        ],
        input=option_extractor.encode(),
    )
    .decode()
    .splitlines()
)
print("Option:", len(option_strings))
for line in option_strings:
    if '"' in line:
        res = None
        try:
            res = ast.literal_eval(line)

        except Exception:
            pass
        if res is None:
            pos1 = line.find('"')
            pos2 = line.rfind('"')
            if pos1 != -1 and pos2 != -1:
                res = ast.literal_eval(line[pos1 : pos2 + 1])
        if len(res) != 0:
            strings.append(res)
inline_options_count = 0
inline_options_count += get_custom_messages(".", "cl::desc(")
inline_options_count += get_custom_messages(".", "clEnumValN(", suffix=True)
inline_options_count += get_custom_messages(".", "clEnumVal(", suffix=True)
inline_options_count += get_custom_messages(".", "cl::OptionCategory")
inline_options_count += get_custom_messages(".", "cl::OptionCategory", suffix=True)
inline_options_count += get_custom_messages(
    "llvm/include/llvm/Target", "addLiteralOption(", suffix=True
)
print("Inline Option:", inline_options_count)

# Passes description using legacy pass manager
old_passes_count = 0
old_passes_count += get_custom_messages(
    ".", "INITIALIZE_PASS_BEGIN(", suffix=True, trunc_for_suffix=True
)
old_passes_count += get_custom_messages(
    ".", "INITIALIZE_PASS_END(", suffix=True, trunc_for_suffix=True
)
old_passes_count += get_custom_messages(
    ".", "INITIALIZE_PASS(", suffix=True, trunc_for_suffix=True
)
old_passes_count += get_custom_messages(
    ".", "static RegisterPass<", suffix=True, trunc_for_suffix=True
)
old_passes_count += get_custom_messages("llvm/lib", "_NAME ", max_len=100)
print("Old Passes:", old_passes_count)
desc_count = get_custom_messages(".", "cl::ParseCommandLineOptions(", suffix=True)
print("Program Desc:", desc_count)
sched_count = 0
sched_count += get_custom_messages(
    "llvm/lib", "static MachineSchedRegistry", suffix=True, trunc_for_suffix=True
)
sched_count += get_custom_messages(
    "llvm/lib", "static RegisterScheduler", suffix=True, trunc_for_suffix=True
)
print("Schedulers:", sched_count)
debug_count = get_custom_messages("llvm/lib", "DEBUG_COUNTER(", suffix=True)
print("Debug Counter:", debug_count)
reg_alloc_count = get_custom_messages(
    "llvm/lib/CodeGen", "static RegisterRegAlloc", suffix=True, trunc_for_suffix=True
)
print("Register Allocators:", reg_alloc_count)

# Special strings
strings.append("clang LLVM compiler")
strings.append("OVERVIEW: ")
strings.append("USAGE: ")
strings.append("OPTIONS:\n")
strings.append("SUBCOMMANDS:\n\n")
strings.append('  Type "')
strings.append(' <subcommand> --help" to get more help on a specific ' "subcommand")
strings.append(" [options]")
strings.append("SUBCOMMAND '")
strings.append(" [subcommand]")
strings.append("= *cannot print option value*\n")
strings.append("*no default*")
strings.append(" (default: ")
strings.append("= *unknown option value*\n")
strings.append(
    "PLEASE submit a bug report to https://github.com/llvm/llvm-project/issues/ and include the crash backtrace, preprocessed source, and associated run script.\n"
)
strings.append(
    "PLEASE submit a bug report to https://github.com/llvm/llvm-project/issues/ and include the crash backtrace.\n"
)
strings.append(
    "WARNING: You're attempting to print out a bitcode file.\n"
    "This is inadvisable as it may cause display problems. If\n"
    "you REALLY want to taste LLVM bitcode first-hand, you\n"
    "can force output with the `-f' option.\n\n"
)
strings.append(
    "\n********************\n\n"
    "PLEASE ATTACH THE FOLLOWING FILES TO THE BUG REPORT:\n"
    "Preprocessed source(s) and associated run script(s) are located at:"
)
strings.append("Override the behaviour of expand-variadics")
strings.append(
    "Options: <empty>|Legal|Discard|Convert. If non-empty, ignore TargetTransformInfo and always use this transformation for the %evl parameter (Used in testing)."
)
strings.append(": Unknown ")
strings.append("command line argument")
strings.append("subcommand")
strings.append("'.  Try: '")
strings.append(": Did you mean '")
strings.append(
    "This argument does not take a value.\n"
    "\tInstead, it consumes any positional arguments until "
    "the next recognized option."
)
strings.append(": Not enough positional command line arguments specified!\n")
strings.append("Must specify at least ")
strings.append(" positional argument")
strings.append(": See: ")
strings.append(": Too many positional arguments specified!\n")
strings.append("Can specify at most ")
strings.append(" positional arguments: See: ")
strings.append("must be specified at least once!")
strings.append("invalid case style for %0 '%1'")
strings.append(
    "declaration uses identifier '%0', which is %select{a reserved "
    "identifier|not a reserved identifier|reserved in the global namespace}1"
)

strings = list(set(filter(lambda x: x.lower() != x.upper(), strings)))
block_words = [
    "All",
    "all",
    "never",
    "Enabled",
    "Disabled",
    "Default",
    "directory",
    "filename",
    " position!",
    " version ",
    "' attribute: ",
]
strings = sorted(filter(lambda x: x not in block_words, strings))

with open(output_path, "w") as f:
    for line in strings:
        f.write(repr(line) + "\n")
