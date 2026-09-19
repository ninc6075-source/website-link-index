from __future__ import annotations

import hashlib
import json
import os
import random
import re
from collections import Counter
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


TITLE_BASES = [
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
    "网络资源访问记录",
    "网站入口分组记录",
    "域名访问核验记录",
    "公开站点维护索引",
    "网站资源检查记录",
    "网络地址整理记录",
    "公开入口更新记录",
    "站点地址维护清单",
    "第三方域名整理记录",
    "网站资源复核目录",
    "站点访问状态记录",
    "域名入口巡检记录",
    "公开链接分类记录",
    "网络入口维护档案",
    "第三方网站检查目录",
    "网站入口批次记录",
    "域名访问整理清单",
    "公开站点复核记录",
    "网站资源分组索引",
    "外部站点入口记录",
]

TITLE_QUALIFIERS = [
    "访问说明",
    "整理与核验",
    "分批记录",
    "维护参考",
    "公开索引",
    "访问检查",
    "资源汇总",
    "更新记录",
    "分类整理",
    "安全访问提示",
    "日常维护",
    "入口复核",
    "状态记录",
    "批次归档",
    "检查备忘",
    "导航参考",
    "维护索引",
    "地址汇总",
]

INTRODUCTIONS = [
    "本页用于整理一批第三方网站入口，方便后续访问、核验和维护。",
    "以下链接仅作为网站地址索引，不代表推荐、合作或内容来源关系。",
    "本页记录待复核的网站地址，实际状态应以人工访问结果为准。",
    "以下内容属于第三方链接归档，不对网站内容和安全性作保证。",
    "本页面用于分批维护公开网站入口，不构成认证或内容背书。",
    "本页用于记录一组公开可访问的网站地址，并提供基础访问检查提示。",
    "本批内容以域名整理和入口核验为目的，便于后续维护与人工复查。",
    "以下网站地址来自当前维护列表，页面仅承担导航、分类和记录功能。",
    "本页按批次记录公开域名，便于后续核对解析、跳转和页面变化。",
    "以下地址用于建立可追溯的维护记录，实际网站状态以访问时结果为准。",
    "本批次对公开网址进行结构化整理，便于查找、复查和历史对照。",
    "本页汇总一组外部网站入口，重点保留域名本身与基础维护信息。",
]

DISCLAIMERS = [
    "第三方网站内容可能随时变化，请访问者自行判断。",
    "未经实际核验，不应将这些网站描述为官方、权威或安全站点。",
    "遇到异常跳转、自动下载或信息提交要求时，请谨慎操作。",
    "网站被收录仅表示地址已进入整理列表，不代表内容得到认可。",
    "如需提交账号、联系方式或支付信息，请先确认网站真实性和连接安全性。",
    "域名与页面内容之间的对应关系可能变化，请勿仅凭域名名称推断网站用途。",
    "本页只记录公开入口，不对第三方网站的可用性、合法性或持续运营作保证。",
]

# 通用增强正文模块。每篇增强页会随机抽取若干块。
CONTEXT_BLOCKS = [
    (
        "访问前可以检查什么",
        "打开陌生网站前，可以先确认浏览器地址栏中的域名是否与预期一致，并留意 HTTPS 连接、异常跳转和浏览器安全提示。域名能够访问并不等于其内容已经经过核验，因此本页仍保留人工复查状态。",
    ),
    (
        "域名记录为什么需要定期复核",
        "域名的解析、页面内容和跳转目标都可能发生变化。定期复核可以帮助维护者发现失效地址、跳转变化或内容变更，并及时更新后续记录。",
    ),
    (
        "如何使用本页的链接",
        "本页中的链接主要用于导航和检查。访问后如果页面与预期不一致，应以实际页面为准，不要仅依据域名名称判断网站用途，也不要把未核验的网站标注为合作方或权威来源。",
    ),
    (
        "访问陌生站点时的基本原则",
        "对于首次访问的站点，建议避免直接下载未知文件，也不要在尚未确认网站真实性时提交敏感信息。若浏览器出现证书、重定向或下载提醒，应先停止操作并重新核对地址。",
    ),
    (
        "链接记录的维护方式",
        "为了便于持续维护，链接可以按日期、域名后缀和批次进行记录。后续复核时，只需要针对状态发生变化的地址更新备注，不必重新整理全部历史页面。",
    ),
    (
        "为什么保留原始域名作为锚文本",
        "本页大多数链接直接使用域名作为显示文字，便于访问者在点击前识别目标地址，也便于维护者核对是否出现拼写差异或跳转异常。",
    ),
    (
        "页面状态说明",
        "“待复核”表示该地址已经进入整理列表，但尚未对当前内容、运营主体或安全性做进一步判断。这个状态只用于内部维护，不代表网站存在问题。",
    ),
    (
        "后续检查建议",
        "如果需要进一步检查，可以依次确认域名是否解析、HTTPS 是否正常、首页是否可访问以及页面是否存在异常跳转。检查结果应记录事实，不对无法确认的信息作推断。",
    ),
    (
        "HTTPS 与证书提示",
        "HTTPS 可以帮助保护浏览器与服务器之间的数据传输，但仅有 HTTPS 并不能证明网站本身可信。复核时应同时关注证书提示、域名是否一致以及页面实际内容。",
    ),
    (
        "重定向需要记录什么",
        "部分域名访问后会跳转到其他地址。维护时可以记录最终落地域名和是否存在多次跳转；如果跳转目标与原域名明显无关，应保留备注，避免后续把两者误认为同一站点。",
    ),
    (
        "遇到失效地址如何处理",
        "如果域名无法解析、连接超时或持续返回错误页面，可以先保留历史记录并标注复核日期。短时故障与永久失效并不相同，必要时可间隔一段时间再次检查。",
    ),
    (
        "为什么不根据域名猜测网站内容",
        "域名名称可能与当前页面主题无关，也可能在转让或改版后改变用途。因此整理页面只描述可观察到的地址和状态，不根据名称推断业务、机构身份或内容来源。",
    ),
    (
        "移动端与桌面端可能不同",
        "同一网站在移动端和桌面端可能展示不同导航、跳转或弹窗。如果复核结果需要用于长期维护，最好记录访问环境，避免把设备差异误认为网站异常。",
    ),
    (
        "检查首页响应的意义",
        "首页能否正常返回只是基础状态之一。维护者还可以观察是否存在循环跳转、空白页、错误提示或明显异常的下载行为，从而决定是否需要进一步人工检查。",
    ),
    (
        "域名后缀只是分类信息",
        "`.com`、`.cn`、`.net` 等后缀可以用于整理和统计，但后缀本身不能说明网站质量、所属行业或可信程度。本页仅把后缀作为结构化分类字段使用。",
    ),
    (
        "为什么保留历史批次",
        "历史批次可以帮助维护者比较同一域名在不同日期的出现情况，也方便排查何时发生解析、跳转或页面内容变化，因此旧记录通常不需要因为新批次生成而删除。",
    ),
    (
        "处理浏览器安全警告",
        "如果浏览器提示证书异常、危险下载或欺诈风险，应优先停止继续操作并核对网址。整理页面不应绕过浏览器警告，也不应把出现警告的网站直接标记为安全。",
    ),
    (
        "记录最终落地地址",
        "某些域名会跳转到新的域名或子路径。人工复核时可以记录最终落地地址，但仍保留原始入口，方便后续判断跳转关系是否发生变化。",
    ),
    (
        "避免重复提交敏感信息",
        "站点复核通常不需要登录、付款或提交个人资料。除非明确知道网站身份和操作目的，否则应避免为了测试页面而填写真实账号、电话号码、证件或支付信息。",
    ),
    (
        "批量链接的核验顺序",
        "处理较大的域名列表时，可以先检查解析和首页响应，再对存在跳转或异常提示的站点做二次复核。分层检查能够减少重复操作，并让维护记录更容易追踪。",
    ),
    (
        "为什么需要注明检查日期",
        "网站状态具有时间性，同一个域名今天正常并不代表以后仍保持相同状态。记录检查日期可以让后续使用者判断信息的新旧程度，并决定是否需要重新访问。",
    ),
    (
        "页面标题与实际内容要分开判断",
        "网站标题、域名和页面正文可能并不完全一致。复核时应以实际加载内容为基础，避免仅凭标题或域名字符串对站点性质作结论。",
    ),
    (
        "异常下载应谨慎处理",
        "正常的入口检查通常不需要自动下载文件。如果访问后立即触发未知文件下载，建议取消下载并记录异常现象，不要为了完成核验而打开来源不明的文件。",
    ),
    (
        "DNS 变化可能意味着什么",
        "域名解析地址发生变化可能源于服务器迁移、CDN 调整或运营变更，本身不代表异常。若维护目标包含长期监测，可以把明显的解析变化作为需要重新检查页面内容的信号。",
    ),
    (
        "子域名和主域名要区分",
        "主域名与不同子域名可能承载完全不同的服务。当前列表主要按输入域名记录入口，人工检查时应注意浏览器最终显示的是主域名、子域名还是其他跳转地址。",
    ),
    (
        "避免把目录页当作推荐页",
        "链接出现在整理目录中，只说明它被纳入当前批次。目录的作用是记录和导航，不代表站点质量排序、推荐关系或商业合作。",
    ),
    (
        "复核结果应记录事实",
        "维护记录最好使用可验证的事实，例如“可访问”“跳转到某地址”“证书提示异常”或“页面返回错误”，避免写入无法确认的主体身份、评价或安全结论。",
    ),
    (
        "批次之间保持可追溯性",
        "通过统一的日期、编号和相邻页面链接，可以从任意一篇记录回到同日汇总或前后批次。这种结构便于在大量页面中定位具体记录。",
    ),
    (
        "公开链接与内容背书是两回事",
        "建立公开可点击链接只是让地址更容易被访问和复核，不代表发布者认可目标网站的内容。维护页面应继续保留中性说明和待复核状态。",
    ),
    (
        "检查跳转链时不要只看第一步",
        "有些入口会经过多次 301 或 302 跳转后才到最终页面。人工检查时如果需要记录跳转关系，应以浏览器最终到达的地址为准，并保留原始入口作为历史记录。",
    ),
    (
        "大量站点如何分批处理",
        "当域名数量较多时，按固定批次数量生成独立页面，可以避免单页过长，也方便后续按日期和编号定位。每一批只承担当前列表的整理任务，不需要对全部历史地址重复说明。",
    ),
]


# 统计型增强模块。与通用正文不同，这些段落会根据当前批次真实数据动态生成。
def stats_suffix_distribution(domains: list[str]) -> tuple[str, str]:
    counts = Counter("." + domain.rsplit(".", 1)[-1] for domain in domains)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    text = "、".join(f"`{suffix}` {count} 个" for suffix, count in ordered[:6])
    return (
        "域名后缀分布",
        f"当前批次的主要后缀分布为：{text}。这些统计只用于整理结构，不用于判断网站类型或可信度。",
    )


def stats_name_length(domains: list[str]) -> tuple[str, str]:
    lengths = [len(domain) for domain in domains]
    shortest = min(domains, key=lambda d: (len(d), d))
    longest = max(domains, key=lambda d: (len(d), d))
    average = sum(lengths) / len(lengths)
    return (
        "域名长度概览",
        f"本批域名平均长度约为 **{average:.1f}** 个字符。较短记录示例为 `{shortest}`，较长记录示例为 `{longest}`。长度仅作为列表特征，不代表站点质量。",
    )


def stats_initial_distribution(domains: list[str]) -> tuple[str, str]:
    initials = Counter(domain[0].upper() for domain in domains if domain)
    ordered = sorted(initials.items(), key=lambda item: (-item[1], item[0]))[:6]
    text = "、".join(f"`{initial}` {count} 个" for initial, count in ordered)
    return (
        "首字符分布",
        f"按域名首字符统计，本批出现较多的分组包括：{text}。这一信息主要用于快速浏览和批量核对。",
    )


def stats_hyphen_digits(domains: list[str]) -> tuple[str, str]:
    hyphen_count = sum("-" in domain for domain in domains)
    digit_count = sum(any(ch.isdigit() for ch in domain) for domain in domains)
    return (
        "命名特征概览",
        f"本批中有 **{hyphen_count}** 个域名包含连字符，有 **{digit_count}** 个域名包含数字。此类特征只用于识别和核对地址，不用于推断站点用途。",
    )


def stats_alpha_range(domains: list[str]) -> tuple[str, str]:
    ordered = sorted(domains)
    sample = "、".join(f"`{d}`" for d in ordered[:3])
    tail = "、".join(f"`{d}`" for d in ordered[-3:])
    return (
        "字母顺序位置",
        f"按字母顺序查看时，列表前部包括 {sample}；后部包括 {tail}。维护时可以借助排序快速发现遗漏或重复记录。",
    )


DYNAMIC_BLOCK_BUILDERS = [
    stats_suffix_distribution,
    stats_name_length,
    stats_initial_distribution,
    stats_hyphen_digits,
    stats_alpha_range,
]


def load_config() -> dict:
    # 原有配置完全兼容；下面新增项没有写入 config.json 时会自动使用默认值。
    default = {
        "posts_per_day": 2000,
        "domains_per_post": 54,
        "timezone": "Asia/Shanghai",
        "content_mode": "mixed",
        "content_ratio": 0.20,
        "add_internal_links": True,
        "context_sections": 3,
        "dynamic_sections": 1,
        "account_variation": True,
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
        lines.append(f"| {index} | [{domain}](https://{domain}) | 待核验 |")
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
        lines.extend(["<details>", f"<summary>第 {index} 组网站</summary>", ""])
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


def compact_group_template(domains: list[str]) -> str:
    lines = ["## 分组网站入口", ""]
    group_size = max(5, min(12, len(domains) // 4 or 5))
    for start in range(0, len(domains), group_size):
        group = domains[start : start + group_size]
        lines.append(f"### 第 {start // group_size + 1} 组")
        lines.append("")
        lines.append(" · ".join(f"[{d}](https://{d})" for d in group))
        lines.append("")
    return "\n".join(lines).rstrip()


def simple_index_template(domains: list[str]) -> str:
    lines = ["## 域名索引", ""]
    for index, domain in enumerate(sorted(domains), start=1):
        lines.append(f"- `{index:02d}` [{domain}](https://{domain})")
    return "\n".join(lines)


TEMPLATES = [
    numbered_template,
    checklist_template,
    table_template,
    suffix_template,
    details_template,
    cards_template,
    compact_group_template,
    simple_index_template,
]


def repository_context() -> tuple[str, str, str]:
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY", "YOUR_ACCOUNT/YOUR_REPOSITORY")
    ref_name = os.environ.get("GITHUB_REF_NAME", "main")
    return server_url.rstrip("/"), repository, ref_name


def repository_salt(enabled: bool) -> str:
    if not enabled:
        return ""
    _, repository, _ = repository_context()
    return repository


def build_post_url(post_path: str) -> str:
    server_url, repository, ref_name = repository_context()
    return f"{server_url}/{repository}/blob/{ref_name}/{post_path}"


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
    old_lines = [line for line in old_section.strip().splitlines() if line.strip()]
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


def write_link_collections(date_text: str, post_records: list[dict[str, str]]) -> None:
    DAILY_LINKS_DIR.mkdir(parents=True, exist_ok=True)
    urls = [record["url"] for record in post_records]
    plain_text = "\n".join(urls) + "\n"

    (DAILY_LINKS_DIR / f"{date_text}.txt").write_text(plain_text, encoding="utf-8")
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
        markdown_lines.append(f"{index}. [{record['title']}]({record['url']})")

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
    (DAILY_LINKS_DIR / f"{date_text}.md").write_text(
        "\n".join(markdown_lines), encoding="utf-8"
    )


def select_post_domains(
    all_domains: list[str],
    date_text: str,
    post_number: int,
    count: int,
    salt: str,
) -> list[str]:
    seed = make_seed(date_text, post_number, "domains", salt)
    rng = random.Random(seed)
    copied = all_domains.copy()
    rng.shuffle(copied)
    return copied[:count]


def make_display_title(date_text: str, post_number: int, seed: int) -> str:
    base = TITLE_BASES[seed % len(TITLE_BASES)]
    qualifier = TITLE_QUALIFIERS[(seed // len(TITLE_BASES)) % len(TITLE_QUALIFIERS)]
    return f"{base}｜{qualifier}：{date_text} 第 {post_number} 篇"


def build_batch_overview(domains: list[str]) -> str:
    suffixes = ["." + domain.rsplit(".", 1)[-1] for domain in domains]
    counts = Counter(suffixes)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    suffix_text = "、".join(
        f"`{suffix}` {count} 个" for suffix, count in ordered[:5]
    )
    sorted_domains = sorted(domains)
    return "\n".join(
        [
            "## 本批概览",
            "",
            f"本批共整理 **{len(domains)}** 个不同域名，覆盖 **{len(counts)}** 种域名后缀。",
            f"数量较多的后缀包括：{suffix_text}。",
            f"按字母排序后，本批记录范围从 `{sorted_domains[0]}` 到 `{sorted_domains[-1]}`。",
        ]
    )


def build_context_sections(seed: int, count: int, salt: str) -> str:
    if count <= 0:
        return ""
    rng = random.Random(make_seed(seed, "context", salt))
    blocks = CONTEXT_BLOCKS.copy()
    rng.shuffle(blocks)
    selected = blocks[: min(count, len(blocks))]

    lines: list[str] = []
    for heading, paragraph in selected:
        lines.extend([f"## {heading}", "", paragraph, ""])
    return "\n".join(lines).rstrip()


def build_dynamic_sections(domains: list[str], seed: int, count: int, salt: str) -> str:
    if count <= 0:
        return ""
    rng = random.Random(make_seed(seed, "dynamic", salt))
    builders = DYNAMIC_BLOCK_BUILDERS.copy()
    rng.shuffle(builders)
    selected = builders[: min(count, len(builders))]

    lines: list[str] = []
    for builder in selected:
        heading, paragraph = builder(domains)
        lines.extend([f"## {heading}", "", paragraph, ""])
    return "\n".join(lines).rstrip()


def should_use_enriched_content(content_mode: str, content_ratio: float, seed: int) -> bool:
    mode = content_mode.strip().lower()
    if mode == "directory":
        return False
    if mode in {"content", "enriched"}:
        return True

    ratio = max(0.0, min(1.0, content_ratio))
    bucket = make_seed(seed, "content-mode") % 10000
    return bucket < int(ratio * 10000)


def build_internal_links(date_text: str, post_number: int, posts_per_day: int) -> str:
    links = ["## 相关记录", ""]
    if post_number > 1:
        links.append(f"- [上一条记录]({date_text}-{post_number - 1:02d}.md)")
    if post_number < posts_per_day:
        links.append(f"- [下一条记录]({date_text}-{post_number + 1:02d}.md)")
    links.append("- [返回自动发布目录](../README.md)")
    links.append(f"- [查看 {date_text} 当日汇总](../daily-links/{date_text}.md)")
    return "\n".join(links)


def main() -> None:
    config = load_config()

    posts_per_day = int(config["posts_per_day"])
    domains_per_post = int(config["domains_per_post"])
    timezone_name = str(config["timezone"])
    content_mode = str(config.get("content_mode", "mixed"))
    content_ratio = float(config.get("content_ratio", 0.20))
    add_internal_links = bool(config.get("add_internal_links", True))
    context_sections = int(config.get("context_sections", 3))
    dynamic_sections = int(config.get("dynamic_sections", 1))
    account_variation = bool(config.get("account_variation", True))

    if posts_per_day < 1:
        raise ValueError("posts_per_day 必须大于0")
    if domains_per_post < 1:
        raise ValueError("domains_per_post 必须大于0")
    if context_sections < 0:
        raise ValueError("context_sections 不能小于0")
    if dynamic_sections < 0:
        raise ValueError("dynamic_sections 不能小于0")

    all_domains = load_domains()
    if len(all_domains) < domains_per_post:
        raise ValueError(
            f"至少需要 {domains_per_post} 个不同域名，当前只有 {len(all_domains)} 个。"
        )

    now = datetime.now(ZoneInfo(timezone_name))
    date_text = now.strftime("%Y-%m-%d")
    salt = repository_salt(account_variation)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_records: list[dict[str, str]] = []
    readme_entries: list[str] = []

    for post_number in range(1, posts_per_day + 1):
        seed = make_seed(date_text, post_number, salt)

        introduction = INTRODUCTIONS[(seed // 7) % len(INTRODUCTIONS)]
        disclaimer = DISCLAIMERS[(seed // 13) % len(DISCLAIMERS)]
        template_function = TEMPLATES[(seed // 17) % len(TEMPLATES)]

        selected = select_post_domains(
            all_domains,
            date_text,
            post_number,
            domains_per_post,
            salt,
        )

        post_code = f"{post_number:02d}"
        post_name = f"{date_text}-{post_code}.md"
        post_path = f"posts/{post_name}"
        output_file = POSTS_DIR / post_name
        display_title = make_display_title(date_text, post_number, seed)

        enriched = should_use_enriched_content(content_mode, content_ratio, seed)
        sections: list[str] = []

        if enriched:
            sections.append(build_batch_overview(selected))
            context_text = build_context_sections(seed, context_sections, salt)
            if context_text:
                sections.append(context_text)
            dynamic_text = build_dynamic_sections(selected, seed, dynamic_sections, salt)
            if dynamic_text:
                sections.append(dynamic_text)

        if add_internal_links:
            sections.append(build_internal_links(date_text, post_number, posts_per_day))

        sections.append(template_function(selected))
        body = "\n\n".join(section for section in sections if section)

        content = f"""# {display_title}

> {introduction}  
> {disclaimer}

- 发布日期：{date_text}
- 当日编号：{post_code}
- 本批数量：{len(selected)}
- 页面状态：待复核


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
            {"title": display_title, "path": post_path, "url": post_url}
        )
        readme_entries.append(f"- [{display_title}]({post_path})")
        mode_label = "增强型" if enriched else "目录型"
        print(f"已生成：{post_path} [{mode_label}]")

    write_link_collections(date_text, post_records)
    update_readme(readme_entries, date_text)

    print(f"本次共生成 {len(post_records)} 篇。")
    print(f"链接汇总：daily-links/{date_text}.txt")
    print("最近链接：latest-links.txt")


if __name__ == "__main__":
    main()
