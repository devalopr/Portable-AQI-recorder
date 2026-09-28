#include "battery_pwm.h"
#include "ch32v00x.h"
/* PC1/package pin11 drives Q5 gate. No GPIO alternate-function remap needed.
 * TIM2 owns the 10ms frame and compare interrupt. Do not share TIM2.
 * Each frame snapshots the pending value; updates never split a pulse.
 */
static volatile uint16_t pending; /* 0 means unavailable; otherwise HIGH time */
static volatile uint8_t submitted;
static uint16_t frame_high;
static unsigned age_frames;

bool battery_pwm_init(uint32_t timer_clock_hz) {
    if (timer_clock_hz < 1000000u || timer_clock_hz % 1000000u) return false;
    if (timer_clock_hz / 1000000u > 65536u) return false;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    GPIO_ResetBits(GPIOC, GPIO_Pin_1); /* Q5 off: output released until valid */
    GPIO_InitTypeDef gpio = {0};
    gpio.GPIO_Pin = GPIO_Pin_1;
    gpio.GPIO_Mode = GPIO_Mode_Out_PP;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOC, &gpio);
    TIM_DeInit(TIM2);
    TIM_TimeBaseInitTypeDef base = {0};
    base.TIM_Period = 9999;
    base.TIM_Prescaler = timer_clock_hz / 1000000u - 1u;
    base.TIM_ClockDivision = TIM_CKD_DIV1;
    base.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM2, &base);
    TIM_OCInitTypeDef oc = {0};
    oc.TIM_OCMode = TIM_OCMode_Timing;
    oc.TIM_Pulse = 5000;
    TIM_OC1Init(TIM2, &oc);
    pending = 0; submitted = 0; frame_high = 0; age_frames = 200;
    TIM_ClearITPendingBit(TIM2, TIM_IT_Update | TIM_IT_CC1);
    TIM_ITConfig(TIM2, TIM_IT_Update | TIM_IT_CC1, ENABLE);
    NVIC_EnableIRQ(TIM2_IRQn);
    TIM_Cmd(TIM2, ENABLE);
    return true;
}
void battery_pwm_submit(unsigned percent, bool valid) {
    pending = valid ? battery_pwm_high_us(percent) : 0;
    submitted = 1;
}
void battery_pwm_tim2_irq(void) {
    if (TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET) {
        TIM_ClearITPendingBit(TIM2, TIM_IT_Update | TIM_IT_CC1);
        if (submitted) { submitted = 0; age_frames = 0; }
        else if (age_frames < 200) ++age_frames;
        frame_high = age_frames < 200 ? pending : 0;
        GPIO_ResetBits(GPIOC, GPIO_Pin_1); /* rising wire edge */
        if (frame_high) TIM_SetCompare1(TIM2, frame_high);
    }
    if (TIM_GetITStatus(TIM2, TIM_IT_CC1) != RESET) {
        TIM_ClearITPendingBit(TIM2, TIM_IT_CC1);
        if (frame_high) GPIO_SetBits(GPIOC, GPIO_Pin_1); /* falling wire edge */
    }
}
