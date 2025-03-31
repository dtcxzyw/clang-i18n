# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import hashlib
import sys
import os
import ast
import json

corpus = list(open(sys.argv[1]).read().splitlines())
prompt = open(sys.argv[2]).read()
output = sys.argv[3]

endpoint = os.environ["LLM_ENDPOINT"]
model = os.environ["LLM_MODEL"]


def compute_hash(str: str):
    return "H" + hashlib.sha1(str.encode("utf-8")).digest().hex()[:12].upper()


with open(output, "w", encoding="utf-8") as fout:
    for val in corpus:
        src = ast.literal_eval(val)
        batch_prompt = prompt
        batch_prompt += """\n```python\n"""
        batch_prompt += f"message = {val}\n"
        batch_prompt += "```\n"
        body = {
            "model": model,
            "messages": [
                {"role": "user", "content": batch_prompt},
            ],
        }
        request = {
            "custom_id": compute_hash(src),
            "method": "POST",
            "url": endpoint,
            "body": body,
        }
        fout.write(
            json.dumps(request, separators=(",", ":"), ensure_ascii=False) + "\n"
        )
