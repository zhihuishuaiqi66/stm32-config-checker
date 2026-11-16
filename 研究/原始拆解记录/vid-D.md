# vid-D 逐格画面拆解：11:15 – 14:53

> 视频：B 站 keysking《【STM32】超清晰STM32时钟树动画讲解》BV1ph4y1e7Ey
> 本段：11:15–14:53（675s – 893s；原片 1920×960 / 24fps / 总长 892.958s）
> 拼图：`segD_01.jpg`（11:15–13:15）、`segD_02.jpg`（13:20–14:53），各 5×5=25 格，逐格按阅读顺序看过
> **另做的核对**：为把图里的小字读准，按换算公式把每格对应时间点的**原生分辨率帧**从原片抽出（675,680,…,890 共 44 帧，存于 `_视频拆解\frames_D\`），逐帧看过一遍；关键方框/数值再裁切放大复核。
> 记录原则：**只写画面上出现的文字、数字、图形**。底部烧录字幕属于画面内容，按原文引用（原文错字保留）。ASR 台词只用于定位，不作依据。

---

## 时间轴

| 时间 | 画面内容 | 讲什么（画面底部字幕原文） |
|---|---|---|
| 11:15 (675s) | 黑底动画时钟树（全图）：HSI`8MHz`/HSE`8MHz` → MUX（绿点在 HSI）→ SYSCLK 框显示`8MHz` → AHB 预分频为空框 → HCLK 框`72MHz`；右侧 72/72/36/72/72/72/12 全亮；**此时还没有 PLL 方框** | 是的 所以其实系统时钟还有另外一个选项可以选择 |
| 11:20 (680s) | 画出橙色圆角框「PLL锁相环」（框内空），一条线接到 MUX 的第三个输入 | 锁相环(PLL)的具体原理我们不去深究 |
| 11:25 (685s) | PLL 框内出现一个白框 + 一个黄框（都还空着） | 它在此处起到的是倍频器的作用 |
| 11:30 (690s) | PLL 输入侧出现蓝色 `/2` 框（HSI 侧，从 HSI 干线向下引）和第二个蓝框（HSE 侧）；HSE 分两路：一路进 MUX，一路进 PLL | 也就是高速内部时钟HSI与高速外部时钟HSE |
| 11:35 (695s) | HSI 侧固定 `/2` 分频框点亮，旁白点明"固定大小" | 来自HSI的输入前有一个固定大小为/2的分频器 |
| 11:40 (700s) | HSE 侧两个蓝框上下叠放（上`/2`、下空），框下标注`/1 /2` | 而来自HSE的输入前则有一个可以选择/1或/2的分频器 |
| 11:45 (705s) | PLL 框内白框、黄框仍空；PLL 框下方出现`×2 ×3 … ×16` | 而PPL锁相环可以×2 ×3 ×4 …一直到×16（画面原文把 PLL 打成 PPL） |
| 11:50 (710s) | HSE 侧 `/1` 框被绿点点亮（选中 /1），`/2` 仍亮蓝 | 因而 只要我们使用8MHz的高速外部时钟源 分频器/1 锁相环×9 |
| 11:55 (715s) | PLL 内白框显示`8MHz`、黄框显示`×9`；SYSCLK`72MHz`、AHB`/1`、HCLK`72MHz` 整条点亮；ADC `/6` 框下出现`/2 /4 /6 /8` | （该格无字幕，两句之间） |
| 12:00 (720s) | 全树 72MHz 贯通 | 而只要AHB预分频器是/1 那么HCLK也就是72MHz了 |
| 12:05 (725s) | 全树 | 嗯~ 不错 我们已经得到了STM32时钟树最主要的部分 |
| 12:10 (730s) | 切到 **CubeMX → Clock Configuration** 时钟树全图：SYSCLK `72` / AHB Prescaler `/1` / HCLK `72`（`72 MHz max`）/ `/1`→`To Cortex System timer 72` / `FCLK (MHz) 72` / APB1 `/2`→`36`（`36 MHz max`）+`X 2`→`72` / APB2 `/1`→`72`（`72 MHz max`）+`X 1`→`72` / ADC `/2`→`36 To ADC1,2`；字幕位置偏高 | 可以发现 我们的时钟树还少些东西 |
| 12:15 (735s) | 同一张 CubeMX 图（画面略移），`FCLK (MHz) 72` 一栏就在这里 | 首先是这一个 FCLK 我们可以称其为 自由运行时钟 |
| 12:20 (740s) | 回到黑底动画树（全亮） | 需要STM32进入低功耗模式之一的"停止模式"时 |
| 12:25 (745s) | 动画树：HCLK 框与部分支路变灰 | AHB总线会停止运行 HCLK会停止传输时钟脉冲 |
| 12:30 (750s) | 右侧下游分支（SysTick / APB1 / APB2 / ADC）全部变灰 | 进而所有连接到AHB总线的外设全部停止运行 |
| 12:35 (755s) | 仍全灰 | 我们还需要重新唤醒STM32 |
| 12:40 (760s) | 右侧**新增一行** `72MHz FCLK(自由运行时钟)`（在 SysTick 下面） | 此时 FCLK 自由运行时钟的作用就得以展现 |
| 12:45 (765s) | CubeMX 截图：一条**红色粗折线**从 HCLK 框引到 `FCLK (MHz) 72` 框（绕开 APB1 预分频） | 虽然在CubeMX上看 它来自HCLK |
| 12:50 (770s) | 动画树（含 FCLK 行） | 它的真正来源是AHB的预分频器 |
| 12:55 (775s) | FCLK 的连线改画到 AHB 预分频输出处（HCLK 之前分叉） | 因而在HCLK停止运行时 FCLK会继续运行 |
| 13:00 (780s) | CubeMX 截图，聚焦 `8 To FLITFCLK (MHz)` 这条支路 | 然后是这一条分支 这是Flash编程接口的时钟 它永远来自于HSI |
| 13:05 (785s) | CubeMX 截图（PLL / USB 区域完整可见：`PLL Source Mux` → `PLL`(`*PLLMul ×9`) → `USB Prescaler /1` → `72 To USB (MHz)`） | 然后是这一条分支 这是Flash编程接口的时钟 它永远来自于HSI |
| 13:10 (790s) | 同上，画面停在 PLL→USB 一段 | 这一条分支是用于给USB功能提供时钟 来自PLL锁相环 |
| 13:15 (795s) | CubeMX 截图，`Enable CSS` 旁出现**书法感粗体加注「时钟安全系统」** | 在时钟源是HSE或者经过PLL倍频过的HSE时 |
| 13:20 (800s) | 同图 + **橙色粗折线**三条：HSE→System Clock Mux 的 HSE 输入；HSE→PLL Source Mux 的 HSE 输入；PLL 输出→System Clock Mux 的 PLLCLK 输入 | 就可以选择开启CSS功能 |
| 13:25 (805s) | 左下 `Input frequency 8 / HSE` 框被**红色大叉**划掉 | 它可以在HSE发生故障时 立即将时钟源切换回HSI |
| 13:30 (810s) | **橙色粗箭头**从 `HSI RC 8` 直指 System Clock Mux 的 HSI 输入；红叉仍在 | 并且产生中断 让我们可以进行紧急制动等紧急处理 |
| 13:35 (815s) | CubeMX 图上半部（LSE / LSI RC / RTC Clock Mux / IWDG / FLITFCLK） | 时钟源是低速内部时钟LSI与低速外部时钟LSE |
| 13:40 (820s) | 同区域，LSE 与 LSI 输入端旁有**橙色小实心方块**标记 | 或者是高速外部时钟的128分频 |
| 13:45 (825s) | **橙色粗方括号**框住 `40 To RTC (KHz)` 输出框 | 挂在上面的外设是RTC实时时钟与看门狗 |
| 13:50 (830s) | 同页，标注已撤 | 整个结构非常简单 小伙伴们应该可以一眼看透了 |
| 13:55 (835s) | CubeMX 下滚到最底部：`MCO source Mux`（`/2`←`PLLCLK`、`HSI`、`HSE`）与 `(MHz) MCO` | 然后最下面这一部分是MCO(Master Clock Output)时钟输出功能 |
| 14:00 (840s) | 切 **Pinout & Configuration → RCC**：`High Speed Clock (HSE) = Crystal/Ceramic Resonator`、`Low Speed Clock (LSE) = Disable`、`Master Clock Output` 未勾；右侧 LQFP48 引脚图 PA8 为普通引脚 | 回到基本设置 勾选Master Clock Output后 |
| 14:05 (845s) | `Master Clock Output` 已勾选，**PA8 变绿并标出 `RCC_MCO`** | 回到时钟设置 选择其中一个时钟信号 就可以将其从PA8引脚输出出来 |
| 14:10 (850s) | 切回 Clock Configuration 并下滚：MCO 源 mux 选中 `/2 → PLLCLK`，`(MHz) MCO` 框 =`36` | 回到时钟设置 选择其中一个时钟信号 就可以将其从PA8引脚输出出来 |
| 14:15 (855s) | CubeMX 画面淡出 | 那么至此 我们的整个时钟树就全部讲解完成了～ |
| 14:20 (860s) | 黑底动画树（含 FCLK 行的完整版） | 涉及的概念非常多 有许多我们尚未学习到 |
| 14:25 (865s) | 同图（ADC `/6` 下 `' /2 /4 /6 /8'` 可见） | 没有关系 常看常新 |
| 14:30 (870s) | 同图 | 相信过段时间 又成长了许多的你再来看看 会有新的收获 |
| 14:35 (875s) | 同图 + 二维码浮层「keysking和他的朋友们」 | 或者加入交流QQ群 与众多小伙伴们一起讨论 |
| 14:40 (880s) | 纯背景（KK / STM32教程 水印） | 那么本期视频的内容到这里就结束了 |
| 14:45 (885s) | 标题卡「下期预告 / TIM 定时器」 | 下期视频我们将开始STM32中非常重要的一部分 定时器 的学习 |
| 14:50 (890s) | 标题卡「KEYSKINTG & 博哥在学习」（左侧红色小方块） | 我们下期视频见~ |

> 换算公式里 14:55–15:20（895–920s，即两张拼图各第 45 格之后）**超出片长**，拼图上为黑格，无画面。

---

## 分频器与倍频器全表

### A. 黑底动画时钟树里的方框（本段画面的主体）

| # | 位置 | 方框写法（当前值） | 可选值（画面原文） | 说明 |
|---|---|---|---|---|
| 1 | HSI → PLL 输入 | 蓝框`/2` | 只有`/2`（无其它选项） | 字幕称"固定大小为/2" |
| 2 | HSE → PLL 输入 | 蓝框`/1`（选中，绿点）；上方另一个蓝框`/2` | 框下标注`/1 /2` | 两框叠放，二选一 |
| 3 | PLL 倍频 | 黄框`×9` | PLL 框下方标注`×2 ×3 … ×16` | 白框(输入频率)+黄框(倍频)在同一个橙色圆角框「PLL锁相环」内 |
| 4 | AHB 预分频 | 蓝方框`/1`（11:15–11:50 为空框） | 框上方标注`/1 /2 /4 … /256` | 输出即 HCLK |
| 5 | SysTick 分频 | 蓝框`/1` | 框下标注`/1 /8` | 输出给「SysTick(系统滴答)」 |
| 6 | APB1 预分频 | 蓝框`/2` | 框上方标注`/1 /2 /4 /8 /16` | 输出 PCLK1 → APB1外设 |
| 7 | APB1 定时器倍频 | 黄框`×2` | 框旁标注`×1 ×2` | 输出 APB1定时器 |
| 8 | APB2 预分频 | 蓝框`/1` | 框上方标注`/1 /2 /4 /8 /16` | 输出 PCLK2 → APB2外设 |
| 9 | APB2 定时器倍频 | 黄框`×1` | 框旁标注`×1 ×2` | 输出 APB2定时器 |
| 10 | ADC 预分频 | 蓝框`/6` | 框下标注`/2 /4 /6 /8` | 输出 ADC |

### B. CubeMX 截图里的分频/倍频控件（本段 12:10 起大量出现）

| # | 控件名（画面原文） | 画面上的值 | 输出/备注 |
|---|---|---|---|
| 11 | AHB Prescaler | `/1`（下拉） | → HCLK (MHz) 72 |
| 12 | APB1 Prescaler | `/2`（下拉） | → PCLK1 36，标 `36 MHz max` |
| 13 | APB2 Prescaler | `/1`（下拉） | → PCLK2 72，标 `72 MHz max` |
| 14 | ADC Prescaler | `/2`（下拉） | → 36 To ADC1,2 |
| 15 | USB Prescaler | `/1`（下拉） | → 72 To USB (MHz) |
| 16 | PLL Source Mux 前的 HSI 支路 | `/2` 方框 | 固定 |
| 17 | PLL Source Mux 前的 HSE 支路 | `/1`（下拉） | 可 `/1`/`/2` |
| 18 | *PLLMul | `×9`（下拉） | PLL 内 `8` → `×9` |
| 19 | HSE → RTC 支路 | `/ 128` 方框 → `HSE_RTC` | 进 RTC Clock Mux |
| 20 | To Cortex System timer 前 | `/1`（下拉） | → 72 |
| 21 | APB1 Timer clocks 前 | `X 2` 方框 | 36×2 → 72 |
| 22 | APB2 timer clocks 前 | `X 1` 方框 | 72×1 → 72 |
| 23 | MCO source Mux 里 PLLCLK 前 | `/2` 方框 | → (MHz) MCO |

---

## 所有数值

### A. 动画图（黑底）上的数值与走向

| 节点 | 画面数值 | 怎么从上一级来（画面所示） |
|---|---|---|
| HSI 高速内部时钟 | `8MHz` | 源头 |
| HSE 高速外部时钟 | `8MHz` | 源头 |
| HSI→PLL 分频 | `/2` | 画面只写 `/2`，未写结果值 |
| HSE→PLL 分频 | `/1`（选中）/ `/2` | 画面只写分频比 |
| PLL 输入（白框） | `8MHz` | 选中 HSE`/1` 时显示 8MHz |
| PLL 输出 | `×9` | 8MHz ×9 = 72MHz（**72 这个结果直接显示在 SYSCLK 框上**） |
| SYSCLK | `72MHz` | PLL ×9 的输出 |
| AHB 预分频 | `/1` | — |
| HCLK | `72MHz` | 72 ÷ 1 |
| 内核/内存/DMA | `72MHz` | 直连 HCLK |
| SysTick(系统滴答) | `72MHz` | HCLK ÷1（另可选 /8） |
| FCLK(自由运行时钟) | `72MHz` | 画面说"真正的来源是AHB的预分频器"，与 HCLK 同频 |
| APB1外设 | `36MHz` | 72 ÷ 2 |
| APB1定时器 | `72MHz` | 36 × 2 |
| APB2外设 | `72MHz` | 72 ÷ 1 |
| APB2定时器 | `72MHz` | 72 × 1 |
| ADC | `12MHz` | 72 ÷ 6 |

### B. CubeMX 截图上的数值

| 项 | 画面值 |
|---|---|
| Input frequency（LSE） | `32.768`，标注 `0-1000 KHz` |
| LSE | 灰色框 `32.768` |
| LSI RC | `40`，`40 KHz` |
| To RTC (KHz) | `40` |
| To IWDG (KHz) | `40` |
| HSE | `8`，`4-16 MHz` |
| HSI RC | `8`，`8 MHz` |
| To FLITFCLK (MHz) | `8` |
| SYSCLK (MHz) | `72` |
| HCLK (MHz) | `72`，标 `72 MHz max` |
| PCLK1 | `36`，标 `36 MHz max` → APB1 peripheral clocks `36` |
| APB1 Timer clocks (MHz) | `72`（经 `X 2`） |
| PCLK2 | `72`，标 `72 MHz max` → APB2 peripheral clocks `72` |
| APB2 timer clocks (MHz) | `72`（经 `X 1`） |
| ADC Prescaler 输出 | `36` To ADC1,2 |
| USB | `72` To USB (MHz) |
| MCO | `36` (MHz) |
| FCLK (MHz) | `72` |
| PLL | 输入 `8` → `*PLLMul ×9` → `PLLCLK` |
| System Parameters | `VDD voltage (V) 3.3 V`、`Prefetch Buffer Enabled`、`Flash Latency(WS) 2 WS (3 CPU cycle)` |
| RCC Parameters | `HSI Calibration Value 16`、`HSE Startup Timeout Value (ms) 100` |
| 芯片 | `STM32F103C8Tx` / `LQFP48` |

### C. 画面直接给出的算式（字幕原话）

- 11:50：`8MHz 的高速外部时钟源` + `分频器/1` + `锁相环×9` → `72MHz`
- 12:00：`AHB分频器是/1` → `HCLK 也就是 72MHz`

---

## 交叉核对差异

对照 `D:\qoder cn\heikeson\Qoder参赛包\stm32-data\data.json` → `mcus["STM32F103C8T6"]`

| # | 项目 | 画面上写的 | data.json | 结论 |
|---|---|---|---|---|
| 1 | sysclk | SYSCLK `72MHz`（动画）/ CubeMX `72` | `limits.sysclk=72`、`max_sysclk_mhz=72` | ✅ 一致 |
| 2 | hclk | `72`，标 `72 MHz max` | `limits.hclk=72` | ✅ 一致 |
| 3 | apb1 | `36`，标 `36 MHz max`；动画 APB1外设 `36MHz` | `limits.apb1=36` | ✅ 一致 |
| 4 | apb2 | `72`，标 `72 MHz max`；动画 APB2外设 `72MHz` | `limits.apb2=72` | ✅ 一致 |
| 5 | adc | 动画示例 `/6 → 12MHz`（12 ≤ 14，合规）；**但 CubeMX 截图里 `ADC Prescaler /2 → 36 To ADC1,2`**，且画面没标红、没解释 | `limits.adc=14` | ❌ **对不上**：截图里的 ADC 时钟 36MHz 超过 14MHz 上限（这段画面本身没给解释） |
| 6 | pll_mul | 动画 `×2 ×3 … ×16`；CubeMX `×9` | `pll_mul=[2..16]` | ✅ 一致 |
| 7 | HSE 进 PLL 的分频 | 动画明确 `HSE → /1 或 /2`；CubeMX `PLL Source Mux` 前 HSE 侧是 `/1` 下拉 | 任务给的参考键 `hse_pll_div=[1,2]`；但 data.json 里**没有** `hse_pll_div` 键，相关的是 `pll_input_div=null`、`pll_source=["HSE","HSI/2"]` | ⚠️ **数据表缺这一项**（键名/字段与要求不符，`pll_input_div` 为 null 就没表达出 HSE 的 /1 或 /2） |
| 8 | apb_presc | 动画 `APB1/APB2` 预分频均标 `/1 /2 /4 /8 /16` | `apb_presc=[1,2,4,8,16]` | ✅ 一致 |
| 9 | ahb_presc | 动画只写 `/1 /2 /4 … /256`（用省略号） | `ahb_presc=[1,2,4,8,16,32,64,128,256,512]` | ⚠️ **范围不同**：画面最高只列到 `/256`，数据表到 `/512`（画面用省略号，不能断定它排除了 /512，但画面上确实没出现 /512） |
| 10 | adc_presc | 动画 `/6` 框下 `/2 /4 /6 /8` | `adc_presc=[2,4,6,8]` | ✅ 一致 |
| 11 | tim_doubling | 动画 `×1 ×2` | `tim_doubling=true` | ✅ 一致 |
| 12 | hse_default | `HSE 8`、`4-16 MHz` | `hse_default_mhz=8`、`hse_options_mhz=[8,12,16,25]` | ✅ 一致 |
| 13 | hsi | `HSI RC 8`、`8 MHz` | `hsi_mhz=8` | ✅ 一致 |
| 14 | pll_source | HSI 前固定 `/2`，HSE 前 `/1` 或 `/2` | `pll_source=["HSE","HSI/2"]` | ✅ 一致（但只写了 HSI/2 与 HSE，未写 HSE 的 /2） |
| 15 | usb | `USB Prescaler /1 → 72 To USB (MHz)` | `limits.usb=null` | ⚠️ **无法核对**：数据表没给 USB 参考值，画面也没有说明 72 是否符合 USB 要求 |

---

## 看不清存疑

1. **11:15（675s）这一格自相矛盾**：SYSCLK 框显示 `8MHz`，但后面 HCLK 框显示 `72MHz`，AHB 预分频还是个空框；到 11:55（715s）才统一成 SYSCLK 72 / AHB /1 / HCLK 72。画面本身如此，原因画面里没有交代。
2. **13:05 / 13:10（785s / 790s）**：字幕条正好压在 CubeMX 图下半部，`USB Prescaler` 那一行会被遮住一部分；完整可读的只有 785 与 790 两格的上下错位。
3. `To USB (MHz)` 的 `72` 与 `To ADC1,2` 的 `36` 都是**灰色字**（CubeMX 里未高亮的样式），画面没给任何说明。
4. `时钟安全系统` 这几个字是**粗体书法风字体 + 白边**，不是手写笔迹，无法判断是作者手写还是直接打的字。
5. 13:35–13:50（815–830s）几格是 CubeMX 同一页的不同滚动位置，画面**没有**给出 LSI / LSE / RTC / IWDG 的具体频率换算过程（RTC 那栏显示 `40 To RTC (KHz)`，与 `32.768` 的 LSE 数值对不上，画面未解释）。
6. 拼图第 45–50 格（895s 之后）超出片长，是黑格，不是画面内容。

---

## 附录 A：画面上出现的总线 / 外设 / 引脚 / 寄存器 / 控件名

**总线与时钟线名**
`AHB`、`AHB bus`、`APB1`、`APB2`、`HCLK`、`SYSCLK`、`PCLK1`、`PCLK2`、`FCLK`、`PLLCLK`、`HSE_RTC`

**外设 / 时钟域（动画图右侧标签）**
`内核/内存/DMA`、`SysTick(系统滴答)`、`FCLK(自由运行时钟)`、`APB1外设`、`APB1定时器`、`APB2外设`、`APB2定时器`、`ADC`
（CubeMX 英文写法：`HCLK to AHB bus, core, memory and DMA (MHz)`、`To Cortex System timer (MHz)`、`APB1 peripheral clocks (MHz)`、`APB1 Timer clocks (MHz)`、`APB2 peripheral clocks (MHz)`、`APB2 timer clocks (MHz)`、`To ADC1,2`、`To USB (MHz)`、`To RTC (KHz)`、`To IWDG (KHz)`、`To FLITFCLK (MHz)`、`(MHz) MCO`）

**CubeMX 内部模块名**
`RTC Clock Mux`、`LSI RC`、`HSI RC`、`LSE`、`HSE`、`Input frequency`、`PLL Source Mux`、`PLL`、`*PLLMul`、`System Clock Mux`、`AHB Prescaler`、`APB1 Prescaler`、`APB2 Prescaler`、`ADC Prescaler`、`USB Prescaler`、`MCO source Mux`、`Enable CSS`、`72 MHz max` / `36 MHz max` / `4-16 MHz` / `0-1000 KHz` / `40 KHz` / `8 MHz`

**引脚 / 芯片**
`PA8`（= `RCC_MCO`）、`PD0`（`RCC_OSC_IN`）、`PD1`（`RCC_OSC_OUT`）、`PC14`/`PC15`、`NRST`、`BOOT0`、`VBAT`、`VDD`/`VSS`/`VDDA`/`VSSA`、`TIM3_CH1`、`STM32F103C8Tx`、`LQFP48`

**界面元素**
`Pinout & Configuration`、`Clock Configuration`、`Project Manager`、`Software Packs`、`Pinout`、`Resolve Clock Issues`、`System Core`、`DMA`、`GPIO`、`IWDG`、`NVIC`、`RCC`、`SYS`、`WWDG`、`Analog`、`Timers`、`Connectivity`、`Computing`、`Middleware and Software`、`Parameter Settings`、`User Constants`、`NVIC Settings`、`GPIO Settings`、`Reset Configuration`、`RCC Mode and Configuration`、`High Speed Clock (HSE)`、`Low Speed Clock (LSE)`、`Master Clock Output`、`Crystal/Ceramic Resonator`、`Disable`、`System Parameters`、`RCC Parameters`、`Pinout view`、`System view`

**寄存器名**：本段画面**没有**出现任何寄存器名（无 RCC_CR / RCC_CFGR 之类）。

---

## 附录 B：手写/手绘标注

| 时间 | 标注 | 画在什么上 |
|---|---|---|
| 13:15 (795s) 起 | 加注文字「**时钟安全系统**」（粗体书法风、白字黑边） | 压在 CubeMX 的 `Enable CSS` 与 `USB Prescaler` 之间 |
| 13:20 (800s) 起 | **橙色粗折线 3 条**：① HSE 干线 → System Clock Mux 的 `HSE` 输入；② HSE 干线 → PLL Source Mux 的 `HSE` 输入；③ PLL 输出 → System Clock Mux 的 `PLLCLK` 输入 | CubeMX 时钟树截图 |
| 13:25 (805s) 起 | **红色大叉**（两笔交叉） | 划在左下「Input frequency `8` / `HSE`」框上 |
| 13:30 (810s) | **橙色粗箭头** | 从 `HSI RC 8` 指向 System Clock Mux 的 `HSI` 输入（红叉同时保留） |
| 13:40 (820s) | **橙色小实心方块**（2 处） | LSE 输入旁、LSI 输入端旁 |
| 13:45 (825s) | **橙色粗方括号** | 框住 `40 To RTC (KHz)` 输出框 |
| 12:45 (765s) | **红色粗折线** | 从 `HCLK (MHz) 72` 框拉到 `FCLK (MHz) 72` 框 |

---

## 附录 C：作者的论证顺序与总结结论

**论证顺序（本段）**
1. 先给结论：系统时钟还有"另一个选项"——PLL（11:15）。画出空的 `PLL锁相环` 框（11:20），说明它在此处起**倍频器**作用（11:25）。
2. 讲 PLL 的两个输入前级：HSI 是**固定 /2**（11:35），HSE 是**可选 /1 或 /2**（11:40）。
3. 讲 PLL 的倍频范围 `×2…×16`（11:45），再代入具体值：HSE 8MHz `/1` `×9` = 72MHz（11:50），AHB `/1` → HCLK 72MHz（11:55–12:00）。
4. 收束："已经得到了 STM32 时钟树最主要的部分"（12:05）。
5. 拿 CubeMX 的时钟树图对照刚才的动画树，指出动画树"还少些东西"（12:10），然后逐样补：
   - **FCLK**：停止模式下 AHB/HCLK 停，外设全停；唤醒靠外部中断，此时 FCLK 继续跑给中断采样供时钟（12:20–12:55）。CubeMX 上它看起来来自 HCLK，但那只是表示同步、同频；真正来源是 AHB 预分频器（12:45–12:55）。
   - **FLITFCLK**（Flash 编程接口时钟）：永远来自 HSI，8MHz（13:00–13:05）。
   - **USB 时钟**：来自 PLL（13:10）。
   - **CSS 时钟安全系统**：当系统时钟源是 HSE 或经 PLL 倍频过的 HSE 时可开启；HSE 故障时立刻把时钟源切回 HSI，并产生中断以便紧急处理（13:15–13:30）。
   - **独立的小时钟树**：时钟源是 LSI、LSE，或高速外部时钟的 128 分频；上面挂 RTC 实时时钟与看门狗；结构很简单，RTC/看门狗章节再细讲（13:35–13:50）。
   - **MCO 时钟输出**：Pinout 里勾选 Master Clock Output 后 PA8 变成 RCC_MCO；回到时钟树选一路时钟信号即可从 PA8 输出（13:55–14:10）。
6. 收尾："至此整个时钟树全部讲解完成"（14:15）；概念很多、许多还没学到，"没有关系 常看常新"，过段时间再回来看会有新收获（14:20–14:30）；引导三连、评论区提问、加 QQ 群；预告下期 TIM 定时器（14:35–14:50）。

**总结结论**
- 本段把 STM32F103 时钟树补全到完整版：**HSI/HSE 8MHz → (HSI 固定 /2；HSE /1 或 /2) → PLL ×2…×16（本例 ×9）→ SYSCLK 72MHz → AHB /1 → HCLK 72MHz**，再经 SysTick`/1`、APB1`/2`(+`×2`)、APB2`/1`(+`×1`)、ADC`/6` 分到各外设，另外补出 **FCLK**（源自 AHB 预分频器、HCLK 停时继续跑）、**FLITFCLK**（恒为 HSI 8MHz）、**USB**（来自 PLL）、**CSS**（HSE 故障切回 HSI + 中断）、**LSI/LSE→RTC/IWDG 小时钟树**、**MCO→PA8** 这几块。
- 作者的落点：**CubeMX 上能看到的只是结果，理解"谁分频、谁倍频、谁直连"才看得懂时钟树**；本段先动画后 CubeMX 截图一一对照，把抽象结构落到界面上。
