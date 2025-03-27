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
for line in diagnostic_strings:
    strings.append(ast.literal_eval(line))

strings = list(set(strings))
strings.sort()

with open(output_path, "w") as f:
    for line in strings:
        f.write(repr(line) + "\n")
