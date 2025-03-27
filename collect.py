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

custom_diagnostic_strings_count = 0


def get_custom_diagnostic_messages(path, keyword):
    global custom_diagnostic_strings_count
    global strings

    for r, ds, fs in os.walk(os.path.join(llvm_src_path, path)):
        for f in fs:
            if (
                not f.endswith(".cpp")
                and not f.endswith(".h")
                and not f.startswith("__")
            ):
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
                    pos += 1
                expr = srcstr[beg:pos].replace("\n", "")
                if len(expr) == 0:
                    continue
                substr = ast.literal_eval(expr)
                strings.append(substr)
                custom_diagnostic_strings_count += 1


get_custom_diagnostic_messages("clang/lib", ".getCustomDiagID(")
get_custom_diagnostic_messages("libcxx/include", "_LIBCPP_DIAGNOSE_WARNING(")
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


strings = list(set(strings))
strings.sort()

with open(output_path, "w") as f:
    for line in strings:
        f.write(repr(line) + "\n")
