/* bleuart_pin_ctrl.h
 * A simple pin control class that utilizes BLE UART to control pins on this device.
 * Functionality:
 *      - Control GPIO (set, clear, toggle)
 *      - Control PWM (0-255)
 *      - Get status
 */

#pragma once

#include <cstdint>

#include <bluefruit.h>

namespace BleUartPinCtrl {

/**
 * Messages shall be 1 command byte followed by data byte(s). 
 * Data bytes will be organized based on structs below.
 */

/** Types of commands */
enum class Command : std::uint8_t {
    /** GPIO commands */
    GPIO_CONFIGURE = 0x01,  /*!< Central -> this: configure GPIO pin(s) */
    GPIO_SET = 0x02,        /*!< Central -> this: set GPIO pin(s) */
    GPIO_CLEAR = 0x03,      /*!< Central -> this: clear GPIO pin(s) */
    // TODO CMK (11/14/20): implement or delete
    GPIO_QUERY = 0x04,      /*!< this -> Central: get GPIO status info */
    
    /** PWM commands */
    PWM_SET = 0x05,         /*!< Central -> this: set PWM output on pin(s) */

    /** Query commands */
    // TODO CMK (11/14/20): implement or delete
    QUERY_STATE = 0x06,     /*!< this -> Central: get info about device state */
};

/** GPIO direction options */
enum class GpioDirection : std::uint8_t {
    DIR_INPUT = 0,
    DIR_OUTPUT
};

/** GPIO configure parameter */
struct __attribute__((packed)) GpioConfigure {
    Command command;
    std::uint32_t gpio_port; // unused on Arduino
    std::uint32_t gpio_bitset; // if the n-th bit is 1, GPIO n is being configured
    std::uint8_t gpio_direction;
};

/** GPIO set parameters */
struct __attribute__((packed)) GpioSet {
    Command command;
    std::uint32_t gpio_port; // unused on Arduino
    std::uint32_t gpio_bitset; // if the n-th bit is 1, GPIO n is being configured
};

/** GPIO clear parameters */
struct __attribute__((packed)) GpioClear {
    Command command;
    std::uint32_t gpio_port; // unused on Arduino
    std::uint32_t gpio_bitset; // if the n-th bit is 1, GPIO n is being configured
};

/** GPIO toggle parameters */
struct __attribute__((packed)) GpioToggle {
    Command command;
    std::uint32_t gpio_port; // unused on Arduino
    std::uint32_t gpio_bitset; // if the n-th bit is 1, GPIO n is being configured
};

/** GPIO query */
struct __attribute__((packed)) GpioQuery {
    // TODO
};

/** PWM set parameters */
struct __attribute__((packed)) PwmSet {
    Command command;
    std::uint32_t gpio_port; // unused on Arduino
    std::uint32_t gpio_bitset; // if the n-th bit is 1, GPIO n is being configured
    std::uint8_t intensity; // 0-255
};

/** Query state parameters */
struct __attribute__((packed)) QueryState {
    // TODO
};

/**
 * Services any interrupts/callbacks that have occurred.
 */ 
void service(BLEUart *uart);

}
