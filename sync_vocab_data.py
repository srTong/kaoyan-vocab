#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一词根词汇数据，并补充音标、释义和缺失例句。"""

import json
import re
import random
import collections
import csv
import eng_to_ipa as ipa
try:
    import pronouncing
except ImportError:
    pronouncing = None
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "material" / "website" / "data"
MAIN_FILE = DATA_DIR / "data.json"
ENGRA_FILE = DATA_DIR / "engra_roots_specific.json"
WORDDECODER_DIR = ROOT / "third_party" / "worddecoder"
WORDDECODER_FILE = WORDDECODER_DIR / "data" / "lexicon.json"
VERIFIED_EXAMPLES_FILE = DATA_DIR / "verified_examples.json"
EXAMPLE_CORPUS_AUDIT_FILE = DATA_DIR / "example_corpus_audit.json"
ECDICT_FILE = ROOT / "third_party" / "ecdict" / "ecdict.csv"

# WordDecoder 的规范词根偶尔以历史异形作为 key。面向学习者展示时，优先沿用更直观的形态。
WORDDECODER_ROOT_PREFERRED = {
    "phos": "photo",   # phot/phos（光）沿用项目已有 photo 卡片
    "string": "struct",  # string/strict/strain/stress/struct 中，构词教学优先展示 struct
    "un": "uni",       # 拉丁词根 un/uni（一）与否定前缀 un- 分卡
    "bi": "bio",       # 希腊词根 bi（生命）与数字前缀 bi-（二）分卡
    "de": "dei",       # 词根 de（神）与方向前缀 de- 分卡
    "di": "diurn",     # 词根 di（日）与数字/分离前缀 di- 分卡
    "mis": "mit",      # mis（发送）并入 mit/miss 词族，与否定前缀 mis- 分卡
    "em": "empt",      # em/empt（买）与使动前缀 em- 分卡
}
VOCAB_SCOPES = ["中考", "高考", "四级", "六级", "考研", "托福", "雅思"]
WORDDECODER_MEANING_FIXES = {
    "absent": "缺席的；不在场的",
    "affirm": "断言；确认；肯定",
    "abroad": "在国外；到国外",
    "counterclockwise": "逆时针地",
    "demobilize": "使复员；遣散",
    "menace": "威胁；恐吓",
    "patricide": "弑父；弑父者",
    "solidify": "使凝固；巩固",
    "upstairs": "在楼上；楼上的",
    "unequal": "不相等的；不平等的",
    "gratify": "使满意；满足",
    "grandiloquent": "言辞浮夸的；夸夸其谈的",
    "instrument": "工具；仪器；手段",
    "stringent": "严格的；严厉的",
    "disdain": "鄙视；蔑视",
    "secretary": "秘书；部长；大臣",
    "rank": "等级；地位；排列",
    "damn": "诅咒；该死",
    "ac": "交流电；空调（常用缩写）",
    "children": "儿童；孩子们（child 的复数）",
    "feet": "脚；英尺（foot 的复数）",
    "at": "在（某处或某时）；向；以",
    "under": "在……下面；低于；在……之下",
    "up": "向上；在上方；增加",
}
WORDDECODER_WORD_FIXES = {
    # WordDecoder 原串写作 sent=to be，但 sent 在根表中误命中“感觉”；实际来自拉丁 esse（存在）。
    "absent": {
        "root": "ess",
        "parts": [
            {"kind": "prefix", "form": "ab", "mean": "离开"},
            {"kind": "root", "form": "ess", "group": "ess", "mean": "存在"},
        ],
    },
}
# 同形但词源完全不同的词不能仅凭拼写归入 dict/dic 词族。
WORDDECODER_ROOT_EXCLUSIONS = {"ditch"}

# 第一批人工精选例句：尽量贴近考研阅读中常见的教育、经济、科技和社会议题。
CURATED_EXAMPLES = {
    "its": "The company changed its policy after the review.",
    "ac": "AC power is common in modern buildings.",
    "children": "Children learn better when they feel safe at school.",
    "feet": "The child hurt his feet while running.",
    "at": "The meeting starts at nine in the morning.",
    "under": "The temperature fell under the level expected by researchers.",
    "up": "The new policy pushed up the cost of housing.",
    "ag": "The root ag means “to do” in related words.",
    "direct": "The direct route takes less time.",
    "franc": "The franc was once used as the national currency.",
    "consume": "People consume less energy when buildings are well designed.",
    "ced": "The root ced means “go” in words such as precede and proceed.",
    "accessible": "The library is accessible to students with disabilities.",
    "concede": "The committee conceded the point after reviewing the evidence.",
    "concession": "The company received a tax concession for creating local jobs.",
    "concessioner": "The concessioner received a permit to operate the market stall.",
    "collegian": "The collegian joined a student research group.",
    "collegium": "The collegium brought together scholars from several fields.",
    "commuter": "Many commuters use public transport to reach work.",
    "commuting": "Commuting takes less time when buses are reliable.",
    "coevolution": "The coevolution of plants and insects shaped the ecosystem.",
    "coevolutionary": "The coevolutionary process changed both species.",
    "levying": "The government is levying a tax on imported goods.",
    "exceed": "The cost may exceed the original estimate.",
    "exceedingly": "The method is exceedingly difficult to apply.",
    "excess": "Excess water can damage the crop.",
    "excessive": "Excessive screen time can reduce sleep.",
    "precede": "A short introduction precedes the main discussion.",
    "preceding": "The preceding paragraph explains the main assumption.",
    "precedent": "The court's decision set a useful precedent for later cases.",
    "preceded": "The reform was preceded by several years of public debate.",
    "precedented": "The action was precedented by an earlier court ruling.",
    "precedential": "The ruling may have precedential value in future cases.",
    "predecessor": "The new director thanked her predecessor for the work.",
    "precedence": "Public safety should take precedence over short-term profit.",
    "precession": "The telescope measures the precession of the planet's axis.",
    "proceed": "After the review, the committee decided to proceed with the plan.",
    "proceeding": "The legal proceeding lasted several months.",
    "proceedings": "The court published the proceedings after the hearing.",
    "concessionaire": "The concessionaire operates the food service at the station.",
    "concessionary": "The government offers concessionary loans to small firms.",
    "recede": "The floodwaters began to recede after the storm.",
    "receding": "The receding water exposed new land.",
    "recess": "The court took a short recess before the hearing.",
    "recessed": "The lights were recessed into the ceiling.",
    "recessional": "The economy entered a recessional period.",
    "recessionary": "Recessionary pressure can reduce household spending.",
    "recession": "The recession reduced household income and public spending.",
    "recessive": "The trait is recessive and may remain hidden for a generation.",
    "secession": "The debate over secession divided the region.",
    "secessionist": "The government arrested several secessionist leaders.",
    "successive": "The policy failed in three successive years.",
    "unprecedented": "The country faced an unprecedented rise in housing costs.",
    "unprecedentedly": "Demand rose unprecedentedly fast during the crisis.",
    "affluence": "Rising affluence has increased demand for private education.",
    "affluent": "Affluent families can afford private education.",
    "afflux": "The afflux of workers into the city put pressure on housing.",
    "circumfluent": "The circumfluent river surrounds the small island.",
    "confluence": "The confluence of two rivers created a fertile plain.",
    "confluent": "The two confluent rivers meet near the village.",
    "defluent": "Defluent water moved away from the lake.",
    "effluent": "The factory must treat its effluent before releasing it.",
    "flu": "The flu kept the student away from school for a week.",
    "fluency": "Regular practice can improve students' fluency in English.",
    "fluent": "She is fluent in English and can read research papers with ease.",
    "fluently": "The student speaks English fluently after years of practice.",
    "fluid": "The market remains fluid as the policy changes.",
    "fluidity": "The fluidity of the labor market affects job changes.",
    "fluidize": "The process can fluidize the solid material with heat.",
    "fluidized": "The powder was fluidized by heated air.",
    "flux": "The constant flux of workers changed the character of the town.",
    "fluxion": "The model describes the fluxion of heat through the material.",
    "fluxional": "The fluxional nature of the market makes forecasts difficult.",
    "influenced": "The final decision was influenced by the new evidence.",
    "influencing": "Social media is influencing how students learn.",
    "influential": "The paper was influential in shaping later research.",
    "influenza": "Influenza can spread quickly in crowded classrooms.",
    "influx": "The city struggled to provide housing after an influx of workers.",
    "interfluent": "The interfluent streams joined before entering the lake.",
    "refluence": "The refluence of seawater changed the shape of the coast.",
    "refluent": "Refluent water returned to the channel after the storm.",
    "reflux": "The device controls reflux during the experiment.",
    "superfluid": "At very low temperatures, helium can become a superfluid.",
    "superfluidity": "Superfluidity allows helium to flow with almost no resistance.",
    "superfluity": "The editor removed the superfluity from the report.",
    "superfluous": "The final paragraph was superfluous and added no new evidence.",
    "uninfluenced": "The decision was uninfluenced by political pressure.",
    "uninfluential": "The minor detail was uninfluential in the final decision.",
    "vadvas": "The root vad means “go” in related words.",
    "adviseradvisor": "The adviser gave the committee practical advice.",
    "vitamine": "The body needs vitamin E for normal growth.",
    "define": "The study defines success as long-term social progress.",
    "definition": "The paper gives a clear definition of the key term.",
    "fined": "The company was fined for breaking the safety rules.",
    "finish": "The team hopes to finish the project this month.",
    "finishing": "Finishing the work on time required careful planning.",
    "predefine": "The software can predefine the basic settings.",
    "redefine": "New evidence may redefine the problem.",
    "refinance": "The firm plans to refinance its debt.",
    "definitional": "The paper makes a clear definitional distinction between the two terms.",
    "definitively": "The evidence does not definitively prove the claim.",
    "refinery": "The refinery processes crude oil into fuel.",
    "refining": "Refining crude oil produces fuel and other products.",
    "refined": "The company refined its method after the trial.",
    "unrefined": "The data were still unrefined and difficult to use.",
    "refine": "Workers refine raw materials before they are used.",
    "refinish": "Workers refinish the table after repairing it.",
    "refiner": "The refiner removes impurities from the material.",
    "addict": "The doctor treated the addict with care.",
    "dict": "The root dict means “to say” and appears in words such as predict and contradict.",
    "dictate": "The manager dictated the terms of the agreement.",
    "dictated": "The terms were dictated by the manager.",
    "dictation": "The teacher read the sentence aloud for dictation.",
    "dictator": "The dictator ruled the country for many years.",
    "americanophile": "The scholar was an Americanophile who supported closer ties with the United States.",
    "anglophile": "The Anglophile scholar often wrote about British history.",
    "philogyny": "The article examines philogyny in early educational writing.",
    "confine": "The policy confines the use of the data to research purposes.",
    # ject 词族：例句必须体现“投掷、驱逐、反对、插入”等具体用法，
    # 不使用“这个词是名词/动词”的元语言句。
    "abject": "The refugees lived in abject poverty after the disaster.",
    "abjection": "The novel describes the abjection of people excluded from society.",
    "abjectly": "The plan failed abjectly to protect the poor.",
    "adjacent": "The two buildings are adjacent to each other.",
    "adjectival": "The word “economic” has an adjectival use in this sentence.",
    "adjective": "In “public policy,” “public” is an adjective.",
    "conjecturable": "The cause is conjecturable from the available evidence.",
    "conjectural": "The explanation remains conjectural because the evidence is limited.",
    "conjecture": "The claim is still a conjecture, not a proven fact.",
    "deject": "Repeated failure may deject young researchers.",
    "dejected": "The student felt dejected after receiving the result.",
    "eject": "The referee may eject a player who breaks the rules.",
    "ejecta": "The volcano sent ejecta into the air.",
    "ejected": "The player was ejected from the game for breaking the rules.",
    "ejection": "The ejection of the player stopped the match.",
    "ejector": "The ejector pushed the empty cartridge out of the machine.",
    "inject": "The doctor injected the medicine into the patient's arm.",
    "injectable": "The medicine is injectable and can be given at home.",
    "injected": "The doctor injected the medicine into the patient's arm.",
    "injection": "The injection reduced the patient's pain.",
    "injector": "The injector delivered fuel into the engine.",
    "interject": "She interjected with a brief comment during the meeting.",
    "interjection": "“Oh” is an interjection that expresses surprise.",
    "intersubjective": "The researchers reached an intersubjective understanding of the experience.",
    "intersubjectivity": "The study emphasizes intersubjectivity in research interviews.",
    "nonobjective": "The article gives a nonobjective account of the dispute.",
    "object": "Many residents object to the plan.",
    "objectification": "The objectification of women in advertising has drawn criticism.",
    "objectify": "The campaign should not objectify people for commercial gain.",
    "objection": "The lawyer raised an objection to the question.",
    "objectionable": "The advertisement contains objectionable language.",
    "objective": "The main objective is to improve access to education.",
    "objectively": "The evidence should be assessed objectively.",
    "objectivism": "The paper compares objectivism with other theories of knowledge.",
    "objectivist": "The objectivist argues that facts exist independently of opinion.",
    "objectivity": "Researchers should aim for objectivity when evaluating evidence.",
    "objector": "The objector explained why the proposal violated the rules.",
    "projected": "The model projected a rise in energy demand.",
    "projectile": "The device launched a projectile across the test area.",
    "projecting": "The model is projecting higher energy demand next year.",
    "projection": "The projection of future costs helped the committee plan.",
    "projectionist": "The projectionist started the film at eight.",
    "projective": "The test uses a projective method to explore hidden attitudes.",
    "projector": "The teacher used a projector to display the data.",
    "reject": "The committee may reject the proposal if costs rise.",
    "rejected": "The committee rejected the proposal after reviewing the evidence.",
    "rejecter": "The rejecter signed a report opposing the plan.",
    "rejection": "The rejection of the proposal surprised the committee.",
    "rejectionist": "The rejectionist opposed the agreement in the debate.",
    "subject": "The subject of the study is access to education.",
    "subjection": "The study examines the subjection of workers to unsafe conditions.",
    "subjective": "The judgment was subjective and depended on personal opinion.",
    "subjectively": "The results were interpreted subjectively by the reviewer.",
    "subjectivism": "The course discusses subjectivism in modern philosophy.",
    "subjectivist": "The subjectivist emphasizes personal experience over universal rules.",
    "subjectivity": "The study examines how subjectivity affects judgment.",
    "unobjectionable": "The committee found the proposal unobjectionable.",
    "quarterfinal": "The team reached the quarterfinal after a close match.",
    "finisher": "The finisher completed the last stage of the process.",
    "finalist": "The finalist presented a strong plan to the committee.",
    "finality": "The court's decision brought finality to the long dispute.",
    "financier": "The financier invested in projects that support rural development.",
    "fineness": "The fineness of the powder affects how quickly it dissolves.",
    "absent": "Workers who are absent from training may find it harder to adapt to technological change.",
    "alike": "The two education systems are alike in principle but differ greatly in how they are funded.",
    "affirm": "The court's decision affirmed the principle that all citizens should be treated equally.",
    "affirmable": "The claim is affirmable only if it is supported by evidence that other researchers can verify.",
    "affirmation": "Public support for the policy was seen as an affirmation of the need for reform.",
    "affirmative": "Only a minority of respondents gave an affirmative answer to the final question.",
    "affirmatively": "The committee responded affirmatively after reviewing the evidence presented by the researchers.",
    "affirming": "An affirming school environment can encourage students to express their ideas with confidence.",
    "disaffirm": "An appeals court may disaffirm a ruling if the lower court applied the law incorrectly.",
    "disaffirmation": "The disaffirmation of the earlier ruling forced regulators to reconsider the policy.",
    "reaffirm": "The report reaffirms the importance of public investment in basic research.",
    "reaffirmation": "The agreement represented a reaffirmation of both countries' commitment to scientific cooperation.",
    "access": "Equal access to quality education remains a major challenge for children in rural areas.",
    "achieve": "Schools need stable funding if they are to achieve meaningful improvements in student performance.",
    "acknowledge": "The report acknowledges that economic growth alone cannot solve the problem of inequality.",
    "adapt": "Universities must adapt their teaching methods as artificial intelligence changes the workplace.",
    "address": "The new policy aims to address the shortage of affordable housing in large cities.",
    "advantage": "Online courses offer the advantage of flexibility, but they also require students to manage their time well.",
    "affect": "Rising temperatures are likely to affect agricultural production in many regions.",
    "alternative": "Public transport is a practical alternative to private cars in densely populated cities.",
    "approach": "The researchers adopted a more cautious approach when interpreting the survey results.",
    "assess": "Before changing the curriculum, the university should assess what skills employers actually need.",
    "benefit": "Small businesses can benefit from digital tools that reduce administrative costs.",
    "challenge": "The central challenge is to protect personal data without slowing technological innovation.",
    "claim": "The author claims that convenience should not be treated as the only measure of progress.",
    "consequence": "A lack of investment in public libraries may have serious consequences for disadvantaged students.",
    "consume": "People consume less energy when buildings are well designed.",
    "contribute": "Scientific research can contribute to economic development when its findings are shared widely.",
    "decline": "The decline in local manufacturing has changed the employment structure of the region.",
    "demand": "The demand for workers with technical and communication skills continues to grow.",
    "despite": "Despite rapid advances in medicine, preventive care remains unavailable to many communities.",
    "environment": "A healthy learning environment encourages students to ask questions and revise their assumptions.",
    "eastern": "Manufacturing remains concentrated in the eastern part of the country, where transport links are stronger.",
    "evidence": "There is growing evidence that early reading experience improves children's later academic performance.",
    "factor": "Income is an important factor, but it is not the only factor influencing educational opportunity.",
    "impact": "The impact of automation will depend partly on whether workers receive opportunities for retraining.",
    "improve": "Better data can help local governments improve the delivery of public services.",
    "innovation": "Innovation is most useful when it responds to a real social need rather than creating demand for its own sake.",
    "investment": "Long-term investment in basic research often produces benefits that cannot be predicted in advance.",
    "maintain": "The institution must maintain public trust by explaining clearly how it uses personal information.",
    "measure": "Economic output is an important measure, but it does not fully describe people's quality of life.",
    "policy": "A successful climate policy must combine environmental goals with practical support for affected workers.",
    "pile": "A growing pile of electronic waste has raised concerns about the environmental cost of new technology.",
    "predict": "No model can predict social change perfectly, because human decisions are difficult to reduce to a formula.",
    "predicted": "The predicted result was close to the actual result.",
    "unindicted": "The unindicted suspect was released after the investigation.",
    "prevent": "Simple safety rules can prevent many accidents in laboratories and factories.",
    "promote": "The program was designed to promote cooperation between universities and local industries.",
    "reduce": "Investing in public transport could reduce both traffic congestion and urban pollution.",
    "regulate": "Governments are still debating how to regulate online platforms without limiting legitimate speech.",
    "require": "Remote work requires managers to evaluate performance by results rather than by hours spent in an office.",
    "resource": "Water is a limited resource, so its use must be planned carefully in areas facing drought.",
    "research": "The research suggests that students learn more effectively when they receive timely feedback.",
    "significant": "The study found a significant difference between students who read regularly and those who did not.",
    "sustain": "Economic growth cannot be sustained if it depends on the continued destruction of natural resources.",
    "stable": "A stable policy environment allows businesses to make long-term investments with greater confidence.",
    "technology": "Technology can widen access to education, but only when reliable internet is available to everyone.",
    "tend": "People tend to underestimate long-term risks when immediate costs are visible.",
    "transform": "Digital archives have transformed the way researchers study historical documents.",
    "value": "The value of a university should not be judged solely by the salaries of its graduates.",
    "vary": "The effects of the policy vary according to income, age, and access to public services.",
}

CURATED_ETYMOLOGY = {
    "ced": "ced（构词词根，不作为独立单词使用）→ 走；前进",
    "ac": "AC（air conditioning 或 alternating current 的缩写）→ 空调；交流电",
    "children": "child（孩子）+ 不规则复数 → 儿童；孩子们",
    "feet": "foot（脚）+ 不规则复数 → 脚；英尺",
    "classical": "class（类别；等级）+ -ical（表示与……有关）→ 古典的；经典的",
    "acquaintance": "acquaint（使熟悉）+ -ance（表示状态）→ 熟人；认识",
    "collegian": "college（学院）+ -ian（表示人）→ 大学生；学院成员",
    "collegium": "collegium（学院；学术团体）→ 学院；学术团体",
    "commuter": "commute（通勤）+ -er（表示人）→ 通勤者",
    "commuting": "commute（通勤）+ -ing（表示动作）→ 通勤",
    "coevolution": "co-（共同）+ evolution（进化）→ 共同进化",
    "coevolutionary": "coevolution（共同进化）+ -ary（表示与……有关）→ 共同进化的",
    "levying": "levy（征税；征收）+ -ing（表示进行）→ 征税；征收",
    "at": "at（表示时间或位置）→ 在（某处或某时）；向；以",
    "under": "under（在下方）→ 在……下面；低于；在……之下",
    "up": "up（向上）→ 向上；在上方；增加",
    "concessionaire": "concession（特许权）+ -aire（表示人）→ 特许经营者；特许权获得者",
    "concessionary": "concession（让步；特许权）+ -ary（表示与……有关）→ 让步的；特许的；优惠的",
    "concession": "concede（让步）+ -ion（表示行为或结果）→ 让步；优惠；特许权",
    "concessioner": "concession（让步；特许权）+ -er（表示人）→ 让步者；特许权授予者",
    "receding": "re-（向后）+ ced（走）+ -ing（表示状态）→ 后退的；逐渐减退的",
    "recessed": "re-（向后）+ cess（走）+ -ed（表示状态）→ 嵌入式的；凹进的；后退的",
    "recessional": "re-（向后）+ cess（走）+ -ion + -al → 衰退的；经济衰退的",
    "recessionary": "recession（经济衰退）+ -ary（表示与……有关）→ 衰退的；经济衰退的",
    "recession": "re-（向后）+ cess（走）+ -ion（表示状态或结果）→ 经济衰退；衰退",
    "recessive": "recess（退隐）+ -ive（表示具有……性质）→ 隐性的；隐性遗传的",
    "secessionist": "secession（脱离；分裂）+ -ist（表示……主义者）→ 脱离主义者；分裂主义者",
    "procedurally": "procedural（程序的）+ -ly（表示以……方式）→ 程序上；按程序地",
    "proceedings": "proceed（进行）+ -ings（名词形式）→ 诉讼程序；会议记录",
    "precedential": "precedent（先例）+ -ial（表示与……有关）→ 作为先例的；有先例效力的",
    "americanophile": "American（美国的）+ -phile（喜爱……的人）→ 亲美者",
    "anglophile": "Anglo-（英国的；英格兰的）+ -phile（喜爱……的人）→ 亲英派的人；亲英者",
    "philogyny": "phil（喜爱）+ gyn（女性）+ -y（名词后缀）→ 对女性的喜爱或亲近倾向",
    "confine": "con-（共同、加强）+ fine（界限）→ 把范围限定在一起 → 限制；使局限",
    "condutor": "con-（共同、一起）+ duct（引导）+ -or（表示人或物）→ 引导或传导的人或物",
    "paraeducator": "para-（辅助）+ educator（教育者）→ 教育助理",
    "interfacing": "inter-（在……之间）+ face（界面）+ -ing（表示过程）→ 建立接口或连接",
    "referential": "refer（指向、提及）+ -ential（形容词后缀）→ 指示的；所指的",
    "antiintellectually": "anti-（反对）+ intellectual（智力的）+ -ly（以……方式）→ 反智地",
    "unelectable": "un-（不）+ elect（选举）+ -able（能够……的）→ 不可当选的",
    "irrelevance": "ir-（不）+ relevance（相关性）→ 不相关；离题",
    "overconsumption": "over-（过度）+ consumption（消费）→ 过度消费",
    "invisiblity": "in-（不、无）+ visibility（可见性）→ 不可见性；隐形",
    "define": "de-（明确、彻底）+ fine（界限）→ 划定界限 → 定义；界定",
    "definite": "define（定义；界定）+ -ite（形容词后缀）→ 明确的；确定的",
    "definition": "define（定义；界定）+ -ition（表示行为或结果）→ 定义；界定；释义",
    "definitive": "define（明确界定）+ -itive（形容词后缀）→ 明确的；决定性的",
    "financial": "finance（财政；金融）+ -ial（表示与……有关）→ 财政的；金融的",
    "financially": "financial（财政的；金融的）+ -ly（表示以……方式）→ 在财政上；在经济上",
    "finisher": "finish（完成）+ -er（表示人或事物）→ 完成者；最后加工者",
    "finished": "finish（完成；结束）+ -ed（表示完成）→ 完成的；结束的",
    "finite": "fin（界限）+ -ite（具有……性质的）→ 有限的；有界的",
    "infinitesimally": "infinitesimal（极小的）+ -ly（表示以……方式）→ 极小地；以无穷小量地",
    "confined": "con-（共同、加强）+ fine（界限）+ -ed（表示被动或完成）→ 受限制的；被局限的",
    "defined": "define（定义；界定）+ -ed（表示被动或完成）→ 明确的；有定义的",
    "definer": "define（定义；界定）+ -er（表示人）→ 定义者；界定者",
    "defining": "define（定义；界定）+ -ing（表示动作或特征）→ 定义性的；关键的",
    "definitional": "definition（定义；释义）+ -al（表示与……有关）→ 定义的；释义的",
    "definitively": "definitive（明确的；决定性的）+ -ly（表示以……方式）→ 明确地；决定性地",
    "definitude": "definite（明确的）+ -ude（表示性质或状态）→ 明确性；确定性",
    "fined": "fine（罚款）+ -ed（表示被动或完成）→ 被罚款的",
    "fineness": "fine（精细的；纯的）+ -ness（表示性质或状态）→ 精细；纯度",
    "finishing": "finish（完成；加工）+ -ing（表示动作或过程）→ 完成；最后加工",
    "indefinable": "in-（不、无法）+ definable（可定义的）→ 无法定义的；难以界定的",
    "infinitesimal": "in-（不、无）+ finite（有限的）+ -esimal（表示极小）→ 极小的；无穷小的",
    "infinitival": "infinitive（不定式）+ -al（表示与……有关）→ 不定式的",
    "infinitive": "in-（不、无）+ fin（界限）+ -itive（形容词后缀）→ 不定式",
    "infinitude": "in-（不、无）+ finite（有限的）+ -ude（表示状态）→ 无限；无穷",
    "predefine": "pre-（预先）+ define（定义；规定）→ 预先规定；预先定义",
    "predefined": "predefine（预先定义）+ -ed（表示被动或完成）→ 预先确定的；预先定义的",
    "prefinished": "pre-（预先）+ finish（完成；加工）+ -ed（表示完成）→ 预先完成表面处理的",
    "quarterfinal": "quarter（四分之一）+ final（决赛）→ 四分之一决赛",
    "redefine": "re-（再次）+ define（定义；界定）→ 重新定义；重新界定",
    "redefined": "redefine（重新定义）+ -ed（表示被动或完成）→ 重新定义的；重新界定的",
    "redefinition": "redefine（重新定义）+ -ition（表示行为或结果）→ 重新定义；重新界定",
    "refinance": "re-（再次）+ finance（融资）→ 再融资；重新筹资",
    "refinancing": "refinance（再融资）+ -ing（表示动作或过程）→ 再融资；重新筹资",
    "semifinal": "semi-（半）+ final（决赛）→ 半决赛；半决赛的",
    "unconfined": "un-（不）+ confined（受限制的）→ 不受限制的；不受约束的",
    "undefinable": "un-（不、无法）+ definable（可定义的）→ 无法定义的；难以界定的",
    "unfinished": "un-（不、未）+ finished（完成的）→ 未完成的；未结束的",
    "refine": "re-（再次）+ fine（精细）→ 再加工使之更精细 → 改进；提炼",
    "refinery": "refine（精炼）+ -ery（表示场所或行业）→ 精炼或加工的场所 → 炼油厂；精炼厂",
    "refining": "refine（精炼；改进）+ -ing（表示动作或过程）→ 精炼；提炼",
    "refined": "refine（精炼；改进）+ -ed（表示完成或被动）→ 精炼的；改进的；精致的",
    "unrefined": "un-（不、未）+ refined（精炼的）→ 未精炼的；粗糙的",
    "refiner": "refine（精炼）+ -er（表示人或设备）→ 精炼者；精炼设备",
    "refinish": "re-（再次）+ finish（完成；加工）→ 重新加工表面 → 重新整修表面",
    "dict": "dict/dic（说；讲）→ 词根：说；讲",
    "dictate": "dictat（说；口述）+ -e → 口述；命令",
    "dictated": "dictat（说；口述）+ -ed（表示过去式或过去分词）→ 听写的；口述的；由……决定的",
    "dictation": "dictat（口述）+ -ion（行为或结果）→ 口述；听写",
    "dictator": "dictat（命令）+ -or（表示人）→ 独裁者；专政者",
    "dictaphone": "dict（说；口述）+ -a-（连接字母）+ phone（声音）→ 口述录音机",
    "dictum": "dict（说；讲）+ -um（名词后缀）→ 说出的话；格言",
    "dictatory": "dictat（命令；说）+ -ory（形容词后缀）→ 独裁的；命令式的",
    "predictable": "pre-（预先）+ dict（说；讲）+ -able（能够……的）→ 可预测的；可预见的",
    "predictability": "pre-（预先）+ dict（说；讲）+ -ability（能力或性质）→ 可预测性",
    "prediction": "pre-（预先）+ dict（说；讲）+ -ion（行为或结果）→ 预测；预言",
    "unpredictability": "un-（不）+ predictability（可预测性）→ 不可预测性",
    "unindicted": "un-（不、未）+ indict（起诉）+ -ed（表示被动或完成）→ 未被起诉的；未被控告的",
    "indict": "in-（对、向）+ dict（说；讲）→ 指控；起诉",
    "indictable": "indict（起诉）+ -able（能够……的）→ 可起诉的；构成犯罪的",
    "indicted": "indict（起诉）+ -ed（表示被动或完成）→ 被起诉的",
    "indictee": "indict（起诉）+ -ee（表示承受动作的人）→ 被告；被起诉者",
    "indictor": "indict（起诉）+ -or（表示人）→ 起诉人；控告人",
    "predictably": "predict（预测）+ -ably（能够……地）→ 可预测地",
    "predicted": "predict（预测）+ -ed（表示被动或完成）→ 预测的",
    "predictor": "predict（预测）+ -or（表示人或事物）→ 预测因素；预测器",
    "unpredictably": "un-（不）+ predictably（可预测地）→ 不可预测地",
    "unpredicted": "un-（不、未）+ predicted（预测的）→ 未预测到的",
    "alike": "a-（处于……状态）+ like（相似）→ 相似的；相像地",
    "affirm": "af-（加强；ad- 在 f 前的同化形式）+ firm（牢固）→ 使说法牢固 → 断言；确认；肯定",
    "affirmable": "affirm（断言、确认）+ -able（能够……的）→ 可以断言或确认的",
    "affirmation": "affirm（断言、确认）+ -ation（行为或结果）→ 肯定；确认；断言",
    "affirmative": "affirm（肯定）+ -ative（具有……性质的）→ 肯定的；赞成的",
    "affirmatively": "affirmative（肯定的）+ -ly（以……方式）→ 肯定地；赞成地",
    "affirming": "affirm（肯定、支持）+ -ing（形容词或分词后缀）→ 肯定的；支持性的",
    "reaffirm": "re-（再次）+ affirm（确认、肯定）→ 重申；再次确认",
    "reaffirmation": "reaffirm（重申）+ -ation（行为或结果）→ 重申；再次确认",
    "disaffirm": "dis-（否定、撤销）+ affirm（确认）→ 否认；撤销原判",
    "disaffirmation": "disaffirm（否认、撤销）+ -ation（行为或结果）→ 否认；撤销",
    "eastern": "east（东方）+ -ern（表示方向的形容词后缀）→ 东方的；东部的",
    "pile": "pile（堆）→ 堆；堆积",
    "stable": "st（站立）+ -able（能够……的）→ 能够站稳的 → 稳定的；稳固的",
    "hyperacid": "hyper-（超过、过度）+ acid（酸）→ 酸性过强的；胃酸过多的",
    "photograph": "photo（光）+ graph（写、记录）→ 用光记录形成的图像 → 照片；拍照",
    "photography": "photo（光）+ graph（写、记录）+ -y（名词后缀）→ 用光记录图像的技术 → 摄影术",
    "photophilous": "photo（光）+ phil（喜爱）+ -ous（形容词后缀）→ 喜爱光的 → 喜光的",
    "photophobia": "photo（光）+ phob（恐惧）+ -ia（名词后缀）→ 对光敏感或畏惧 → 畏光",
    "photodecomposition": "photo（光）+ de-（分离、去除）+ composition（组成）→ 在光作用下分解 → 光分解、光解作用",
}

CURATED_MEANINGS = {
    "ced": "（词根）走；前进",
    "precede": "先于；在……之前发生",
    "preceding": "在前的；先前的",
    "precedent": "先例；前例",
    "preceded": "先于；在……之前发生（过去式或过去分词）",
    "precedented": "有先例的；有前例的",
    "precedential": "作为先例的；有先例效力的",
    "predecessor": "前任；前身",
    "precedence": "优先；优先权",
    "proceed": "继续进行；继续前进",
    "proceeding": "进行；诉讼程序",
    "proceedings": "诉讼程序；会议记录",
    "concessionaire": "特许经营者；特许权获得者",
    "concessionary": "让步的；特许的；优惠的",
    "concession": "让步；优惠；特许权",
    "concessioner": "让步者；特许权授予者",
    "receding": "后退的；逐渐减退的",
    "recessed": "嵌入式的；凹进的；后退的",
    "recessional": "衰退的；经济衰退的",
    "recessionary": "衰退的；经济衰退的",
    "recession": "经济衰退；衰退",
    "recessive": "隐性的；隐性遗传的",
    "secessionist": "脱离主义者；分裂主义者",
    "procedurally": "程序上；按程序地",
    "collegian": "大学生；学院成员",
    "collegium": "学院；学术团体",
    "commuter": "通勤者",
    "commuting": "通勤；通勤的",
    "coevolution": "共同进化",
    "coevolutionary": "共同进化的",
    "levying": "征税；征收",
    "levity": "轻浮；轻率；轻松诙谐的态度",
    "alleviate": "减轻；缓和（痛苦、问题等）",
    "alleviation": "减轻；缓和（痛苦、问题等）",
    "alleviatory": "减轻痛苦的；起缓和作用的",
    "enactor": "执行者；制定者",
    "inequitably": "不公平地；不公正地",
    "nonpartisanship": "不偏不倚；无党派立场",
    "unconscionably": "无情地；极不合理地",
    "unselfconsciously": "不经意地；不自觉地",
    "institutionally": "在制度层面；在机构方面",
    "reconstructionist": "重建主义者；重建主义的",
    "novelization": "小说化；小说改编",
    "pluralization": "复数化；多元化",
    "covenantal": "盟约的；契约的",
    "ac": "交流电；空调（常用缩写）",
    "children": "儿童；孩子们（child 的复数）",
    "feet": "脚；英尺（foot 的复数）",
    "at": "在（某处或某时）；向；以",
    "under": "在……下面；低于；在……之下",
    "up": "向上；在上方；增加",
    "define": "定义；界定；说明",
    "definite": "明确的；确定的",
    "definition": "定义；界定；释义",
    "definitional": "定义的；释义的",
    "definitive": "明确的；决定性的",
    "financial": "财政的；金融的",
    "financially": "在财政上；在经济上",
    "finisher": "完成者；最后加工者",
    "finished": "完成的；结束的",
    "finite": "有限的；有界的",
    "infinitesimally": "极小地；以无穷小量地",
    "confined": "受限制的；被局限的",
    "defined": "明确的；有定义的",
    "definer": "定义者；界定者",
    "defining": "定义性的；关键的",
    "definitional": "定义的；释义的",
    "definitively": "明确地；决定性地",
    "definitude": "明确性；确定性",
    "fined": "被罚款的",
    "fineness": "精细；纯度",
    "finishing": "完成；最后加工",
    "indefinable": "无法定义的；难以界定的",
    "infinitesimal": "极小的；无穷小的",
    "infinitival": "不定式的",
    "infinitive": "不定式",
    "infinitude": "无限；无穷",
    "predefine": "预先规定；预先定义",
    "predefined": "预先确定的；预先定义的",
    "prefinished": "预先完成表面处理的",
    "quarterfinal": "四分之一决赛；四分之一决赛的",
    "redefine": "重新定义；重新界定",
    "redefined": "重新定义的；重新界定的",
    "redefinition": "重新定义；重新界定",
    "refinance": "再融资；重新筹资",
    "refinancing": "再融资；重新筹资",
    "semifinal": "半决赛；半决赛的",
    "unconfined": "不受限制的；不受约束的",
    "undefinable": "无法定义的；难以界定的",
    "unfinished": "未完成的；未结束的",
    "refine": "改进；提炼；精炼",
    "refinery": "炼油厂；精炼厂",
    "refining": "精炼；提炼；改进",
    "refined": "精炼的；改进的；精致的",
    "unrefined": "未精炼的；粗糙的",
    "refiner": "精炼者；精炼设备",
    "refinish": "重新整修表面",
    "dict": "说；讲（词根）",
    "dictate": "口述；听写；命令",
    "dictated": "听写的；口述的；由……决定的",
    "dictation": "口述；听写",
    "dictator": "独裁者；专政者",
    "americanophile": "亲美者",
    "confine": "限制；禁闭；使局限",
    "anglophile": "亲英派的人；亲英者",
    "philogyny": "亲近或喜爱女性的倾向；女性崇拜",
    "condutor": "指导者；管理者；指挥；导体",
    "paraeducator": "教育助理；辅助教育工作者",
    "interfacing": "接口；连接；接合；相邻的",
    "referential": "指示的；所指的；参考的",
    "laborage": "劳动的；工作方面的",
    "antiintellectually": "反智地；反对知识和理性的",
    "unelectable": "不可当选的",
    "irrelevance": "不相关；离题；不恰当",
    "componential": "成分的；组成部分的",
    "associative": "联合的；结合的；联想的；关联的",
    "homosocial": "同性社交的",
    "spectialization": "专业化；专门化",
    "stit": "站立；放置",
    "overconsumption": "过度消费",
    "untenured": "无固定职位的；未获终身职位的",
    "invisiblity": "不可见性；隐形",
    "concerned": "关心的；涉及的；担心的",
    "significatum": "所指；意义对象",
    "dictum": "格言；权威性的说法",
    "dictatory": "独裁的；命令式的",
    "predictable": "可预测的；可预见的",
    "predictability": "可预测性",
    "prediction": "预测；预言",
    "unpredictability": "不可预测性",
    "unindicted": "未被起诉的；未被控告的",
    "loqu": "说；讲",
    "plic": "折叠；重叠",
    "plur": "多；多数",
    "punct": "点；刺",
    "sanct": "神圣",
    "scrib": "写；记录",
    "sequ": "跟随",
    "techn": "技艺；技术",
    "ultim": "最终；极限",
    "vadvas": "走；行走",
    "paraeducator": "教育助理；辅助教育工作者",
    "indict": "指控；起诉",
    "indictable": "可起诉的；构成犯罪的",
    "indicted": "被起诉的",
    "indictee": "被告；被起诉者",
    "indictor": "起诉人；控告人",
    "predictably": "可预测地",
    "predicted": "预测的",
    "predictor": "预测因素；预测器",
    "unpredictably": "不可预测地",
    "unpredicted": "未预测到的",
    "alike": "相似的；相像地",
    "affirm": "断言；确认；肯定",
    "affirmable": "可以断言的；可以确认的",
    "affirmation": "肯定；确认；断言",
    "affirmative": "肯定的；赞成的",
    "affirmatively": "肯定地；赞成地",
    "affirming": "肯定的；支持性的",
    "reaffirm": "重申；再次确认",
    "reaffirmation": "重申；再次确认",
    "disaffirm": "否认；撤销原判",
    "disaffirmation": "否认；撤销",
    "eastern": "东方的；东部的",
    "pile": "堆；堆积",
    "stable": "稳定的；稳固的；马厩",
    "photograph": "照片；拍照",
    "photography": "摄影术",
    "photophilous": "喜光的",
    "photophobia": "畏光，怕光",
    "photodecomposition": "光分解，光解作用",
}

CURATED_PHONETICS = {
    # ced 是构词词根，不是独立英语词，不能伪造一个单词音标。
    "ced": "/—/",
    "ac": "/ˌeɪˈsiː/",
    "children": "/ˈtʃɪldrən/",
    "feet": "/fiːt/",
    "at": "/æt/",
    "under": "/ˈʌndər/",
    "up": "/ʌp/",
    "precede": "/prɪˈsiːd/",
    "preceding": "/prɪˈsiːdɪŋ/",
    "precedent": "/ˈpresɪdənt/",
    "preceded": "/prɪˈsiːdɪd/",
    "precedented": "/ˈpresɪdentɪd/",
    "precedential": "/ˌpresɪˈdenʃəl/",
    "predecessor": "/ˈpredəsesər/",
    "precedence": "/ˈpresɪdəns/",
    "proceed": "/prəˈsiːd/",
    "proceeding": "/prəˈsiːdɪŋ/",
    "proceedings": "/prəˈsiːdɪŋz/",
    "confine": "/kənˈfaɪn/",
    "quarterfinal": "/ˌkwɔːrtərˈfaɪnəl/",
    "dict": "/dɪkt/",
    "dictaphone": "/ˈdɪktəfoʊn/",
    "dictatory": "/ˈdɪktəˌtɔːri/",
    "unpredicted": "/ˌʌnprɪˈdɪktɪd/",
    "affirm": "/əˈfɜːrm/",
    "affirmable": "/əˈfɜːrməbəl/",
    "affirmation": "/ˌæfərˈmeɪʃən/",
    "affirmative": "/əˈfɜːrmətɪv/",
    "affirmatively": "/əˈfɜːrmətɪvli/",
    "affirming": "/əˈfɜːrmɪŋ/",
    "reaffirm": "/ˌriːəˈfɜːrm/",
    "reaffirmation": "/ˌriːæfərˈmeɪʃən/",
    "disaffirm": "/ˌdɪsəˈfɜːrm/",
    "disaffirmation": "/ˌdɪsˌæfərˈmeɪʃən/",
}

PREFIX_MEANINGS = {
    "counter": "反对、相反", "contra": "反对、相反", "inter": "在……之间", "trans": "横跨、转变",
    "super": "在上、超过", "under": "在下、不足", "over": "在上、过度", "hyper": "超过、过度",
    "extra": "在外、超出", "multi": "多", "micro": "微小", "macro": "宏大", "anti": "反对、防止",
    "auto": "自己、自动", "semi": "半", "sub": "在下、次级", "pre": "在前、预先", "post": "在后",
    "non": "不、无", "mis": "错误、坏", "dis": "不、分开", "un": "不、相反", "re": "再、向后",
    "pro": "向前、赞成", "ex": "向外、前任", "en": "使、进入", "em": "使、进入", "in": "进入、不",
    "im": "进入、不", "de": "向下、去除", "co": "共同、一起", "com": "共同、加强", "con": "共同、加强",
    "bi": "二、双", "tri": "三", "eco": "环境、生态", "fore": "在前、预先",
    "infra": "在下、低于",
}

SUFFIX_MEANINGS = {
    "ization": "名词后缀，表示过程或结果", "isation": "名词后缀，表示过程或结果",
    "ability": "名词后缀，表示能力或性质", "ibility": "名词后缀，表示能力或性质",
    "ational": "形容词后缀，表示与……有关", "fulness": "名词后缀，表示充满某种性质",
    "lessness": "名词后缀，表示缺少某种性质", "ologist": "名词后缀，表示研究者",
    "ology": "名词后缀，表示学科、研究", "ically": "副词后缀，表示以某种方式",
    "ically": "副词后缀，表示以某种方式", "ation": "名词后缀，表示行为、过程或结果",
    "ition": "名词后缀，表示行为或结果", "tion": "名词后缀，表示行为、过程或结果",
    "sion": "名词后缀，表示行为、过程或结果", "ment": "名词后缀，表示行为或结果",
    "ness": "名词后缀，表示性质或状态", "ance": "名词后缀，表示性质或状态",
    "ence": "名词后缀，表示性质或状态", "ity": "名词后缀，表示性质或状态",
    "ship": "名词后缀，表示身份、关系或状态", "ism": "名词后缀，表示思想、制度或现象",
    "ist": "名词后缀，表示人或从业者", "er": "名词后缀，表示人或事物",
    "or": "名词后缀，表示人或事物", "ant": "名词或形容词后缀", "ent": "名词或形容词后缀",
    "able": "形容词后缀，表示能够……的", "ible": "形容词后缀，表示能够……的",
    "ous": "形容词后缀，表示具有……性质", "ive": "形容词后缀，表示具有……性质",
    "ful": "形容词后缀，表示充满……的", "less": "形容词后缀，表示缺少……的",
    "al": "形容词或名词后缀，表示与……有关", "ic": "形容词后缀，表示与……有关",
    "ize": "动词后缀，表示使成为", "ise": "动词后缀，表示使成为", "ify": "动词后缀，表示使成为",
    "ly": "副词后缀，表示以……方式", "ing": "词形后缀，表示进行或事物", "ed": "词形后缀，表示完成或被动",
}

# 核心语义词根优先：这些词族不能因为后半部分也恰好是词根而被拆散。
ROOT_FAMILY_OVERRIDES = {
    "photo": "photo",
    "auto": "auto",
    "techno": "techn",
    "techn": "techn",
    "psycho": "psych",
    "psych": "psych",
    "dict": "dict",
    "grad": "grad",
    "magn": "magn",
    "mater": "mater",
    "phil": "phil",
    "prim": "prim",
    "rect": "rect",
    "sacr": "sacr",
    "sanct": "sanct",
    "serv": "serv",
    "sign": "sign",
    "soci": "soci",
    "soph": "soph",
    "spec": "spec",
    "spir": "spir",
    "stat": "stat",
    "struct": "struct",
    "trib": "trib",
    "vers": "vers",
    "infra": "infra",
}

COMMON_AFFIX_ROOTS = {
    "ab", "ad", "circum", "co", "contra", "counter", "de", "di", "dis", "en", "ex", "extra",
    "fore", "im", "in", "mal", "mis", "non", "ob", "out", "over", "para", "per", "pre", "pro",
    "re", "sub", "trans", "un", "under", "vice", "bi",
}

AFFIX_COMPONENT_TOKENS = COMMON_AFFIX_ROOTS | set(PREFIX_MEANINGS) | {
    "ac", "af", "ag", "al", "an", "ap", "ar", "as", "at",
    "col", "cor", "ef", "oc", "of", "op", "suc", "suf", "sug", "sup", "sus",
    "il", "ir", "for", "dia",
}

ROOT_COMPONENT_ALIASES = {
    "duce": "duc", "duct": "duc", "duction": "duc",
    "cede": "ced", "ceed": "ced", "cess": "ced",
    "fact": "fac", "fect": "fac",
    "scribe": "scrib", "scription": "script",
    "pose": "pos", "posite": "pos", "position": "pos",
    "vide": "vid", "vision": "vis", "vise": "vis",
    "tend": "ten", "tention": "ten",
    "verse": "vers", "version": "vers",
    "vent": "ven", "venture": "ven",
    "volve": "volv", "volution": "volv",
    "clus": "clud", "clude": "clud",
    "literate": "liter",
    "corpor": "corp", "gred": "grad", "quire": "quer",
    "iti": "init", "stance": "stat", "stant": "stat",
    "stru": "struct", "voke": "voc", "vite": "voc",
}

ADDITIONAL_CORE_ROOTS = {
    "liter": "文字、字母", "lumin": "光", "lus": "玩、欺骗", "lustr": "光、照亮",
    "cid": "落下、发生", "clin": "倾斜", "clud": "关闭、包含", "corp": "身体、整体",
    "dign": "价值、尊严", "flict": "打击", "form": "形状、形式", "fus": "流、倾倒",
    "habit": "居住、拥有", "herit": "继承", "hibit": "持有、阻止", "init": "开始",
    "noc": "伤害", "sect": "切割", "sert": "连接、插入", "teg": "覆盖、完整",
    "lig": "选择、连接", "medi": "中间", "mit": "送、放出", "trud": "推",
    "vari": "变化", "vest": "衣服、赋予", "voc": "声音、呼喊",
    "inter": "在……之间、相互",
    "infra": "在下、低于",
}

# 容易因字母重合而误判的词，明确保留/归入正确词根。
FORCED_ROOT_ASSIGNMENTS = {
    "contrive": "co",
    "intricate": "in", "intrigue": "in", "intrinsic": "in",
    "retrieve": "re", "transparent": "trans", "imperative": "im",
    "reluctant": "re", "remark": "re", "remarkable": "re", "revenge": "re",
    "proportion": "pro", "devise": "de", "division": "di", "impossible": "im",
    "inferior": "in", "invitation": "in", "invite": "in",
    "preface": "pre", "revolution": "volv",
    # in- 卡片中的非 in- 构词词与被截断的 inter- 词。
    "in": "", "inch": "", "index": "", "ink": "", "inn": "", "dean": "",
    "ill": "", "illness": "", "iron": "", "irony": "",
    "internet": "inter", "intercourse": "inter", "interim": "inter", "interpret": "inter",
    "irrespective": "spec",
    "irrigate": "", "irritate": "",
    "infrared": "infra", "infrastructure": "infra",
}


def clean_word(value):
    return re.sub(r"[^a-z]", "", str(value).lower())


def load_ecdict_meanings():
    """读取本地 ECDICT 中文释义，作为脏释义的词典级回退。"""
    meanings = {}
    if not ECDICT_FILE.exists():
        return meanings
    with ECDICT_FILE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = clean_word(row.get("word", ""))
            raw = row.get("translation", "") or ""
            if not key or not re.search(r"[\u4e00-\u9fff]", raw):
                continue
            lines = re.split(r"(?:[\r\n]+|\\n)", raw)
            cleaned = []
            for line in lines:
                line = re.sub(r"^\s*(?:a|ad|adj|adv|n|v|vt|vi|prep|conj|pron|aux|num)\.\s*", "", line, flags=re.I)
                line = re.sub(r"\[[^]]*\]", "", line)
                line = re.sub(r"[A-Za-z]+", "", line)
                line = re.sub(r"\s+", "", line).strip(" ;；,，。")
                if line and line not in cleaned:
                    cleaned.append(line)
            if cleaned:
                meanings[key] = "；".join(cleaned)
    return meanings


ECDICT_MEANINGS = load_ecdict_meanings()


def load_ecdict_phonetics():
    phonetics = {}
    if not ECDICT_FILE.exists():
        return phonetics
    with ECDICT_FILE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = clean_word(row.get("word", ""))
            value = (row.get("phonetic", "") or "").strip().strip("/[]［］")
            if key and value and not any(ch in value for ch in "，,；;"):
                phonetics[key] = f"/{value}/"
    return phonetics


ECDICT_PHONETICS = load_ecdict_phonetics()


POS_MARKER_RE = re.compile(
    r"(^|[；，,\n])\s*(a|ad|adj|adv|n|v|vt|vi|prep|conj|pron|aux|num)\.\s*",
    re.IGNORECASE,
)


def normalize_meaning(value):
    """把词性缩写从释义中剥离，避免被页面误判为英文混排或待校对。"""
    # 同时处理真正换行和历史数据里保存下来的字面量\\n。
    meaning = re.sub(r"(?:[\r\n]+|\\n)", "；", str(value or "")).strip()
    meaning = POS_MARKER_RE.sub(r"\1", meaning)
    meaning = re.sub(r"^\s*[a-eA-E]\.\s*", "", meaning)
    meaning = re.sub(r"\s*[①②③④⑤]\s*", "；", meaning)
    # 清理旧词表中反复出现的词典排版残片；这些不是学习者需要记忆的释义。
    meaning = re.sub(r"(^|[；，,])\s*[de]\.\s*", r"\1", meaning, flags=re.IGNORECASE)
    meaning = meaning.replace("物质名词", "")
    meaning = meaning.replace("居先", "优先")
    meaning = meaning.replace("流利的地", "流利地")
    meaning = meaning.replace("go行走", "走").replace("flow流", "流动")
    meaning = meaning.replace("的变形", "的词形变化")
    meaning = meaning.replace("已的，被的", "的；被动形式")
    meaning = meaning.replace("信任的的", "信任的")
    meaning = re.sub(r"[，,；]\s*(?:已|正在)?\.\.\.的(?:[，,；、]\s*被?\.\.\.的)?", "", meaning)
    meaning = re.sub(r"[，,；]\s*\.\.\.的", "", meaning)
    # 省略号本身也是旧词典的占位符，不能留在最终释义里。
    meaning = meaning.replace("...", "")
    meaning = meaning.replace("的地", "地")
    meaning = re.sub(r"\s*([，,；])\s*", r"\1", meaning)
    meaning = re.sub(r"\s+", " ", meaning).strip()
    meaning = meaning.lstrip(".& ")
    meaning = re.sub(r"\s*；\s*", "；", meaning)
    meaning = re.sub(r"；{2,}", "；", meaning).strip("； ")
    return meaning


def normalize_etymology(value, word="", meaning=""):
    """清理词根解释中的历史换行、词性标记和错误词典残片。"""
    etymology = re.sub(r"(?:[\r\n]+|\\n)", "；", str(value or "")).strip()
    etymology = POS_MARKER_RE.sub(r"\1", etymology)
    etymology = re.sub(r"\b[a-eA-E]\.\s*", "", etymology)
    etymology = re.sub(r"\s*[①②③④⑤]\s*", "；", etymology)
    etymology = etymology.replace("go行走", "走").replace("flow流", "流动")
    etymology = etymology.replace("say言", "说；讲")
    etymology = etymology.replace("物质名词", "")
    # WordDecoder 的少数双语 gloss 会把英文解释直接粘进中文词根串，
    # 例如 ``one一``、``graph（write）``。统一翻译后再展示，避免学习者
    # 看到半截英文或“已的，被的”这类机器拼接残片。
    etymology = etymology.replace("one一", "一")
    etymology = etymology.replace("throw投掷", "投掷")
    etymology = etymology.replace("raise举", "举起")
    etymology = etymology.replace("see看", "看")
    etymology = etymology.replace("speak言", "说")
    etymology = etymology.replace("do有性质的", "做")
    etymology = etymology.replace("滚有性质的", "进化的")
    etymology = etymology.replace("滚行为", "进化过程")
    etymology = etymology.replace("举起有性质的", "征收的")
    etymology = etymology.replace("ced（走（ced也作ceed）", "ced（走；也作 ceed）")
    etymology = etymology.replace("ced（走；ced也作 ceed", "ced（走；也作 ceed）")
    etymology = etymology.replace("write", "写")
    etymology = etymology.replace("lead引导", "引导")
    etymology = etymology.replace("bring", "带来")
    etymology = etymology.replace("take拿", "拿")
    etymology = etymology.replace("已的，被的", "的；被动形式")
    etymology = etymology.replace("已的", "的；被动形式")
    etymology = etymology.replace("被的", "被动形式")
    etymology = etymology.replace("有...性质的", "有性质的")
    etymology = etymology.replace("...者，...器", "者；器")
    etymology = re.sub(r"[，,；]\s*(?:已|正在)?\.\.\.的(?:[，,；、]\s*被?\.\.\.的)?", "", etymology)
    etymology = etymology.replace("...", "")
    etymology = etymology.replace("的地", "地")
    etymology = re.sub(r"\s+", " ", etymology).strip()
    etymology = re.sub(r"\b(?:a|ad|adj|adv|n|v|vt|vi|prep|conj|pron|aux|num)\.\s*", "", etymology, flags=re.I)
    etymology = re.sub(r"\s*；\s*", "；", etymology)
    etymology = re.sub(r"；{2,}", "；", etymology).strip("； ")
    # 右侧结论如果只是词典模板残片，就回到已经清洗过的中文释义；
    # 左侧仍保留词根组合，确保“词根 + 词缀 → 词义”的教学结构不丢失。
    if "→" in etymology:
        left, right = etymology.split("→", 1)
        if re.search(
            r"回一|未一|与结束|与名称|与做|共同，一起走|共同，一起.*(?:主义|者|行为|地|的)|"
            r"有性质的|与有关的|共同，一起|走(?:有性质|者)|[A-Za-z]{3,}[\u4e00-\u9fff]",
            right,
        ):
            etymology = f"{left.strip()} → {meaning or right.strip()}"
    if "见习驾驶员" in etymology or "读作" in etymology:
        label = word or "该词"
        etymology = f"{label}（整体词源词，当前不宜机械拆分）→ {meaning or label}"
    return etymology


def meaning_is_suspicious(value):
    meaning = str(value or "").strip()
    return bool(
        not meaning
        or re.search(r"待校对|待补充|相关的|有关的|读作", meaning)
        or re.search(r"居先|物质名词|流利的地|go行走|flow流|\.\.\.|的变形|组件选通|号元素|读地|的地|信任的的|已的|被的|有性质的|除下列用法外|用法\s*\d|^的复数$|^的词形变化$|共同[，,]一起走|共同[，,]一起(?:读|变换|滚|拿|行为|者|的)|的词形变化|(?:^|[；，,])\s*[a-eA-E]\.\s*|[①②③④⑤]", meaning)
        or re.search(r"(^|[；，\n])\s*(a|ad|adj|adv|n|v|vt|vi|prep|conj|pron|aux|num)\.", meaning, re.I)
        or re.search(r"[A-Za-z]{3,}", meaning)
    )


def example_matches_word(example, word):
    """确认例句中出现目标词或常见词形；括号和编号只视为词条标记。"""
    sentence = example or ""
    parts = re.findall(r"[A-Za-z]+", (word or "").lower())
    for base in parts:
        forms = {base, base + "s", base + "es", base + "ed", base + "ing"}
        if base.endswith("e"):
            forms.update({base + "d", base[:-1] + "ing"})
        if base.endswith("y") and len(base) > 2:
            forms.update({base[:-1] + "ies", base[:-1] + "ied"})
        if any(re.search(rf"\b{re.escape(form)}\b", sentence, re.IGNORECASE) for form in forms):
            return True
    return False


def root_key(name):
    """按核心词根合并，忽略连字符、空格和括号释义。"""
    return clean_word(str(name).split("(", 1)[0])


def root_meaning_from_name(name):
    match = re.search(r"\(([^)]*)\)", str(name))
    return match.group(1).replace(";", "、").replace(",", "、") if match else ""


def root_story(name, meaning):
    label = name.split("(", 1)[0].strip()
    return f"{label} 是一个核心词根，主要表示“{meaning}”。相关单词通常保留这一核心语义，具体含义需要结合词根分解和上下文判断。"


def chinese_part(value):
    """从 WordDecoder 的双语释义中提取适合卡片展示的中文部分。"""
    value = str(value or "").strip()
    match = re.search(r"[\u4e00-\u9fff]", value)
    if match:
        cleaned = re.sub(r"[A-Za-z]+", "", value[match.start():])
        cleaned = re.sub(r"\s+", "", cleaned)
        return cleaned.strip(" ；;,，。")
    return value


def worddecoder_meaning(word, entry):
    key = clean_word(word)
    if key in WORDDECODER_MEANING_FIXES:
        return WORDDECODER_MEANING_FIXES[key]
    value = str(entry.get("gloss_cn", "") or "").strip()
    if not re.search(r"[\u4e00-\u9fff]", value):
        return ""
    if re.match(r"^\s*[.．]?[\[［](寻根问底|望文生义|词义判断)", value):
        return ""
    return value


def worddecoder_maps(db):
    """构造 WordDecoder 的词根异形、前缀和后缀索引。"""
    root_forms = {}
    for group_key, info in db.get("roots", {}).items():
        for form in info.get("forms", []):
            root_forms.setdefault(clean_word(form), group_key)

    prefixes = {}
    for item in db.get("affixes", {}).get("prefixes", []):
        canonical = clean_word(item.get("form", ""))
        if not canonical:
            continue
        prefixes[canonical] = item
        for alt in item.get("alts", []):
            prefixes.setdefault(clean_word(alt), item)

    suffixes = {}
    for item in db.get("affixes", {}).get("suffixes", []):
        form = clean_word(item.get("form", ""))
        if form:
            suffixes[form] = item
        for alt in item.get("alts", []):
            suffixes.setdefault(clean_word(alt), item)
    # 补齐项目已有的常见派生/屈折词尾，仅用于把派生词回溯到已有可靠词根。
    for form, meaning in SUFFIX_MEANINGS.items():
        suffixes.setdefault(form, {"form": f"-{form}", "mean": meaning})
    # 教材断法 assumption = as + sump + tion；sump 是 sum/sumpt 的表层异形。
    if "sum" in db.get("roots", {}):
        root_forms.setdefault("sump", "sum")
    known_forms = set().union(*(set(items) for items in db.get("tags", {}).values()),
                              *(set(items) for items in db.get("syllabi", {}).values()))
    return root_forms, prefixes, suffixes, db.get("roots", {}), known_forms


def parse_worddecoder_analysis(analysis, maps):
    """解析 WordDecoder 原书分析串，并修复其 JS 解析器对 `col-（com-）` 一类写法的遗漏。"""
    root_forms, prefixes, suffixes, wd_roots, _ = maps
    parts = []
    normalized = str(analysis or "").replace("＝", "=").replace("（", "(").replace("）", ")")
    if normalized.strip().startswith("提示"):
        return []
    for raw in re.split(r"[;；]", normalized):
        raw = raw.strip()
        if not raw:
            continue
        head, _, tail = raw.partition("=")
        head = re.split(r"[→⇒]", head, maxsplit=1)[0].strip()
        mean = re.split(r"[→⇒“\"]", tail, maxsplit=1)[0].strip() if tail else ""

        prefix_match = re.match(r"^([a-z]+)\s*(?:\([^)]*\)\s*)?-", head, flags=re.I)
        suffix_match = re.match(r"^-\s*([a-z]+)-?", head, flags=re.I)
        if prefix_match:
            form = clean_word(prefix_match.group(1))
            info = prefixes.get(form, {})
            parts.append({"kind": "prefix", "form": form,
                          "mean": chinese_part(mean or info.get("mean", ""))})
            continue
        if suffix_match:
            form = clean_word(suffix_match.group(1))
            info = suffixes.get(form, {})
            parts.append({"kind": "suffix", "form": form,
                          "mean": chinese_part(mean or info.get("mean", ""))})
            continue

        base_match = re.match(r"^([a-z]+)(?:\([a-z]*\))?", head, flags=re.I)
        if not base_match:
            continue
        form = clean_word(base_match.group(1))
        group = root_forms.get(form, "")
        if group:
            root_info = wd_roots.get(group, {})
            parts.append({"kind": "root", "form": form, "group": group,
                          "mean": chinese_part(root_info.get("mean", "") or mean)})
        else:
            parts.append({"kind": "base", "form": form, "mean": chinese_part(mean)})
    return parts


def worddecoder_components(word, db, maps, depth=0, seen=None):
    """返回经原书分析、教材断法或已验证词基递归得到的构词部件。"""
    if depth > 4:
        return []
    seen = set(seen or ())
    key = clean_word(word)
    if not key or key in seen:
        return []
    seen.add(key)
    root_forms, prefixes, suffixes, _, known_forms = maps
    entry = db.get("words", {}).get(key, {})
    raw_parts = parse_worddecoder_analysis(entry.get("analysis", ""), maps)

    # 教材明确分析里的词基继续向下展开，直到找到核心词根。
    if raw_parts:
        expanded = []
        for part in raw_parts:
            if part["kind"] == "base" and part["form"] != key and part["form"] in db.get("words", {}):
                nested = worddecoder_components(part["form"], db, maps, depth + 1, seen)
                if nested and any(p["kind"] == "root" for p in nested):
                    expanded.extend(nested)
                    continue
                if not part.get("mean"):
                    part["mean"] = db["words"][part["form"]].get("gloss_cn", "")
            expanded.append(part)
        return expanded

    split = db.get("splits", {}).get(key, [])
    if split:
        parts = []
        has_leading_affix = False
        for index, token in enumerate(split):
            token_key = clean_word(token)
            if not token_key:
                continue
            if index == len(split) - 1 and token_key in suffixes:
                info = suffixes[token_key]
                parts.append({"kind": "suffix", "form": token_key, "mean": chinese_part(info.get("mean", ""))})
            elif token_key in prefixes:
                info = prefixes[token_key]
                parts.append({"kind": "prefix", "form": token_key, "mean": chinese_part(info.get("mean", ""))})
                has_leading_affix = index == 0
            elif token_key in suffixes:
                info = suffixes[token_key]
                parts.append({"kind": "suffix", "form": token_key, "mean": chinese_part(info.get("mean", ""))})
            elif token_key in root_forms:
                group = root_forms[token_key]
                parts.append({"kind": "root", "form": token_key, "group": group,
                              "mean": chinese_part(db["roots"][group].get("mean", ""))})
            elif token_key in db.get("words", {}) and (index == 0 or has_leading_affix):
                nested = worddecoder_components(token_key, db, maps, depth + 1, seen)
                parts.extend(nested or [{"kind": "base", "form": token_key,
                                         "mean": db["words"][token_key].get("gloss_cn", "")}])
            else:
                parts.append({"kind": "base", "form": token_key, "mean": ""})
        if parts:
            return parts

    # 没有明示断法时，只在剩余词基本身有词条依据时剥离前后缀，避免按拼写硬拆。
    for prefix in sorted(prefixes, key=len, reverse=True):
        if key.startswith(prefix) and len(key) - len(prefix) >= 3:
            base = key[len(prefix):]
            if ((entry or base in known_forms)
                    and (base in db.get("words", {}) or base in db.get("splits", {}) or base in root_forms)):
                nested = worddecoder_components(base, db, maps, depth + 1, seen)
                if nested and any(p["kind"] == "root" for p in nested):
                    info = prefixes[prefix]
                    return [{"kind": "prefix", "form": prefix,
                             "mean": chinese_part(info.get("mean", ""))}] + nested
    for suffix in (sorted(suffixes, key=len, reverse=True) if entry else ()):
        if key.endswith(suffix) and len(key) - len(suffix) >= 3:
            base = key[:-len(suffix)]
            candidates = [base, base + "e", base[:-1] + "y" if base.endswith("i") else ""]
            for candidate in candidates:
                if candidate and candidate in db.get("words", {}):
                    nested = worddecoder_components(candidate, db, maps, depth + 1, seen)
                    if nested and any(p["kind"] == "root" for p in nested):
                        info = suffixes[suffix]
                        return nested + [{"kind": "suffix", "form": suffix,
                                          "mean": chinese_part(info.get("mean", ""))}]
    return []


def worddecoder_etymology(word, meaning, db, maps):
    key = clean_word(word)
    if key in WORDDECODER_WORD_FIXES:
        fix = WORDDECODER_WORD_FIXES[key]
        parts = fix["parts"]
        rendered = []
        for part in parts:
            form = part["form"] + ("-" if part["kind"] == "prefix" else "")
            rendered.append(f"{form}（{part['mean']}）")
        return " + ".join(rendered) + f" → {meaning or word}", fix["root"], parts
    parts = worddecoder_components(word, db, maps)
    if not parts:
        return "", "", []
    has_root = any(part.get("kind") == "root" for part in parts)
    has_explicit_analysis = bool(db.get("words", {}).get(clean_word(word), {}).get("analysis", "").strip())
    if not has_root and not has_explicit_analysis:
        return "", "", []
    rendered = []
    for part in parts:
        form = part.get("form", "")
        if part.get("kind") == "prefix":
            form += "-"
        elif part.get("kind") == "suffix":
            form = "-" + form
        label = f"{form}（{part['mean']}）" if part.get("mean") else form
        rendered.append(label)
    root_group = next((p.get("group", "") for p in parts if p.get("kind") == "root"), "")
    return " + ".join(rendered) + f" → {meaning or word}", root_group, parts


def ensure_other_root(data):
    other = next((r for r in data.get("roots", []) if r.get("name") == "其他常用词"), None)
    if other:
        return other
    other = {"name": "其他常用词", "meaning": "无法可靠拆分的基础词",
             "story": "这些词没有足够可靠的拉丁、希腊词根拆分依据，按整体词或词基记忆。", "words": []}
    data.setdefault("roots", []).append(other)
    return other


def add_worddecoder_words(data, db):
    """扩充各考试范围内带完整释义的词；不导入仅属于小学范围的词。"""
    other = ensure_other_root(data)
    existing = {clean_word(w.get("word", "")) for r in data.get("roots", []) for w in r.get("words", [])}
    added = []
    scoped_words = set().union(*(set(db.get("tags", {}).get(scope, [])) for scope in VOCAB_SCOPES))
    for key in sorted(scoped_words):
        entry = db.get("words", {}).get(key, {})
        meaning = worddecoder_meaning(key, entry)
        if not key or clean_word(key) in existing or not meaning:
            continue
        other["words"].append({
            "word": key,
            "meaning": meaning,
            "example": "",
            "source": "",
            "phonetic": "",
            "wordDecoderAnalysis": entry.get("analysis", ""),
            "wordDecoderSource": "WordDecoder",
            "scopes": [scope for scope in VOCAB_SCOPES if key in db.get("tags", {}).get(scope, [])],
        })
        existing.add(key)
        added.append(key)
    return added


def annotate_word_scopes(data, db):
    tag_sets = {scope: {clean_word(x) for x in db.get("tags", {}).get(scope, [])} for scope in VOCAB_SCOPES}
    for root in data.get("roots", []):
        for word in root.get("words", []):
            key = clean_word(word.get("word", ""))
            matched = [scope for scope in VOCAB_SCOPES if key in tag_sets[scope]]
            # 原项目即考研词库；WordDecoder 未标注到的历史词继续保留考研范围。
            word["scopes"] = matched or ["考研"]
    data["availableScopes"] = VOCAB_SCOPES


def regroup_by_worddecoder(data, db, maps):
    """以 WordDecoder 的核心词根为最终归类依据，通用前缀只保留无核心词根的例外。"""
    root_forms, prefixes, _, _, known_forms = maps
    existing = {root_key(r.get("name", "")): r for r in data.get("roots", []) if root_key(r.get("name", ""))}
    group_target_keys = {}
    alias_groups = {}
    for group_key, info in db.get("roots", {}).items():
        preferred = WORDDECODER_ROOT_PREFERRED.get(group_key, "")
        non_affix_existing = [clean_word(x) for x in info.get("forms", [])
                              if clean_word(x) in existing and clean_word(x) not in COMMON_AFFIX_ROOTS]
        candidates = [preferred] + non_affix_existing + [group_key] + [clean_word(x) for x in info.get("forms", [])]
        target_key = preferred or next((x for x in candidates if x and x in existing), "") or group_key
        group_target_keys[group_key] = target_key
        for form in info.get("forms", []):
            alias_groups[clean_word(form)] = group_key

    group_targets = {}

    def target_for(group_key):
        if not group_key:
            return None
        if group_key in group_targets:
            return group_targets[group_key]
        info = db.get("roots", {}).get(group_key, {})
        target_key = group_target_keys[group_key]
        target = existing.get(target_key)
        if target is None:
            meaning = chinese_part(info.get("mean", "")) or "核心词根"
            target = {"name": target_key, "meaning": meaning, "story": root_story(target_key, meaning), "words": []}
            data["roots"].append(target)
            existing[target_key] = target
        target["wordDecoderRoot"] = group_key
        target["aliases"] = info.get("forms", [])
        target["rootSource"] = "WordDecoder"
        if chinese_part(info.get("mean", "")):
            target["meaning"] = chinese_part(info.get("mean", ""))
            target["story"] = root_story(target.get("name", target_key), target["meaning"])
        group_targets[group_key] = target
        return target

    other = ensure_other_root(data)
    locations = []
    for root in list(data.get("roots", [])):
        for word in list(root.get("words", [])):
            locations.append((root, word))

    audit = []
    for source, word in locations:
        key = clean_word(word.get("word", ""))
        if key in WORDDECODER_ROOT_EXCLUSIONS:
            explanation, group, parts = "", "", []
        else:
            explanation, group, parts = worddecoder_etymology(key, word.get("meaning", ""), db, maps)
        entry = db.get("words", {}).get(key, {})
        if entry:
            word["wordDecoderAnalysis"] = entry.get("analysis", "")
            word["wordDecoderSource"] = "WordDecoder"
        if key in CURATED_ETYMOLOGY:
            word["etymology"] = CURATED_ETYMOLOGY[key]
            word["etymologySource"] = "curated"
            word.pop("morphemes", None)
        elif explanation:
            word["etymology"] = explanation
            word["etymologySource"] = "WordDecoder"
            word["morphemes"] = parts
        elif word.get("etymologySource") == "WordDecoder":
            word.pop("etymology", None)
            word.pop("etymologySource", None)
            word.pop("morphemes", None)

        target = target_for(group)
        current_key = root_key(source.get("name", ""))
        # 同一规范词根的异形卡片合并，例如 lect → leg；只按完整卡片名匹配，不按单词拼写猜测。
        if target is None and current_key not in COMMON_AFFIX_ROOTS and current_key in alias_groups:
            target = target_for(alias_groups[current_key])
            group = alias_groups[current_key]
        # WordDecoder 明确收录但找不到核心词根时，清理掉仅凭拼写落入通用前缀的词。
        verified_affix_base = any(
            key.startswith(prefix) and key[len(prefix):] in db.get("words", {}) and key[len(prefix):] in known_forms
            for prefix in prefixes if len(key) - len(prefix) >= 3
        )
        if key in WORDDECODER_ROOT_EXCLUSIONS:
            target = other
            group = "other"
        if target is None and (entry or verified_affix_base) and (current_key in COMMON_AFFIX_ROOTS or current_key in prefixes):
            target = other
        if target is None or target is source:
            continue
        source["words"].remove(word)
        if not any(clean_word(x.get("word", "")) == key for x in target.get("words", [])):
            target["words"].append(word)
        audit.append({"word": word.get("word", ""), "from": source.get("name", ""),
                      "to": target.get("name", ""), "matchedFamily": "WordDecoder",
                      "wordDecoderRoot": group})

    for root in data.get("roots", []):
        root["words"] = sorted(root.get("words", []), key=lambda x: clean_word(x.get("word", "")))
    data["roots"] = [r for r in data.get("roots", []) if r.get("words")]
    return audit


def restore_affix_card_metadata(data):
    """防止同形词根（de=神、bi=生命等）覆盖通用前缀卡片的释义。"""
    for root in data.get("roots", []):
        key = root_key(root.get("name", ""))
        label = root.get("name", "").split("(", 1)[0].strip()
        if key not in COMMON_AFFIX_ROOTS or "-" not in label:
            continue
        meaning = root_meaning_from_name(root.get("name", "")) or PREFIX_MEANINGS.get(key, "通用前缀")
        root["meaning"] = meaning
        root["story"] = f"{label} 是通用前缀，主要表示“{meaning}”。学习时应结合后面的核心词根理解完整词义。"
        root.pop("wordDecoderRoot", None)
        root.pop("aliases", None)
        root.pop("rootSource", None)


def evacuate_unverified_affix_cards(data, db, maps):
    """通用前缀不能充当兜底词根；无核心词根证据的残留词统一转入基础词区。"""
    other = ensure_other_root(data)
    audit = []
    for root in list(data.get("roots", [])):
        key = root_key(root.get("name", ""))
        label = root.get("name", "").split("(", 1)[0].strip()
        if root is other or key not in COMMON_AFFIX_ROOTS or "-" not in label:
            continue
        for word in list(root.get("words", [])):
            _, group, _ = worddecoder_etymology(word.get("word", ""), word.get("meaning", ""), db, maps)
            if group:
                continue
            root["words"].remove(word)
            word_key = clean_word(word.get("word", ""))
            if not any(clean_word(x.get("word", "")) == word_key for x in other.get("words", [])):
                other["words"].append(word)
            audit.append({"word": word.get("word", ""), "from": root.get("name", ""),
                          "to": other.get("name", ""), "matchedFamily": "unverified-affix-evacuation"})
    data["roots"] = [r for r in data.get("roots", []) if r.get("words")]
    return audit


def get_phonetic(word):
    """返回 IPA 音标；eng-to-ipa 无法识别时返回空值，避免伪造。"""
    candidates = [word.lower()]
    # 词典对派生词覆盖不足时，用常见词形还原再查询词典。
    for suffix in ("ization", "isation", "ational", "fulness", "ability", "ibility", "ingly", "edly", "ment", "tion", "sion", "ness", "able", "ible", "ity", "ive", "ing", "ed", "es", "ly", "er", "al", "s"):
        if word.lower().endswith(suffix) and len(word) - len(suffix) >= 4:
            candidates.append(word.lower()[:-len(suffix)])
            break
    for candidate in candidates:
        value = ipa.convert(candidate).strip()
        if value and value.lower() != candidate.lower() and "*" not in value:
            return f"/{value}/"
        if pronouncing:
            phones = pronouncing.phones_for_word(candidate)
            if phones:
                arpabet_to_ipa = {
                    "AA":"ɑ", "AE":"æ", "AH":"ə", "AO":"ɔ", "AW":"aʊ", "AY":"aɪ",
                    "B":"b", "CH":"tʃ", "D":"d", "DH":"ð", "EH":"ɛ", "ER":"ɝ", "EY":"eɪ",
                    "F":"f", "G":"ɡ", "HH":"h", "IH":"ɪ", "IY":"i", "JH":"dʒ", "K":"k",
                    "L":"l", "M":"m", "N":"n", "NG":"ŋ", "OW":"oʊ", "OY":"ɔɪ", "P":"p",
                    "R":"r", "S":"s", "SH":"ʃ", "T":"t", "TH":"θ", "UH":"ʊ", "UW":"u",
                    "V":"v", "W":"w", "Y":"j", "Z":"z", "ZH":"ʒ",
                }
                rendered = "".join(arpabet_to_ipa.get(token.rstrip("012"), token.rstrip("012")) for token in phones[0].split())
                if rendered:
                    return f"/{rendered}/"
    return "/音标待校对/"


def is_reliable_etymology(value):
    value = value or ""
    return bool(value) and "词根 →" not in value and "词根家族" not in value and "见上" not in value


def derive_etymology(word, meaning, root, lexicon):
    """按前缀 + 核心词/词根 + 后缀生成保守的组合解释。"""
    raw = clean_word(word)
    if not raw:
        return "", ""
    if raw in CURATED_ETYMOLOGY:
        return CURATED_ETYMOLOGY[raw], "curated"

    prefix = next((p for p in sorted(PREFIX_MEANINGS, key=len, reverse=True) if raw.startswith(p) and len(raw) - len(p) >= 3), "")
    remainder = raw[len(prefix):] if prefix else raw
    suffix = next((s for s in sorted(SUFFIX_MEANINGS, key=len, reverse=True) if remainder.endswith(s) and len(remainder) - len(s) >= 3), "")
    base = remainder[:-len(suffix)] if suffix else remainder

    # 优先选择词表中真实存在的基础词，避免机械拆出不存在的字符串。
    base_meaning = lexicon.get(base, "")
    root_id = root_key(root.get("name", ""))
    root_meaning = root.get("meaning", "")
    if not base_meaning and root_id and len(root_id) >= 3 and root_id in raw:
        base = root_id
        base_meaning = root_meaning

    components = []
    if prefix:
        components.append(f"{prefix}-（{PREFIX_MEANINGS[prefix]}）")
    if base_meaning:
        components.append(f"{base}（{base_meaning.split('、')[0].split('，')[0]}）")
    elif base and base != raw:
        components.append(f"{base}（核心词干）")
    if suffix:
        components.append(f"-{suffix}（{SUFFIX_MEANINGS[suffix]}）")

    # 至少有两个可辨认成分时才称为“组合”，否则明确说明整体记忆。
    if len(components) >= 2:
        return " + ".join(components) + f" → {meaning or word}", "rule-based"
    return f"{word}（整体词源词，当前不宜机械拆分）→ {meaning or word}", "whole-word"


def regroup_core_families(data):
    """将明确的核心词族归入同一词根卡片，并在归并时去重。"""
    roots_by_key = {root_key(root.get("name", "")): root for root in data.get("roots", [])}
    moved = []
    for family_prefix, target_key in ROOT_FAMILY_OVERRIDES.items():
        target = roots_by_key.get(target_key)
        if not target:
            continue
        gathered = {clean_word(w.get("word", "")): w for w in target.get("words", [])}
        for root in data.get("roots", []):
            if root is target:
                continue
            retained = []
            for word in root.get("words", []):
                key = clean_word(word.get("word", ""))
                if key.startswith(family_prefix) and len(key) > len(family_prefix):
                    if key not in gathered:
                        gathered[key] = word
                        moved.append({"word": word.get("word", ""), "from": root.get("name", ""), "to": target.get("name", ""), "matchedFamily": family_prefix})
                else:
                    retained.append(word)
            root["words"] = retained
        target["words"] = sorted(gathered.values(), key=lambda w: clean_word(w.get("word", "")))
    data["roots"] = [root for root in data.get("roots", []) if root.get("words") or root_key(root.get("name", "")) == "othercommonwords"]
    return moved


def regroup_by_reference(data, source):
    """按专业词根表的核心词根映射重新归类现有词汇。"""
    roots_by_key = {root_key(root.get("name", "")): root for root in data.get("roots", [])}
    word_targets = {}
    for source_root in source.get("roots", []):
        target_key = root_key(source_root.get("root", ""))
        if target_key not in roots_by_key:
            continue
        for word in source_root.get("words", []):
            key = clean_word(word.get("word", ""))
            if key:
                word_targets[key] = target_key

    buckets = {key: {} for key in roots_by_key}
    audit = []
    for current_key, root in roots_by_key.items():
        for word in root.get("words", []):
            word_key = clean_word(word.get("word", ""))
            target_key = word_targets.get(word_key, current_key)
            if word_key in FORCED_ROOT_ASSIGNMENTS:
                target_key = FORCED_ROOT_ASSIGNMENTS[word_key]
            family_match = next(
                (prefix for prefix in sorted(ROOT_FAMILY_OVERRIDES, key=len, reverse=True)
                 if word_key.startswith(prefix) and len(word_key) > len(prefix)),
                "",
            )
            if family_match:
                target_key = ROOT_FAMILY_OVERRIDES[family_match]
            decomposition = word.get("etymology", "").split("→", 1)[0]
            first_part = decomposition.split("+", 1)[0].strip()
            first_token = clean_word(re.split(r"[（(]", first_part, maxsplit=1)[0].rstrip("-"))
            if (
                first_token in roots_by_key
                and target_key in COMMON_AFFIX_ROOTS
                and first_token in COMMON_AFFIX_ROOTS
                and first_token.startswith(target_key)
                and len(first_token) > len(target_key)
            ):
                target_key = first_token
            target = roots_by_key.get(target_key, root)
            final_key = root_key(target.get("name", ""))
            buckets.setdefault(final_key, {})[word_key] = word
            if final_key != current_key:
                audit.append({
                    "word": word.get("word", ""),
                    "from": root.get("name", ""),
                    "to": target.get("name", ""),
                    "matchedFamily": "reference-root-map",
                })

    for key, root in roots_by_key.items():
        root["words"] = sorted(buckets.get(key, {}).values(), key=lambda w: clean_word(w.get("word", "")))
    protected_targets = set(ROOT_FAMILY_OVERRIDES.values())
    data["roots"] = [root for root in data.get("roots", []) if root.get("words") or root_key(root.get("name", "")) in protected_targets]
    return audit


def regroup_longer_prefixes(data):
    """修复 in/inter/infra、di/dis 等前缀包含关系造成的截断归类。"""
    roots_by_key = {root_key(root.get("name", "")): root for root in data.get("roots", [])}
    moves = []
    for root in list(data.get("roots", [])):
        current_key = root_key(root.get("name", ""))
        if current_key not in COMMON_AFFIX_ROOTS:
            continue
        for word in list(root.get("words", [])):
            decomposition = word.get("etymology", "").split("→", 1)[0]
            first_part = decomposition.split("+", 1)[0].strip()
            first_token = clean_word(re.split(r"[（(]", first_part, maxsplit=1)[0].rstrip("-"))
            if not (
                first_token in roots_by_key
                and first_token in COMMON_AFFIX_ROOTS
                and first_token.startswith(current_key)
                and len(first_token) > len(current_key)
            ):
                continue
            target = roots_by_key[first_token]
            root["words"].remove(word)
            if not any(clean_word(w.get("word", "")) == clean_word(word.get("word", "")) for w in target.get("words", [])):
                target["words"].append(word)
            moves.append({"word": word.get("word", ""), "from": root.get("name", ""), "to": target.get("name", ""), "matchedFamily": "longer-prefix"})
    data["roots"] = [root for root in data.get("roots", []) if root.get("words")]
    return moves


def component_target(component, roots_by_key):
    token = clean_word(component)
    if not token:
        return ""
    if token in ROOT_COMPONENT_ALIASES and ROOT_COMPONENT_ALIASES[token] in roots_by_key:
        return ROOT_COMPONENT_ALIASES[token]
    if token in roots_by_key and token not in COMMON_AFFIX_ROOTS:
        return token
    return ""


def apply_forced_assignments(data):
    roots_by_key = {root_key(root.get("name", "")): root for root in data.get("roots", [])}
    locations = {}
    for root in data.get("roots", []):
        for word in root.get("words", []):
            locations[clean_word(word.get("word", ""))] = (root, word)
    moves = []
    for word_key, target_key in FORCED_ROOT_ASSIGNMENTS.items():
        if word_key not in locations or target_key not in roots_by_key:
            continue
        source, word = locations[word_key]
        target = roots_by_key[target_key]
        if source is target:
            continue
        source["words"].remove(word)
        if not any(clean_word(w.get("word", "")) == word_key for w in target.get("words", [])):
            target["words"].append(word)
        moves.append({"word": word.get("word", ""), "from": source.get("name", ""), "to": target.get("name", ""), "matchedFamily": "manual-correction"})
    return moves


def ensure_additional_core_roots(data):
    existing = {root_key(root.get("name", "")) for root in data.get("roots", [])}
    for key, meaning in ADDITIONAL_CORE_ROOTS.items():
        if key in existing:
            continue
        data["roots"].append({
            "name": key,
            "meaning": meaning,
            "story": root_story(key, meaning),
            "words": [],
        })


def discover_repeated_core_roots(data, minimum_words=2):
    """从可靠拆解中发现重复核心成分，并提升为独立词根卡片。"""
    occurrences = {}
    for root in data.get("roots", []):
        if root_key(root.get("name", "")) not in COMMON_AFFIX_ROOTS:
            continue
        for word in root.get("words", []):
            if clean_word(word.get("word", "")) in FORCED_ROOT_ASSIGNMENTS:
                continue
            if word.get("etymologySource") != "source-data":
                continue
            decomposition = word.get("etymology", "").split("→", 1)[0]
            for part in decomposition.split("+"):
                text = part.strip()
                if not text or text.startswith("-"):
                    continue
                token_text = re.split(r"[（(]", text, maxsplit=1)[0].strip().rstrip("-")
                token = clean_word(token_text)
                if len(token) < 3 or token in AFFIX_COMPONENT_TOKENS or token in SUFFIX_MEANINGS:
                    continue
                meaning_match = re.search(r"[（(]([^）)]*)[）)]", text)
                meaning = meaning_match.group(1).strip() if meaning_match else ""
                if not meaning or meaning.startswith(("名词后缀", "形容词后缀", "副词后缀", "动词后缀", "词形后缀")):
                    continue
                item = occurrences.setdefault(token, {"words": set(), "meanings": []})
                item["words"].add(clean_word(word.get("word", "")))
                item["meanings"].append(meaning)

    existing = {root_key(root.get("name", "")) for root in data.get("roots", [])}
    created = []
    for token, info in sorted(occurrences.items()):
        if len(info["words"]) < minimum_words or token in existing:
            continue
        meaning = collections.Counter(info["meanings"]).most_common(1)[0][0]
        data["roots"].append({
            "name": token,
            "meaning": meaning,
            "story": root_story(token, meaning),
            "words": [],
        })
        existing.add(token)
        created.append({"root": token, "meaning": meaning, "wordCount": len(info["words"])})
    return created


def regroup_from_decomposition(data):
    """从已有人工作出的词根拆解中提取核心词根并迁移。"""
    roots_by_key = {root_key(root.get("name", "")): root for root in data.get("roots", [])}
    moves = []
    planned = []
    for root in data.get("roots", []):
        current_key = root_key(root.get("name", ""))
        if current_key not in COMMON_AFFIX_ROOTS:
            continue
        for word in list(root.get("words", [])):
            if clean_word(word.get("word", "")) in FORCED_ROOT_ASSIGNMENTS:
                continue
            if word.get("etymologySource") != "source-data":
                continue
            decomposition = word.get("etymology", "").split("→", 1)[0]
            parts = [part.strip() for part in decomposition.split("+")]
            targets = []
            for part in parts:
                if part.startswith("-"):
                    continue
                token = re.split(r"[（(]", part, maxsplit=1)[0].strip().rstrip("-")
                target_key = component_target(token, roots_by_key)
                if target_key and target_key != current_key:
                    targets.append(target_key)
            if targets:
                target_key = max(targets, key=len)
                planned.append((root, roots_by_key[target_key], word, target_key))

    for source_root, target_root, word, matched in planned:
        if word not in source_root.get("words", []):
            continue
        source_root["words"].remove(word)
        if not any(clean_word(w.get("word", "")) == clean_word(word.get("word", "")) for w in target_root.get("words", [])):
            target_root["words"].append(word)
        moves.append({
            "word": word.get("word", ""), "from": source_root.get("name", ""),
            "to": target_root.get("name", ""), "matchedFamily": f"decomposition:{matched}",
        })
    for root in data.get("roots", []):
        root["words"] = sorted(root.get("words", []), key=lambda w: clean_word(w.get("word", "")))
    data["roots"] = [root for root in data.get("roots", []) if root.get("words")]
    return moves


def unresolved_affix_audit(data):
    rows = []
    for root in data.get("roots", []):
        if root_key(root.get("name", "")) not in COMMON_AFFIX_ROOTS:
            continue
        for word in root.get("words", []):
            rows.append({
                "root": root.get("name", ""), "word": word.get("word", ""),
                "meaning": word.get("meaning", ""), "etymology": word.get("etymology", ""),
            })
    return rows


def move_false_prefix_matches_to_other(data):
    """清理仅因拼写开头相同而落入前缀卡片的普通词。"""
    other = next((root for root in data.get("roots", []) if root.get("name") == "其他常用词"), None)
    if not other:
        return []
    keep_standalone = {"extra", "vice"}
    moves = []
    for root in data.get("roots", []):
        if root is other or root_key(root.get("name", "")) not in COMMON_AFFIX_ROOTS:
            continue
        for word in list(root.get("words", [])):
            key = clean_word(word.get("word", ""))
            if key in keep_standalone:
                continue
            source = word.get("etymologySource")
            decomposition = word.get("etymology", "").split("→", 1)[0]
            source_without_composition = source == "source-data" and "+" not in decomposition
            if source not in {"whole-word", "rule-based"} and not source_without_composition:
                continue
            root["words"].remove(word)
            if not any(clean_word(w.get("word", "")) == key for w in other.get("words", [])):
                other["words"].append(word)
            moves.append({"word": word.get("word", ""), "from": root.get("name", ""), "to": other.get("name", ""), "matchedFamily": "false-prefix-match"})
    data["roots"] = [root for root in data.get("roots", []) if root.get("words")]
    return moves


QUESTION_UNSAFE_PATTERNS = (
    # 历史自动模板虽然通常“语法像句子”，但没有提供目标词的真实语境。
    "The article discusses",
    "The study links",
    "The evidence shows why",
    "Researchers observed",
    "The approach seems",
    "Researchers described the policy as",
    "The evidence points to",
    "The change made the system more",
    "The policy was implemented",
    "The change occurred",
    "The results were reported",
    "The researchers tried to",
    "The researchers assessed the evidence",
    "The result was",
    "includes the word",
)


def question_sentence_is_safe(answer):
    """判断例句是否足以支撑完形式练习。

    题目不能仅因为句子中出现了答案词就使用它。旧模板会制造诸如
    ``The study links levity to changes in public life``、
    ``The researchers tried to levitate the issue`` 的伪语境；这类句子
    统一退回释义题，避免把错误搭配变成“标准答案”。
    """
    sentence = (answer.get("example") or "").strip()
    if not sentence or answer.get("source") == "暂无可靠例句":
        return False
    lowered = sentence.lower()
    if any(pattern.lower() in lowered for pattern in QUESTION_UNSAFE_PATTERNS):
        return False
    # 元语言句适合词卡，不适合测试句意；练习题退回释义模式。
    if re.search(r"\b(?:the term|the sentence uses|the root)\b", lowered):
        return False
    if sentence.count(".") == 0 and sentence.count("?") == 0 and sentence.count("!") == 0:
        return False
    return True


def build_questions(data, count=240):
    """为每个核心词根生成四选一模拟题，干扰项来自同一词根。"""
    rng = random.Random(20261026)
    questions = []
    for root in data.get("roots", []):
        candidates = [w for w in root.get("words", []) if w.get("word") and w.get("meaning")]
        if len(candidates) < 4:
            continue
        for answer in candidates:
            distractors = [w for w in candidates if w is not answer]
            rng.shuffle(distractors)
            distractors = distractors[:3]
            options = [answer] + distractors
            rng.shuffle(options)
            sentence = answer.get("example", "")
            reliable = question_sentence_is_safe(answer)
            blanked = re.sub(rf"\b{re.escape(answer['word'])}\w*\b", "________", sentence, flags=re.IGNORECASE)
            if not reliable or blanked == sentence:
                blanked = f"选择与“{answer.get('meaning', '')}”意思最相符的单词。"
            questions.append({
                "root": root.get("name", ""),
                "word": answer["word"],
                "prompt": f"根据句意，选择最适合填入空格的词：{blanked}",
                "options": [{"word": w["word"], "meaning": w.get("meaning", "")} for w in options],
                "answer": answer["word"],
                "explanation": f"答案：{answer['word']}（{answer.get('meaning', '')}）。其他选项同属词根 {root.get('name', '')}，但在本句语境中含义不合适。"
            })
    rng.shuffle(questions)
    return questions[:count]


def main():
    data = json.loads(MAIN_FILE.read_text(encoding="utf-8"))
    source = json.loads(ENGRA_FILE.read_text(encoding="utf-8"))
    if not WORDDECODER_FILE.exists():
        raise FileNotFoundError(f"缺少 WordDecoder 数据文件：{WORDDECODER_FILE}")
    worddecoder = json.loads(WORDDECODER_FILE.read_text(encoding="utf-8"))
    verified_examples = (
        json.loads(VERIFIED_EXAMPLES_FILE.read_text(encoding="utf-8"))
        if VERIFIED_EXAMPLES_FILE.exists() else {}
    )
    wd_maps = worddecoder_maps(worddecoder)

    source_words = {}
    source_roots = {}
    for root in source.get("roots", []):
        key = clean_word(root.get("root", ""))
        if key:
            source_roots[key] = root
        for item in root.get("words", []):
            key = clean_word(item.get("word", ""))
            if key:
                source_words[key] = item

    lexicon = {}
    for root in data.get("roots", []):
        for item in root.get("words", []):
            key = clean_word(item.get("word", ""))
            if key and item.get("meaning"):
                lexicon[key] = item["meaning"]
    for key, item in source_words.items():
        if item.get("meaning"):
            lexicon.setdefault(key, item["meaning"])
    for key, item in worddecoder.get("words", {}).items():
        if item.get("gloss_cn"):
            lexicon.setdefault(key, item["gloss_cn"])

    # 先按核心词根合并已有卡片，避免 contra-/contra- (...) 变成两张卡。
    merged_roots = {}
    for root in data.get("roots", []):
        key = root_key(root.get("name", "")) or root.get("name", "")
        if key not in merged_roots:
            merged_roots[key] = root
            root["meaning"] = root.get("meaning") or root_meaning_from_name(root.get("name", ""))
        else:
            target = merged_roots[key]
            if not target.get("meaning"):
                target["meaning"] = root.get("meaning") or root_meaning_from_name(root.get("name", ""))
            target["words"].extend(root.get("words", []))
    data["roots"] = list(merged_roots.values())
    worddecoder_added = add_worddecoder_words(data, worddecoder)
    # 首次升级时用旧专业表恢复历史卡片，再由 WordDecoder 最终裁决；后续构建不再反复搬运。
    regroup_audit = []
    if data.get("wordDecoderSchemaVersion") != 3:
        regroup_audit.extend(regroup_by_reference(data, source))
    discovered_roots = []
    worddecoder_audit = regroup_by_worddecoder(data, worddecoder, wd_maps)
    regroup_audit.extend(worddecoder_audit)
    existing_roots = {r.get("name", ""): r for r in data.get("roots", [])}
    existing_word_keys = set()
    stats = {"phonetic": 0, "meaning": 0, "etymology": 0, "examples": 0,
             "new_words": len(worddecoder_added), "new_roots": 0}

    for root in data.get("roots", []):
        for word in root.get("words", []):
            key = clean_word(word.get("word", ""))
            existing_word_keys.add(key)
            ref = source_words.get(key, {})
            if not word.get("phonetic"):
                word["phonetic"] = get_phonetic(word.get("word", ""))
                if word["phonetic"]:
                    stats["phonetic"] += 1
            if not word.get("phonetic") and ref.get("phonetic"):
                word["phonetic"] = ref["phonetic"]
                stats["phonetic"] += 1
            if key in CURATED_PHONETICS:
                word["phonetic"] = CURATED_PHONETICS[key]
            if not word.get("meaning") and ref.get("meaning"):
                word["meaning"] = ref["meaning"]
                stats["meaning"] += 1
            wd_entry = worddecoder.get("words", {}).get(key, {})
            wd_meaning = worddecoder_meaning(key, wd_entry)
            if wd_meaning:
                word["meaning"] = wd_meaning
            if key in CURATED_MEANINGS:
                word["meaning"] = CURATED_MEANINGS[key]
            wd_explanation, _, wd_parts = worddecoder_etymology(
                word.get("word", ""), word.get("meaning", ""), worddecoder, wd_maps
            )
            if wd_explanation and key not in CURATED_ETYMOLOGY:
                word["etymology"] = wd_explanation
                word["etymologySource"] = "WordDecoder"
                word["morphemes"] = wd_parts
            elif word.get("etymologySource") == "WordDecoder":
                word.pop("etymology", None)
                word.pop("etymologySource", None)
                word.pop("morphemes", None)
            if not word.get("etymology") and ref.get("mnemonic"):
                word["etymology"] = ref["mnemonic"]
                stats["etymology"] += 1
            if word_key := clean_word(word.get("word", "")):
                if word_key in CURATED_ETYMOLOGY:
                    word["etymology"] = CURATED_ETYMOLOGY[word_key]
                    word["etymologySource"] = "curated"
            if not is_reliable_etymology(word.get("etymology")):
                explanation, explanation_source = derive_etymology(
                    word.get("word", ""), word.get("meaning", ""), root, lexicon
                )
                word["etymology"] = explanation
                word["etymologySource"] = explanation_source
                stats["etymology"] += 1
            elif not word.get("etymologySource"):
                word["etymologySource"] = "source-data"
            word_key = clean_word(word.get("word", ""))
            # 人工精选例句优先于历史缓存/自动补充，避免旧的错误例句覆盖修订结果。
            if word_key in CURATED_EXAMPLES:
                word["example"] = CURATED_EXAMPLES[word_key]
                word["source"] = "人工精选例句"
                word.pop("exampleSourceFile", None)
                stats["examples"] += 1
            elif word_key in verified_examples:
                verified = verified_examples[word_key]
                word["example"] = verified["example"]
                word["source"] = verified["source"]
                word["exampleSourceFile"] = verified["sourceFile"]
                stats["examples"] += 1
            else:
                # 不再用无法保证词性和语义的模板伪造例句。
                word["example"] = ""
                word["source"] = "暂无可靠例句"
                word.pop("exampleSourceFile", None)

    # 将第二张表中主表没有的词根/词汇纳入统一主表。
    for source_root in source.get("roots", []):
        root_name = source_root.get("root", "").strip()
        if not root_name:
            continue
        missing_refs = [ref for ref in source_root.get("words", [])
                        if clean_word(ref.get("word", ""))
                        and clean_word(ref.get("word", "")) not in existing_word_keys]
        if not missing_refs:
            continue
        target = next((r for r in data["roots"] if root_key(r.get("name", "")) == root_key(root_name)), None)
        if target is None:
            meaning = source_root.get("meaning", "") or root_meaning_from_name(root_name)
            target = {"name": root_name, "meaning": meaning, "story": root_story(root_name, meaning), "words": []}
            data["roots"].append(target)
            stats["new_roots"] += 1
        for ref in missing_refs:
            key = clean_word(ref.get("word", ""))
            if not key or key in existing_word_keys:
                continue
            word = {"word": ref.get("word", ""), "meaning": ref.get("meaning", ""), "example": "", "source": "暂无可靠例句"}
            if key in CURATED_EXAMPLES:
                word.update(example=CURATED_EXAMPLES[key], source="人工精选例句")
            elif key in verified_examples:
                verified = verified_examples[key]
                word.update(example=verified["example"], source=verified["source"], exampleSourceFile=verified["sourceFile"])
            if ref.get("phonetic"):
                word["phonetic"] = ref["phonetic"]
            if ref.get("mnemonic"):
                word["etymology"] = ref["mnemonic"]
            if clean_word(word.get("word", "")) in CURATED_ETYMOLOGY:
                word["etymology"] = CURATED_ETYMOLOGY[clean_word(word["word"])]
                word["etymologySource"] = "curated"
            if not is_reliable_etymology(word.get("etymology")):
                explanation, explanation_source = derive_etymology(
                    word.get("word", ""), word.get("meaning", ""), target, lexicon
                )
                word["etymology"] = explanation
                word["etymologySource"] = explanation_source
            if not word.get("phonetic"):
                word["phonetic"] = get_phonetic(word.get("word", ""))
            target["words"].append(word)
            existing_word_keys.add(key)
            stats["new_words"] += 1

    # engra 补充词也接受 WordDecoder 的最终归类；第二次执行只会处理刚加入的词，已有词保持幂等。
    late_worddecoder_audit = regroup_by_worddecoder(data, worddecoder, wd_maps)
    worddecoder_audit.extend(late_worddecoder_audit)
    regroup_audit.extend(late_worddecoder_audit)
    affix_cleanup_audit = evacuate_unverified_affix_cards(data, worddecoder, wd_maps)
    worddecoder_audit.extend(affix_cleanup_audit)
    regroup_audit.extend(affix_cleanup_audit)
    restore_affix_card_metadata(data)
    annotate_word_scopes(data, worddecoder)
    data["wordDecoderSchemaVersion"] = 3

    data["totalWords"] = sum(len(r.get("words", [])) for r in data["roots"])
    for root in data["roots"]:
        root["meaning"] = root.get("meaning") or root_meaning_from_name(root.get("name", "")) or "其他常用词"
        # dict/dic 是同一词根的异形，统一展示为可理解的核心义“说；讲”。
        if clean_word(root.get("name", "")) in {"dic", "dict", "dict/dic"} or root.get("name", "") == "dic":
            root["meaning"] = "说；讲"
            root["story"] = "dic/dict 来自拉丁语 dicere，核心含义是“说、讲”。它出现在 predict（预先说出→预测）和 contradict（反着说→反驳）等词中。"
        if not root.get("story") or "这个词根包含" in root.get("story", ""):
            root["story"] = root_story(root.get("name", ""), root["meaning"])
        for word in root.get("words", []):
            key = clean_word(word.get("word", ""))
            if key in CURATED_MEANINGS:
                word["meaning"] = CURATED_MEANINGS[key]
            if key in CURATED_ETYMOLOGY:
                word["etymology"] = CURATED_ETYMOLOGY[key]
                word["etymologySource"] = "curated"
            if key in CURATED_EXAMPLES:
                word["example"] = CURATED_EXAMPLES[key]
                word["source"] = "人工精选例句"
                word.pop("exampleSourceFile", None)
            if (not word.get("phonetic") or "待校对" in word.get("phonetic", "")) and key in ECDICT_PHONETICS:
                word["phonetic"] = ECDICT_PHONETICS[key]
            if "待校对" in word.get("phonetic", ""):
                fallback_phonetic = get_phonetic(word.get("word", ""))
                if "待校对" not in fallback_phonetic:
                    word["phonetic"] = fallback_phonetic
            raw_meaning = str(word.get("meaning", "") or "")
            raw_meaning_has_dictionary_artifact = bool(
                re.search(r"(?:^|[；，,\s])\s*[a-eA-E]\.\s*|[①②③④⑤]", raw_meaning)
            )
            word["meaning"] = normalize_meaning(raw_meaning)
            # 词源拆解串曾被错误写入 meaning；只有在释义明显污染时才使用词典回退。
            if raw_meaning_has_dictionary_artifact or meaning_is_suspicious(word["meaning"]):
                dictionary_meaning = ECDICT_MEANINGS.get(key, "")
                if dictionary_meaning:
                    word["meaning"] = normalize_meaning(dictionary_meaning)
            # 根词卡片里偶尔会把“词根本身”误当成普通英语单词，进而带入
            # vi/ced 之类完全无关的词典义项或音标占位符。对这类短根词统一
            # 明确标注为构词成分，不伪造独立单词释义和读音。
            root_label = clean_word(str(root.get("name", "")).split("(", 1)[0])
            if key == root_label and len(key) <= 5:
                root_meaning = root.get("meaning", "") or "构词核心义"
                word["meaning"] = f"（词根）{root_meaning}"
                word["phonetic"] = "/—/"
                word["etymology"] = f"{word.get('word', key)}（构词词根，不作为独立单词使用）→ {root_meaning}"
                word["etymologySource"] = "curated"
                word["example"] = f"The root {word.get('word', key)} means “{root_meaning}” in related words."
                word["source"] = "人工精选例句"
                word.pop("exampleSourceFile", None)
            # 最后一层防线：旧版本的自动模板不得再次回流到页面。
            # 没有人工或可靠语料替代时宁可留空，也不展示语法错误的伪例句。
            example = word.get("example", "")
            source_label = word.get("source", "")
            legacy_template = (
                source_label.startswith(("模拟例句", "通用例句"))
                or "The study shows that people can " in example
            )
            if legacy_template and key not in CURATED_EXAMPLES:
                word["example"] = ""
                word["source"] = "暂无可靠例句"
                word.pop("exampleSourceFile", None)
            if word.get("example") and not example_matches_word(word["example"], word.get("word", "")):
                word["example"] = ""
                word["source"] = "暂无可靠例句"
                word.pop("exampleSourceFile", None)
            # 清理历史数据中的中英混排占位串，统一为可读的中文根义。
            if "say言" in word.get("meaning", ""):
                word["meaning"] = word["meaning"].replace("say言", "说；讲")
            if "say言" in word.get("etymology", ""):
                word["etymology"] = word["etymology"].replace("say言", "说；讲")
            word["etymology"] = normalize_etymology(
                word.get("etymology", ""), word.get("word", ""), word.get("meaning", "")
            )
            # WordDecoder 的少量分析把英文词典释义、选项字母或残句直接
            # 拼进词源卡片。遇到这类情况，重新用当前词根和中文释义生成
            # 保守解释；生成不了就退回整词说明，也不把机器残片展示给用户。
            if word.get("etymologySource") == "WordDecoder" and re.search(
                r"\b(?:to|the|of|and|in order|write|lead|bring|take|one|two|core)\b|\b[a-e]\.\s*|（[^）]*[A-Za-z]{3,}[^）]*）|[A-Za-z]{3,}[\u4e00-\u9fff]|[\u4e00-\u9fff][A-Za-z]{3,}",
                word.get("etymology", ""), re.I,
            ):
                word["etymology"] = (
                    f"{word.get('word', key)}（整体词源词，当前不宜机械拆分）→ "
                    f"{word.get('meaning', word.get('word', key))}"
                )
                word["etymologySource"] = "whole-word"
    data["totalWordsWithExamples"] = sum(bool(w.get("example")) for r in data["roots"] for w in r.get("words", []))
    MAIN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    questions = build_questions(data)
    question_file = DATA_DIR / "mock_questions.json"
    question_file.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    audit_file = DATA_DIR / "root_regroup_audit.json"
    audit_file.write_text(json.dumps(regroup_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    unresolved_file = DATA_DIR / "unresolved_affix_words.json"
    unresolved_file.write_text(json.dumps(unresolved_affix_audit(data), ensure_ascii=False, indent=2), encoding="utf-8")
    discovered_file = DATA_DIR / "discovered_core_roots.json"
    discovered_file.write_text(json.dumps(discovered_roots, ensure_ascii=False, indent=2), encoding="utf-8")
    worddecoder_audit_file = DATA_DIR / "worddecoder_import_audit.json"
    worddecoder_audit_file.write_text(json.dumps({
        "source": "https://github.com/RichardoZhao/WordDecoder",
        "version": worddecoder.get("meta", {}).get("version", ""),
        "excludedScopes": ["小学"],
        "availableScopes": VOCAB_SCOPES,
        "addedWords": worddecoder_added,
        "moves": worddecoder_audit,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    all_words = [word for root in data["roots"] for word in root.get("words", [])]
    example_pattern_counts = {}
    unsafe_example_patterns = (
        "The study examines the role of",
        "The report describes the policy as",
        "The report describes the result as",
        "The prices changed",
        "The results are",
        "The policy may",
        "The study examines how the policy",
        "The report mentions",
        "includes the word",
    )
    for pattern in unsafe_example_patterns:
        example_pattern_counts[pattern] = sum(
            pattern.lower() in word.get("example", "").lower() for word in all_words
        )
    auxiliary_examples = [
        word.get("example", "") for word in all_words
        if word.get("source") == "简明示例句（辅助）" and word.get("example")
    ]
    duplicate_auxiliary_examples = sum(
        count - 1 for count in collections.Counter(auxiliary_examples).values() if count > 1
    )
    meaning_artifact_patterns = (
        "居先", "物质名词", "流利的地", "go行走", "flow流", "...", "的变形",
        "组件选通", "号元素", "读作", "待校对",
    )
    meaning_artifact_counts = {
        pattern: sum(pattern in word.get("meaning", "") for word in all_words)
        for pattern in meaning_artifact_patterns
    }
    etymology_artifact_patterns = (
        "物质名词", "go行走", "flow流", "say言", "有...性质的", "...者，...器",
        "已...的", "被...的", "已的", "被的", "one一", "lead引导", "有性质的", "与有关的", "共同，一起", "走者", "读作", "待校对",
    )
    etymology_artifact_counts = {
        pattern: sum(
            pattern in (
                word.get("etymology", "").split("→", 1)[-1]
                if pattern in {"有性质的", "共同，一起"}
                else word.get("etymology", "")
            )
            for word in all_words
        )
        for pattern in etymology_artifact_patterns
    }
    auxiliary_grammar_patterns = {
        "modal-before-ed-ing": sum(
            word.get("source") == "简明示例句（辅助）"
            and bool(re.search(r"\b(?:can|may|might|must|could|should|will|would)\s+\w+ed\b|\bto\s+\w+ing\b", word.get("example", ""), re.I))
            for word in all_words
        ),
        "seems-before-non-adjective": sum(
            word.get("source") == "简明示例句（辅助）"
            and bool(re.search(r"\bseems\s+(?:ac|feet|trib|urb)\b", word.get("example", ""), re.I))
            for word in all_words
        ),
    }
    quality_audit_file = DATA_DIR / "vocab_quality_audit.json"
    external_corpus_audit = (
        json.loads(EXAMPLE_CORPUS_AUDIT_FILE.read_text(encoding="utf-8"))
        if EXAMPLE_CORPUS_AUDIT_FILE.exists() else {}
    )
    external_source_counts = collections.Counter(
        word.get("source", "") for word in all_words
        if word.get("source", "").endswith("语料")
    )
    quality_audit_file.write_text(json.dumps({
        "totalWords": len(all_words),
        "verifiedExamExamples": sum("真题（本地原文）" in word.get("source", "") for word in all_words),
        "workbookExamples": sum("项目词根表" in word.get("source", "") for word in all_words),
        "wordDecoderExamples": sum(word.get("source") == "WordDecoder例句" for word in all_words),
        "curatedExamples": sum(word.get("source") == "人工精选例句" for word in all_words),
        "generatedSimpleExamples": sum(word.get("source") == "简明示例句（辅助）" for word in all_words),
        "externalExamExamples": dict(external_source_counts),
        "externalExamCorpus": external_corpus_audit,
        "withoutExample": sum(not word.get("example") for word in all_words),
        # 用户已明确允许使用低难度辅助例句；这里仅把真正缺少例句的词计为缺失。
        "withoutReliableExample": sum(not word.get("example") for word in all_words),
        "automaticTemplateExamples": sum(word.get("source", "").startswith(("模拟例句", "通用例句")) for word in all_words),
        "phoneticsPendingReview": sum("待校对" in word.get("phonetic", "") for word in all_words),
        "meaningsPendingReview": sum(meaning_is_suspicious(word.get("meaning", "")) for word in all_words),
        "missingEtymology": sum(not word.get("etymology") for word in all_words),
        "examplesMissingTarget": sum(
            bool(word.get("example")) and not example_matches_word(word.get("example", ""), word.get("word", ""))
            for word in all_words
        ),
        "duplicateAuxiliaryExamples": duplicate_auxiliary_examples,
        "unsafeExamplePatterns": example_pattern_counts,
        "meaningArtifactPatterns": meaning_artifact_counts,
        "etymologyArtifactPatterns": etymology_artifact_counts,
        "auxiliaryGrammarPatterns": auxiliary_grammar_patterns,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # 所有前端版本都使用同一份主表，避免词根数量和例句状态分叉。
    for deploy in (ROOT / "dist" / "data" / "data.json", ROOT / "kaoyan-vocab-site" / "data" / "data.json"):
        deploy.parent.mkdir(parents=True, exist_ok=True)
        deploy.write_text(MAIN_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "mock_questions.json").write_text(question_file.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "root_regroup_audit.json").write_text(audit_file.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "unresolved_affix_words.json").write_text(unresolved_file.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "discovered_core_roots.json").write_text(discovered_file.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "worddecoder_import_audit.json").write_text(worddecoder_audit_file.read_text(encoding="utf-8"), encoding="utf-8")
        (deploy.parent / "vocab_quality_audit.json").write_text(quality_audit_file.read_text(encoding="utf-8"), encoding="utf-8")
        if EXAMPLE_CORPUS_AUDIT_FILE.exists():
            (deploy.parent / "example_corpus_audit.json").write_text(EXAMPLE_CORPUS_AUDIT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    stats["questions"] = len(questions)
    stats["rootReassigned"] = len(regroup_audit)
    stats["coreRootsDiscovered"] = len(discovered_roots)
    stats["wordDecoderAdded"] = len(worddecoder_added)
    stats["wordDecoderReassigned"] = len(worddecoder_audit)
    print(json.dumps({**stats, "roots": len(data["roots"]), "words": data["totalWords"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
