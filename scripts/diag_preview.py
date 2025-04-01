# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import sys
import json
import os
import subprocess
from diag_coverage import materalize_run_line

llvm_dir = sys.argv[1]
llvm_bin_dir = sys.argv[2]
preload_lib = sys.argv[3]
coverage_map = json.load(open(sys.argv[4]))
language = sys.argv[5]
hash_val = sys.argv[6]
clang_test_dir = os.path.join(llvm_dir, "clang", "test")
clang_bin = os.path.join(llvm_bin_dir, "clang")

best_file = ""
best_run_line = ""
best_complexity = 1_000_000_000

for file in coverage_map:
    for run_line in file["run_lines"]:
        if (
            hash_val in run_line["activated"]
            and run_line["complexity"] < best_complexity
        ):
            best_complexity = run_line["complexity"]
            best_file = file["filename"]
            best_run_line = run_line["command"]

if best_file == "":
    print("No activated run line found")
    exit(-1)

file_path = os.path.join(clang_test_dir, best_file)
command = materalize_run_line(
    best_run_line, os.path.dirname(file_path), file_path, clang_bin
)

env = os.environ.copy()
env["LD_PRELOAD"] = preload_lib
env["CLANG_I18N_LANG"] = language

print("Original version:", flush=True)
subprocess.run(command)

print("Translated version:", flush=True)
subprocess.run(command, env=env)
