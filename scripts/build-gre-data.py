"""Generate GRE lesson manifest from official book table of contents."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src" / "data" / "gre"

# Official TOC from 高等教育出版社书目 (200 stories)
TOC = """
1．The Road to Royston Valley 通往罗伊斯顿山谷的公路
2．Turn the Key in the Ignition 发动引擎
3．His Latest Trick 他的最新小把戏
4．An Affidavit 一份宣誓书
5．Of All the Ways 各种方法
6．Snowflake 雪花
7．The Analogous Anagram 类似的颠倒字
8．An Anonymous Anecdote 匿名轶事
9．An Anthropoid in Antarctica 南极洲的类人猿
10．The Appealing Applicant 有吸引力的申请者
11．The Apprentice 学徒
12．The Arena 竞技场
13．Family Man 居家男人
14．The Family Photo 家庭照片
15．Northern Autonomous Region 北方自治区
16．Pity the Inappropriate 可怜不合时宜的人
17．The County Town 小县城
18．Consider This 想想看
19．Through the Ages 历尽沧桑
20．Murder World 谋杀世界
21．Tom's Day in the Park 汤姆逛公园
22．The Treasure Chest 财宝箱
23．The Pirate Named Captain Roberts 海盗罗伯茨船长
24．Billy and the Bully 比利和坏蛋
25．An Old Man's Story 一位老人的故事
26．The Cantankerous Old Vicar 坏脾气的老牧师
27．What the Cat Saw 猫之所见
28．The Mystical Army of Mousedale 毛斯戴尔的神秘军队
29．The Crazy,Chauvinistic Chef疯狂的沙文主义大厨
30．Mrs．Simpson's Little Stars 辛普森夫人的小明星们
31．The Citadel 城堡
32．The Clumsy Clown 笨拙的小丑
33．Roman Investigation 罗马调查
34．The Compassionate Society 仁爱社会
35．The Beautician 美容师
36．The Con Artist 背信弃义的艺术家
37．Friendly Fire 友谊之火
38．The King's Consort 国王的配偶
39．Even Presidents Make Mistakes 总统也会犯错
40．The Coroner's Conscience 验尸官的良心
41．Jonesville 琼斯维尔小镇
42．Postal Couriers'Creed 信使的信条
43．A Cryptic Cult 神秘的邪教
44．The Caretaker 管理人
45．The Debutante 初进社交界的少女
46．The Detective and the Deceased 侦探与死者
47．The Contract 合同
48．The Football Game 足球赛
49．The Conspiracy 阴谋
50．The Desperado 亡命之徒
51．Local Government 地方政府
52．The Highwayman's Story 骑马强盗的故事
53．Take It Easy！别紧张！
54．Cleaning Day 清洁日
55．Cutting up People 解剖人体
56．The Retired Couple 退休夫妇
57．Restless 坐立不安
58．The Rural Garage 乡下汽车修理厂
59．The Home for Retired Scientists 退休科学家之家
60．The Polluter 污染者
61．Death of a Salesman 推销员之死
62．The Guest 客人
63．The Enigma 谜
64．The Entrepreneur 企业家
65．Mother Earth Meets General Zog 大地母亲遇到佐格将军
66．New Kind of School 新型学校
67．Traditional Architecture 传统建筑
68．Search for a Serial Killer 寻找连环杀手
69．Meeting of International Council 国际委员会会议
70．Extradition Hearings 引渡审讯
71．Pigeon Racing 鸽子比赛
72．Down on the Farm 在农场上
73．Meet the Fickers! 见见菲克一家人！
74．Master and Commande 船长兼指挥官
75．A Farmhouse by the Coast 海边农舍
76．A History in the Trees 林中历史
77．Equality Under Attack 平等受到攻击
78．From Frivolity to Fame 从轻浮到成名
79．Fungi Are Fun Guys 真菌是有趣的家伙
80．Born to Be Gauche 天生的笨蛋
81．The Science of Age 年龄的科学
82．An Afternoon with a Gladiator 与角斗士共度一下午
83．The Graduate 毕业生
84．American Football 美式足球
85．A Morning in the Wilderness 荒野中的早晨
86．In Hertford,Hereford and Hampshire,Hurricanes-Hardly Ever Happen 飓风何所惧
87．Loving London 爱上伦敦
88．Amoeba or Henpecked Husband－They're One and the Same!! 变形虫还是惧内的丈夫——本是同根生
89．Head for Some Houmous in This Hotspot 旅游热点
90．All Hail to the Hubbub! 向喧闹致敬！
91．The Mad Scientist 疯狂的科学家
92．The Cave Dweller 穴居的人
93．Imp Wars 小魔鬼之战
94．Jim's Den 吉姆的老巢
95．The Accident 事故
96．The Explorer 探索者
97．The Indigenous Cultures 本土文化
98．The World of Films 电影世界
99．The Escape 逃跑
100．Human Nature 人类本性
101．The Revolutionary Musician 革命音乐家
102．The Reporter 记者
103．The Two Mayors 两个市长
104．The Inheritance 遗产
105．I Like Trucking! 我喜欢开货车！
106．A Close-Knit Family 亲密家庭
107．The Truth About Love 爱的真谛
108．All the Fun of the Fair! 快活的狂欢节！
109．Lingering Stars 徘徊的明星
110．The Courtroom 法庭
111．The Lumberjack 伐木工人
112．Employee of the Month 月度最佳员工
113．Resurrection 复活
114．Classmates 同班同学
115．The Pianist 钢琴家
116．Experimental 实验性的
117．Operation Lift 军事行动
118．The Arms Dealer 军火商
119．In Search of Death 寻找死亡
120．Our Street 我们的街道
121．The Artistic So1dier 艺术家士兵
122．A Strange Flight 奇怪的飞行
123．An Evening with a Philosopher 与哲学家共度一个夜晚
124．A Numismatist's Dream 钱币收藏家的梦想
125．The Hit 职业杀手
126．Moving to the West 走向西方
127．The Life of a Priest 神父的生活
128．The General 将军
129．The Success of a Football Club 足球俱乐部的成功
130．The Pageant 盛会
131．The Parish Pantomime 教区哑剧
132．Learning 学习
133．The Paediatrician 儿科医师
134．The Road to Perdition 走向地狱之路
135．The Petitioner 请愿者
136．A Phenomenal Phonetic Class 非凡的语音班
137．The Plagiarizing Pilgrim 抄袭的朝圣者
138．The Plumber's Mother 水管工人的母亲
139．The Podiatrist and the Polygamist 足病医生和多妻的男人
140．Clairvoyant Powers 透视能力
141．T-Rex 霸王龙
142．The Fortune Teller 算命先生
143．Precious,the Principal Proctor 宝贝，主学监
144．The Profiteer 投机商
145．The Environmentally Friendly Vehicle 环保车辆
146．The Psychology of Boxing 拳击心理学
147．A Short Tale 小故事
148．Lighting Fires 放火
149．Forest Fights 森林之战
150．Talking with Talent 很会说话
151．A Medieval Trial 中世纪的审判
152．Three Election Manifestoes 三份选举宣言
153．The Dress Rehearsal 彩排
154．The Bounty Hunter 为了赏金
155．Extortion 强取豪夺
156．The Return of the King 国王归来
157．The Debate 辩论
158．The Border Guard 边境卫兵
159．The Boarding School 寄宿学校
160．The Outlaw 歹徒
161．The Execution 执行死刑
162．Emergency Room 急诊室
163．On Ship 在船上
164．Think Before You Speak 想好再说
165．The Holy Man 圣人
166．Houses Built with Love 用爱建造的小屋
167．The Shrine 神殿
168．Tough Cooking 厨师难当
169．Sleeping on the Job 偷懒
170．Drinking Stories 杯中故事
171．Caught in a Blizzard 遇到大风雪
172．Cave Man 洞穴爱好者
173．The Parachute Jump 跳伞
174．Killer Zombies 6－The Ultimate Penultimate Massacre 电影《鬼吃鬼6》——终极第二大屠杀
175．Body on Board 船上的尸体
176．Under Siege 被包围
177．The Art Exhibition 美术展览
178．Construction Corruption 建筑腐败
179．Science and Money 科学与金钱
180．On Watch 监视
181．The Date 约会
182．Who's Afraid of Spiders？ 谁害怕蜘蛛？
183．A Cottage for Rent 待租的小屋
184．A Song for Every Occasion 适于一切场合的歌曲
185．The People You Meet 你遇到的人
186．Pollution on the Sarang Canal 萨兰运河上的污染
187．The Circus 马戏团
188．Tnvia Contests 问答竞猜
189．International Adoption 跨国领养
190．Battle of the Architects 建筑师之争
191．Unicorn Extinction 独角兽的灭绝
192．Raising Arizona 培养亚利桑那
193．The Vampire 吸血鬼
194．A Man of Many Talents 多才多艺的男人
195．The Vicar 教区牧师
196．Man and Wife 夫妇
197．At the Zoo 在动物园
198．At the Log Cabin 在小木屋
199．The Wild West 狂野的西部
200．Wayne's World 韦恩的世界
""".strip()


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "lesson"


def parse_toc() -> list[dict]:
    lessons = []
    line_re = re.compile(r"^(\d+)．(.+?)([\u4e00-\u9fff].*)$")
    for line in TOC.splitlines():
        m = line_re.match(line.strip())
        if not m:
            continue
        num = int(m.group(1))
        title_en = m.group(2).strip()
        title_zh = m.group(3).strip()
        lessons.append(
            {
                "id": num,
                "slug": f"{num:03d}-{slugify(title_en)}",
                "title": title_en,
                "titleZh": title_zh,
            }
        )
    return lessons


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lessons = parse_toc()
    (OUT_DIR / "lessons.json").write_text(json.dumps(lessons, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(lessons)} lessons to {OUT_DIR}")


if __name__ == "__main__":
    main()
