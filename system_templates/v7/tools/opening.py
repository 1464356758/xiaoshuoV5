"""A7 opening workshop. Facts come from text bytes; editorial judgments remain attributed."""
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re


class OpeningError(ValueError):
    pass


def check(ok, message):
    if not ok:
        raise OpeningError(message)


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def as_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def nonempty(value, label):
    check(isinstance(value, str) and bool(value.strip()), label + "缺少内容")
    return value.strip()


def check_repeated_text(text):
    """Reject only substantial verbatim padding. Short refrains remain an editorial choice."""
    letters = re.sub(r"[^\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U000323af]", "", text)
    width = 16
    total = len(letters) - width + 1
    if total < 100:
        return
    counts = Counter(letters[i:i + width] for i in range(total))
    repeated = sum(count for count in counts.values() if count >= 4)
    check(repeated * 2 < total, "大段逐字循环填充，请恢复实际场景再审读")


def text_units(raw, encoding):
    text = html.unescape(raw.decode(encoding).lstrip("\ufeff"))
    text = re.sub(r"</?(?:p|div)\b[^>]*>|<br\b[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</?(?:b|i|strong|em|span|a)\b[^>]*>", "", text, flags=re.I)
    return [line.strip() for line in text.splitlines() if line.strip()]


def source_excerpt(args):
    raw = Path(args.file).read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    check(git_blob == args.blob, "实际参考原文件字节与固定目录中的 Git blob 不同")
    check(args.encoding.lower() in {"utf-8", "utf-8-sig", "gbk", "gb18030", "utf-16", "big5"}, "请指定实际文本编码")
    units = text_units(raw, args.encoding)
    check(1 <= args.first <= args.last <= len(units), "实读段落范围超出原文")
    return "\n".join(units[args.first-1:args.last])


def register(book, args, excerpt):
    check(re.fullmatch(r"[0-9a-f]{40}", args.commit), "需要参考库固定提交")
    parts = args.source_path.split("/")
    check(all(p and p not in {".", ".."} for p in parts) and "\\" not in args.source_path
          and parts[0] not in {"tools", "books", "docs", "studies", "reviews", "practices"}
          and args.source_path not in {"catalog.json", "README.md", "AGENTS.md"}, "需要库内实际原文路径")
    row = {"commit": args.commit, "path": args.source_path, "blob": args.blob,
           "family": nonempty(args.family, "目录作品组"), "range": [args.first, args.last],
           "encoding": args.encoding, "text_sha256": checksum(excerpt.encode()),
           "lesson": nonempty(args.lesson, "阅读发现"), "limit": nonempty(args.limit, "失效条件")}
    with book.lock():
        s = book.state()
        check(s["revision"] == 0 and not book.pending(s), "开书实读依据已进入首章任务；后续材料记入计划")
        path = "book/opening/sources.json"
        data = book.json(path) if book.path(path).exists() else {"book_id":s["book_id"],"repository":"1464356758/XS-KU","samples":[]}
        check(data["book_id"] == s["book_id"] and data["repository"] == "1464356758/XS-KU", "参考记录串书")
        data["samples"] = [x for x in data["samples"] if x["family"] != row["family"]] + [row]
        data["samples"].sort(key=lambda x: x["family"])
        book.atomic(path, as_json(data))
        return {"registered": row["path"], "families": len(data["samples"])}


def seal(book, args, han):
    with book.lock():
        state = book.state()
        check(state["platform"] and state["title"], "先完成平台与作品选择")
        check(state["revision"] == 0 and not book.pending(state), "已有正式章或在途任务，沿用已登记的开篇依据")
        check(1 <= args.window <= 200000, "试读窗口超出支持范围")
        notes = book.json("book/opening/sources.json")
        rows = notes["samples"]
        check(notes["book_id"] == state["book_id"] and notes["repository"] == "1464356758/XS-KU", "参考记录串书")
        check(len({r["family"] for r in rows}) >= 2 and len({r["blob"] for r in rows}) >= 2
              and len({r["path"] for r in rows}) >= 2, "需要两部独立参考原作的实际阅读记录")
        texts = [book.read(f"book/opening/{name}.txt").decode("utf-8") for name in ["a","b"]]
        check(all(han(t) >= 120 for t in texts), "请把两种开法各写成一段可读的场景")
        for text in texts:
            check_repeated_text(text)
        compact = [re.sub(r"[\W_]+", "", t) for t in texts]
        check(compact[0] != compact[1], "两份试写是相同正文")
        choice = nonempty(book.read("book/opening/choice.md").decode(), "试写取舍")
        evidence = {"book_id":state["book_id"], "title":state["title"], "platform":state["platform"],
                    "selected":args.pick, "basis":nonempty(args.basis, "试读窗口依据"), "window_han":args.window,
                    "sources":notes, "options":dict(zip(["a","b"], texts)), "choice":choice}
        data = as_json(evidence)
        pointer = book.object(data, "json")
        if state.get("opening_path") != pointer:
            state["opening_path"] = pointer
            book.atomic("book/state.json", as_json(state))
        book._index()
        return {"opening_path":pointer, "window_han":args.window, "selected":args.pick}


def load_opening(book, state):
    path = state.get("opening_path")
    if not path:
        check(state["revision"] == 0, "已冻结作品缺少开篇依据")
        return None
    check(isinstance(path, str) and re.fullmatch(r"book/objects/[0-9a-f]{64}\.json", path), "开篇快照路径无效")
    raw = book.read(path)
    check(path == f"book/objects/{checksum(raw)}.json", "开篇实读记录或试稿快照已变")
    value = json.loads(raw)
    check(all(value[k] == state[k] for k in ("book_id", "title", "platform")), "开篇材料绑定到其他作品")
    return value


def prefix(text, budget, han):
    for i, char in enumerate(text):
        budget -= han(char)
        if budget <= 0:
            return text[:i+1]
    return text


def first_pages(book, state, number, draft, budget, han):
    """Return text-only windows; chapter headings are rendered separately from the budget."""
    result = []
    for n in range(1, number+1):
        if n == number:
            text = draft
        else:
            item = state["chapters"][str(n)]
            text = book.read("book/" + item["text_path"]).decode()
        part = prefix(text, budget, han)
        result.append((n, part))
        budget -= han(part)
        if budget <= 0:
            break
    return result


def packet(book, budget, han):
    state = book.state()
    book.verify(state)
    active = book.pending(state)
    n = state["revision"] + int(bool(active))
    check(n > 0, "尚无正文可供试读")
    if active:
        draft = book.read(book.work_path(n) + "/draft.txt").decode()
    else:
        draft = book.read("book/" + state["chapters"][str(n)]["text_path"]).decode()
    opening = load_opening(book, state)
    if budget is None:
        budget = opening["window_han"]
    check(1 <= budget <= 200000, "试读窗口超出支持范围")
    return "\n\n".join(f"第{i}章\n\n{part}" for i,part in first_pages(book, state, n, draft, budget, han))


def within_window(book, state, number, draft, opening, han):
    budget = opening["window_han"]
    # Only early chapters can cross this bounded window (each adopted chapter has at least 5500 Han).
    if (number - 1) * 5500 >= budget:
        return False
    previous = sum(state["chapters"][str(i)]["han_count"] for i in range(1, number))
    return previous < budget <= previous + han(draft)


def need_reading(number, crossing):
    return number <= 5 or crossing or number % 5 == 0


def anchored(entry, text, label):
    check(isinstance(entry, dict), label + "缺少正文位置")
    quote = nonempty(entry.get("quote"), label + "原句")
    nonempty(entry.get("why"), label + "判断")
    check(4 <= len(quote) <= 120 and quote in text, label + "短引不在对应的实际正文中")
    return quote


def window_reading(window, pages):
    check(isinstance(window, dict), "请重读首章或送审窗口内已经写出的正文")
    available = dict(pages)
    spans = {}
    for key, label in [("promise", "读者产生期待的位置"), ("delivery", "读者看到结果的位置")]:
        entry = window.get(key)
        check(isinstance(entry, dict) and type(entry.get("chapter")) is int
              and entry["chapter"] in available, label + "缺少窗口内的原文章号")
        chapter = entry["chapter"]
        text = available[chapter]
        quote = anchored(entry, text, label)
        offset = text.index(quote)
        check(text.find(quote, offset + 1) < 0, label + "在同章有多处，请补上下文定位")
        spans[key] = ((chapter, offset), (chapter, offset + len(quote)))
    order = window.get("order", "setup_first")
    check(order in ("setup_first", "result_first"), "请选择顺叙或先见结果再揭起因")
    first, second = ("promise", "delivery") if order == "setup_first" else ("delivery", "promise")
    check(spans[first][1] <= spans[second][0], "两处证据重叠或与所报呈现顺序不符")
    effect = nonempty(window.get("effect"), "已发生结果的正文原段")
    delivery = window["delivery"]
    check(len(effect) <= 600 and delivery["quote"].strip() in effect
          and effect in available[delivery["chapter"]],
          "结果原段须在同一可见章节逐字出现，并含结果短引；推断请写在 why")


def reading(book, state, number, body, evidence, opening, han):
    crossing = within_window(book, state, number, body, opening, han)
    if not need_reading(number, crossing):
        check(evidence is None, "该章使用常规编辑意见")
        return
    check(isinstance(evidence, dict) and evidence.get("verdict") == "ready", "试读意见仍需返修")
    for label, key in [("最想跳过的位置","friction"),("本章已经给读者的结果","payoff")]:
        anchored(evidence.get(key), body, label)
    nonempty(evidence.get("next"), "读完还想知道的具体问题或完结余味")
    if number == 1:
        anchored(evidence.get("front"), prefix(body, 1200, han), "首场戏")
    if number > 1:
        item = state["chapters"][str(number-1)]
        prev = book.read("book/" + item["text_path"]).decode()
        anchored(evidence.get("previous"), prev, "上一章留下的后果与本章差别")
    if number == 1 or crossing:
        pages = first_pages(book, state, number, body, opening["window_han"], han)
        window_reading(evidence.get("window"), pages)


def add_arguments(sub):
    for name in ("excerpt", "sample"):
        p = sub.add_parser(name)
        p.add_argument("--file", required=True)
        p.add_argument("--blob", required=True)
        p.add_argument("--first", type=int, required=True)
        p.add_argument("--last", type=int, required=True)
        p.add_argument("--encoding", default="utf-8")
        if name == "sample":
            for field in ("commit","source-path","family","lesson","limit"):
                p.add_argument("--" + field, required=True)
    p = sub.add_parser("audition")
    p.add_argument("--pick", choices=["a","b"], required=True)
    p.add_argument("--window", type=int, required=True)
    p.add_argument("--basis", required=True)
    p.add_argument("--author-started", action="store_true", required=True)
    p = sub.add_parser("packet")
    p.add_argument("--han", type=int)
