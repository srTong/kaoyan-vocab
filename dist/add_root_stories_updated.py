#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个词根添加词源故事和记忆技巧（更新版）
"""

import json

# 词根词源故事字典
root_stories = {
    "其他常用词": "这些是英语中的基础词汇，不属于特定的词根系统，但同样重要。它们通常源自古英语或其他日耳曼语系，是日常交流的核心。",

    "ab- (离开,相反)": "ab- 来自拉丁语，意为'从...离开、相反'。表示远离或相反方向。比如：absent(缺席的) = ab(离开) + sent(存在) → 不在场；abstract(抽象的) = ab(离开) + tract(拉) → 从具体中拉出来。想象从某个位置或状态中脱离。",

    "ad- (向,加强)": "ad- 来自拉丁语，意为'向、到、加强'。表示方向或加强语气。比如：advance(前进) = ad(向) + vance(前) → 向前进；admit(承认) = ad(向) + mit(送) → 送进来 → 接纳。在 d, n 前变为 a-，如 ascribe。",

    "anti- (反对,对抗)": "anti- 来自希腊语，意为'反对、对抗'。表示对立或抵抗。比如：antibiotic(抗生素) = anti(反对) + biotic(生命的) → 反对生命的(细菌)；antivirus(杀毒软件) = anti(反对) + virus(病毒)。想象与某物作斗争。",

    "auto- (自己,自动)": "auto- 来自希腊语，意为'自己、自动'。表示自我或自动。比如：automatic(自动的) = auto(自己) + matic(思考) → 自己思考的；autobiography(自传) = auto(自己) + bio(生命) + graphy(写) → 自己写自己的生命。",

    "bi- (二,双)": "bi- 来自拉丁语，意为'二、双'。表示两个或双重。比如：bicycle(自行车) = bi(二) + cycle(轮) → 两个轮子；bilingual(双语的) = bi(二) + lingual(语言的)。想象成对的事物。",

    "co- (共同,一起)": "co- 来自拉丁语 cum，意为'共同、一起'。想象一群人聚在一起(co-lect, collect)做某事。比如：collect(收集) = co(一起) + lect(选择) → 把东西选到一起；combat(战斗) = co(一起) + bat(打) → 一起打斗。这个前缀强调合作、共同行动的概念。",

    "com- (共同,完全)": "com- 是 co- 的变体，在 l, m, n, r 前使用。意为'共同、完全'。比如：combine(结合) = com(共同) + bine(两个) → 把两个合在一起；complete(完成) = com(完全) + plete(填充) → 完全填满。强调共同行动或完整状态。",

    "con- (共同,加强)": "con- 是 com- 的变体，意为'共同、加强'。比如：connect(连接) = con(共同) + nect(绑) → 绑在一起；conclude(结论) = con(共同) + clude(关闭) → 把所有信息关在一起 → 得出结论。强调共同参与或加强语气。",

    "counter- (反对,相反)": "counter- 来自拉丁语 contra，意为'反对、相反'。表示对抗或回应。比如：counterattack(反击) = counter(反对) + attack(攻击) → 反向攻击；counterbalance(平衡) = counter(反对) + balance(平衡) → 相反的平衡。想象对某个动作的回应。",

    "de- (向下,离开)": "de- 来自拉丁语，有两个核心含义：1)'向下'，如 descend(下降) = de(向下) + scend(爬) → 向下爬；2)'离开、去除'，如 depart(离开) = de(离开) + part(部分) → 从整体中离开。decade(十年)来自拉丁语 decas，deca- 是'十'的意思，-ade 表示集合，十年是一个完整的周期。decay(腐烂) = de(向下) + cay(落下) → 向下坠落 → 衰败腐烂。",

    "di- (二,双)": "di- 来自希腊语，意为'二、双'。表示两个。比如：dilemma(困境) = di(二) + lemma(选择) → 两个选择；dioxide(二氧化物) = di(二) + oxide(氧化物)。与 bi- 类似，但多用于科学术语。",

    "dis- (不,无;分开)": "dis- 来自拉丁语，意为'不、分开'。表示否定或分离。比如：disagree(不同意) = dis(不) + agree(同意)；discover(发现) = dis(分开) + cover(覆盖) → 揭开覆盖物 → 发现。这个前缀常表示从整体中分离或否定某种状态。",

    "eco- (环境,生态)": "eco- 来自希腊语 oikos，意为'家、环境'。表示与生态环境相关。比如：ecology(生态学) = eco(环境) + logy(学科)；economy(经济) = eco(家) + nomy(管理) → 管理家庭。想象我们生活的环境。",

    "en- (使,进入)": "en- 来自拉丁语或古英语，意为'使成为、进入'。表示使某物进入某种状态。比如：enable(使能够) = en(使) + able(能够)；encourage(鼓励) = en(使) + courage(勇气) → 使有勇气。想象把某物放入某个状态。",

    "ex- (出,外)": "ex- 来自拉丁语，意为'向外、出去'。从内部到外部的运动。比如：export(出口) = ex(出) + port(港口) → 从港口出去；exit(出口) = ex(出) + it(走) → 走出去。这个前缀强调从内到外的转变，有时也表示'完全、彻底'，如 explode(爆炸) = ex(出) + plode(拍手) → 掌声爆发出来。",

    "extra- (超出,额外)": "extra- 来自拉丁语，意为'超出、在...之外'。表示超出正常范围。比如：extraordinary(非凡的) = extra(超出) + ordinary(普通的) → 超出普通的；extracurricular(课外的) = extra(超出) + curricular(课程的)。想象超出边界。",

    "fore- (前,预先)": "fore- 来自古英语，意为'在...之前'。表示时间或位置的前置。比如：forecast(预测) = fore(前) + cast(投) → 向前投掷目光；forehead(前额) = fore(前) + head(头)。想象在某个事物的前面。",

    "hetero- (不同,异)": "hetero- 来自希腊语 heteros，意为'不同的、其他的'。表示差异。比如：heterogeneous(异质的) = hetero(不同) + geneous(种类) → 不同种类的；heterosexual(异性恋的) = hetero(不同) + sexual(性的)。想象两个不同的事物。",

    "homo- (相同,同)": "homo- 来自希腊语 homos，意为'相同的'。表示相同或相似。比如：homogeneous(同质的) = homo(相同) + geneous(种类) → 相同种类的；homosexual(同性恋的) = homo(相同) + sexual(性的)。注意与表示'人'的 homo 区分。",

    "hyper- (超过,过度)": "hyper- 来自希腊语，意为'超过、过度'。表示超出正常程度。比如：hyperactive(过度活跃的) = hyper(过度) + active(活跃的)；hypertension(高血压) = hyper(过度) + tension(压力)。想象超过正常限度。",

    "hypo- (下,次)": "hypo- 来自希腊语，意为'在...下面、次于'。表示低于正常程度。比如：hypothermia(低体温) = hypo(低于) + thermia(温度)；hypotension(低血压) = hypo(低于) + tension(压力)。与 hyper- 相反。",

    "im- (不,无;进入)": "im- 是 in- 的变体，在 m, p, b 前使用。有两个相反的含义：1)否定'不、无'，如 impossible(不可能的) = im(不) + possible(可能的)；2)'进入'，如 import(进口) = im(进入) + port(港口) → 进入港口。需要根据上下文判断是哪种含义。",

    "in- (不,无;向内)": "in- 来自拉丁语，有两个核心含义：1)否定前缀'不、无'，如 incorrect(不正确的) = in(不) + correct(正确的)；2)'向内、进入'，如 include(包含) = in(向内) + clude(关闭) → 关在里面。这是英语中最容易混淆的前缀之一，需要根据词义判断。",

    "inter- (之间,相互)": "inter- 来自拉丁语，意为'在...之间、相互'。表示两者或多者之间。比如：international(国际的) = inter(之间) + national(国家的) → 国家之间的；interact(互动) = inter(相互) + act(行动) → 相互行动。想象在多个事物之间。",

    "macro- (大,宏观)": "macro- 来自希腊语 makros，意为'大的、长的'。表示宏观或大规模。比如：macroeconomics(宏观经济学) = macro(大) + economics(经济学)；macroworld(宏观世界)。与 micro- 相反。",

    "mal- (坏,恶)": "mal- 来自拉丁语 male，意为'坏、恶'。表示不良或有害。比如：malfunction(故障) = mal(坏) + function(功能) → 功能坏了；malnutrition(营养不良) = mal(坏) + nutrition(营养)。想象不好的状态。",

    "micro- (小,微观)": "micro- 来自希腊语 mikros，意为'小的'。表示微观或小规模。比如：microscope(显微镜) = micro(小) + scope(看) → 看小的东西；microeconomics(微观经济学)。与 macro- 相反。",

    "mid- (中间)": "mid- 来自古英语，意为'中间'。表示位置或时间的中间。比如：middle(中间)、midnight(午夜) = mid(中间) + night(夜晚) → 夜晚的中间；midterm(期中) = mid(中间) + term(学期)。想象在两个端点之间。",

    "mis- (错,坏)": "mis- 来自古英语或古法语，意为'错误、坏'。表示错误或不良。比如：mistake(错误) = mis(错) + take(拿) → 拿错了；misunderstand(误解) = mis(错) + understand(理解)。想象做错了某事。",

    "mono- (一,单)": "mono- 来自希腊语 monos，意为'单一的'。表示一个或单独。比如：monologue(独白) = mono(一) + logue(说) → 一个人说；monopoly(垄断) = mono(一) + poly(卖) → 一个人卖。想象只有一个。",

    "multi- (多)": "multi- 来自拉丁语 multus，意为'多的'。表示多个或大量。比如：multiple(多个的)、multicultural(多元文化的) = multi(多) + cultural(文化的)。想象数量很多。",

    "non- (不,无)": "non- 来自拉丁语，意为'不、无'。表示否定。比如：nonfiction(非小说) = non(不) + fiction(小说)；nonsense(胡说) = non(不) + sense(意义)。与 un- 类似，但更正式。",

    "ob- (反对,朝向)": "ob- 来自拉丁语，意为'反对、朝向'。表示对抗或面对。比如：object(反对) = ob(反对) + ject(扔) → 扔出去反对；observe(观察) = ob(朝向) + serve(保持) → 保持注意力朝向。在 c 前变为 oc-，如 occur。",

    "out- (外,超过)": "out- 来自古英语，意为'向外、超过'。表示向外或超越。比如：output(输出) = out(出) + put(放) → 放出去；outperform(超过) = out(超过) + perform(表现)。想象超出边界。",

    "over- (过度,在上)": "over- 来自古英语，意为'过度、在...上方'。表示超过或在上方。比如：overcome(克服) = over(超过) + come(来) → 超过困难；overlook(忽视) = over(上方) + look(看) → 从上面看过去。想象超出正常范围。",

    "per- (完全,贯穿)": "per- 来自拉丁语，意为'完全、贯穿'。表示彻底或穿过。比如：perfect(完美的) = per(完全) + fect(做) → 完全做好的；perform(执行) = per(完全) + form(形成) → 完全形成。想象从头到尾贯穿。",

    "poly- (多)": "poly- 来自希腊语 polys，意为'多的'。表示多个。比如：polygon(多边形) = poly(多) + gon(角)；polyglot(多语言的) = poly(多) + glot(舌头)。与 multi- 类似，但多用于学术术语。",

    "post- (后,之后)": "post- 来自拉丁语，意为'在...之后'。表示时间或位置的后置。比如：postpone(推迟) = post(后) + pone(放置) → 放到后面；postwar(战后的) = post(后) + war(战争)。与 pre- 相反。",

    "pre- (预先,前)": "pre- 来自拉丁语 prae，意为'在...之前'。时间或空间上的前置。比如：predict(预测) = pre(预先) + dict(说) → 提前说出来；prevent(阻止) = pre(预先) + vent(来) → 提前来到以阻止。想象在事情发生之前就采取行动。",

    "pro- (向前,赞成)": "pro- 来自拉丁语，意为'向前、支持'。向前移动代表进步和支持。比如：progress(进步) = pro(向前) + gress(走) → 向前走；propose(提议) = pro(向前) + pose(放置) → 把想法向前提出。这个前缀常表示积极推进的态度。",

    "re- (再次,回)": "re- 来自拉丁语，意为'再次、回到'。表示重复或返回。比如：return(返回) = re(回) + turn(转) → 转回来；rewrite(重写) = re(再次) + write(写) → 再写一次。这个前缀强调动作的重复性或回归原点。",

    "semi- (半,部分)": "semi- 来自拉丁语，意为'一半、部分'。表示一半或不完全。比如：semicircle(半圆) = semi(半) + circle(圆)；semiconductor(半导体) = semi(半) + conductor(导体)。想象只有一半。",

    "sub- (下,次)": "sub- 来自拉丁语，意为'在...下面、次于'。表示位置低下或等级次之。比如：subway(地铁) = sub(下面) + way(路) → 下面的路；subordinate(下级的) = sub(下面) + ordinate(顺序) → 在下面的顺序。想象在某个主体的下方或从属地位。",

    "super- (上,超)": "super- 来自拉丁语，意为'在...上方、超过'。表示超越或在上方。比如：supermarket(超市) = super(超) + market(市场)；supernatural(超自然的) = super(超) + natural(自然的)。想象超出正常范围。",

    "sym- (共同,相同)": "sym- 是 syn- 的变体，在 m, p, b 前使用。意为'共同、相同'。比如：sympathy(同情) = sym(共同) + pathy(感受) → 共同感受；symbol(符号) = sym(共同) + bol(投) → 共同理解的东西。想象共同分享。",

    "syn- (共同,合成)": "syn- 来自希腊语，意为'共同、合成'。表示共同作用或合成。比如：synthesis(合成) = syn(共同) + thesis(放置) → 放在一起；synergy(协同) = syn(共同) + ergy(工作) → 共同工作。想象多个部分合在一起。",

    "tele- (远,远程)": "tele- 来自希腊语 tēle，意为'远的'。表示远距离。比如：television(电视) = tele(远) + vision(视觉) → 远程视觉；telephone(电话) = tele(远) + phone(声音)。想象跨越远距离。",

    "trans- (跨越,转移)": "trans- 来自拉丁语，意为'跨越、转移'。表示从一个地方到另一个地方。比如：transport(运输) = trans(跨越) + port(港口) → 从一个港口到另一个；transform(改变) = trans(跨越) + form(形状) → 跨越形状 → 转变。想象穿越边界或转变形态。",

    "tri- (三)": "tri- 来自希腊语，意为'三'。表示数字三。比如：triangle(三角形) = tri(三) + angle(角)；trilogy(三部曲) = tri(三) + logy(学科)。想象三个一组。",

    "ultra- (超,极端)": "ultra- 来自拉丁语，意为'超出、极端'。表示超越正常范围。比如：ultraviolet(紫外线的) = ultra(超) + violet(紫色) → 超出紫色的；ultramodern(超现代的)。想象超出极限。",

    "un- (不,无)": "un- 来自日耳曼语，是英语最常用的否定前缀，意为'不、无、相反'。通常加在形容词或动词前。比如：unhappy(不快乐的)、unlock(开锁) = un(相反) + lock(锁) → 打开锁。与 in-/im- 相比，un- 更口语化，多用于日耳曼语源的词汇。",

    "under- (下,不足)": "under- 来自古英语，意为'在...下面、不足'。表示位置低下或程度不足。比如：understand(理解) = under(下面) + stand(站) → 站在下面支撑 → 理解；underestimate(低估) = under(不足) + estimate(估计)。想象在某个标准之下。",

    "uni- (一,单)": "uni- 来自拉丁语 unus，意为'一'。表示单一或统一。比如：universe(宇宙) = uni(一) + verse(转) → 转向一体；uniform(制服) = uni(一) + form(形状) → 统一形状。想象合为一体。",

    "up- (上,增加)": "up- 来自古英语，意为'向上、增加'。表示向上或增加。比如：upgrade(升级) = up(上) + grade(等级) → 向上提升等级；upload(上传) = up(上) + load(装载)。想象从低到高。",

    "with- (反对,离开)": "with- 来自古英语，意为'反对、离开'。表示对抗或远离。比如：withdraw(撤回) = with(离开) + draw(拉) → 拉开；withstand(抵抗) = with(反对) + stand(站) → 站着反对。想象与某物对抗。"
}

# 读取现有数据
with open('data/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 为每个词根添加故事
added_count = 0
for root in data['roots']:
    root_name = root['name']
    if root_name in root_stories:
        root['story'] = root_stories[root_name]
        added_count += 1
    else:
        # 如果没有找到对应的故事，添加默认故事
        root['story'] = f"这个词根包含 {len(root['words'])} 个相关词汇，通过共同的词源联系帮助记忆。"
        added_count += 1

# 保存更新后的数据
with open('data/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已为 {added_count} 个词根添加词源故事")
print("\n前10个词根的故事预览：")
for i, root in enumerate(data['roots'][:10]):
    print(f"\n{i+1}. {root['name']}")
    story = root.get('story', '无')
    print(f"   {story[:100]}...")
