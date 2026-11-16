# -*- coding: utf-8 -*-
"""
「Qoder 参赛包」完整性自检。

跑法（本机 Python）：
    python "D:\\qoder cn\\heikeson\\Qoder参赛包\\脚本\\自检.py"

它会逐项检查：数据文件能不能解析、字段齐不齐、数值合不合理、
规格书里写的数字和 data.json 对不对得上、有没有把敏感信息写进去。
最后生成 `自检报告.md`。任何一项 ❌ 都不要去投稿。
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, ".."))          # 包/仓库根目录
DATA = os.path.join(PKG, "stm32-data")


def _first_exist(*cands):
    """按顺序返回第一个存在的路径；都不存在就返回第一个（报错时能看出在找什么）。"""
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


# 规格书：公开仓库里在 规格书/ 下、文件名带版本号；旧参赛包里在根目录、名字固定。
# 两种布局都认，取版本号最大的那一份。
_spec_cands = sorted(glob.glob(os.path.join(PKG, "规格书", "作品规格书-v*.md")))
SPEC = _spec_cands[-1] if _spec_cands else _first_exist(
    os.path.join(PKG, "作品规格书-STM32配置台.md"))
# 这两份是内部资料，公开仓库里故意不放 → 缺失只提示、不算失败
INTEL = os.path.join(PKG, "比赛情报.md")
ASSETS = os.path.join(PKG, "我的近期作品盘点.md")

EXPECT = {
    "STM32F103C8T6": dict(pkg="LQFP48",   fam="F1", max=72,  io=37,  hse=8),
    "STM32F407ZGT6": dict(pkg="LQFP144",  fam="F4", max=168, io=114, hse=25),
    "STM32F411CEU6": dict(pkg="UFQFPN48", fam="F4", max=100, io=36,  hse=25),
}

results = []   # (级别, 项目, 说明)


def ok(item, msg=""):
    results.append(("✅", item, msg))


def warn(item, msg=""):
    results.append(("⚠️", item, msg))


def skip(item, msg=""):
    """可选文件缺失：既不算通过也不算失败，只记一笔。"""
    results.append(("⏭", item, msg))


def bad(item, msg=""):
    results.append(("❌", item, msg))


# ---------------- A. 文件存在 ----------------
def check_files():
    # (路径, 名称, 是否必需)  —— 内部资料在公开仓库里故意不放，不算失败
    need = [
        (SPEC, "作品规格书", True),
        (INTEL, "比赛情报", False),
        (ASSETS, "近期作品盘点", False),
        (os.path.join(PKG, "README.md"), "README", True),
        (os.path.join(PKG, "参考实现.html"), "参考实现（前端逻辑样板）", True),
        (os.path.join(DATA, "data.json"), "data.json", True),
        (os.path.join(DATA, "stm32-pins.json"), "stm32-pins.json", True),
        (os.path.join(DATA, "数据核对表.md"), "数据核对表", True),
        (os.path.join(DATA, "引脚核对表.md"), "引脚核对表", True),
        (os.path.join(HERE, "浏览器自测.py"), "浏览器自测脚本", True),
    ]
    for p, name, required in need:
        if os.path.exists(p):
            ok(f"文件存在：{name}", f"{os.path.getsize(p):,} B")
        elif required:
            bad(f"文件存在：{name}", p)
        else:
            skip(f"文件存在：{name}", "未纳入本仓库（内部资料，按设计排除）")
    # 放错位置的旧路径（整理前的残留）
    stale = os.path.join(os.path.dirname(PKG), "stm32-data")
    if os.path.exists(stale):
        warn("旧路径残留", f"{stale} 还在，可删")
    else:
        ok("旧路径已清理")


# ---------------- B. data.json 结构 ----------------
def check_data():
    p = os.path.join(DATA, "data.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
        ok("data.json 可解析", f"{os.path.getsize(p):,} B")
    except Exception as e:
        bad("data.json 可解析", str(e))
        return None

    mc = d.get("mcus", {})
    if set(mc) == set(EXPECT):
        ok("芯片数量正确", "3 款：" + " / ".join(mc))
    else:
        bad("芯片数量正确", f"实际 {list(mc)}")

    for part, exp in EXPECT.items():
        m = mc.get(part)
        if not m:
            bad(f"{part} 存在")
            continue

        # 基本字段
        miss = [k for k in ("package", "core", "max_sysclk_mhz", "limits",
                            "hse_default_mhz", "hse_options_mhz",
                            "ahb_presc", "apb_presc", "pins", "special",
                            "assignable_pins") if k not in m]
        if miss:
            bad(f"{part} 字段齐全", "缺 " + ", ".join(miss))
        else:
            ok(f"{part} 字段齐全")

        # 封装 / 主频 / IO / HSE
        if m["package"] == exp["pkg"]:
            ok(f"{part} 封装", m["package"])
        else:
            bad(f"{part} 封装", f"期望 {exp['pkg']} 实际 {m['package']}")
        if m["max_sysclk_mhz"] == exp["max"]:
            ok(f"{part} 主频上限", f"{exp['max']} MHz")
        else:
            bad(f"{part} 主频上限", f"期望 {exp['max']} 实际 {m['max_sysclk_mhz']}")
        io = sum(1 for x in m["pins"] if x.get("assignable"))
        if io == exp["io"]:
            ok(f"{part} 可用 IO", f"{io} 个")
        else:
            bad(f"{part} 可用 IO", f"期望 {exp['io']} 实际 {io}")
        if m["hse_default_mhz"] == exp["hse"]:
            ok(f"{part} 默认 HSE", f"{exp['hse']} MHz")
        else:
            bad(f"{part} 默认 HSE", f"期望 {exp['hse']} 实际 {m['hse_default_mhz']}")
        if m["hse_default_mhz"] in m.get("hse_options_mhz", []):
            ok(f"{part} HSE 默认值在可选项里")
        else:
            bad(f"{part} HSE 默认值不在可选项里", str(m.get("hse_options_mhz")))

        # 引脚
        pins = m["pins"]
        names = [x["name"] for x in pins]
        if len(names) == len(set(names)):
            ok(f"{part} 引脚不重复", f"{len(pins)} 个")
        else:
            dup = [n for n in set(names) if names.count(n) > 1]
            bad(f"{part} 引脚不重复", "重复：" + ", ".join(dup))

        badfield = [x["name"] for x in pins
                    if not all(k in x for k in ("name", "num", "type",
                                                "assignable", "funcs", "warn"))]
        if badfield:
            bad(f"{part} 引脚字段齐全", "缺字段：" + ", ".join(badfield[:5]))
        else:
            ok(f"{part} 引脚字段齐全")

        nonum = [x["name"] for x in pins if not isinstance(x.get("num"), int)]
        if nonum:
            bad(f"{part} 物理脚号都是整数", ", ".join(nonum[:5]))
        else:
            ok(f"{part} 物理脚号都是整数", f"范围 {pins[0]['num']}~{pins[-1]['num']}")

        # special 里的引脚必须真存在
        allnames = set(names)
        ghost = []
        for k, v in m["special"].items():
            for n in v:
                if n not in allnames:
                    ghost.append(f"{k}:{n}")
        if ghost:
            bad(f"{part} 特殊引脚都在引脚表里", ", ".join(ghost))
        else:
            ok(f"{part} 特殊引脚都在引脚表里",
               " / ".join(f"{k}={'/'.join(v)}" for k, v in m["special"].items() if v))

        # 上限
        lim = m["limits"]
        nonpos = [k for k, v in lim.items() if v is not None and (not isinstance(v, (int, float)) or v <= 0)]
        if nonpos:
            bad(f"{part} 时钟上限都是正数", ", ".join(nonpos))
        else:
            ok(f"{part} 时钟上限", ", ".join(f"{k}={v}" for k, v in lim.items()))
        if lim.get("sysclk") == m["max_sysclk_mhz"]:
            ok(f"{part} limits.sysclk 与主频一致")
        else:
            bad(f"{part} limits.sysclk 与主频不一致")

        # PLL 结构必须按系列对
        if exp["fam"] == "F1":
            if "pll_mul" in m and "pll_p" not in m:
                ok(f"{part} PLL 结构符合 F1（只有倍频）")
            else:
                bad(f"{part} PLL 结构不符合 F1")
        else:
            if all(k in m for k in ("pll_m", "pll_n", "pll_p", "pll_q")):
                ok(f"{part} PLL 结构符合 F4（M/N/P/Q）")
            else:
                bad(f"{part} PLL 结构不符合 F4")

        # 可选值列表不能空
        empt = []
        for k in ("ahb_presc", "apb_presc", "pll_mul", "pll_m", "pll_n", "pll_p", "pll_q"):
            if k in m and (not isinstance(m[k], list) or len(m[k]) == 0):
                empt.append(k)
        if empt:
            bad(f"{part} 可选值列表非空", ", ".join(empt))
        else:
            ok(f"{part} 可选值列表非空")
    return d


# ---------------- C. 规格书与数据一致 ----------------
def check_spec_consistency(d):
    if not d:
        bad("规格书一致性", "data.json 不可用，跳过")
        return
    try:
        t = open(SPEC, encoding="utf-8").read()
    except Exception as e:
        bad("规格书可读", str(e))
        return
    ok("规格书可读", f"{len(t):,} 字符")

    mc = d["mcus"]
    io = {p: sum(1 for x in mc[p]["pins"] if x.get("assignable")) for p in mc}
    # 规格书里的写法是「F103 LQFP48 37 IO、F407 LQFP144 114 IO、F411 UFQFPN48 36 IO」，
    # 所以按「芯片简称 … 数字 … IO」同段匹配，不要求固定串。
    miss = []
    for short, n in (("F103", io["STM32F103C8T6"]),
                     ("F407", io["STM32F407ZGT6"]),
                     ("F411", io["STM32F411CEU6"])):
        if not re.search(short + r"[^\n]{0,40}?" + str(n) + r"[^\n]{0,12}?IO", t):
            miss.append(f"{short}={n}")
    if not miss:
        ok("规格书 IO 数字与 data.json 一致", "37 / 114 / 36")
    else:
        bad("规格书 IO 数字与 data.json 一致", "缺 " + "、".join(miss))

    maxs = "／".join([str(mc[p]["max_sysclk_mhz"]) for p in ("STM32F103C8T6", "STM32F407ZGT6", "STM32F411CEU6")])
    pat = re.escape(maxs).replace("／", r"\s*/\s*")
    if re.search(pat, t):
        ok("规格书主频与 data.json 一致", maxs)
    else:
        warn("规格书主频表述", f"没精确匹配「{maxs}」，人工看一眼")

    hse_expect = [mc["STM32F103C8T6"]["hse_default_mhz"],
                  mc["STM32F407ZGT6"]["hse_default_mhz"],
                  mc["STM32F411CEU6"]["hse_default_mhz"]]
    hs = f"F103={hse_expect[0]}MHz、F407={hse_expect[1]}MHz、F411={hse_expect[2]}MHz"
    hs2 = f"F103={hse_expect[0]} / F407={hse_expect[1]} / F411={hse_expect[2]} MHz"
    # v2.1 的写法是「F103 8、F407 25、F411 25 MHz」，所以再挂一条宽松匹配
    m_hse = re.search(r"F103\s*(\d+)\s*[、,／/]\s*F407\s*(\d+)\s*[、,／/]\s*F411\s*(\d+)", t)
    got = [int(x) for x in m_hse.groups()] if m_hse else None
    if hs in t or hs2 in t or got == hse_expect:
        ok("规格书 HSE 默认值与 data.json 一致", "8 / 25 / 25 MHz")
    else:
        warn("规格书 HSE 表述", "没精确匹配，人工看一眼第 8 节")

    # 关键结论都要在。
    # ★ 2026-11-16 更新：这两条原来是按「旧结论」写的断言（F1 不除 2 / CubeMX 不拦超频），
    #   后来经视频拆解 + 器件库核实把结论改对了，断言也必须跟着改，否则会反过来报错。
    keys = {
        "HSE 必须可配": "HSE 必须做成可选项",
        "HSE 进 PLL 有可选 ÷1/÷2": "÷1 或 ÷2",
        "定时器 ×2 是硬件自动": "×2 是硬件自动",
        "定时器 ×2 用户改不了": "无法自己设置",
        "CubeMX 管总线不管外设上限": "不管外设",
        "F411 96MHz+USB": "96MHz",
    }
    for name, kw in keys.items():
        if kw in t:
            ok(f"关键结论在规格书里：{name}")
        else:
            bad(f"关键结论在规格书里：{name}", f"找不到「{kw}」")


# ---------------- D. 敏感信息 ----------------
def check_privacy():
    bad_words = ["DEEPSEEK_API_KEY", "CODEX_API_KEY", "sk-", "Bearer ",
                 "C:\\Users\\25215", "25215"]
    hits = []
    for p in (SPEC, INTEL, ASSETS,
              os.path.join(DATA, "数据核对表.md"),
              os.path.join(DATA, "引脚核对表.md")):
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        for w in bad_words:
            if w in t:
                hits.append(f"{os.path.basename(p)}: {w}")
    if hits:
        bad("敏感信息扫描", "；".join(hits))
    else:
        ok("敏感信息扫描", "文档里无用户名 / 密钥 / 令牌")


# ---------------- E. 脚本可重跑 ----------------
def check_stale_paths():
    """整理过目录之后，文档里残留的旧绝对路径会让人照着跑失败。"""
    stale = []
    for p in (SPEC, INTEL, ASSETS,
              os.path.join(DATA, "数据核对表.md"),
              os.path.join(DATA, "引脚核对表.md")):
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r"D:\\qoder cn\\heikeson\\[^\s\"\\]+", t):
            if "Qoder参赛包" not in m.group(0):
                stale.append(f"{os.path.basename(p)}: {m.group(0)}")
    if stale:
        bad("路径已同步（无旧目录残留）", "；".join(sorted(set(stale))))
    else:
        ok("路径已同步（无旧目录残留）")


def check_doc_numbers(d):
    """文档里写死的「736 行」「60 KB」「194 引脚」这类数字，必须和实际一致。
    这类错误最容易在改完文件之后出现，而且没人会去数。"""
    readme = os.path.join(PKG, "README.md")
    if not os.path.exists(readme):
        bad("README 存在")
        return
    ok("README 存在", f"{os.path.getsize(readme):,} B")

    n_lines = len(open(SPEC, encoding="utf-8").read().split("\n"))
    # 用和 Windows 资源管理器一致的算法：整除，不四舍五入
    size_kb = os.path.getsize(os.path.join(DATA, "data.json")) // 1024
    n_pins = sum(len(m["pins"]) for m in d["mcus"].values()) if d else 0

    for doc, path in (("README", readme), ("规格书", SPEC)):
        t = open(path, encoding="utf-8").read()
        # 行数声明：只认明确指向「规格书」的行数。
        # （早先直接用 r"(\d{3})\s*行" 会把「我做过 2866 行的 ESP32 项目」误判成规格书 866 行）
        claim_bad = None
        for m in re.finditer(r"规格书[^\n]{0,30}?(\d{3,4})\s*行", t):
            if int(m.group(1)) != n_lines:
                claim_bad = f"说 {m.group(1)} 行，实际 {n_lines} 行"
                break
        # README 里的模糊说法「2000+ 行」只校验下限
        if not claim_bad:
            for m in re.finditer(r"(\d{3,4})\+\s*行", t):
                if int(m.group(1)) > n_lines:
                    claim_bad = f"说 {m.group(1)}+ 行，实际只有 {n_lines} 行"
        if claim_bad:
            bad(f"{doc} 行数声明", claim_bad)
        else:
            ok(f"{doc} 行数声明与文件一致", f"规格书 {n_lines} 行")
    # data.json 体积 + 引脚总数
    for doc, path in (("README", readme), ("规格书", SPEC)):
        t = open(path, encoding="utf-8").read()
        for m in re.finditer(r"(\d{2})\s*KB（?62,100", t):
            if int(m.group(1)) != size_kb:
                bad(f"{doc} data.json 体积声明", f"说 {m.group(1)} KB，实际 {size_kb} KB")
        if "194 引脚" in t and n_pins != 194:
            bad(f"{doc} 引脚总数声明", f"说 194，实际 {n_pins}")
    ok("文档数字自洽", f"规格书 {n_lines} 行 / data.json {size_kb} KB / 共 {n_pins} 引脚")


def check_scripts():
    need = ["_parse_mcu_db.py", "_build_data.py"]
    for n in need:
        p = os.path.join(HERE, n)
        if os.path.exists(p):
            ok(f"脚本存在：{n}", f"{os.path.getsize(p):,} B")
        else:
            bad(f"脚本存在：{n}")
    # 脚本里不该再写死盘符输出路径
    for n in need:
        p = os.path.join(HERE, n)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        if 'OUT = r"D:' in t:
            bad(f"{n} 输出路径不写死", "还写死 D: 盘路径")
        else:
            ok(f"{n} 输出路径跟着脚本走")


# ---------------- 报告 ----------------
def report():
    n_bad = sum(1 for r in results if r[0] == "❌")
    n_warn = sum(1 for r in results if r[0] == "⚠️")
    n_ok = sum(1 for r in results if r[0] == "✅")
    n_skip = sum(1 for r in results if r[0] == "⏭")

    L = ["# 自检报告", ""]
    L.append(f"**结论：{'❌ 有 ' + str(n_bad) + ' 项不通过，先别投稿' if n_bad else '✅ 全部通过，可以投稿'}**")
    L.append("")
    L.append(f"| 项 | 数量 |")
    L.append("|---|---|")
    L.append(f"| ✅ 通过 | {n_ok} |")
    L.append(f"| ⚠️ 提醒 | {n_warn} |")
    L.append(f"| ⏭ 跳过（按设计排除） | {n_skip} |")
    L.append(f"| ❌ 不通过 | {n_bad} |")
    L.append("")
    L.append("## 逐项结果")
    L.append("")
    L.append("| 结果 | 检查项 | 详情 |")
    L.append("|---|---|---|")
    for r, item, msg in results:
        L.append(f"| {r} | {item} | {msg} |")
    L.append("")
    out = os.path.join(PKG, "自检报告.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))

    # 控制台
    for r, item, msg in results:
        if r != "✅":
            print(f"{r} {item}  {msg}")
    print(f"\n通过 {n_ok} / 提醒 {n_warn} / 跳过 {n_skip} / 不通过 {n_bad}")
    print("报告：", out)
    return n_bad


if __name__ == "__main__":
    check_files()
    d = check_data()
    check_spec_consistency(d)
    check_privacy()
    check_stale_paths()
    check_doc_numbers(d)
    check_scripts()
    sys.exit(1 if report() else 0)
