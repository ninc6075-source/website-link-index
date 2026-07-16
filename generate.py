from __future__ import annotations

import hashlib
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
DOMAIN_FILE = ROOT / "domains.txt"
CONFIG_FILE = ROOT / "config.json"
POSTS_DIR = ROOT / "posts"
DAILY_LINKS_DIR = ROOT / "daily-links"
LATEST_LINKS_FILE = ROOT / "latest-links.txt"
README_FILE = ROOT / "README.md"


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
    "公开域名整理清单",
    "链接状态检查档案",
    "网站入口维护计划",
    "第三方地址核验记录",
    "站点资源归档目录",
]


INTRODUCTIONS = [
    "本页用于整理一批第三方网站入口，方便后续访问、核验和维护。",
    "以下链接仅作为网站地址索引，不代表推荐、合作或内容来源关系。",
    "本页记录待复核的网站地址，实际状态应以人工访问结果为准。",
    "以下内容属于第三方链接归档，不对网站内容和安全性作保证。",
    "本页面用于分批维护公开网站入口，不构成认证或内容背书。",
]


DISCLAIMERS = [
    "第三方网站内容可能随时变化，请访问者自行判断。",
    "未经实际核验，不应将这些网站描述为官方、权威或安全站点。",
    "遇到异常跳转、自动下载或信息提交要求时，请谨慎操作。",
    "网站被收录仅表示地址已进入整理列表，不代表内容得到认可。",
]


def load_config() -> dict:
    default = {
        "posts_per_day": 20,
        "domains_per_post": 6,
        "timezone": "Asia/Shanghai",
    }

    if not CONFIG_FILE.exists():
        return default

    loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    default.update(loaded)
    return default


def normalize_domain(value: str) -> str:
    value = value.strip()

    if not value or value.startswith("#"):
        return ""

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    domain = parsed.netloc or parsed.path
    domain = domain.strip().strip("/").lower()

    if "@" in domain:
        domain = domain.rsplit("@", 1)[-1]

    if ":" in domain:
        domain = domain.split(":", 1)[0]

    if not re.fullmatch(r"[a-z0-9.-]+", domain):
        return ""

    return domain


def load_domains() -> list[str]:
    if not DOMAIN_FILE.exists():
        raise FileNotFoundError("找不到 domains.txt")

    domains: list[str] = []

    for line in DOMAIN_FILE.read_text(encoding="utf-8").splitlines():
        domain = normalize_domain(line)

        if domain:
            domains.append(domain)

    return list(dict.fromkeys(domains))


def make_seed(*parts: object) -> int:
    source = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


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
    split_point = max(1, len(domains) // 2)
    groups = [domains[:split_point], domains[split_point:]]
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


def repository_context() -> tuple[str, str, str]:
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get(
        "GITHUB_REPOSITORY",
        "YOUR_ACCOUNT/YOUR_REPOSITORY",
    )

    ref_name = os.environ.get("GITHUB_REF_NAME", "main")

    return server_url.rstrip("/"), repository, ref_name


def build_post_url(post_path: str) -> str:
    server_url, repository, ref_name = repository_context()
    return (
        f"{server_url}/{repository}/blob/"
        f"{ref_name}/{post_path}"
    )


def update_readme(entries: list[str], date_text: str) -> None:
    marker_start = "<!-- AUTO-POSTS-START -->"
    marker_end = "<!-- AUTO-POSTS-END -->"

    if README_FILE.exists():
        current = README_FILE.read_text(encoding="utf-8")
    else:
        current = "# 网站链接整理记录\n"

    if marker_start not in current or marker_end not in current:
        current = (
            current.rstrip()
            + "\n\n## 自动发布记录\n\n"
            + marker_start
            + "\n"
            + marker_end
            + "\n"
        )

    before, remaining = current.split(marker_start, 1)
    old_section, after = remaining.split(marker_end, 1)

    old_lines = [
        line
        for line in old_section.strip().splitlines()
        if line.strip()
    ]

    date_heading = f"### {date_text}"

    filtered_lines: list[str] = []
    skip_date_section = False

    for line in old_lines:
        if line.startswith("### "):
            skip_date_section = line == date_heading

            if skip_date_section:
                continue

        if skip_date_section:
            continue

        filtered_lines.append(line)

    new_section_lines = [date_heading, "", *entries, ""]

    if filtered_lines:
        new_section_lines.extend(filtered_lines)

    updated = (
        before.rstrip()
        + "\n\n"
        + marker_start
        + "\n"
        + "\n".join(new_section_lines).rstrip()
        + "\n"
        + marker_end
        + after
    )

    README_FILE.write_text(updated, encoding="utf-8")


def write_link_collections(
    date_text: str,
    post_records: list[dict[str, str]],
) -> None:
    DAILY_LINKS_DIR.mkdir(parents=True, exist_ok=True)

    urls = [record["url"] for record in post_records]
    plain_text = "\n".join(urls) + "\n"

    daily_txt = DAILY_LINKS_DIR / f"{date_text}.txt"
    daily_txt.write_text(plain_text, encoding="utf-8")

    LATEST_LINKS_FILE.write_text(plain_text, encoding="utf-8")

    markdown_lines = [
        f"# {date_text} 自动发布链接汇总",
        "",
        f"> 当天共生成 {len(post_records)} 篇。",
        "",
        "## 一键复制",
        "",
        "```text",
        *urls,
        "```",
        "",
        "## 可点击链接",
        "",
    ]

    for index, record in enumerate(post_records, start=1):
        markdown_lines.append(
            f"{index}. [{record['title']}]({record['url']})"
        )

    markdown_lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 本页由 GitHub Actions 自动生成。",
            "- `latest-links.txt` 始终保存最近一次生成的链接。",
            "",
        ]
    )

    daily_md = DAILY_LINKS_DIR / f"{date_text}.md"
    daily_md.write_text(
        "\n".join(markdown_lines),
        encoding="utf-8",
    )


def select_post_domains(
    all_domains: list[str],
    date_text: str,
    post_number: int,
    count: int,
) -> list[str]:
    seed = make_seed(date_text, post_number, "domains")
    rng = random.Random(seed)
    copied = all_domains.copy()
    rng.shuffle(copied)

    return copied[:count]


def main() -> None:
    config = load_config()

    posts_per_day = int(config["posts_per_day"])
    domains_per_post = int(config["domains_per_post"])
    timezone_name = str(config["timezone"])

    if posts_per_day < 1:
        raise ValueError("posts_per_day 必须大于0")

    if domains_per_post < 1:
        raise ValueError("domains_per_post 必须大于0")

    all_domains = load_domains()

    if len(all_domains) < domains_per_post:
        raise ValueError(
            f"至少需要 {domains_per_post} 个不同域名，"
            f"当前只有 {len(all_domains)} 个。"
        )

    now = datetime.now(ZoneInfo(timezone_name))
    date_text = now.strftime("%Y-%m-%d")

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    post_records: list[dict[str, str]] = []
    readme_entries: list[str] = []

    for post_number in range(1, posts_per_day + 1):
        seed = make_seed(date_text, post_number)

        title = TITLES[seed % len(TITLES)]
        introduction = INTRODUCTIONS[
            (seed // len(TITLES)) % len(INTRODUCTIONS)
        ]
        disclaimer = DISCLAIMERS[
            (seed // len(INTRODUCTIONS)) % len(DISCLAIMERS)
        ]
        template_function = TEMPLATES[
            seed % len(TEMPLATES)
        ]

        selected = select_post_domains(
            all_domains,
            date_text,
            post_number,
            domains_per_post,
        )

        post_code = f"{post_number:02d}"
        post_name = f"{date_text}-{post_code}.md"
        post_path = f"posts/{post_name}"
        output_file = POSTS_DIR / post_name

        display_title = (
            f"{title}：{date_text} 第 {post_number} 篇"
        )

        body = template_function(selected)

        content = f"""# {display_title}

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

        post_url = build_post_url(post_path)

        post_records.append(
            {
                "title": display_title,
                "path": post_path,
                "url": post_url,
            }
        )

        readme_entries.append(
            f"- [{display_title}]({post_path})"
        )

        print(f"已生成：{post_path}")

    write_link_collections(date_text, post_records)
    update_readme(readme_entries, date_text)

    print(f"本次共生成 {len(post_records)} 篇。")
    print(f"链接汇总：daily-links/{date_text}.txt")
    print("最近链接：latest-links.txt")


if __name__ == "__main__":
    main()
