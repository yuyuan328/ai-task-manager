"""
AI作业截止日/任务管理器
基于 DeepSeek API 的智能任务调度系统
"""

import json
import os
import sys
import argparse
from datetime import datetime, date
from openai import OpenAI

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "api_key": "your-ai-apikey",   # 填写自己的api key
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "task_file": "data/tasks.json",
    "history_file": "data/history.json",
    "max_tokens": 2000,
    "temperature": 0.7,
}

client = OpenAI(api_key=CONFIG["api_key"], base_url=CONFIG["base_url"])

# ============================================================
# 数据管理
# ============================================================

def load_json(path, default):
    """加载 JSON 文件，不存在则返回默认值"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tasks():
    return load_json(CONFIG["task_file"], [])


def save_tasks(tasks):
    save_json(CONFIG["task_file"], tasks)


def load_history():
    return load_json(CONFIG["history_file"], [])


def save_history(history):
    save_json(CONFIG["history_file"], history)


# ============================================================
# AI 调用
# ============================================================

def ask_ai(system_prompt, user_message):
    """调用 DeepSeek API"""
    try:
        resp = client.chat.completions.create(
            model=CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=CONFIG["temperature"],
            max_tokens=CONFIG["max_tokens"],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[AI 调用失败] {e}"


# ============================================================
# 核心功能
# ============================================================

def add_task():
    """添加新任务"""
    print("\n=== 添加新任务 ===")
    name = input("任务名称: ").strip()
    if not name:
        print("任务名称不能为空！")
        return

    ddl = input("截止日期 (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(ddl, "%Y-%m-%d")
    except ValueError:
        print("日期格式错误！")
        return

    try:
        estimated_hours = float(input("预计耗时(小时): ").strip())
    except ValueError:
        print("请输入数字！")
        return

    subject = input("科目/类型: ").strip()
    try:
        difficulty = int(input("难度 (1-5): ").strip())
        difficulty = max(1, min(5, difficulty))
    except ValueError:
        difficulty = 3

    tasks = load_tasks()
    tasks.append({
        "id": len(tasks) + 1,
        "name": name,
        "ddl": ddl,
        "estimated_hours": estimated_hours,
        "subject": subject,
        "difficulty": difficulty,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "actual_hours": None,
        "completed_at": None,
    })
    save_tasks(tasks)
    print(f"✅ 任务「{name}」已添加！")


def view_tasks():
    """查看所有任务"""
    tasks = load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    done = [t for t in tasks if t["status"] == "done"]

    print("\n=== 📋 待完成任务 ===")
    if not pending:
        print("  (暂无待完成任务)")
    else:
        for t in pending:
            days_left = (datetime.strptime(t["ddl"], "%Y-%m-%d").date() - date.today()).days
            flag = "🔴" if days_left <= 1 else ("🟡" if days_left <= 3 else "🟢")
            print(f"  [{t['id']}] {flag} {t['name']} | DDL: {t['ddl']} ({days_left}天后) | {t['subject']} | 预计{t['estimated_hours']}h | 难度{t['difficulty']}/5")

    print("\n=== ✅ 已完成任务 ===")
    if not done:
        print("  (暂无已完成任务)")
    else:
        for t in done[-5:]:
            print(f"  [{t['id']}] {t['name']} | 实际耗时: {t.get('actual_hours', '?')}h | 完成于: {t.get('completed_at', '?')}")


def ai_sort():
    """AI 智能排序"""
    tasks = load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        print("\n🎉 没有待完成任务！")
        return

    history = load_history()
    today = date.today().isoformat()

    # 构建任务描述
    task_desc = "\n".join([
        f"- ID:{t['id']} | {t['name']} | DDL:{t['ddl']} | 预计:{t['estimated_hours']}h | {t['subject']} | 难度:{t['difficulty']}/5"
        for t in pending
    ])

    # 构建历史数据摘要
    history_summary = ""
    if history:
        # 计算平均完成速度偏差
        deviations = [h.get("deviation", 0) for h in history if "deviation" in h]
        avg_dev = sum(deviations) / len(deviations) if deviations else 0
        history_summary = f"\n历史数据：你平均实际耗时比预估{'多' if avg_dev > 0 else '少'}{abs(avg_dev):.1f}小时。"
        # 找出容易拖延的任务类型
        subj_delays = {}
        for h in history:
            subj = h.get("subject", "")
            if subj and h.get("deviation", 0) > 0.5:
                subj_delays[subj] = subj_delays.get(subj, 0) + 1
        if subj_delays:
            worst = max(subj_delays, key=subj_delays.get)
            history_summary += f" 你最容易拖延「{worst}」类任务。"

    system_prompt = """你是一个智能任务调度助手。根据任务信息和用户历史数据，给出今日最优执行顺序。
要求：
1. 综合 DDL 紧迫度、难度、预计耗时、历史拖延模式排序
2. 给出排序理由（简明扼要）
3. 对每个任务给出执行建议（如：什么时间段做、是否需要拆分）
4. 识别可能被拖延的任务并给出预警
返回格式保持简洁，用中文。"""

    user_msg = f"""今天是 {today}，请帮我安排以下任务的执行顺序：

{task_desc}
{history_summary}

请给出：
1. 推荐执行顺序（从高到低）
2. 每个任务的执行建议
3. 拖延预警"""

    print("\n🤖 AI 正在分析任务...\n")
    result = ask_ai(system_prompt, user_msg)
    print(result)


def complete_task():
    """标记任务完成"""
    tasks = load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        print("\n没有待完成的任务！")
        return

    view_tasks()
    try:
        tid = int(input("\n请输入完成的任务 ID: ").strip())
    except ValueError:
        print("请输入数字！")
        return

    task = next((t for t in tasks if t["id"] == tid and t["status"] == "pending"), None)
    if not task:
        print("未找到该任务或任务已完成！")
        return

    try:
        actual = float(input(f"实际耗时(小时) [预估{task['estimated_hours']}h]: ").strip() or task["estimated_hours"])
    except ValueError:
        actual = task["estimated_hours"]

    task["status"] = "done"
    task["actual_hours"] = actual
    task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_tasks(tasks)

    # 记录到历史
    history = load_history()
    deviation = actual - task["estimated_hours"]
    history.append({
        "task_id": tid,
        "name": task["name"],
        "subject": task["subject"],
        "difficulty": task["difficulty"],
        "estimated_hours": task["estimated_hours"],
        "actual_hours": actual,
        "deviation": round(deviation, 2),
        "completed_at": task["completed_at"],
    })
    save_history(history)

    print(f"✅ 任务「{task['name']}」已完成！实际耗时 {actual}h，偏差 {deviation:+.1f}h")


def ddl_warning():
    """DDL 预警"""
    tasks = load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    if not pending:
        print("\n🎉 没有待完成任务！")
        return

    urgent = []
    for t in pending:
        days = (datetime.strptime(t["ddl"], "%Y-%m-%d").date() - date.today()).days
        if days <= 3:
            urgent.append((t, days))

    if not urgent:
        print("\n✅ 暂无紧急任务，所有任务 DDL 都在 3 天以上。")
        return

    print("\n=== 🚨 DDL 预警 ===")
    task_desc = "\n".join([
        f"- {t['name']} | DDL:{t['ddl']} ({d}天后!) | 预计{t['estimated_hours']}h | 难度{t['difficulty']}/5"
        for t, d in urgent
    ])

    system_prompt = "你是任务管理专家。用户有即将到期的任务，请给出紧急应对建议。简明扼要。"
    user_msg = f"以下任务即将到期：\n{task_desc}\n\n请给出应对建议：哪些必须今天做？哪些可以拆分？时间怎么分配？"

    print(task_desc)
    print("\n🤖 AI 紧急应对建议：\n")
    result = ask_ai(system_prompt, user_msg)
    print(result)


def weekly_report():
    """周报总结"""
    history = load_history()
    tasks = load_tasks()

    if not history:
        print("\n还没有完成过任何任务，无法生成周报。")
        return

    # 筛选本周完成的任务
    today = date.today()
    week_ago = (today - __import__("datetime").timedelta(days=7)).isoformat()
    this_week = [h for h in history if h.get("completed_at", "")[:10] >= week_ago]

    if not this_week:
        print("\n本周还没有完成任务。")
        return

    pending_count = len([t for t in tasks if t["status"] == "pending"])

    report_data = f"""本周完成任务: {len(this_week)}个
待完成任务: {pending_count}个
详情:
""" + "\n".join([
        f"- {h['name']}({h['subject']}): 预估{h['estimated_hours']}h → 实际{h['actual_hours']}h (偏差{h['deviation']:+.1f}h)"
        for h in this_week
    ])

    system_prompt = """你是时间管理教练。根据用户本周任务数据，做简洁的周报分析：
1. 总体评价（1句话）
2. 时间估算准确度分析
3. 什么类型任务效率高/低
4. 下周改进建议（1-2条具体可操作建议）"""

    print("\n🤖 AI 周报分析中...\n")
    result = ask_ai(system_prompt, report_data)
    print(result)


# ============================================================
# 主菜单
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="AI作业截止日/任务管理器")
    parser.add_argument("--task-file", help="任务文件路径")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()

    if args.task_file:
        CONFIG["task_file"] = args.task_file

    # 加载外部配置
    config_path = args.config or "references/config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            ext_config = json.load(f)
            CONFIG.update(ext_config)

    # 更新 client（如果配置变了）
    global client
    client = OpenAI(api_key=CONFIG["api_key"], base_url=CONFIG["base_url"])

    menu = """
╔══════════════════════════════════╗
║   🤖 AI 作业截止日/任务管理器   ║
╠══════════════════════════════════╣
║  1. 添加任务                     ║
║  2. 查看所有任务                 ║
║  3. AI 智能排序                  ║
║  4. 标记完成任务                 ║
║  5. DDL 预警                     ║
║  6. 周报总结                     ║
║  7. 退出                         ║
╚══════════════════════════════════╝"""

    while True:
        print(menu)
        choice = input("请选择 (1-7): ").strip()

        if choice == "1":
            add_task()
        elif choice == "2":
            view_tasks()
        elif choice == "3":
            ai_sort()
        elif choice == "4":
            complete_task()
        elif choice == "5":
            ddl_warning()
        elif choice == "6":
            weekly_report()
        elif choice == "7":
            print("\n👋 再见！记得按时完成任务哦~")
            break
        else:
            print("无效选择，请重新输入！")

        input("\n按回车键继续...")


if __name__ == "__main__":
    main()
