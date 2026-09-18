--- /mnt/data/generate_original.py	2026-09-18 16:29:04.729437244 +0000
+++ /mnt/data/generate.py	2026-09-18 16:30:38.121380019 +0000
@@ -5,6 +5,7 @@
 import os
 import random
 import re
+from collections import Counter
 from datetime import datetime
 from pathlib import Path
 from urllib.parse import urlparse
@@ -20,7 +21,7 @@
 README_FILE = ROOT / "README.md"
 
 
-TITLES = [
+TITLE_BASES = [
     "公开网站入口整理",
     "第三方链接维护记录",
     "网站访问核验清单",
@@ -41,8 +42,32 @@
     "网站入口维护计划",
     "第三方地址核验记录",
     "站点资源归档目录",
+    "网络资源访问记录",
+    "网站入口分组记录",
+    "域名访问核验记录",
+    "公开站点维护索引",
+    "网站资源检查记录",
+    "网络地址整理记录",
+    "公开入口更新记录",
+    "站点地址维护清单",
+    "第三方域名整理记录",
+    "网站资源复核目录",
 ]
 
+TITLE_QUALIFIERS = [
+    "访问说明",
+    "整理与核验",
+    "分批记录",
+    "维护参考",
+    "公开索引",
+    "访问检查",
+    "资源汇总",
+    "更新记录",
+    "分类整理",
+    "安全访问提示",
+    "日常维护",
+    "入口复核",
+]
 
 INTRODUCTIONS = [
     "本页用于整理一批第三方网站入口，方便后续访问、核验和维护。",
@@ -50,22 +75,66 @@
     "本页记录待复核的网站地址，实际状态应以人工访问结果为准。",
     "以下内容属于第三方链接归档，不对网站内容和安全性作保证。",
     "本页面用于分批维护公开网站入口，不构成认证或内容背书。",
+    "本页用于记录一组公开可访问的网站地址，并提供基础访问检查提示。",
+    "本批内容以域名整理和入口核验为目的，便于后续维护与人工复查。",
+    "以下网站地址来自当前维护列表，页面仅承担导航、分类和记录功能。",
 ]
 
-
 DISCLAIMERS = [
     "第三方网站内容可能随时变化，请访问者自行判断。",
     "未经实际核验，不应将这些网站描述为官方、权威或安全站点。",
     "遇到异常跳转、自动下载或信息提交要求时，请谨慎操作。",
     "网站被收录仅表示地址已进入整理列表，不代表内容得到认可。",
+    "如需提交账号、联系方式或支付信息，请先确认网站真实性和连接安全性。",
+]
+
+CONTEXT_BLOCKS = [
+    (
+        "访问前可以检查什么",
+        "打开陌生网站前，可以先确认浏览器地址栏中的域名是否与预期一致，并留意 HTTPS 连接、异常跳转和浏览器安全提示。域名能够访问并不等于其内容已经经过核验，因此本页仍保留人工复查状态。",
+    ),
+    (
+        "域名记录为什么需要定期复核",
+        "域名的解析、页面内容和跳转目标都可能发生变化。定期复核可以帮助维护者发现失效地址、跳转变化或内容变更，并及时更新后续记录。",
+    ),
+    (
+        "如何使用本页的链接",
+        "本页中的链接主要用于导航和检查。访问后如果页面与预期不一致，应以实际页面为准，不要仅依据域名名称判断网站用途，也不要把未核验的网站标注为合作方或权威来源。",
+    ),
+    (
+        "访问陌生站点时的基本原则",
+        "对于首次访问的站点，建议避免直接下载未知文件，也不要在尚未确认网站真实性时提交敏感信息。若浏览器出现证书、重定向或下载提醒，应先停止操作并重新核对地址。",
+    ),
+    (
+        "链接记录的维护方式",
+        "为了便于持续维护，链接可以按日期、域名后缀和批次进行记录。后续复核时，只需要针对状态发生变化的地址更新备注，不必重新整理全部历史页面。",
+    ),
+    (
+        "为什么保留原始域名作为锚文本",
+        "本页大多数链接直接使用域名作为显示文字，便于访问者在点击前识别目标地址，也便于维护者核对是否出现拼写差异或跳转异常。",
+    ),
+    (
+        "页面状态说明",
+        "“待复核”表示该地址已经进入整理列表，但尚未对当前内容、运营主体或安全性做进一步判断。这个状态只用于内部维护，不代表网站存在问题。",
+    ),
+    (
+        "后续检查建议",
+        "如果需要进一步检查，可以依次确认域名是否解析、HTTPS 是否正常、首页是否可访问以及页面是否存在异常跳转。检查结果应记录事实，不对无法确认的信息作推断。",
+    ),
 ]
 
 
 def load_config() -> dict:
+    # 保留原有三个配置项，同时新增可选增强项。
+    # 旧 config.json 不需要修改也可以直接继续运行。
     default = {
         "posts_per_day": 2000,
         "domains_per_post": 54,
         "timezone": "Asia/Shanghai",
+        "content_mode": "mixed",
+        "content_ratio": 0.20,
+        "add_internal_links": True,
+        "context_sections": 2,
     }
 
     if not CONFIG_FILE.exists():
@@ -384,12 +453,108 @@
     return copied[:count]
 
 
+def make_display_title(date_text: str, post_number: int, seed: int) -> str:
+    base = TITLE_BASES[seed % len(TITLE_BASES)]
+    qualifier = TITLE_QUALIFIERS[
+        (seed // len(TITLE_BASES)) % len(TITLE_QUALIFIERS)
+    ]
+    return f"{base}｜{qualifier}：{date_text} 第 {post_number} 篇"
+
+
+def build_batch_overview(domains: list[str]) -> str:
+    suffixes = ["." + domain.rsplit(".", 1)[-1] for domain in domains]
+    counts = Counter(suffixes)
+    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
+
+    top_items = ordered[:5]
+    suffix_text = "、".join(
+        f"`{suffix}` {count} 个" for suffix, count in top_items
+    )
+
+    sorted_domains = sorted(domains)
+    first_domain = sorted_domains[0]
+    last_domain = sorted_domains[-1]
+
+    lines = [
+        "## 本批概览",
+        "",
+        f"本批共整理 **{len(domains)}** 个不同域名，覆盖 **{len(counts)}** 种域名后缀。",
+        f"数量较多的后缀包括：{suffix_text}。",
+        f"按字母排序后，本批记录范围从 `{first_domain}` 到 `{last_domain}`。",
+        "",
+    ]
+
+    return "\n".join(lines).rstrip()
+
+
+def build_context_sections(seed: int, count: int) -> str:
+    if count <= 0:
+        return ""
+
+    rng = random.Random(make_seed(seed, "context"))
+    blocks = CONTEXT_BLOCKS.copy()
+    rng.shuffle(blocks)
+    selected = blocks[: min(count, len(blocks))]
+
+    lines: list[str] = []
+    for heading, paragraph in selected:
+        lines.extend([f"## {heading}", "", paragraph, ""])
+
+    return "\n".join(lines).rstrip()
+
+
+def should_use_enriched_content(
+    content_mode: str,
+    content_ratio: float,
+    seed: int,
+) -> bool:
+    mode = content_mode.strip().lower()
+
+    if mode == "directory":
+        return False
+
+    if mode in {"content", "enriched"}:
+        return True
+
+    # mixed 模式：使用确定性随机，保证同一天重复运行结果一致。
+    ratio = max(0.0, min(1.0, content_ratio))
+    bucket = make_seed(seed, "content-mode") % 10000
+    return bucket < int(ratio * 10000)
+
+
+def build_internal_links(
+    date_text: str,
+    post_number: int,
+    posts_per_day: int,
+) -> str:
+    links = ["## 相关记录", ""]
+
+    if post_number > 1:
+        prev_name = f"{date_text}-{post_number - 1:02d}.md"
+        links.append(f"- [上一条记录]({prev_name})")
+
+    if post_number < posts_per_day:
+        next_name = f"{date_text}-{post_number + 1:02d}.md"
+        links.append(f"- [下一条记录]({next_name})")
+
+    links.append("- [返回自动发布目录](../README.md)")
+    links.append(
+        f"- [查看 {date_text} 当日汇总](../daily-links/{date_text}.md)"
+    )
+
+    return "\n".join(links)
+
+
 def main() -> None:
     config = load_config()
 
     posts_per_day = int(config["posts_per_day"])
     domains_per_post = int(config["domains_per_post"])
     timezone_name = str(config["timezone"])
+    content_mode = str(config.get("content_mode", "mixed"))
+    content_ratio = float(config.get("content_ratio", 0.20))
+    add_internal_links = bool(config.get("add_internal_links", True))
+    context_sections = int(config.get("context_sections", 2))
 
     if posts_per_day < 1:
         raise ValueError("posts_per_day 必须大于0")
@@ -397,6 +562,9 @@
     if domains_per_post < 1:
         raise ValueError("domains_per_post 必须大于0")
 
+    if context_sections < 0:
+        raise ValueError("context_sections 不能小于0")
+
     all_domains = load_domains()
 
     if len(all_domains) < domains_per_post:
@@ -416,16 +584,13 @@
     for post_number in range(1, posts_per_day + 1):
         seed = make_seed(date_text, post_number)
 
-        title = TITLES[seed % len(TITLES)]
         introduction = INTRODUCTIONS[
-            (seed // len(TITLES)) % len(INTRODUCTIONS)
+            (seed // len(TITLE_BASES)) % len(INTRODUCTIONS)
         ]
         disclaimer = DISCLAIMERS[
             (seed // len(INTRODUCTIONS)) % len(DISCLAIMERS)
         ]
-        template_function = TEMPLATES[
-            seed % len(TEMPLATES)
-        ]
+        template_function = TEMPLATES[seed % len(TEMPLATES)]
 
         selected = select_post_domains(
             all_domains,
@@ -439,11 +604,38 @@
         post_path = f"posts/{post_name}"
         output_file = POSTS_DIR / post_name
 
-        display_title = (
-            f"{title}：{date_text} 第 {post_number} 篇"
+        display_title = make_display_title(
+            date_text,
+            post_number,
+            seed,
         )
 
         body = template_function(selected)
+        enriched = should_use_enriched_content(
+            content_mode,
+            content_ratio,
+            seed,
+        )
+
+        extra_sections: list[str] = []
+        if enriched:
+            extra_sections.append(build_batch_overview(selected))
+            extra_sections.append(
+                build_context_sections(seed, context_sections)
+            )
+
+        if add_internal_links:
+            extra_sections.append(
+                build_internal_links(
+                    date_text,
+                    post_number,
+                    posts_per_day,
+                )
+            )
+
+        extras = "\n\n".join(
+            section for section in extra_sections if section
+        )
 
         content = f"""# {display_title}
 
@@ -456,6 +648,8 @@
 - 页面状态：待复核
 
 
+{extras}
+
 {body}
 
 ## 维护说明
@@ -486,7 +680,8 @@
             f"- [{display_title}]({post_path})"
         )
 
-        print(f"已生成：{post_path}")
+        mode_text = "增强型" if enriched else "目录型"
+        print(f"已生成：{post_path} [{mode_text}]")
 
     write_link_collections(date_text, post_records)
     update_readme(readme_entries, date_text)
