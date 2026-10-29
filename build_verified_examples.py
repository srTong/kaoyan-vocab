#!/usr/bin/env python3
"""从项目内考试语料和词典例句生成可追溯的例句索引。

支持的外部考试语料目录：
    material/exam_corpus/
    material/考试语料/

文件名中包含 TOEFL/托福、IELTS/雅思、CET4/四级、CET6/六级、GRE、GMAT
等标识时，会自动写入对应来源。支持 txt、md、csv、json；JSON/CSV 只读取
example/sentence/context/text/例句/句子等字段，不会把词表误当成句子。
"""

import json
import re
import subprocess
import csv
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
PAPERS_DIR = ROOT / "material" / "Kaoyan-English1-Papers" / "solutions"
DATA_FILE = ROOT / "material" / "website" / "data" / "data.json"
OUTPUT_FILE = ROOT / "material" / "website" / "data" / "verified_examples.json"
EXTERNAL_AUDIT_FILE = ROOT / "material" / "website" / "data" / "example_corpus_audit.json"
WORDDECODER_FILE = ROOT / "third_party" / "worddecoder" / "data" / "lexicon.json"
ECDICT_FILE = ROOT / "third_party" / "ecdict" / "ecdict.csv"
WORKBOOK_DIR = ROOT / "material" / "研究生英语"
EXAM_CORPUS_DIRS = (
    ROOT / "material" / "exam_corpus",
    ROOT / "material" / "考试语料",
    ROOT / "material" / "website" / "data" / "exam_corpus",
)

EXAM_LABELS = (
    (r"toefl|托福", "托福语料"),
    (r"ielts|雅思", "雅思语料"),
    (r"cet[ -]?4|四级", "四级语料"),
    (r"cet[ -]?6|六级", "六级语料"),
    (r"gre", "GRE语料"),
    (r"gmat", "GMAT语料"),
    (r"pte", "PTE语料"),
    (r"专四", "专四语料"),
    (r"专八", "专八语料"),
)


def clean_word(value):
    return re.sub(r"[^a-z]", "", (value or "").lower())


def load_ecdict_pos():
    result = {}
    if not ECDICT_FILE.exists():
        return result
    with ECDICT_FILE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = clean_word(row.get("word", ""))
            if not key:
                continue
            pos = row.get("pos", "") or ""
            if not pos:
                match = re.match(r"\s*(a|ad|adj|adv|n|v|vt|vi|prep|conj|pron|aux|num)\.", row.get("translation", ""), re.I)
                pos = match.group(1) if match else ""
            if pos:
                result[key] = pos
    return result


ECDICT_POS = load_ecdict_pos()


def sentence_candidates(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    heading = re.search(r"#\s*(20\d{2})\s*年", text)
    year = heading.group(1) if heading else path.parent.name
    # 只采用阅读理解原文；排除完形填空的残缺句、解析文字和写作范文。
    section_two = re.search(r"(?im)^#*\s*Section\s+II\b", text)
    section_three = re.search(r"(?im)^#*\s*Section\s+III\b", text)
    if section_two:
        text = text[section_two.start():section_three.start() if section_three else None]
    rows = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if (not line or line.startswith("#") or re.search(r"[\u4e00-\u9fff]", line)
                or "_" in line or re.match(r"^\d+\s*[.、]", line)
                or re.match(r"^\[[A-D]\]", line)):
            continue
        line = re.sub(r"\$[^$]*\$", " ", line)
        line = re.sub(r"\s+", " ", line).strip(" -*")
        for sentence in re.split(r'(?<=[.!?])\s+(?=[\"“‘A-Z])', line):
            sentence = sentence.strip()
            tokens = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", sentence)
            if not (8 <= len(tokens) <= 55):
                continue
            if not re.search(r'[.!?][\"”’]?$', sentence):
                continue
            if re.match(
                r"^(Directions|Read the|Choose the|Mark your|Answer the|Write an essay|You should)",
                sentence,
                re.IGNORECASE,
            ):
                continue
            rows.append((year, sentence, [clean_word(token) for token in tokens]))
    return rows


def word_forms(word):
    forms = {word, word + "s", word + "es", word + "ed", word + "ing"}
    if word.endswith("e"):
        forms.update({word + "d", word[:-1] + "ing"})
    if word.endswith("y") and len(word) > 2:
        forms.update({word[:-1] + "ies", word[:-1] + "ied"})
    return forms


def contains_word(sentence, word):
    """只接受句子中实际出现目标词或常见词形的记录。"""
    variants = sorted(word_forms(word), key=len, reverse=True)
    return any(re.search(rf"\b{re.escape(form)}\b", sentence, re.IGNORECASE) for form in variants)


def exam_label(path):
    """根据语料文件名或父目录确定考试来源；无法识别则跳过。"""
    label_text = str(path).lower()
    for pattern, label in EXAM_LABELS:
        if re.search(pattern, label_text, re.IGNORECASE):
            return label
    return ""


def split_external_sentences(text):
    """把外部语料切成完整英文句子，并过滤题目说明、选项和残片。"""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    rows = []
    for sentence in re.split(r"(?<=[.!?])\s+(?=[\"“‘A-Z])", text):
        sentence = sentence.strip(" -*\"“”‘’")
        if not sentence or re.search(r"[\u4e00-\u9fff]", sentence):
            continue
        if re.match(
            r"^(Directions|Read the|Choose the|Mark your|Answer the|Write an essay|You should|Part [A-C]|Question|\[[A-D]\])",
            sentence,
            re.IGNORECASE,
        ):
            continue
        tokens = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", sentence)
        if not (6 <= len(tokens) <= 55):
            continue
        if not re.search(r"[.!?][\"”’]?$", sentence):
            continue
        rows.append((sentence, [clean_word(token) for token in tokens]))
    return rows


def external_exam_candidates(path):
    """读取托福/雅思/四六级等外部语料，返回完整句子而不是词表条目。"""
    label = exam_label(path)
    if not label:
        return []
    suffix = path.suffix.lower()
    texts = []
    try:
        if suffix in {".txt", ".md"}:
            texts = [path.read_text(encoding="utf-8", errors="ignore")]
        elif suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = [field for field in (reader.fieldnames or [])
                          if re.search(r"example|sentence|context|text|例句|句子", field, re.I)]
                for row in reader:
                    texts.extend(str(row.get(field, "")) for field in fields)
        elif suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))

            def collect(value, key=""):
                if isinstance(value, dict):
                    for child_key, child in value.items():
                        collect(child, str(child_key))
                elif isinstance(value, list):
                    for child in value:
                        collect(child, key)
                elif isinstance(value, str) and re.search(
                    r"example|sentence|context|text|content|例句|句子", key, re.I
                ):
                    texts.append(value)

            collect(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
        return []
    rows = []
    for text in texts:
        rows.extend(split_external_sentences(text))
    return rows


def external_exam_files():
    files = []
    for directory in EXAM_CORPUS_DIRS:
        if directory.exists():
            files.extend(path for path in directory.rglob("*")
                         if path.is_file() and path.suffix.lower() in {".txt", ".md", ".csv", ".json"}
                         and exam_label(path))
    return sorted(set(files))


def worddecoder_example(entry, word):
    """从 WordDecoder gloss 中提取英文例句，排除中文释义和短语残片。"""
    if not entry:
        return ""
    for part in str(entry.get("gloss", "")).split("/"):
        sentence = re.split(r"[\u4e00-\u9fff]", part, maxsplit=1)[0].strip(" ;")
        tokens = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", sentence)
        if not (7 <= len(tokens) <= 35):
            continue
        if not re.search(r"[.!?]$", sentence) or not contains_word(sentence, word):
            continue
        if re.match(r"^(a|an|the)\s+(study|person|thing|state|quality)\s+of\b", sentence, re.I):
            continue
        return sentence
    return ""


def workbook_examples():
    """读取项目已有的词根表例句；只纳入带年份且目标词出现在句中的记录。"""
    result = {}
    for filename in ("考研英语词汇-词根分类-带例句.xlsx", "考研英语词汇-词根分类-完整例句版.xlsx"):
        path = WORKBOOK_DIR / filename
        if not path.exists():
            continue
        sheet = load_workbook(path, read_only=True, data_only=True).active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            word = clean_word(str(row[2] or ""))
            sentence = re.sub(r"\s+", " ", str(row[4] or "").strip())
            source = str(row[5] or "").strip()
            if not word or not sentence or not source or source.startswith(("通用", "模拟")):
                continue
            if not re.search(r"(?:19|20)\d{2}", source) or not contains_word(sentence, word):
                continue
            candidate = {
                "example": sentence,
                "source": f"{source}（项目词根表）",
                "sourceFile": str(path.relative_to(ROOT)),
            }
            # 带例句版的来源更具体，完整例句版作为补充。
            if word not in result or "带例句" in filename:
                result[word] = candidate
    return result


def doc_sentence_candidates(path):
    """从项目内可转换的真题 DOC 中提取阅读原文句子。"""
    try:
        completed = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    text = completed.stdout
    section_two = re.search(r"(?im)Section\s+II\b", text)
    section_three = re.search(r"(?im)Section\s+III\b", text)
    if section_two:
        text = text[section_two.start():section_three.start() if section_three else None]
    rows = []
    for raw_line in text.splitlines():
        sentence = re.sub(r"\s+", " ", raw_line.strip())
        if (not sentence or re.search(r"[\u4e00-\u9fff]", sentence) or "_" in sentence
                or re.match(r"^\s*(\d+\s*[.、)]|\[[A-D]\]|[A-D][.、)])", sentence)):
            continue
        if re.match(r"^(Directions|Read the|Choose the|Mark your|Answer the|Write an essay|You should|Part [A-C]|Text\s*\d)", sentence, re.I):
            continue
        tokens = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", sentence)
        if not (8 <= len(tokens) <= 55) or not re.search(r"[.!?][\"”’]?$", sentence):
            continue
        rows.append((sentence, [clean_word(token) for token in tokens]))
    return rows


def verb_example(w, meaning, pos=""):
    """按中文释义选择一个最小但语义相容的动词语境。

    不能把所有动词都写成 ``The policy may WORD the problem``：
    abhor、bathe、bark 等词即使词性正确，也会因此得到明显错误的搭配。
    对无法可靠判断搭配的词，退回到明确的语言学习句，而不是伪造一个
    看似有语境、实际不通的句子。
    """
    m = meaning or ""
    if any(x in m for x in ("厌恶", "憎恨", "痛恨", "憎恶", "讨厌", "发誓断绝")):
        return f"Many people {w} violence."
    if any(x in m for x in ("惊奇", "惊讶", "使惊", "娱乐", "消遣")):
        return f"The finding may {w} many readers."
    if any(x in m for x in ("分析", "审查", "审计", "研究", "评估", "检查")):
        return f"Researchers {w} the data carefully."
    if any(x in m for x in ("攻击", "反对", "批评", "猛击", "击打", "打击", "殴打")):
        return f"The group may {w} the proposal."
    if any(x in m for x in ("定义", "描述", "说明", "表明", "表示", "传达", "宣布")):
        return f"The report {w} the idea clearly."
    if any(x in m for x in ("影响", "改变", "改善", "提高", "降低", "增加", "减少", "解决", "处理", "促进", "限制", "禁止", "约束", "限定")):
        return f"The policy may {w} access to education."
    if any(x in m for x in ("移动", "转移", "旋转", "弯", "弯曲", "折叠")):
        return f"The machine can {w} the material safely."
    if any(x in m for x in ("吠", "犬吠")):
        return f"The dog may {w} at night."
    if any(x in m for x in ("沐浴", "洗澡")):
        return f"People may {w} after work."
    if any(x in m for x in ("发生", "出现", "存在", "持续")):
        return f"The change may {w} over time."
    if any(x in m for x in ("使用", "采用", "消费", "雇用", "聘用")):
        return f"People may {w} the resource responsibly."
    if any(x in m for x in ("废除", "取消", "撤销", "宣布无效")):
        return f"The court may {w} the rule."
    if any(x in m for x in ("请求", "恳求", "乞求", "申请", "请愿")):
        return f"The group may {w} for support."
    if any(x in m for x in ("停止", "结束", "开始", "继续", "中断")):
        return f"The project may {w} after the review."
    if pos.startswith("vi"):
        return f"The process may {w} over time."
    if pos.startswith("v") or any(x in m for x in (
        "使", "导致", "承认", "支持", "避免", "保护", "遵守", "完成", "选择", "接受", "拒绝",
        "提供", "要求", "允许", "包括", "强调", "比较", "建议", "维持", "建立", "发现", "抛弃",
        "担心", "采取", "引起", "构成", "产生", "形成", "反映", "适应", "依赖", "参与", "确保",
        "管理", "发展", "调查", "打算", "意图", "包含", "需要", "代表", "获得", "涉及",
    )):
        # 不确定及物搭配时不再伪造 “try to WORD the issue”；这句会让
        # bark、breathe、cater 等词全部得到错误宾语。用元语言句保底。
        return ""
    return ""


def simple_example(word, meaning, pos=""):
    """为没有现成语料的词生成低难度、词性明确的辅助示例句。

    这里不再把所有单词套进 ``discuss X in simple terms`` 模板；该模板会把
    动词、形容词也误当成名词。辅助句的最低要求是：词性基本匹配、句法完整、
    目标词确实承担对应成分。它仍然不是原文语料，所以在页面上明确标注为辅助句。
    """
    raw_word = word.strip().lower()
    w = re.split(r"[，,/()（）]", raw_word, maxsplit=1)[0].strip()
    lower_meaning = (meaning or "").lower()
    pos = (pos or "").lower()
    if not re.fullmatch(r"[A-Za-z][A-Za-z-]*", w):
        return ""

    special = {
        "abide": "People should abide by the rules.",
        "aboard": "The passengers are aboard.",
        "abroad": "Some students study abroad.",
        "acquaint": "The teacher acquaints students with the plan.",
        "accustomed": "People are accustomed to change.",
        "afraid": "The child is afraid.",
        "agonize": "The problem may agonize many people.",
        "aids": "The report discusses AIDS as a public-health issue.",
        "contradiction": "The results contain a clear contradiction.",
        "dedicate": "The university dedicated more funds to research.",
        "dictaphone": "The reporter recorded the interview on a dictaphone.",
        "dictatorial": "The government became dictatorial after the crisis.",
        "dictatory": "The rule was dictatory rather than fair.",
        "indict": "The court may indict the suspect after the trial.",
        "indictable": "The act is indictable under the new law.",
        "indicted": "The suspect was indicted after the investigation.",
        "predictably": "The policy predictably increased the cost.",
        "predicted": "The predicted result was close to the actual result.",
        "predictor": "Income is a useful predictor of health.",
        "unpredicted": "The unpredicted change surprised the researchers.",
        "unpredictability": "Market unpredictability makes planning difficult.",
        "unpredictably": "Demand changed unpredictably during the crisis.",
        "intend": "The policy intends to reduce energy use.",
        "consume": "People consume less energy when buildings are efficient.",
        "confirm": "The new data confirm the earlier result.",
        "define": "The study defines success in clear terms.",
        "refine": "Researchers refine the method after each trial.",
        "adapt": "Schools adapt their teaching to new needs.",
        "address": "The policy addresses the housing problem.",
        "affect": "The change affects low-income families most.",
        "employ": "The firm employs many local workers.",
        "promote": "The program promotes equal access to education.",
        # 常见词根页中的高频词：这些词不能再交给词性模板，否则容易出现
        # “describe ... as affluent/circumfluent”一类不合语境的句子。
        "afflux": "The afflux of workers into the city put pressure on housing.",
        "affluent": "Affluent families can afford private education.",
        "circumfluent": "The circumfluent river surrounds the small island.",
        "sing": "The singer can sing clearly in a small room.",
        "swing": "The door can swing in the wind.",
        "reunified": "The two groups were reunified after the agreement.",
        "unified": "The two systems were unified after the reform.",
        "credited": "The result was credited to the new method.",
        "accredited": "The program was accredited after a formal review.",
        "financially": "The policy helped the family become financially stable.",
        "infinitesimally": "The value changed infinitesimally as the input increased.",
        "infinitive": "In “to read,” the words “to read” form an infinitive.",
        "finitude": "The study discusses the finitude of natural resources.",
        "infinitude": "The theory assumes the infinitude of space.",
        "semifinal": "The team advanced to the semifinal after a close match.",
        "finite": "The resources available to the project are finite.",
        "definable": "The concept is definable in precise terms.",
        "definite": "The evidence provides a definite answer.",
        "predefined": "The software uses predefined settings.",
        "prefinished": "The factory supplied prefinished panels for the building.",
        "undefinable": "Some human experiences remain undefinable in simple words.",
        "unconfined": "The animals moved freely in an unconfined space.",
        "unfinished": "The bridge remained unfinished after funding stopped.",
        "refinancing": "Refinancing can lower the firm's borrowing costs.",
        "definer": "The definer of the rule must explain its purpose.",
        "bind": "The agreement binds both sides to the same rule.",
        "facilitate": "The new system may facilitate online learning.",
        "forbid": "The rule forbids visitors from entering the area.",
        "wrestle": "Researchers wrestle with the problem for many years.",
        "transact": "The company transacts business through a secure website.",
        "cept": "In this example, “cept” is treated as a technical abbreviation.",
        "abbreviate": "Editors often abbreviate long titles.",
        "downgrade": "The agency may downgrade the forecast after new evidence appears.",
        "upgrading": "Upgrading the network can improve access to online classes.",
        "elevate": "The program may elevate the standard of public services.",
        "leveraged": "The firm leveraged its data to improve the service.",
        "leveraging": "Leveraging local knowledge can improve the policy.",
        "translocate": "The process can translocate material from one cell to another.",
        "mutate": "A virus can mutate when conditions change.",
        "permute": "The program can permute the order of the items.",
        "transpose": "The editor had to transpose two figures in the table.",
        "deregulated": "The industry was deregulated after a long public debate.",
        "circumscribe": "The law circumscribes the power of the agency.",
        "restrain": "The rules restrain companies from making false claims.",
        "abate": "The new measure may abate the pressure on housing.",
        "interdict": "The court may interdict the sale of unsafe products.",
        "repress": "Strict rules may repress open discussion.",
        "augment": "The grant will augment the library's research budget.",
        "aware": "The researchers are aware of the possible risk.",
        "blue": "The sky was blue after the storm.",
        "cloudy": "The sky remained cloudy throughout the morning.",
        "foggy": "The road was foggy early in the morning.",
        "bicameral": "The country has a bicameral legislature.",
        "antiseptic": "The nurse cleaned the wound with an antiseptic solution.",
        "compatible": "The two systems are compatible with each other.",
        "Compatible": "The two systems are compatible with each other.",
        "exorbitant": "The exorbitant price made the service hard to afford.",
        "electrical": "The building needs a safer electrical system.",
        # 这些词不能使用“study links ... to public life”之类的抽象模板；
        # 例句必须体现它们在真实语境中的搭配。
        "levity": "The speaker used levity to ease the tension in the room.",
        "alleviate": "The new bus service may alleviate traffic in the city center.",
        "alleviation": "The new measure brought some alleviation to families facing high costs.",
        "alleviatory": "The treatment had an alleviatory effect on the patient's pain.",
        "elevation": "The elevation of the road reduced the risk of flooding.",
        "elevated": "The report found elevated levels of air pollution near the factory.",
        "elevator": "The elevator stopped on the third floor.",
        "elevatory": "The elevatory force lifted the platform slowly.",
        "lever": "The machine uses a lever to lift the heavy cover.",
        "leverage": "The small firm used its local knowledge as leverage in the talks.",
        "levitate": "The device can levitate a small object above the surface.",
        "relief": "The new clinic brought relief to patients in the village.",
        "relievable": "The pain is relievable with rest and simple treatment.",
        "relieve": "The new bus service may relieve traffic in the city center.",
        "permeate": "A feeling of uncertainty began to permeate the workplace.",
        "eject": "The referee may eject a player who breaks the rules.",
        "ejection": "The ejection of the player stopped the match.",
        "ejected": "The player was ejected from the game for breaking the rules.",
        "ejector": "The ejector pushed the empty cartridge out of the machine.",
        "injection": "The injection reduced the patient's pain.",
        "injected": "The doctor injected the medicine into the patient's arm.",
        "rejection": "The rejection of the proposal surprised the committee.",
        "rejected": "The committee rejected the proposal after reviewing the evidence.",
        "projected": "The model projected a rise in energy demand.",
        "dejected": "The student felt dejected after receiving the result.",
        "irrelevance": "The judge rejected the evidence because of its irrelevance to the case.",
        "irrelevancy": "The irrelevancy of the detail became clear during the review.",
        "irrelevant": "The final paragraph contains several irrelevant details.",
        "irrelevantly": "The point was introduced irrelevantly and did not help the discussion.",
        "relevancy": "The committee questioned the relevancy of the old data to the new policy.",
        "relevantly": "The witness answered relevantly and stayed focused on the question.",
    }
    if w in special:
        return special[w]

    if any(mark in pos for mark in ("conj", "prep", "pron")):
        return f'The writer uses “{w}” to connect two ideas.'
    # 词表里大量 -ed/-ing 词条本身是过去分词或现在分词，不能再套
    # ``tried to WORD`` 这类原形动词句式。先处理词形，再处理词性，避免
    # 出现 ``tried to refined``、``may regulating`` 等显眼的语法错误。
    if w.endswith("ed") and len(w) > 4:
        if "被动形式" in lower_meaning:
            if any(mark in lower_meaning for mark in ("驱逐", "逐出")):
                return f"The player was {w} from the game."
            if any(mark in lower_meaning for mark in ("注入", "注射")):
                return f"The medicine was {w} into the patient's arm."
            if any(mark in lower_meaning for mark in ("拒绝", "驳回")):
                return f"The proposal was {w} after the review."
            if any(mark in lower_meaning for mark in ("投影", "预测", "投射")):
                return f"The model {w} a rise in demand."
            return ""
        # 过去分词、形容词和名词同样可能以 -ed 结尾。只有确认它是
        # 动词过去分词时才使用被动结构，否则先给出稳妥的系表句/术语句。
        if pos.startswith("n"):
            return ""
        if pos.startswith("adj") or any(mark in lower_meaning for mark in ("的", "性的", "相关")):
            if any(mark in lower_meaning for mark in ("家具", "设备", "材料")):
                return f"The report lists the {w} items used in the project."
            return ""
        if any(mark in lower_meaning for mark in ("提供", "给予", "提出")):
            return f"The service was {w} to all students."
        if any(mark in lower_meaning for mark in ("驱逐", "赶走", "除名")):
            return f"The person was {w} from the area."
        if any(mark in lower_meaning for mark in ("进口", "出口")):
            return f"The goods were {w} last month."
        if any(mark in lower_meaning for mark in ("取代", "替换")):
            return f"The old system was {w} after the reform."
        if any(mark in lower_meaning for mark in ("定义", "界定", "规定", "限制", "调整", "修复", "重建", "复制")):
            return f"The method was {w} after the review."
        if pos.startswith("v"):
            return f"The result was {w} after the review."
        return ""
    if w.endswith("ing") and len(w) > 5:
        if pos.startswith("n"):
            return ""
        if pos.startswith("adj"):
            return f"The process was {w}."
        if any(mark in lower_meaning for mark in ("征税", "申请", "请求", "请愿")):
            return f"The group is {w} for support."
        if any(mark in lower_meaning for mark in ("发生", "爆发", "期满", "失效", "逝世")):
            return f"The change is {w} over time."
        return ""
    # 不再让所有副词共享一个“prices changed”句型；同一模板会制造大量
    # 与词义无关的例句，例如 financially/infinitesimally。
    if pos.startswith("adv") or w.endswith("ly"):
        # 副词必须修饰一个语义上可被修饰的动作或判断；不能把
        # fortunately、nearby、lately 等全部接到 implemented/occurred 后面。
        if any(mark in lower_meaning for mark in ("清楚", "明确", "明显", "准确", "认真", "仔细")):
            return f"The researchers explained the result {w}."
        if any(mark in lower_meaning for mark in ("频繁", "反复", "逐渐", "突然", "迅速", "缓慢")):
            return f"The situation changed {w} during the year."
        if any(mark in lower_meaning for mark in ("幸好", "不幸", "可能", "大概", "也许")):
            return f"The plan will {w} reduce the cost."
        if any(mark in lower_meaning for mark in ("在附近", "向上", "向下", "向外", "向内", "向后", "向前")):
            return f"The children moved {w} after the lesson."
        return ""
    # 名词后缀判断必须先于中文释义关键词判断；例如 definition 含有“定义”，
    # 但它是名词，不能误生成 “may definition”。
    noun_suffixes = (
        "tion", "sion", "ment", "ness", "ity", "ance", "ence", "ship",
        "ism", "ist", "er", "or", "ee", "ery", "hood", "dom", "ure", "ude",
    )
    if pos.startswith("v"):
        return verb_example(w, meaning, pos)
    if pos.startswith("n") or w.endswith(noun_suffixes):
        # 先按释义选择能与名词自然搭配的主语/动词，避免把“人、地点、
        # 设备、抽象概念”全部塞进同一个模板。例句必须展示该词的用法，
        # 不能用“这个词是名词”之类的元语言句冒充例句。
        if any(mark in lower_meaning for mark in (
            "人；", "人,", "者", "员", "家", "师", "官员", "部长", "学生", "研究者",
        )):
            return f"The {w} joined the meeting and shared a view."
        if any(mark in lower_meaning for mark in ("学院", "学校", "大学", "城市", "国家", "地区", "地点", "场所", "建筑")):
            return f"The {w} is open to the public."
        if any(mark in lower_meaning for mark in ("机器", "设备", "工具", "仪器", "装置", "材料", "物质")):
            return f"The {w} is used in the experiment."
        if any(mark in lower_meaning for mark in ("疾病", "病", "症状", "疼痛", "伤", "治疗")):
            return f"The doctor treated the patient for {w}."
        if any(mark in lower_meaning for mark in ("时间", "月份", "下午", "上午", "昨天", "今天", "明天")):
            return f"The meeting took place in {w}."
        if any(mark in lower_meaning for mark in ("钱", "货币", "税", "费用", "收入", "财富", "经济", "金融", "资金")):
            return f"The policy affected {w} in the region."
        if any(mark in lower_meaning for mark in ("问题", "观点", "想法", "概念", "现象", "过程", "状态", "行为", "关系", "变化", "能力", "意义")):
            return f"The study examines {w} in education."
        if any(mark in lower_meaning for mark in ("结果", "证据", "数据", "报告", "研究", "方法", "理论", "原则", "政策")):
            return f"The report presents new evidence about {w}."
        if any(mark in lower_meaning for mark in ("驱逐", "逐出", "排出", "喷出")):
            return f"The {w} of the player stopped the match."
        if any(mark in lower_meaning for mark in ("注射", "针剂", "注入")):
            return f"The {w} reduced the patient's pain."
        if any(mark in lower_meaning for mark in ("拒绝", "驳回", "抛弃")):
            return f"The {w} of the proposal surprised the committee."
        if any(mark in lower_meaning for mark in ("投影", "发射", "预测", "规划")):
            return f"The {w} of future costs helped the committee plan."
        # -tion/-sion/-ment 等通常是动作或结果名词，用“改变研究结果”
        # 展示名词位置；这比 “The term ... is a noun” 更有学习价值。
        action_suffixes = ("tion", "sion", "ment", "ness", "ity", "ance", "ence", "ism", "ship", "hood", "dom", "ure", "ude")
        if w.endswith(action_suffixes) or any(mark in lower_meaning for mark in (
            "认识", "钦佩", "态度", "意识", "痛苦", "愤怒", "兴趣", "希望", "勇气", "观点", "行为", "过程", "状态", "关系", "能力", "意义", "作用", "影响", "变化",
        )):
            return f"The study examines how {w} affects the final decision."
        # 无法确认自然搭配时不硬造句；交给真题、词典例句或人工精选。
        return ""
    if w.endswith("ed"):
        templates = (
            f"The method was {w} after the first trial.",
            f"The report presents a {w} version of the proposal.",
            f"The data were {w} before the final analysis.",
        )
        return templates[sum(map(ord, w)) % len(templates)]
    if w.endswith("ing"):
        templates = (
            f"The process of {w} requires careful planning.",
            f"The team is {w} the method for wider use.",
            f"{w.capitalize()} the data takes more time than expected.",
        )
        return templates[sum(map(ord, w)) % len(templates)]
    if pos.startswith("adj") or any(mark in lower_meaning for mark in ("的", "性的", "相关")):
        if any(mark in lower_meaning for mark in ("知道", "意识到")):
            return f"The researchers are {w} of the possible risk."
        if any(mark in lower_meaning for mark in ("危险", "风险")):
            return f"The activity may be {w} for young children."
        if any(mark in lower_meaning for mark in ("兼容", "相容", "和睦")):
            return f"The two systems are {w} with each other."
        if any(mark in lower_meaning for mark in ("富裕", "贫穷", "贫困", "有钱")):
            return f"The family is {w} but still supports public education."
        if any(mark in lower_meaning for mark in ("情绪", "高兴", "悲伤", "愤怒", "害怕", "疲惫", "满意")):
            return f"The student felt {w} after the result."
        if any(mark in lower_meaning for mark in ("国家", "地区", "东方", "西方", "北方", "南方", "国际")):
            return f"The report examines {w} policy."
        if any(mark in lower_meaning for mark in ("行政", "管理")):
            return f"The decision was mainly {w} rather than political."
        if any(mark in lower_meaning for mark in ("睡着", "醒着", "生病", "醉", "饥饿", "害怕", "惭愧", "嫉妒", "想家", "喘不过气")):
            return f"The student was {w} after the long journey."
        if any(mark in lower_meaning for mark in ("国家", "地区", "东方", "西方", "北方", "南方", "南极", "北极", "农业", "气候", "植物", "宇宙", "殖民")):
            return f"The report discusses {w} issues."
        if any(mark in lower_meaning for mark in ("错误", "不正确", "可疑", "不明确", "不可能", "无效", "无害", "可避免", "灾难")):
            return f"The claim was {w}."
        if any(mark in lower_meaning for mark in ("高兴", "快乐", "悲伤", "愤怒", "温和", "勇敢", "诚实", "体贴", "好客", "富幽默")):
            return f"The student was {w} during the discussion."
        article = "an" if w[:1] in "aeiou" else "a"
        # 形容词默认修饰一个可讨论的名词；不再生成 “The result was X”
        # 这种看似完整、但经常与词义不相容的句子。
        return ""
    if any(mark in lower_meaning for mark in (
        "使", "导致", "影响", "改变", "增加", "减少", "提高", "降低", "解决", "研究", "描述", "证明",
        "承认", "支持", "避免", "保护", "遵守", "完成", "认可", "选择", "接受", "拒绝", "提供",
        "要求", "允许", "包括", "解释", "强调", "比较", "建议", "促进", "维持", "建立", "发现", "抛弃",
        "攻击", "折磨", "担心", "使用", "采用", "宣布", "传达", "参加", "出现", "发生", "存在",
        "分析", "消遣", "改进", "提炼", "整修", "定义", "限定", "规定", "融资", "再融资",
        "完成", "限制", "澄清", "描述", "处理", "提供", "制造", "生产", "改善", "修正",
        "打算", "意图", "包含", "需要", "代表", "影响", "导致", "表示", "获得", "存在", "涉及",
        "采取", "引起", "构成", "产生", "形成", "反映", "适应", "依赖", "说明", "表明", "参与",
        "确保", "管理", "发展", "调查", "增加", "减少", "提高", "降低", "消费", "采用", "宣布",
    )):
        return verb_example(w, meaning, pos)
    # 词性和搭配无法确认时不再写“这个词是……/句子使用了……”这类元语言句。
    # 这种句子形式完整，却没有展示目标词的真实用法，必须留给可靠语料或人工精选。
    return ""


def quality_score(sentence):
    count = len(sentence.split())
    # 完整、长度适中的阅读句优先，避免把题目说明或超长段落当例句。
    return abs(count - 22) + (12 if "[A]" in sentence else 0)


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    vocab = {
        clean_word(word.get("word", ""))
        for root in data.get("roots", [])
        for word in root.get("words", [])
        if clean_word(word.get("word", ""))
    }
    form_to_words = {}
    for word in vocab:
        for form in word_forms(word):
            form_to_words.setdefault(form, set()).add(word)

    best = {}
    external_stats = {
        "directories": [str(path.relative_to(ROOT)) for path in EXAM_CORPUS_DIRS],
        "files": [],
        "recognizedFiles": 0,
        "candidateSentences": 0,
        "matchedWords": 0,
        "sourceCounts": {},
    }
    files = sorted(PAPERS_DIR.glob("*/*.md"))
    for path in files:
        for year, sentence, tokens in sentence_candidates(path):
            matched = set()
            for token in tokens:
                matched.update(form_to_words.get(token, ()))
            for word in matched:
                candidate = {
                    "example": sentence,
                    "source": f"{year}年真题（本地原文）",
                    "sourceFile": str(path.relative_to(ROOT)),
                }
                score = quality_score(sentence)
                if word not in best or score < best[word][0]:
                    best[word] = (score, candidate)

    # 早期真题以 DOC 保存；这些句子同样来自原文，只作为尚未命中的词的补充。
    doc_files = sorted((ROOT / "material" / "Kaoyan-English1-Papers" / "KaoYan-English").rglob("*.doc"))
    for path in doc_files:
        for sentence, tokens in doc_sentence_candidates(path):
            matched = set()
            for token in tokens:
                matched.update(form_to_words.get(token, ()))
            for word in matched:
                if word not in best:
                    best[word] = (30, {
                        "example": sentence,
                        "source": "历年考研真题（DOC原文）",
                        "sourceFile": str(path.relative_to(ROOT)),
                    })

    # 外部考试语料作为独立来源接入。只有句子本身包含目标词（或常见词形）
    # 才会入库；CET4.json 这类纯词表没有 example/sentence 字段，因此不会
    # 被误判为例句来源。
    for path in external_exam_files():
        label = exam_label(path)
        rows = external_exam_candidates(path)
        external_stats["files"].append({
            "file": str(path.relative_to(ROOT)),
            "source": label,
            "sentences": len(rows),
        })
        if rows:
            external_stats["recognizedFiles"] += 1
        external_stats["candidateSentences"] += len(rows)
        for sentence, tokens in rows:
            matched = set()
            for token in tokens:
                matched.update(form_to_words.get(token, ()))
            for word in matched:
                external_stats["matchedWords"] += 1
                external_stats["sourceCounts"][label] = external_stats["sourceCounts"].get(label, 0) + 1
                candidate = {
                    "example": sentence,
                    "source": label,
                    "sourceFile": str(path.relative_to(ROOT)),
                }
                # 外部考试原文优先于辅助句，但不覆盖已经提取出的考研原文。
                score = quality_score(sentence) + 2
                if word not in best or score < best[word][0]:
                    best[word] = (score, candidate)

    # 补充项目内词根表的考研语境例句，但绝不覆盖已经从真题原文提取的句子。
    for word, candidate in workbook_examples().items():
        best.setdefault(word, (8, candidate))

    # 最后使用 WordDecoder 自带的完整英文例句；这类句子不标为历年真题。
    decoder = json.loads(WORDDECODER_FILE.read_text(encoding="utf-8")) if WORDDECODER_FILE.exists() else {}
    for word in vocab:
        if word in best:
            continue
        sentence = worddecoder_example(decoder.get("words", {}).get(word), word)
        if sentence:
            best[word] = (15, {
                "example": sentence,
                "source": "WordDecoder例句",
                "sourceFile": str(WORDDECODER_FILE.relative_to(ROOT)),
            })

    # 最后为仍没有语料的词提供低难度辅助句，避免把词硬塞进不匹配的语境。
    for root in data.get("roots", []):
        for item in root.get("words", []):
            word = clean_word(item.get("word", ""))
            if word in best:
                continue
            entry = decoder.get("words", {}).get(word, {})
            raw_word = item.get("word", "")
            sentence = simple_example(
                raw_word,
                item.get("meaning", ""),
                entry.get("pos", "") or ECDICT_POS.get(clean_word(raw_word), ""),
            )
            if sentence:
                best[word] = (40, {
                    "example": sentence,
                    "source": "简明示例句（辅助）",
                    "sourceFile": "build_verified_examples.py",
                })

    output = {word: item for word, (_, item) in sorted(best.items())}
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    EXTERNAL_AUDIT_FILE.write_text(
        json.dumps(external_stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "sourceFiles": len(files),
        "verifiedWords": len(output),
        "externalExamFiles": len(external_stats["files"]),
        "externalExamSentences": external_stats["candidateSentences"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
