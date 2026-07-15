from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOMAIN_FILE = ROOT / "domains.txt"
OUTPUT_DIR = ROOT / "posts"
INDEX_FILE = ROOT / "README.md"

# 每篇收录多少个域名
DOMAINS_PER_POST = 12

# 每天生成多少篇
POSTS_PER_DAY = 100


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
    "链接维护工作清单",
    "网站地址分组目录",
    "第三方链接归档记录",
    "站点入口复核任务",
    "网站资源维护日志",
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

    domains: list[str] = []

    for line in DOMAIN_FILE.read_text(encoding="utf-8").splitlines():
        domain = line.strip()

        if not domain or domain.startswith("#"):
            continue

        domains.append(domain)

    # 去重并保持原顺序
    return list(dict.fromkeys(domains))


def make_seed(date_text: str, post_number: int) -> int:
    source = f"{date_text}-{post_number}"
    value = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return int(value[:16], 16)


def select_domains(
    domains: list[str],
    seed: int,
    count: int,
) -> list[str]:
    rng = random.Random(seed)
    copied = domains.copy()
    rng.shuffle(copied)
    return copied[: min(count, len(copied))]


def numbered_template(domains: list[str]) -> str:
    lines = ["## 网站入口", ""]

    for index, domain in enumerate(domains, start=1):
        lines.append(f"{index}. [{domain}](https://{domain})")

    return "\n".join(lines)


def checklist_template(domains: list[str]) -> str:
    lines = ["## 待核验网站", ""]

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

    lines = ["## 按域名后缀分类", ""]

    for suffix in sorted(groups):
        lines.extend([f"### `{suffix}`", ""])

        for domain in groups[suffix]:
            lines.append(f"- [{domain}](https://{domain})")

        lines.append("")

    return "\n".join(lines).rstrip()


def details_template(domains: list[str]) -> str:
    group_size = max(1, len(domains) // 3)
    groups = [
        domains[:group_size],
        domains[group_size : group_size * 2],
        domains[group_size * 2 :],
    ]

    lines = ["## 折叠式网站目录", ""]

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

        lines.extend(["", "</details>", ""])

    return "\n".join(lines).rstrip()


def cards_template(domains: list[str]) -> str:
    lines = ["## 域名记录卡", ""]

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


TEMPLATES = [
    numbered_template,
    checklist_template,
    table_template,
    suffix_template,
    details_template,
    cards_template,
]


def update_index(entries_to_add: list[str]) -> None:
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
    old_section, after = remaining.split(marker_end, 1)

    old_entries = [
        line
        for line in old_section.strip().splitlines()
        if line.strip()
    ]

    for entry in reversed(entries_to_add):
        if entry not in old_entries:
            old_entries.insert(0, entry)

    updated = (
        before.rstrip()
        + "\n\n"
        + marker_start
        + "\n"
        + "\n".join(old_entries)
        + "\n"
        + marker_end
        + after
    )

    INDEX_FILE.write_text(updated, encoding="utf-8")


def build_post(
    date_text: str,
    post_number: int,
    all_domains: list[str],
) -> tuple[str, str] | None:
    seed = make_seed(date_text, post_number)
    selected = select_domains(
        all_domains,
        seed,
        DOMAINS_PER_POST,
    )

    title = TITLES[seed % len(TITLES)]
    introduction = INTRODUCTIONS[
        (seed // len(TITLES)) % len(INTRODUCTIONS)
    ]
    disclaimer = DISCLAIMERS[
        (seed // len(INTRODUCTIONS)) % len(DISCLAIMERS)
    ]
    template_function = TEMPLATES[seed % len(TEMPLATES)]

    post_code = f"{post_number:02d}"
    post_name = f"{date_text}-{post_code}.md"
    output_file = OUTPUT_DIR / post_name

    if output_file.exists():
        print(f"{post_name} 已存在，跳过。")
        return None

    body = template_function(selected)

    content = f"""# {title}：{date_text} 第 {post_number} 篇

> {introduction}  
> {disclaimer}

- 发布日期：{date_text}
- 当日编号：{post_code}
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

    output_file.write_text(content, encoding="utf-8")

    index_entry = (
        f"- [{date_text} 第 {post_number} 篇 · {title}]"
        f"(posts/{post_name})"
    )

    print(f"已生成：{output_file}")
    return post_name, index_entry


def main() -> None:
    now = datetime.now(timezone.utc)
    date_text = now.strftime("%Y-%m-%d")

    all_domains = load_domains()

    if not all_domains:
        raise ValueError("domains.txt 中没有有效域名")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index_entries: list[str] = []
    generated_count = 0

    for post_number in range(1, POSTS_PER_DAY + 1):
        result = build_post(
            date_text,
            post_number,
            all_domains,
        )

        if result is None:
            continue

        _, index_entry = result
        index_entries.append(index_entry)
        generated_count += 1

    if index_entries:
        update_index(index_entries)

    print(f"本次共生成 {generated_count} 篇。")


if __name__ == "__main__":
    main()
