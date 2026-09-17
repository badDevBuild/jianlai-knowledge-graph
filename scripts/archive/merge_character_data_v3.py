
import json
import os

def merge_data():
    # 1. NotebookLM generated data (V3 Structure)
    notebook_data = {
      "name": "陈平安",
      "aliases": [
        "二掌柜",
        "隐官",
        "年轻隐官",
        "陈山主",
        "陈剑仙",
        "曹沫",
        "陈十一",
        "陈好人",
        "陈旧",
        "吴镝",
        "陈迹",
        "陈仁",
        "包袱斋",
        "陈隐官"
      ],
      "bio": "出生于骊珠洞天泥瓶巷的贫寒孤儿，早年做过烧瓷窑工。因本命瓷破碎、长生桥被打断，为求活命习武练拳。曾护送李宝瓶等人远游大隋求学。后游历浩然天下与剑气长城，在剑气长城担任末代隐官，坐镇避暑行宫，率领剑修抵御蛮荒天下妖族大军，并在城头刻字“萍”。身为文圣一脉关门弟子，他兼修剑道与武道，精通符箓、阵法与百家学问。返回浩然天下后，于宝瓶洲建立落魄山祖庭，在桐叶洲建立下宗青萍剑宗。致力于在复杂的世道中讲道理，被誉为“年轻隐官”。",
      "appearance": {
        "facial": "早年皮肤黝黑像炭，双眼明亮清澈、深邃如古井，面容坚毅；跻身中五境后肌肤莹然，神华内敛，面如冠玉，双眸炯炯有神，笑起来温和醇厚。",
        "physique": "身材修长，看似单薄消瘦，实则体魄坚韧至极，脊梁笔直，有一身精粹拳意。",
        "attire": "常穿一袭青衫长褂（有时身穿金色法袍‘金醴’），脚踩千层底布鞋（早年常穿草鞋），头别白玉簪，腰悬朱红养剑葫（姜壶），背负长剑（‘夜游’或‘剑仙’）。",
        "aura": "气质温润如玉，兼具书卷气与江湖气，看似随和实则心志极坚，望之俨然，即之也温，恭而安，守拙且有韧性。"
      },
      "cultivation": [
        {
          "path": "纯粹武夫",
          "realm": "第十境",
          "realm_name": "止境",
          "stage": "气盛层（当前） / 归真层（曾达）",
          "notes": "曾跻身止境第二层‘归真’，因意外跌回第一层‘气盛’。曾以九境山巅境最强武夫跻身止境，曾接下十一境武夫的一记‘半拳’，体内蕴含十一境拳意。追求传说中的十一境武神。"
        },
        {
          "path": "炼气士",
          "realm": "第十四境（历史最高/借法状态）",
          "realm_name": "合道 / 飞升境（当前真实）",
          "stage": "剑修",
          "notes": "当前真实修为为【飞升境】剑修（第十三境）。历史最高曾达到【第十四境】状态：1. 借法陆沉：曾向白玉京三掌教陆沉暂借一身十四境道法，剑斩托月山；2. 合道剑气长城：曾与半座剑气长城合道，在城头拥有匹敌十四境的战力与不死之身。"
        }
      ],
      "techniques": [
        {
          "name": "撼山拳",
          "type": "武学",
          "category": "拳法",
          "description": "源自顾祐拳谱，包含六步走桩、立桩（剑炉）、睡桩（千秋）。拳意厚重，旨在撼动山岳，为陈平安武道根基。"
        },
        {
          "name": "神人擂鼓式",
          "type": "武学",
          "category": "拳法",
          "description": "学自崔诚。拳意刚猛，如神人擂鼓，拳拳递进，气势不断叠加，专门用来换伤换命的霸道拳招。"
        },
        {
          "name": "云蒸大泽式",
          "type": "武学",
          "category": "拳法",
          "description": "学自崔诚。一拳打出，拳意如大泽水汽升腾，气象磅礴，可打退天地雨幕。"
        },
        {
          "name": "剑气十八停",
          "type": "秘术",
          "category": "运气法门",
          "description": "阿良传授，经陈平安改良。一口气在体内窍穴关隘运转十八次，瞬间爆发极大剑气与体魄力量，可用于杀敌或逃遁，亦用于冲刷体魄。"
        },
        {
          "name": "笼中雀",
          "type": "神通",
          "category": "本命飞剑",
          "description": "本命飞剑之一。自成一座小天地，陈平安为天地主宰，可圈定切割战场，在此天地内占据天时地利。"
        },
        {
          "name": "井中月",
          "type": "神通",
          "category": "本命飞剑",
          "description": "本命飞剑之二。可分化出无数飞剑，数量随境界提升，甚至可达百万把，寓意月照深井，真假难辨，虚实相生。"
        },
        {
          "name": "青萍",
          "type": "神通",
          "category": "本命飞剑",
          "description": "本命飞剑之三。由剑气长城老大剑仙陈清都的佩剑‘长气’剑尖炼化而成，寓意‘吾有长气剑，此城剑气长’，杀力极大。"
        },
        {
          "name": "五雷法印（雷局）",
          "type": "道法",
          "category": "雷法/阵法",
          "description": "源自龙虎山天师府秘传与自身感悟，结合炼化的五雷法印，可手掌天地雷电，构建雷局牢狱，镇压妖邪，总摄万法。"
        },
        {
          "name": "符箓之道",
          "type": "道法",
          "category": "符箓",
          "description": "精通《丹书真迹》，擅长绘制缩地符、镇妖符、挑灯符、剑敕符等，常以符箓辅助战斗、赶路或镇压气运。"
        },
        {
          "name": "校大龙",
          "type": "武学",
          "category": "拳法",
          "description": "学自藕花福地种秋。能够精准控制体内气机流转，如龙脊起伏，调整身架，卸力借力。"
        },
        {
          "name": "云水身",
          "type": "秘术",
          "category": "身法",
          "description": "学自九真仙馆云杪。身形如云水飘渺，难以捉摸，可化解攻势。"
        },
        {
          "name": "驭剑术",
          "type": "剑术",
          "category": "御剑",
          "description": "学自剑圣裴旻。能够精准控制飞剑轨迹，神出鬼没。"
        },
        {
          "name": "片月",
          "type": "武学/剑术",
          "category": "自创招式",
          "description": "陈平安自创拳招，亦是剑招，杀力巨大，拳意隐蔽且不可逆，最适宜在战场身陷重围之中使用。"
        }
      ],
      "factions": [
        "落魄山",
        "青萍剑宗",
        "剑气长城（隐官一脉）",
        "文圣一脉"
      ],
      "tags": [
        "剑修",
        "纯粹武夫",
        "读书人",
        "包袱斋",
        "最后一位隐官",
        "二掌柜",
        "好人"
      ],
      "quotes": [],
      "relations": {}
    }

    # 2. Read existing data
    source_file = 'data/build/characters.json'
    if not os.path.exists(source_file):
        print(f"Error: {source_file} not found.")
        return

    with open(source_file, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    existing_char = full_data.get("陈平安", {})
    
    # 3. Merge quotes and relations
    if "quotes" in existing_char:
        notebook_data["quotes"] = existing_char["quotes"]
        print(f"Merged {len(notebook_data['quotes'])} quotes.")
    
    if "relations" in existing_char:
        notebook_data["relations"] = existing_char["relations"]
        print(f"Merged {len(notebook_data['relations'])} relations.")

    # 4. Save to new file
    output_file = 'data/build/character_profile_chen_ping_an_v3.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(notebook_data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully created {output_file}")

if __name__ == "__main__":
    merge_data()
