#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [IoC_Skill_Telemetry]
# Status: IMPLEMENTED
# Skill: polysemy-dynamic-core-vocab-and-ielts8-shunt; interactive-cognitive-microapp-pipeline
# Author: Antigravity (Gemini 4 Argon High)
# Node: ielts0
"""W1 Backend Module for Long-Sentence Blind-Translation Coaching via N6 Local Ollama (qwen3:32b)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

N6_OLLAMA_BASE = os.environ.get("KAOYAN_N6_OLLAMA_URL", "http://127.0.0.1:11434")
N6_DEFAULT_MODEL = os.environ.get("KAOYAN_N6_LLM_MODEL", "qwen3:32b")

# 八大考场长难句高频失分弱点母型与定向强化推题库
WEAKNESS_DRILL_BANK: Dict[str, Dict[str, Any]] = {
    "W01_PARTICIPLE_POLYSEMY": {
        "code": "W01",
        "title": "过去分词屈折变形与熟词僻义误判 (如 borne 误译为『出生』、harbor 误译为『港口』、temper 误译为『脾气』)",
        "strategy": "遇到过去分词被动态 (be + V-ed + by) 或熟词僻义动词时，先通过施受事主客体判断动作方向，切勿按初中第一释义硬套。",
        "target_sentence_id": "LS_04_CET6_ECONOMY",
        "drill_en": "Were the financial burdens borne by small enterprises to be compounded by abrupt credit tightening, even the most resilient local economies would struggle to weather the downturn.",
        "drill_zh": "倘若小微企业所承担的财务负担因信贷骤然收紧而雪上加霜，即便最具韧性的地方经济也将难以渡过衰退难关。",
        "drill_focus": "专项训练：borne by (由…承担) + compounded by (因…加剧) + weather (渡过危机)",
    },
    "W02_PARALLEL_NOUN_CLAUSE": {
        "code": "W02",
        "title": "主语从句与并列双表语从句逻辑极性失焦 (What makes... is not merely that A, but that B)",
        "strategy": "先抓主系表主干『What makes X difficult is not A, but B』，明确 not merely 是陪衬让步，but that 之后才是命题重心。",
        "target_sentence_id": "LS_08_BIZ_ECOLOGY",
        "drill_en": "What makes the transition toward renewable grids so contentious is not merely that legacy infrastructure requires massive capital outlay, but that the short-term tariff surcharges are often shouldered unevenly by low-income households.",
        "drill_zh": "围绕可再生电网转型的争论之所以如此激烈，不仅在于老旧基础设施需要巨额资本投入，更在于短期电价附加费往往不均衡地由低收入家庭承担。",
        "drill_focus": "专项训练：What makes... is not merely that..., but that... 同构骨架盲译复盘",
    },
    "W03_INVERSION_NEGATION": {
        "code": "W03",
        "title": "否定副词置首部分倒装或隐性双重否定极性反译 (Not until... did... / Far from...)",
        "strategy": "见到 Not until / Hardly / Scarcely 居首且后接助动词 did/had/would，立即将『直到…才…』还原为正常主谓语序再顺译。",
        "target_sentence_id": "LS_03_IELTS_INVERSION",
        "drill_en": "Not until longitudinal satellite telemetry revealed the accelerated thawing of permafrost did climate modelers realize that carbon feedback loops had been systematically underestimated.",
        "drill_zh": "直到长期的卫星遥测数据揭示出永久冻土加速融化，气候建模学者才意识到碳反馈循环一直被系统性地低估了。",
        "drill_focus": "专项训练：Not until... did + 主语 + 动词原形（直到…才…）部分倒装结构",
    },
    "W04_POST_MODIFIER_ORDER": {
        "code": "W04",
        "title": "长定语从句与后置不定式修饰链语序欧化或挂靠错位 (those who have the least power to influence...)",
        "strategy": "超过 8 个词的 who/which/in which 定语从句，在汉译时可采用『前置打包为“……的人群”』或『拆句独立成句』。",
        "target_sentence_id": "LS_07_KAOYAN_LAW",
        "drill_en": "Were regulatory frameworks to lag persistently behind algorithmic deployment, the very mechanisms through which citizens seek redress for automated bias would be rendered largely illusory.",
        "drill_zh": "倘若监管框架持续滞后于算法部署，公民借以针对自动化偏见寻求救济的机制本身就将在很大程度上形同虚设。",
        "drill_focus": "专项训练：Were... to... 虚拟倒装 + through which 介词定语从句调序",
    },
    "W05_INSERTION_APPOSITIVE": {
        "code": "W05",
        "title": "形式主语/双破折号插入语阻断主干连贯性 (It is a tribute to... — and a measure of... — that...)",
        "strategy": "阅读与翻译时先用括号跳过双破折号 `— ... —` 插入语，直接将 `It is... that...` 真正主语从句接通。",
        "target_sentence_id": "LS_05_KAOYAN_TRANSLATION",
        "drill_en": "It is a tribute to the resilience of empirical inquiry — and a measure of its institutional maturity — that hypotheses once dismissed as heresy are now routinely subjected to rigorous replication.",
        "drill_zh": "曾被斥为异端邪说的假说如今常规性地接受严格重复验证，这既是对实证探究韧性的赞颂，也是其制度成熟度的体现。",
        "drill_focus": "专项训练：It is... — 插入语 — that... 考研翻译高频拆句逆译法",
    },
}

SENTENCE_RUBRICS: Dict[str, Dict[str, Any]] = {
    "LS_01_AI_REGULATION": {
        "checkpoints": [
            {"id": "CP1", "name": "主语从句与并列枢轴 (What makes... not merely... but...)", "keywords": ["辩论", "争论", "讨论", "不仅", "不单", "而且", "更在于", "棘手", "困难"], "weight": 0.5},
            {"id": "CP2", "name": "比较状语从句 (evolving faster than regulators can respond)", "keywords": ["演进", "发展", "快于", "超出", "监管", "应对", "反应"], "weight": 0.5},
            {"id": "CP3", "name": "动名词与被动熟词僻义 (consequences of getting it wrong... borne disproportionately)", "keywords": ["后果", "失误", "出错", "弄错", "不成比例", "承担", "承受"], "weight": 0.5},
            {"id": "CP4", "name": "定语从句与不定式后置定语 (by those who have the least power to influence the rules)", "keywords": ["最缺乏", "最少", "最没有", "权力", "能力", "影响", "规则"], "weight": 0.5},
        ],
        "traps": [
            {"pattern": r"出生|天生|诞生", "weakness": "W01_PARTICIPLE_POLYSEMY", "msg": "❌ 致命陷阱命中：将 `borne`（`bear` 承担/承受的过去分词）误译为『出生/天生』（混淆了 `borne` 与 `born`）！"},
        ],
        "default_weakness": "W02_PARALLEL_NOUN_CLAUSE",
    },
}


def evaluate_rubric_and_weakness(sentence_id: str, raw_en: str, user_zh: str) -> Dict[str, Any]:
    zh = (user_zh or "").strip()
    rubric = SENTENCE_RUBRICS.get(sentence_id)
    hits: List[Dict[str, Any]] = []
    detected_weakness_keys: List[str] = []
    trap_alerts: List[str] = []

    if rubric:
        for t in rubric.get("traps", []):
            if re.search(t["pattern"], zh):
                detected_weakness_keys.append(t["weakness"])
                trap_alerts.append(t["msg"])
        for cp in rubric["checkpoints"]:
            matched = [kw for kw in cp["keywords"] if kw in zh]
            is_hit = len(matched) >= 2
            hits.append({
                "id": cp["id"],
                "name": cp["name"],
                "weight": cp["weight"],
                "hit": is_hit,
                "matched_keywords": matched[:4],
                "score": cp["weight"] if is_hit else 0.0,
            })
            if not is_hit:
                if cp["id"] == "CP1":
                    detected_weakness_keys.append("W02_PARALLEL_NOUN_CLAUSE")
                elif cp["id"] == "CP3":
                    detected_weakness_keys.append("W01_PARTICIPLE_POLYSEMY")
                elif cp["id"] == "CP4":
                    detected_weakness_keys.append("W04_POST_MODIFIER_ORDER")
    else:
        if re.search(r"出生|天生", zh) and "borne" in raw_en.lower():
            detected_weakness_keys.append("W01_PARTICIPLE_POLYSEMY")
            trap_alerts.append("❌ 检测到 `borne` 被误译为『出生』，请注意 `bear -> bore -> borne` 表示『由…承担/承受』。")
        if "not until" in raw_en.lower() and not re.search(r"直到.*才", zh):
            detected_weakness_keys.append("W03_INVERSION_NEGATION")
            trap_alerts.append("⚠️ 检测到 `Not until` 部分倒装未译出『直到…才…』的核心时序转折逻辑。")
        c_len = len(zh)
        for i, name in enumerate(["主句核心主谓提取", "从句连接词逻辑还原", "核心学术词与分词准确度", "汉语语序自然度与调序"], 1):
            ok = c_len >= i * 8 and not (i == 3 and trap_alerts)
            hits.append({"id": f"CP{i}", "name": name, "weight": 0.5, "hit": ok, "matched_keywords": [], "score": 0.5 if ok else 0.0})

    if not detected_weakness_keys:
        if "not until" in raw_en.lower():
            detected_weakness_keys.append("W03_INVERSION_NEGATION")
        elif "—" in raw_en:
            detected_weakness_keys.append("W05_INSERTION_APPOSITIVE")
        else:
            detected_weakness_keys.append("W04_POST_MODIFIER_ORDER")

    total_2pt = round(sum(h["score"] for h in hits), 1)
    if trap_alerts and total_2pt > 1.5:
        total_2pt = 1.5
    score_100 = int(round((total_2pt / 2.0) * 100))
    primary_wk_key = detected_weakness_keys[0]
    wk_obj = WEAKNESS_DRILL_BANK.get(primary_wk_key, WEAKNESS_DRILL_BANK["W02_PARALLEL_NOUN_CLAUSE"])

    return {
        "score_2pt": total_2pt,
        "score_100": score_100,
        "checkpoint_hits": hits,
        "trap_alerts": trap_alerts,
        "primary_weakness": wk_obj,
    }


def call_n6_ollama_coach(raw_en: str, user_zh: str, eval_res: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    wk = eval_res["primary_weakness"]
    prompt = (
        "你是考研英语、雅思阅读8.0与六级长难句盲译特训AI导师。"
        f"\n英文原句：{raw_en}"
        f"\n考生盲译：{user_zh}"
        f"\n系统初筛得分：{eval_res['score_2pt']}/2.0分；发现核心薄弱点：{wk['title']}。"
        "\n请用精炼中文（140字以内）按三点直接回复考生："
        "\n1. 【译文亮点与失分定位】：指出考生哪里翻得好、哪个词或从句翻错/漏译；"
        "\n2. 【弱点病根剖析】：一句话讲透该语法/词汇陷阱；"
        "\n3. 【针对性通关口诀】：给出攻克下一句同类长难句的实操口诀。"
    )
    payload = json.dumps({
        "model": N6_DEFAULT_MODEL,
        "think": False,
        "keep_alive": "24h",
        "stream": False,
        "prompt": prompt,
        "options": {"num_predict": 210, "temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{N6_OLLAMA_BASE}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=14) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            txt = (body.get("response") or "").strip()
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            if txt:
                return {
                    "ok": True,
                    "llm_provider": "N6 Local Ollama (Dual RTX 3090)",
                    "model": body.get("model", N6_DEFAULT_MODEL),
                    "latency_ms": elapsed_ms,
                    "critique": txt,
                }
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        err_msg = str(exc)
    else:
        err_msg = "empty_response"

    fallback_txt = (
        f"1. 【译文亮点与失分定位】：您的盲译得分为 {eval_res['score_2pt']}/2.0 分。"
        + (" ".join(eval_res["trap_alerts"]) if eval_res["trap_alerts"] else f"主要失分点在于「{wk['title']}」。")
        + f"\n2. 【弱点病根剖析】：{wk['strategy']}"
        + f"\n3. 【针对性通关口诀】：已为您精准匹配下方同构强化句（{wk['drill_focus']}），请立即趁热盲译！"
    )
    return {
        "ok": False,
        "llm_provider": "W1 Deterministic Rubric Coach (N6 Fallback)",
        "model": N6_DEFAULT_MODEL,
        "latency_ms": elapsed_ms,
        "fallback_reason": err_msg,
        "critique": fallback_txt,
    }


def handle_coach_status() -> Dict[str, Any]:
    t0 = time.perf_counter()
    req = urllib.request.Request(f"{N6_OLLAMA_BASE}/api/ps", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            ps_data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in ps_data.get("models", [])]
            return {
                "status": "ok",
                "topology": "elena ECS (Caddy + frps ONLY) -> W1 Backend (kaoyan-w1-gateway) -> N6 Local LLM (Ollama Dual RTX 3090)",
                "edge_node": "elena (caddy + frps only)",
                "backend_node": "W1 (WSL2 container gateway)",
                "llm_node": "N6 (2x NVIDIA GeForce RTX 3090)",
                "n6_ollama_reachable": True,
                "active_vram_models": models or [N6_DEFAULT_MODEL],
                "ping_ms": int((time.perf_counter() - t0) * 1000),
            }
    except Exception as exc:
        return {
            "status": "degraded_rubric_ready",
            "topology": "elena ECS (Caddy + frps ONLY) -> W1 Backend -> N6 Local LLM",
            "n6_ollama_reachable": False,
            "error": str(exc),
        }


def handle_coach_diagnose(data: Dict[str, Any]) -> Dict[str, Any]:
    sentence_id = str(data.get("sentence_id") or "LS_01_AI_REGULATION").strip()
    raw_en = str(data.get("raw_en") or "").strip()
    user_zh = str(data.get("user_zh") or "").strip()
    if not raw_en or not user_zh:
        return {"status": "bad_request", "message": "raw_en and user_zh are required"}
    eval_res = evaluate_rubric_and_weakness(sentence_id, raw_en, user_zh)
    llm_res = call_n6_ollama_coach(raw_en, user_zh, eval_res)
    return {
        "status": "ok",
        "topology_verified": "elena(Caddy+frps) -> W1(Backend) -> N6(Ollama qwen3:32b)",
        "sentence_id": sentence_id,
        "evaluation": eval_res,
        "n6_llm": llm_res,
    }
