/**
 * truetouch.cpp - a simple protocol written on top of a BLE UART for controlling pins on
 *                 the TrueTouch device.
 *
 * Copyright (c) 2021 TrueTouch
 * Distributed under the MIT license (see LICENSE or https://opensource.org/licenses/MIT)
 */

#include "truetouch.hpp"

#include "util.hpp"

#include <cstring>

/* Enable debugging log statements */
#define DEBUG

#ifdef DEBUG
#   define DBG_LOG(...) Serial.print(__VA_ARGS__)
#   define DBG_LOG_LINE(...) Serial.println(__VA_ARGS__)
#else
#   define DBG_LOG(...) 
#   define DBG_LOG_LINE(...)
#endif // DEBUG

TrueTouch::TrueTouch(BLEUart *uart, const int *solenoid_pins, const int *erm_pins) : _uart{uart},
                                                                                     _fingers_to_pulse{0},
                                                                                     _pulse_dur_ms{0},
                                                                                     _pulse_start_ms{0} {
    /* Store all the used pins */
    std::memcpy(_solenoid_pins, solenoid_pins, sizeof(_solenoid_pins));
    std::memcpy(_erm_pins, erm_pins, sizeof(_erm_pins));
}

TrueTouch::~TrueTouch() {

}

void TrueTouch::init() {
    /* Configure all used pins as outputs and set low */
    for (std::size_t i = 0; i < SOLENOID_COUNT; ++i) {
        pinMode(_solenoid_pins[i], OUTPUT);
        digitalWrite(_solenoid_pins[i], LOW);
    }

    for (std::size_t i = 0; i < ERM_COUNT; ++i) {
        pinMode(_erm_pins[i], OUTPUT);
        digitalWrite(_erm_pins[i], LOW);
    }
}

void TrueTouch::service() {
    /* Always service pin pulsing if it's ongoing */
    service_gpio_pulse();

    /* Do nothing if there's no data */
    if (_uart->available() <= 0) {
        return;
    }

    /* First byte is command, peek that */
    const Command command = static_cast<Command>(_uart->peek());

    /* Perform command-specific processing (break if all data bytes aren't received yet) */
    switch (command) {
        case Command::SOLENOID_WRITE:
            handle_solenoid_write();
            break;

        case Command::SOLENOID_PULSE:
            handle_solenoid_pulse();
            break;

        case Command::ERM_SET:
            handle_erm_set();
            break;
    }
}

void TrueTouch::handle_solenoid_write() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(SolenoidWrite)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<SolenoidWrite>();

    /* Fix endianness for multi-byte pieces of data */
    params.finger_bitset = util::byte_swap32(params.finger_bitset);

    DBG_LOG("GPIO_WRITE: finger bitset=");
    DBG_LOG(params.finger_bitset, HEX);
    DBG_LOG(" value=");
    DBG_LOG_LINE(params.output == GpioOutput::OUT_HIGH ? "high" : "low");

    /* Go through each bit and set appropriate pins */
    for (std::size_t pin_idx = 0; pin_idx < SOLENOID_COUNT; ++pin_idx) {
        if (util::is_set(params.finger_bitset, pin_idx)) {
            digitalWrite(_solenoid_pins[pin_idx], params.output == GpioOutput::OUT_HIGH);
        }
    }
}

void TrueTouch::handle_solenoid_pulse() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(SolenoidPulse)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<SolenoidPulse>();

    /* Fix endianness for multi-byte pieces of data */
    params.finger_bitset = util::byte_swap32(params.finger_bitset);
    params.duration_ms = util::byte_swap32(params.duration_ms);

    DBG_LOG("GPIO_PULSE: finger bitset=");
    DBG_LOG(params.finger_bitset, HEX);
    DBG_LOG(" duration=");
    DBG_LOG_LINE(params.duration_ms);

    /* Store data for use by pin pulsing routine */
    _fingers_to_pulse = params.finger_bitset;
    _pulse_dur_ms = params.duration_ms;

    if (!_fingers_to_pulse) { // nothing to do
        return;
    }

    /* Start the first pulse (set the pin high and record the start time) */
    int pin_idx = util::get_highest_bit(_fingers_to_pulse);
    if (pin_idx < 0 || pin_idx >= ERM_COUNT) {
        Serial.println("!!! Invalid values in pulse");
        _fingers_to_pulse = 0;
        return;
    }

    int pin = _erm_pins[pin_idx];

    DBG_LOG("Pulsing pin ");
    DBG_LOG(pin);
    DBG_LOG(" for ");
    DBG_LOG_LINE(_pulse_dur_ms);

    digitalWrite(pin, HIGH);
    _pulse_start_ms = millis();
}

void TrueTouch::handle_erm_set() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(ErmSet)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<ErmSet>();

    /* Fix endianness for multi-byte pieces of data */
    params.finger_bitset = util::byte_swap32(params.finger_bitset);

    DBG_LOG("ERM_SET: ");
    DBG_LOG(params.finger_bitset, HEX);
    DBG_LOG(" ");
    DBG_LOG_LINE(static_cast<int>(params.intensity));

    /* Go through each bit and set PWM on appropriate pins */
    for (std::size_t pin_idx = 0; pin_idx < ERM_COUNT; ++pin_idx) {
        if (util::is_set(params.finger_bitset, pin_idx)) {
            auto pin = _erm_pins[pin_idx];
            analogWrite(pin, params.intensity);
        }
    }
}

void TrueTouch::service_gpio_pulse() {
    /* Do nothing if no pulsing is ongoing */
    if (!_fingers_to_pulse) {
        return;
    }

    /* Do nothing if pulse time hasn't elapsed yet */
    if (millis() - _pulse_start_ms < _pulse_dur_ms) {
        return;
    }

    /* Set the pin low */
    int pin_idx = util::get_highest_bit(_fingers_to_pulse);
    if (pin_idx < 0 || pin_idx >= ERM_COUNT) {
        Serial.println("!!! Invalid values in pulse");
        _fingers_to_pulse = 0;
        return;
    }

    auto pin = _erm_pins[pin_idx];

    digitalWrite(pin, LOW);
    util::clear_highest_bit(_fingers_to_pulse);

    /* If there's nothing left to do, stop */
    if (!_fingers_to_pulse) {
        DBG_LOG("Done with pulsing");
        _pulse_start_ms = 0;
        return;
    }

    /* Start next pulse */
    pin_idx = util::get_highest_bit(_fingers_to_pulse);
    if (pin_idx < 0 || pin_idx >= ERM_COUNT) {
        Serial.println("!!! Invalid values in pulse");
        _fingers_to_pulse = 0;
        return;
    }

    pin = _erm_pins[pin_idx];

    DBG_LOG("Pulsing pin ");
    DBG_LOG(pin);
    DBG_LOG(" for ");
    DBG_LOG_LINE(_pulse_dur_ms);

    digitalWrite(pin, HIGH);
    _pulse_start_ms = millis();
}
