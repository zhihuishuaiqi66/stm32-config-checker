# -*- coding: utf-8 -*-
"""
从 STM32CubeMX 自带器件库 (db/mcu/*.xml) 解析三款芯片的权威引脚数据，
生成作品「不点鼠标配 STM32」要用的 data.json + 人看的核对表。

数据来源：ST 官方 CubeMX 器件库，不是我手写的。这是作品可信度的基础。
"""
import json
import os
import re
import xml.etree.ElementTree as ET

DB = r"D:\STM32CubeMX\db\mcu"
# 输出目录跟着脚本走，不写死盘符：脚本在 <包>\脚本\ 下，数据放 <包>\stm32-data\
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stm32-data"))

SRC = {
    "STM32F103C8T6": "STM32F103C(8-B)Tx.xml",
    "STM32F407ZGT6": "STM32F407Z(E-G)Tx.xml",
    "STM32F411CEU6": "STM32F411C(C-E)Ux.xml",
}

NS = "{http://mcd.rou.st.com/modules.php?name=mcu}"

# 引脚名 → 特殊用途归类用的信号关键字
# 注意 CubeMX 库里的信号名常带 SYS_ 前缀，如 SYS_JTMS-SWDIO / SYS_JTRST
SPECIAL_RULES = [
    ("swd",  ("SWDIO", "SWCLK")),
    ("jtag", ("JTRST", "JTDO", "JTCK", "JTMS", "JTDI", "TRACESWO")),
    ("usb",  ("USB_DM", "USB_DP", "USB_OTG_FS_DM", "USB_OTG_FS_DP",
              "USB_OTG_HS_DM", "USB_OTG_HS_DP")),
    ("osc",  ("OSC_IN", "OSC_OUT")),
    ("lse",  ("OSC32_IN", "OSC32_OUT")),
]


def norm_pin(name):
    """把 'PA0-WKUP' / 'PC13-TAMPER-RTC' 这类名字归一到 'PA0' / 'PC13'"""
    m = re.match(r"^(P[A-K]\d{1,2})", name)
    return m.group(1) if m else name


def classify(signals):
    """把该引脚上挂的所有信号归成特殊用途标记"""
    flags = set()
    joined = " ".join(signals).upper()
    for flag, keys in SPECIAL_RULES:
        for k in keys:
            if k in joined:
                flags.add(flag)
                break
    return sorted(flags)


def funcs_of(signals):
    """把信号名整理成网页上能显示的「可选功能」列表，去掉 GPIO 重复项"""
    out = []
    for s in signals:
        su = s.strip()
        if not su or su.upper() == "GPIO":
            continue
        if su not in out:
            out.append(su)
    return out


def parse(mcu_name, filename):
    path = os.path.join(DB, filename)
    tree = ET.parse(path)
    root = tree.getroot()

    def attr(el, key, default=None):
        return el.get(key, default)

    info = {
        "part": mcu_name,
        "line": attr(root, "Line"),
        "family": attr(root, "Family"),
        "package": attr(root, "Package"),
        "ref": attr(root, "RefName"),
        "core": None,
        "max_sysclk_mhz": None,
        "flash_kb": [],
        "ram_kb": None,
        "io_count": None,
        "voltage": None,
        "pins": [],
        "power_pins": [],
        "special": {"swd": [], "jtag": [], "usb": [], "osc": [], "lse": [], "boot": []},
    }

    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "Core":
            info["core"] = (el.text or "").strip()
        elif tag == "Frequency":
            info["max_sysclk_mhz"] = int((el.text or "0").strip())
        elif tag == "Flash":
            info["flash_kb"].append(int((el.text or "0").strip()))
        elif tag == "Ram":
            info["ram_kb"] = int((el.text or "0").strip())
        elif tag == "IONb":
            info["io_count"] = int((el.text or "0").strip())
        elif tag == "Voltage":
            info["voltage"] = {"min": attr(el, "Min"), "max": attr(el, "Max")}

    # 解析引脚（只在 Mcu 下直接找 Pin，避免抓错层级）
    for pin in root.findall(f"{NS}Pin"):
        raw = attr(pin, "Name")
        pos = attr(pin, "Position")
        ptype = attr(pin, "Type")
        if ptype == "Power":
            info["power_pins"].append({"name": raw, "num": int(pos)})
            continue

        sigs = []
        for sig in pin.findall(f"{NS}Signal"):
            sigs.append(attr(sig, "Name", ""))
        # 老库可能不带命名空间，兜底
        if not sigs:
            for sig in pin.findall("Signal"):
                sigs.append(attr(sig, "Name", ""))

        clean = norm_pin(raw)
        flags = classify(sigs)
        if clean.upper().startswith("BOOT") or ptype == "Boot":
            flags = sorted(set(flags) | {"boot"})
        # 只有 I/O 型引脚才能被分配外设；Boot/Reset 型要单独标出来
        assignable = (ptype == "I/O")

        info["pins"].append({
            "name": clean,
            "raw": raw,
            "num": int(pos),
            "type": ptype,
            "assignable": assignable,
            "funcs": funcs_of(sigs),
            "warn": flags,
        })
        for f in flags:
            info["special"].setdefault(f, []).append(clean)

    info["pins"].sort(key=lambda p: p["num"])
    for k in info["special"]:
        info["special"][k] = sorted(set(info["special"][k]))
    return info


def compress(nums):
    """[0,1,2,3,7,8] → 'Px0–Px3, Px7–Px8' 这类紧凑写法（返回纯数字段，由调用方拼前缀）"""
    if not nums:
        return ""
    nums = sorted(nums)
    segs, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        segs.append((start, prev))
        start = prev = n
    segs.append((start, prev))
    out = []
    for a, b in segs:
        out.append(f"{a}" if a == b else f"{a}–{b}")
    return ", ".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {}
    for part, fn in SRC.items():
        p = os.path.join(DB, fn)
        if not os.path.exists(p):
            print(f"!! 缺文件 {p}")
            continue
        data[part] = parse(part, fn)
        d = data[part]
        print(f"[OK] {part:16s} {d['package']:10s} {d['core']:16s} "
              f"{d['max_sysclk_mhz']:3d}MHz  IO={len(d['pins']):3d}  "
              f"Flash={d['flash_kb']}  RAM={d['ram_kb']}")

    with open(os.path.join(OUT, "stm32-pins.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # 人看的摘要
    lines = ["# 三款芯片引脚数据核对表", "",
             "> 来源：`D:\\STM32CubeMX\\db\\mcu\\*.xml`（ST 官方 CubeMX 器件库，非手写）",
             "> 生成时间：见文件系统时间", ""]
    for part, d in data.items():
        lines.append(f"## {part}")
        lines.append("")
        lines.append(f"| 项 | 值 |")
        lines.append(f"|---|---|")
        lines.append(f"| 封装 | {d['package']} |")
        lines.append(f"| 内核 | {d['core']} |")
        lines.append(f"| 最高主频 | {d['max_sysclk_mhz']} MHz |")
        lines.append(f"| Flash 可选 | {d['flash_kb']} KB |")
        lines.append(f"| RAM | {d['ram_kb']} KB |")
        n_io = sum(1 for p in d["pins"] if p["assignable"])
        lines.append(f"| 可用 IO | {n_io} 个（另 {len(d['pins']) - n_io} 个为 BOOT/RESET） |")
        lines.append("")
        sp = d["special"]
        rows = []
        for label, key in (("SWD 调试口", "swd"), ("JTAG 口", "jtag"),
                           ("USB", "usb"), ("主晶振", "osc"),
                           ("32.768k 晶振", "lse"), ("启动脚", "boot")):
            if sp.get(key):
                rows.append(f"| {label} | {', '.join(sp[key])} |")
        if rows:
            lines.append("| 特殊引脚 | 引脚 |")
            lines.append("|---|---|")
            lines.extend(rows)
            lines.append("")
        names = [p["name"] for p in d["pins"]]
        gpio = [n for n in names if re.match(r"^P[A-K]\d", n)]
        absent = []
        for port in "ABCDEFGHIK":
            have = sorted({int(n[2:]) for n in gpio if n[1] == port})
            if not have:
                absent.append(f"P{port} 整组没有")
                continue
            gaps = [i for i in range(16) if i not in have]
            if gaps:
                absent.append(f"P{port} 缺 P{port}{compress(gaps).replace(', ', f', P{port}').replace('–', f'–P{port}')}")
        if absent:
            lines.append("**这个封装上不存在的脚：** " + "；".join(absent))
            lines.append("")
    with open(os.path.join(OUT, "引脚核对表.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n写出：", os.path.join(OUT, "stm32-pins.json"))
    print("写出：", os.path.join(OUT, "引脚核对表.md"))


if __name__ == "__main__":
    main()
