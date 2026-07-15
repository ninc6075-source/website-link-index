from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOMAIN_FILE = ROOT / "domains.txt"
OUTPUT_DIR = ROOT / "posts"
INDEX_FILE = ROOT / "README.md"

# 每篇放多少个域名
BATCH_SIZE = 12


TITLES = [
    "公开网站入口整理",
    "第三方链接维护记录",
    "网站访问核验清单",
    "域名资源分批归档",
    "公开链接更新日志",
    "网站巡检任务记录",
    "第三方站点导航目录",
    "网站链接整理档案",
    "域名入口检查计划",
    "公开网站索引记录",
]


INTRODUCTIONS = [
    "本页用于整理一批第三方网站入口，方便后续访问、核验和维护。",
    "以下链接仅作为网站地址索引，不代表推荐、合作或内容来源关系。",
    "本页记录待复核的网站地址，实际状态应以人工访问结果为准。",
    "以下内容属于第三方链接归档，不对网站内容和安全性作保证。",
    "本页面用于分批维护公开网站入口，不构成任何形式的认证或背书。",
]


DISCLAIMERS = [
    "第三方网站内容可能随时变化，请访问者自行判断。",
    "未经实际核验，不应将这些网站描述为官方、权威或安全站点。",
    "遇到异常跳转、自动下载或信息提交要求时，请谨慎操作。",
    "网站被收录仅表示地址已进入整理列表，不代表内容得到认可。",
]


def load_domains() -> list[str]:
    if not DOMAIN_FILE.exists():
        raise FileNotFoundError("找不到 domains.txt")

    domains = []

    for line in DOMAIN_FILE.read_text(encoding="utf-8").splitlines():
        domain = line.strip()

        if not domain or domain.startswith("#"):
            continue

        domains.append(domain)

    # 去除重复域名，同时保持原顺序
    return list(dict.fromkeys(domains))


def make_seed(date_text: str) -> int:
    value = hashlib.sha256(date_text.encode("utf-8")).hexdigest()
    return int(value[:16], 16)


def select_domains(
    domains: list[str],
    seed: int,
) -> list[str]:
    rng = random.Random(seed)
    copied = domains.copy()
    rng.shuffle(copied)

    return copied[: min(BATCH_SIZE, len(copied))]


def numbered_template(domains: list[str]) -> str:
    lines = [
        "## 网站入口",
        "",
    ]

    for index, domain in enumerate(domains, start=1):
        lines.append(f"{index}. [{domain}](https://{domain})")

    return "\n".join(lines)


def checklist_template(domains: list[str]) -> str:
    lines = [
        "## 待核验网站",
        "",
    ]

    for domain in domains:
        lines.append(f"- [ ] [{domain}](https://{domain})")

    return "\n".join(lines)


def table_template(domains: list[str]) -> str:
    lines = [
        "## 网站检查表",
        "",
        "| 序号 | 网站 | 当前状态 |",
        "|---:|---|---|",
    ]

    for index, domain in enumerate(domains, start=1):
        lines.append(
            f"| {index} | [{domain}](https://{domain}) | 待核验 |"
        )

    return "\n".join(lines)


def suffix_template(domains: list[str]) -> str:
    groups: dict[str, list[str]] = {}

    for domain in domains:
        suffix = "." + domain.rsplit(".", 1)[-1]
        groups.setdefault(suffix, []).append(domain)

    lines = [
        "## 按域名后缀分类",
        "",
    ]

    for suffix in sorted(groups):
        lines.append(f"### `{suffix}`")
        lines.append("")

        for domain in groups[suffix]:
            lines.append(f"- [{domain}](https://{domain})")

        lines.append("")

    return "\n".join(lines).rstrip()


def details_template(domains: list[str]) -> str:
    midpoint = max(1, len(domains) // 2)
    groups = [
        domains[:midpoint],
        domains[midpoint:],
    ]

    lines = [
        "## 折叠式网站目录",
        "",
    ]

    for index, group in enumerate(groups, start=1):
        if not group:
            continue

        lines.extend(
            [
                "<details>",
                f"<summary>第 {index} 组网站</summary>",
                "",
            ]
        )

        for domain in group:
            lines.append(f"- [{domain}](https://{domain})")

        lines.extend(
            [
                "",
                "</details>",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def cards_template(domains: list[str]) -> str:
    lines = [
        "## 域名记录卡",
        "",
    ]

    for domain in domains:
        suffix = "." + domain.rsplit(".", 1)[-1]

        lines.extend(
            [
                f"### {domain}",
                "",
                f"- 访问地址：[{domain}](https://{domain})",
                f"- 域名后缀：`{suffix}`",
                "- 当前状态：待核验",
                "- 检查日期：待填写",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def update_index(post_name: str, title: str, date_text: str) -> None:
    marker_start = "<!-- AUTO-POSTS-START -->"
    marker_end = "<!-- AUTO-POSTS-END -->"

    if INDEX_FILE.exists():
        current = INDEX_FILE.read_text(encoding="utf-8")
    else:
        current = "# 网站链接整理记录\n"

    if marker_start not in current or marker_end not in current:
        current = (
            current.rstrip()
            + "\n\n"
            + marker_start
            + "\n"
            + marker_end
            + "\n"
        )

    before, remaining = current.split(marker_start, 1)
    _, after = remaining.split(marker_end, 1)

    old_section = remaining.split(marker_end, 1)[0].strip()

    new_entry = f"- [{date_text} · {title}](posts/{post_name})"

    entries = [
        line
        for line in old_section.splitlines()
        if line.strip()
    ]

    if new_entry not in entries:
        entries.insert(0, new_entry)

    new_section = "\n".join(entries)

    updated = (
        before.rstrip()
        + "\n\n"
        + marker_start
        + "\n"
        + new_section
        + "\n"
        + marker_end
        + after
    )

    INDEX_FILE.write_text(updated, encoding="utf-8")


def main() -> None:
    now = datetime.now(timezone.utc)
    date_text = now.strftime("%Y-%m-%d")
    seed = make_seed(date_text)

    all_domains = load_domains()

    if not all_domains:
        raise ValueError("domains.txt 中没有有效域名")

    selected = select_domains(all_domains, seed)

    templates = [
        numbered_template,
        checklist_template,
        table_template,
        suffix_template,
        details_template,
        cards_template,
    ]

    template_function = templates[seed % len(templates)]
    title = TITLES[seed % len(TITLES)]
    introduction = INTRODUCTIONS[
        (seed // len(TITLES)) % len(INTRODUCTIONS)
    ]
    disclaimer = DISCLAIMERS[
        (seed // len(INTRODUCTIONS)) % len(DISCLAIMERS)
    ]

    body = template_function(selected)

    content = f"""# {title}：{date_text}

> {introduction}  
> {disclaimer}

- 发布日期：{date_text}
- 本批数量：{len(selected)}
- 页面状态：待复核
- 生成方式：GitHub Actions 自动生成

{body}

## 维护说明

- 所列链接仅用于导航、检查和归档。
- 未完成实际检查前，应保留“待核验”状态。
- 不应把无关网站标注为新闻来源或合作网站。
- 网站状态可能随时间发生变化。

## 免责声明

本页面不构成推荐、认证、内容背书或安全保证。
"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    post_name = f"{date_text}.md"
    output_file = OUTPUT_DIR / post_name

    if output_file.exists():
        print(f"{post_name} 已存在，本次跳过。")
        return

    output_file.write_text(content, encoding="utf-8")
    update_index(post_name, title, date_text)

    print(f"已生成：{output_file}")
    print("README.md 已更新")


if __name__ == "__main__":
    main()
