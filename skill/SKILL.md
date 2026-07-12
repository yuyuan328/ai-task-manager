---
name: ai-task-manager
description: AI作业截止日/任务管理器 — 智能任务调度官，根据DDL优先级、历史完成速度、科目难度动态安排每日任务
version: 1.0.0
author: yuyuan328
tags: [learning, task-management, productivity, student]
triggers:
  - 今天该做什么
  - 帮我安排任务
  - 任务太多不知道先做什么
  - 赶ddl
  - 作业安排
---

# AI作业截止日/任务管理器

## 概述

AI任务调度官，不是简单列待办，而是根据 DDL 优先级、你的历史完成速度、科目难度，帮你智能安排今天最该先做什么。录入任务后持续跟踪完成情况，AI 动态调整后续安排。

## 核心功能

1. **任务录入** — 支持添加任务（名称、截止日、预计耗时、科目/类型、难度）
2. **智能排序** — AI 综合 DDL 紧迫度、预估耗时、历史完成速度、难度，给出今日优先级排序
3. **动态调整** — 完成任务后反馈实际耗时，AI 动态调整后续计划
4. **拖延预警** — 识别拖延模式，提前预警快到 DDL 的任务
5. **周报总结** — 每周分析任务完成情况，优化时间管理建议

## AI 核心价值

- 传统待办清单只罗列任务，AI 能**综合分析**多个维度给出最优执行顺序
- AI 根据你的**历史完成速度**预测真实耗时，避免低估任务时间
- AI **识别拖延模式**，针对性给出拆分建议
- 没有 AI 的语义理解和推理能力，这些功能根本无法实现

## 依赖要求

- Python 3.8+
- `openai` 库（兼容 DeepSeek API）
- DeepSeek API Key

## 安装

```bash
pip install openai
```

## 使用方式

```bash
# 交互模式
python scripts/task_manager.py

# 指定任务文件
python scripts/task_manager.py --task-file data/tasks.json
```

## 项目结构

```
├── SKILL.md                    # 本文件
├── scripts/
│   └── task_manager.py         # 主程序
├── references/
│   ├── config.example.json     # 配置文件示例
│   └── usage_guide.md          # 使用指南与最佳实践
```
