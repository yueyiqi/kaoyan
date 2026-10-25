#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_kaoyanPeerBenchmarkUxV2_竞品对标与前端优化.py
Rule XXII 同基名伴生编译脚本：调用 kaoyan_english_benchmark_ux_v2_shunt_engine.py 生成 v2 对标报告 JSON。
"""

from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINE_PATH = ROOT / "scripts/3_governance_治理门禁/shunt/kaoyan_english_benchmark_ux_v2_shunt_engine.py"


def main() -> None:
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("kaoyan_v2_engine", ENGINE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.export_v2_report(here / "kaoyan_english_web_v2_benchmark_report.json")


if __name__ == "__main__":
    main()
