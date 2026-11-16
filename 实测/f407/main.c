/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
/* 自检报告写在这里。固件跑完停在 while(1)，用 ST-Link 按地址把这块读回来。 */
volatile char     g_report[2400];
volatile uint32_t g_report_ready = 0;
volatile uint32_t g_heartbeat = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ===================== STM32F407 配置自检固件 ===================== */
#define REP_MAX 2400
static int g_pos = 0;

static void put(const char *fmt, ...)
{
  va_list ap;
  int n;
  if (g_pos >= REP_MAX - 1) return;
  va_start(ap, fmt);
  n = vsnprintf((char *)&g_report[g_pos], REP_MAX - g_pos, fmt, ap);
  va_end(ap);
  if (n > 0) {
    g_pos += n;
    if (g_pos > REP_MAX - 1) g_pos = REP_MAX - 1;
  }
}

static const char *hpre_str(uint32_t v)
{
  switch (v) {
    case 0x8: return "/2";   case 0x9: return "/4";   case 0xA: return "/8";
    case 0xB: return "/16";  case 0xC: return "/64";  case 0xD: return "/128";
    case 0xE: return "/256"; case 0xF: return "/512";
    default:  return "/1";
  }
}
static const char *ppre_str(uint32_t v)
{
  switch (v) {
    case 0x4: return "/2"; case 0x5: return "/4";
    case 0x6: return "/8"; case 0x7: return "/16";
    default:  return "/1";
  }
}

/* ---- PC13 心跳灯（板载 LED）---- */
static void led_init(void)
{
  RCC->AHB1ENR |= RCC_AHB1ENR_GPIOCEN;
  GPIOC->MODER = (GPIOC->MODER & ~(3u << 26)) | (1u << 26);  /* PC13 推挽输出 */
  GPIOC->BSRR = (1u << (13u + 16u));                          /* 先置低 */
}
static void led_toggle(void)
{
  static uint32_t on = 0;
  on = !on;
  if (on) GPIOC->BSRR = (1u << 13u);
  else    GPIOC->BSRR = (1u << (13u + 16u));
}

/* ---- T1：读 RCC 寄存器，看 F4 的 PLL 到底配成了什么 ---- */
static void test_t1_rcc(void)
{
  uint32_t cfgr    = RCC->CFGR;
  uint32_t pllcfgr = RCC->PLLCFGR;
  uint32_t sw      = cfgr & 0x3u;
  uint32_t hpre    = (cfgr >> 4) & 0xFu;
  uint32_t ppre1   = (cfgr >> 10) & 0x7u;
  uint32_t ppre2   = (cfgr >> 13) & 0x7u;
  uint32_t pllm    = pllcfgr & 0x3Fu;
  uint32_t plln    = (pllcfgr >> 6) & 0x1FFu;
  uint32_t pllpraw = (pllcfgr >> 16) & 0x3u;
  uint32_t pllq    = (pllcfgr >> 24) & 0xFu;
  uint32_t pllsrc  = (pllcfgr >> 22) & 0x1u;
  uint32_t pllp    = (pllpraw == 1u) ? 4u : (pllpraw == 2u) ? 6u : (pllpraw == 3u) ? 8u : 2u;

  put("[T1] RCC 寄存器回读\r\n");
  put("  SYSCLK 源    = %s\r\n", sw == 2u ? "PLL" : (sw == 1u ? "HSE" : "HSI"));
  put("  AHB 分频     = %s\r\n", hpre_str(hpre));
  put("  APB1 分频    = %s  (PCLK1)\r\n", ppre_str(ppre1));
  put("  APB2 分频    = %s  (PCLK2)\r\n", ppre_str(ppre2));
  put("  PLL 源       = %s\r\n", pllsrc ? "HSE" : "HSI");
  put("  PLLM=%lu  PLLN=%lu  PLLP=/%lu  PLLQ=%lu\r\n",
      (unsigned long)pllm, (unsigned long)plln, (unsigned long)pllp, (unsigned long)pllq);
}

/* ---- T2：HAL 算出来的频率 ---- */
static void test_t2_hal_clocks(void)
{
  put("[T2] HAL 计算的频率\r\n");
  put("  SYSCLK = %lu Hz\r\n", (unsigned long)HAL_RCC_GetSysClockFreq());
  put("  HCLK   = %lu Hz\r\n", (unsigned long)HAL_RCC_GetHCLKFreq());
  put("  PCLK1  = %lu Hz\r\n", (unsigned long)HAL_RCC_GetPCLK1Freq());
  put("  PCLK2  = %lu Hz\r\n", (unsigned long)HAL_RCC_GetPCLK2Freq());
}

/* ---- T3：定时器 x2 规则实测 ----
   F407: PCLK1 = 42MHz，APB1 分频 = 4（≠1）-> 硬件把 TIM3CLK 翻倍成 84MHz。
   PSC=8399 ARR=9999 -> 84MHz/8400/10000 = 1Hz -> 2 个周期约 2000ms。
   若没翻倍（42MHz）-> 约 4000ms。 */
static void test_t3_timer_double(void)
{
  uint32_t t0, t1, ms, i;
  volatile uint32_t guard;

  RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
  TIM3->CR1 = 0;
  TIM3->PSC = 8399;
  TIM3->ARR = 9999;
  TIM3->EGR = TIM_EGR_UG;
  TIM3->SR  = 0;
  TIM3->CR1 = TIM_CR1_CEN;

  t0 = HAL_GetTick();
  for (i = 0; i < 2u; i++) {
    guard = 0;
    while ((TIM3->SR & TIM_SR_UIF) == 0) {
      if (++guard > 20000000u) break;
    }
    TIM3->SR = ~TIM_SR_UIF;
  }
  t1 = HAL_GetTick();
  TIM3->CR1 = 0;
  ms = t1 - t0;

  put("[T3] 定时器 x2 规则实测\r\n");
  put("  PCLK1 = %lu Hz, APB1 分频 = %s\r\n",
      (unsigned long)HAL_RCC_GetPCLK1Freq(), ppre_str((RCC->CFGR >> 10) & 0x7u));
  put("  TIM3 PSC=8399 ARR=9999 -> 若 TIM3CLK=84MHz 应 1Hz\r\n");
  put("  实测 2 个周期 = %lu ms\r\n", (unsigned long)ms);
  if (ms > 1800u && ms < 2200u)
    put("  判定：约 2000ms -> TIM3CLK=84MHz，**x2 翻倍成立**\r\n");
  else if (ms > 3600u && ms < 4400u)
    put("  判定：约 4000ms -> TIM3CLK=42MHz，**x2 没发生**\r\n");
  else
    put("  判定：%lu ms 不在预期内\r\n", (unsigned long)ms);
}

/* ---- T4：F4 的 ADC 预分频（PCLK2=84MHz）----
   F4 的 ADC 时钟上限 36MHz。
   /4 -> 21MHz 合规；/2 -> 42MHz 超限。
   注意：① F4 的 ADC 预分频在 CubeMX 的 **ADC 参数页**，不在时钟树；
        ② 器件库里超限档位带 Action="DISABLE"，CubeMX 会禁用（和 F103 相反）；
        ③ F4 的 ADC 没有 F1 那样的 RSTCAL/CAL 校准位，这里不做校准。 */
static void f4_adc_setup(uint32_t adcpre)
{
  RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
  ADC->CCR = (ADC->CCR & ~ADC_CCR_ADCPRE) | adcpre | ADC_CCR_TSVREFE;
  ADC1->CR1 = 0;
  ADC1->CR2 = ADC_CR2_ADON;
  for (volatile int d = 0; d < 20000; d++) { }          /* ADC 上电稳定 */
  ADC1->SMPR1 = (ADC1->SMPR1 & ~(7u << 24)) | (7u << 24); /* ch17 采样 480 周期 */
  ADC1->SQR1 = 0;
  ADC1->SQR3 = 17;                                       /* 通道 17 = VREFINT */
}

static void f4_adc_sample(uint32_t *mean, uint32_t *mn, uint32_t *mx)
{
  uint32_t sum = 0, lo = 0xFFFFu, hi = 0, i, v;
  ADC1->CR2 |= ADC_CR2_SWSTART;                          /* 丢掉第一次 */
  while ((ADC1->SR & ADC_SR_EOC) == 0) { }
  (void)ADC1->DR;
  for (i = 0; i < 48u; i++) {
    ADC1->CR2 |= ADC_CR2_SWSTART;
    while ((ADC1->SR & ADC_SR_EOC) == 0) { }
    v = ADC1->DR;
    sum += v;
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  *mean = sum / 48u; *mn = lo; *mx = hi;
}

static void test_t4_adc_clock(void)
{
  uint32_t m1, n1, x1, m2, n2, x2;

  /* (a) /4 -> 84/4 = 21MHz，合规 */
  f4_adc_setup(ADC_CCR_ADCPRE_0);
  f4_adc_sample(&m1, &n1, &x1);
  ADC1->CR2 &= ~ADC_CR2_ADON;
  for (volatile int d = 0; d < 5000; d++) { }

  /* (b) /2 -> 84/2 = 42MHz，超 36MHz 上限 */
  f4_adc_setup(0);
  f4_adc_sample(&m2, &n2, &x2);
  ADC1->CR2 &= ~ADC_CR2_ADON;

  put("[T4] ADC 预分频实测（PCLK2=84MHz，上限 36MHz）\r\n");
  put("  ADC时钟=/4 -> 21MHz(合规) mean=%lu min=%lu max=%lu 峰峰=%lu\r\n",
      (unsigned long)m1, (unsigned long)n1, (unsigned long)x1, (unsigned long)(x1 - n1));
  put("  ADC时钟=/2 -> 42MHz(超限) mean=%lu min=%lu max=%lu 峰峰=%lu\r\n",
      (unsigned long)m2, (unsigned long)n2, (unsigned long)x2, (unsigned long)(x2 - n2));
  put("  均值差 = %ld\r\n", (long)m1 - (long)m2);
  put("  注：F4 的 ADC 预分频在 CubeMX 的【ADC 参数页】，不在时钟树；\r\n");
  put("      器件库里超限档位带 Action=DISABLE，CubeMX 会禁用（和 F103 相反）。\r\n");
}

/* ---- T5：HSE 假设说明 ---- */
static void test_t5_hse(void)
{
  uint32_t cr = RCC->CR;
  put("[T5] HSE 与晶振假设\r\n");
  put("  HSE 就绪(HSERDY) = %s\r\n", (cr & RCC_CR_HSERDY) ? "是" : "否");
  put("  本固件按 **HSE = 8MHz** 编译：PLLM=8 -> VCO 输入 1MHz（规格 1~2MHz）\r\n");
  put("  若这块板其实是 25MHz 晶振：VCO 输入 = 25/8 = 3.125MHz，超出规格，PLL 锁不上\r\n");
  put("  -> 芯片根本不会跑到这里。所以能看到本报告，本身就证明晶振是 8MHz。\r\n");
}

static void build_report(void)
{
  g_pos = 0;
  put("\r\n===== STM32F407ZGT6 配置自检报告 =====\r\n");
  put("固件编译: %s %s\r\n", __DATE__, __TIME__);
  test_t1_rcc();
  test_t2_hal_clocks();
  test_t3_timer_double();
  test_t4_adc_clock();
  test_t5_hse();
  put("===== 报告结束，固件停在 while(1)，RAM 保持 =====\r\n");
  g_report_ready = 0x5A5A1234u;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  led_init();
  build_report();
  /* 串口接着就发一份（没接 USB-TTL 也不影响：结果在 RAM 里，可用 ST-Link 读） */
  HAL_UART_Transmit(&huart1, (uint8_t *)&g_report[0], (uint16_t)g_pos, 500);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    /* 心跳：PC13 LED 闪烁 + 每 2 秒重发一次报告 */
    led_toggle();
    g_heartbeat++;
    HAL_Delay(500);
    if (g_heartbeat >= 4u) {
      g_heartbeat = 0;
      HAL_UART_Transmit(&huart1, (uint8_t *)&g_report[0], (uint16_t)g_pos, 500);
    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 7;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
