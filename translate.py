# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import hashlib
from openai import OpenAI
import sys
import os
import ast
import copy

corpus = list(open(sys.argv[1]).read().splitlines())
prompt = open(sys.argv[2]).read()
errata = open(sys.argv[3]).read().splitlines()
output = sys.argv[4]
batch_size = int(sys.argv[5])

endpoint = os.environ["LLM_ENDPOINT"]
model = os.environ["LLM_MODEL"]
token = os.environ["LLM_TOKEN"]
client = OpenAI(api_key=token, base_url=endpoint)


def compute_hash(strval: str):
    return "H" + hashlib.sha1(strval.encode("utf-8")).digest().hex()[:12].upper()


errata_map = dict()
for strval in errata:
    pos = strval.find(" ")
    if pos == -1:
        continue
    errata_map[strval[:pos]] = strval[pos + 1 :]

keys = [
    "%0",
    "%1",
    "%2",
    "%3",
    "%4",
    "%5",
    "%6",
    "%7",
    "%8",
    "%9",
    "%select{",
    "%enum_select<",
    "%plural{",
    "%ordinal",
    "%human",
    "%objcclass",
    "%objcinstance",
    "%q",
    "%diff{",
    "%sub{",
    "|",
    "{",
    "}",
    "\\",
    "\\n",
    "consteval",
    "constexpr",
    "constinit",
    "const_cast",
    "dynamic_cast",
    "reinterpret_cast",
    "static_cast",
    "typeid",
    "typename",
    "co_await",
    "co_return",
    "co_yield",
    "alignas",
    "alignof",
    "decltype",
    "goto",
    "noexcept",
    "nullptr",
    "static_assert",
    "thread_local",
    "#pragma",
    "X86",
    "ARM",
    "AArch64",
    "RISCV",
    "RISC-V",
    "MIPS",
    "SPARC",
    "PowerPC",
    "Alpha",
    "AMDGPU",
    "M68k",
    "SystemZ",
    "NVPTX",
    "WebAssembly",
    "JIT",
    "GNU",
    "MSVC",
    "DXIL",
    "Visual Studio",
]


def validate(src, tgt):
    if not isinstance(tgt, str):
        return False
    for k in keys:
        if src.count(k) != tgt.count(k):
            return False
    for k, v in errata_map.items():
        should_contain = False
        if k.startswith("!"):
            should_contain = True
            k = k[1:]
        if k in src or k.capitalize() in src:
            if should_contain:
                if v not in tgt:
                    return False
            elif v in tgt:
                return False
    return True


def chat(prompt):
    print(prompt)
    content = ""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=300,
            stream=True,
        )
        is_thinking = False
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content != None:
                if not is_thinking:
                    print("Thinking:")
                    is_thinking = True
                print(delta.reasoning_content, end="", flush=True)
            else:
                if delta.content is not None:
                    content += delta.content
                    print(delta.content, end="", flush=True)

    except Exception as e:
        print(e)
        return ""
    print("")
    return content


tasks = dict()
corpus_map = dict()
for strval in corpus:
    hash = compute_hash(ast.literal_eval(strval))
    corpus_map[hash] = ast.literal_eval(strval)
    tasks[hash] = strval

translation = dict()


def dump():
    with open(output, "w") as f:
        for strval in corpus:
            hash = compute_hash(ast.literal_eval(strval))
            if hash in translation:
                f.write(f"# {strval}\n{hash}: {repr(translation[hash])}\n")


if os.path.exists(output):
    with open(output) as f:
        for line in f.readlines():
            if not line.startswith("H"):
                continue
            key = line[:13]
            value = ast.literal_eval(line[15:])
            if key not in corpus_map:
                continue
            src = corpus_map[key]
            if not validate(src, value):
                continue
            translation[key] = value
            tasks.pop(key)
        dump()


def expand(code):
    exec(code)
    return copy.deepcopy(locals())


print("Tasks", len(tasks))

while len(tasks) != 0:
    batch = list(tasks.keys())[:batch_size]
    batch_prompt = prompt
    batch_prompt += """\n```python\n"""
    for idx, key in enumerate(batch):
        batch_prompt += f"message{idx} = {tasks[key]}\n"
    batch_prompt += "```\n"

    ret = chat(batch_prompt)
    if "```" not in ret:
        continue

    start = ret.find("\n", ret.find("```"))
    end = ret.find("```", start + 1)
    eval_code = ret[start + 1 : end]
    try:
        res = expand(eval_code)
    except Exception as e:
        print(e)
        continue
    for idx, key in enumerate(batch):
        var = f"message{idx}"
        if var in res:
            src = ast.literal_eval(tasks[key])
            hash = compute_hash(src)
            if not validate(src, res[var]):
                continue
            translation[hash] = res[var]
            tasks.pop(hash)

    dump()
