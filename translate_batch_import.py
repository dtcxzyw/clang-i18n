# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import sys
import json

input_file = sys.argv[1]
output_file = sys.argv[2]


def get_message(code):
    exec(code)
    return locals()["message"]


with open(input_file, "r") as f:
    with open(output_file, "w") as out:
        for line in f.read().splitlines():
            res = json.loads(line)
            try:
                content = res["response"]["body"]["choices"][0]["message"]["content"]
                hashval = res["custom_id"]
                start = content.find("\n", content.find("```"))
                end = content.find("```", start + 1)
                eval_code = content[start + 1 : end]
                msg = get_message(eval_code)
                if msg:
                    out.write(f"{hashval}: {repr(msg)}\n")
            except Exception:
                pass
