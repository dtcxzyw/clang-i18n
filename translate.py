# SPDX-License-Identifier: MIT License
# Copyright (c) 2025 Yingwei Zheng
# This file is licensed under the MIT License.
# See the LICENSE file for more information.

import hashlib


def compute_hash(str: str):
    return hashlib.sha1(str.encode("utf-8")).digest().hex()[:12].upper()
