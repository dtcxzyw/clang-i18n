# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import os
import sys
import re
import json
import subprocess
from multiprocessing import Pool
import tqdm

llvm_dir = sys.argv[1]
llvm_bin_dir = sys.argv[2]
preload_lib = sys.argv[3]
output_file = sys.argv[4]
clang_test_dir = os.path.join(llvm_dir, "clang", "test")
clang_bin = os.path.join(llvm_bin_dir, "clang")


def extract_run_lines(content: str):
    run_lines = []
    buf = ""
    for line in content.splitlines():
        if line.startswith("// RUN:"):
            val = line.removeprefix("// RUN:").strip()
            if val.endswith("\\"):
                buf += " " + val[:-1]
                pass
            else:
                buf += " " + val
                run_lines.append(buf.strip())
                buf = ""
    if buf != "":
        run_lines.append(buf.strip())
    run_lines = [
        " ".join(re.split(r"\s+", x))
        for x in run_lines
        if x.startswith("%clang")
        and "%t" not in x
        and "%if" not in x
        and "%llvmshlibdir" not in x
        and "%{openmp" not in x
        and "%{limit}" not in x
        and "%(line" not in x
    ]
    return run_lines


def materalize_run_line(command: str, dirname: str, path: str):
    pos = command.find("|")
    if pos != -1:
        command = command[:pos]
    command = command.replace("%clang_cc1", clang_bin + " -cc1")
    command = command.replace("%clangxx", clang_bin + " --driver-mode=g++")
    command = command.replace("%clang", clang_bin)
    command = command.replace("%s", path)
    command = command.replace("%S", dirname)
    triple = "x86_64-unknown-linux-gnu"
    command = command.replace("%itanium_abi_triple", triple)
    command = command.replace("%ms_abi_triple", triple)
    command = command.replace("2>&1", "")
    command = command.replace("-verify", "")
    if "%" in command:
        print(f"Unrecognized substitution in command: {command}")
        exit(-1)
    if "&" in command:
        print(f"Unrecognized pattern in command: {command}")
        exit(-1)
    return re.split(r"\s+", command.strip())


env = os.environ.copy()
env["LD_PRELOAD"] = preload_lib
env["CLANG_I18N_LANG"] = "zh_CN"
env["CLANG_I18N_DEBUG"] = "1"
hash_pattern = re.compile(r"(H[0-9A-F]+)")
tasks = []

for r, ds, fs in os.walk(clang_test_dir):
    for f in fs:
        try:
            filename = os.path.join(r, f)
            with open(filename) as file:
                content = file.read()
                if "// RUN:" not in content:
                    continue
                valid = False
                for key in [
                    "// expected-error",
                    "// expected-note",
                    "// expected-warning",
                    "// expected-remark",
                    "// expected-fatal",
                ]:
                    if key in content:
                        valid = True
                        break
                if not valid:
                    continue

                run_lines = extract_run_lines(content)
                if len(run_lines) == 0:
                    continue
                tasks.append((r, filename, run_lines))
        except Exception:
            pass


def run_task(task):
    r, filename, run_lines = task
    valid_run_lines = []
    for run_line in run_lines:
        cmd = materalize_run_line(run_line, r, filename)
        if len(cmd) == 0:
            continue
        try:
            activated = set()
            run = subprocess.run(
                cmd, capture_output=True, env=env, text=True, timeout=1.0
            )
            output = run.stdout + run.stderr
            activated_items = re.findall(hash_pattern, output)
            for item in activated_items:
                activated.add(item)
            if len(activated) == 0:
                continue
            sorted_activated = sorted(activated)
            interesting = True
            for prev in valid_run_lines:
                if (
                    prev["complexity"] <= len(activated_items)
                    and prev["activated"] == sorted_activated
                ):
                    interesting = False
                    break
            if not interesting:
                continue
            valid_run_lines.append(
                {
                    "command": run_line,
                    "complexity": len(activated_items),
                    "activated": sorted_activated,
                }
            )
        except Exception:
            pass
    return {
        "filename": os.path.relpath(filename, clang_test_dir),
        "run_lines": valid_run_lines,
    }


results = []
coverage = set()
progress = tqdm.tqdm(tasks, ncols=70, miniters=100)
with Pool(processes=os.cpu_count()) as pool:
    for res in pool.imap_unordered(run_task, tasks):
        if len(res["run_lines"]) != 0:
            for run_line in res["run_lines"]:
                for item in run_line["activated"]:
                    coverage.add(item)
            results.append(res)
        progress.update(1)
    progress.close()

print(f"Total activated items: {len(coverage)}")
with open(output_file, "w") as file:
    json.dump(results, file, indent=2)
