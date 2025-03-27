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
output = sys.argv[3]
batch_size = int(sys.argv[4])

endpoint = os.environ["LLM_ENDPOINT"]
model = os.environ["LLM_MODEL"]
token = os.environ["LLM_TOKEN"]
client = OpenAI(api_key=token, base_url=endpoint)


def compute_hash(str: str):
    return "H" + hashlib.sha1(str.encode("utf-8")).digest().hex()[:12].upper()


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
        for chunk in completion:
            delta = chunk.choices[0].delta
            if delta.content is not None:
                content += delta.content

    except Exception as e:
        print(e)
        return ""
    print(content)
    return content


tasks = dict()
for str in corpus:
    tasks[compute_hash(ast.literal_eval(str))] = str

translation = dict()

if os.path.exists(output):
    with open(output) as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            key = line[:13]
            value = ast.literal_eval(line[15:])
            translation[key] = value
            tasks.pop(key)


def expand(code):
    exec(code)
    return copy.deepcopy(locals())


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
    res = expand(eval_code)
    for idx, key in enumerate(batch):
        var = f"message{idx}"
        if var in res:
            hash = compute_hash(ast.literal_eval(tasks[key]))
            translation[hash] = res[var]
            tasks.pop(hash)

    with open(output, "w") as f:
        for str in corpus:
            hash = compute_hash(ast.literal_eval(str))
            if hash in translation:
                f.write(f"# {str}\n{hash}: {repr(translation[hash])}\n")
