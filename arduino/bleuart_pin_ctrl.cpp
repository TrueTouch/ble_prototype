/* bleuart_pin_ctrl.cpp
 * A simple pin control class that utilizes BLE UART to control pins on this device.
 * Functionality:
 *      - Control GPIO (set, clear, toggle)
 *      - Control PWM (0-255)
 *      - Get status
 */

#include "bleuart_pin_ctrl.h"

using namespace ble_uart_pin_ctrl;

/* Enable debugging log statements */
#define DEBUG

#ifdef DEBUG
#   define DBG_LOG(...) Serial.print(__VA_ARGS__)
#   define DBG_LOG_LINE(...) Serial.println(__VA_ARGS__)
#else
#   define DBG_LOG(...) 
#   define DBG_LOG_LINE(...)
#endif // DEBUG

PinCtrl::PinCtrl(BLEUart *uart) : _uart{uart},
                                  _pins_to_pulse{0},
                                  _pulse_dur_ms{0},
                                  _pulse_start_ms{0} {}

void PinCtrl::service() {
    /* Always service pin pulsing if it's ongoing */
    service_gpio_pulse();
  
    /* Do nothing if there's no data */
    if (_uart->available() <= 0) {
        return;
    }

    /* First byte is command, peek that */
    const Command command = static_cast<Command>(_uart->peek());
    
    /* Perform command-specific processing (break if all data bytes aren't recieved yet) */
    switch (command) {
        case Command::GPIO_CONFIGURE: {
            handle_gpio_configure();
        } break;

        case Command::GPIO_WRITE: {
            handle_gpio_write();
        } break;

        case Command::GPIO_PULSE: {
            handle_gpio_pulse();
        } break;

        case Command::GPIO_QUERY: {
            handle_gpio_query();
            // TODO CMK (11/14/20): implement
        } break;

        case Command::PWM_SET: {
            handle_pwm_set();
        } break;

        case Command::QUERY_STATE: {
            handle_query_state();
            // TODO CMK (11/14/20): implement
        } break;
    }
}

void PinCtrl::handle_gpio_configure() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(GpioConfigure)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<GpioConfigure>();
    // fix endianness for multi-byte pieces of data
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);
    
    DBG_LOG("GPIO_CONFIGURE: ");
    DBG_LOG(params.gpio_bitset, HEX);
    DBG_LOG(" ");
    DBG_LOG_LINE(static_cast<int>(params.gpio_direction));

    /* Go through each bit and configure appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            if (params.gpio_direction == GpioDirection::DIR_INPUT) {
                pinMode(pin, INPUT);
            } else {
                pinMode(pin, OUTPUT);
                digitalWrite(pin, LOW);
            }
        }
    }
}

void PinCtrl::handle_gpio_write() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(GpioWrite)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<GpioWrite>();
    // fix endianness for multi-byte pieces of data
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);
    
    DBG_LOG("GPIO_WRITE: ");
    DBG_LOG_LINE(params.gpio_bitset, HEX);

    /* Go through each bit and set appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            digitalWrite(pin, params.output == GpioOutput::OUT_HIGH); // true if high, false if low
        }
    }
}

void PinCtrl::handle_gpio_pulse() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(GpioPulse)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<GpioPulse>();
    // fix endianness for multi-byte pieces of data
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);
    params.duration_ms = byte_swap32(params.duration_ms);
    
    DBG_LOG("GPIO_PULSE: ");
    DBG_LOG(params.gpio_bitset, HEX);
    DBG_LOG(" ");
    DBG_LOG_LINE(params.duration_ms);

    /* Store data for use by pin pulsing routine */
    _pins_to_pulse = params.gpio_bitset;
    _pulse_dur_ms = params.duration_ms;

    if (!_pins_to_pulse) { // nothing to do
        return;
    }
    
    /* Start the first pulse (set the pin high and record the start time) */
    int pin = PinCtrl::get_highest_bit(_pins_to_pulse);
    if (pin < 0) { // note - should never happen
        Serial.println("!!! Pulse starting with no pin set");
        return; 
    }

    DBG_LOG("Pulsing pin ");
    DBG_LOG(pin);
    DBG_LOG(" for ");
    DBG_LOG_LINE(_pulse_dur_ms);

    digitalWrite(pin, HIGH);
    _pulse_start_ms = millis();
}

void PinCtrl::handle_gpio_query() {
    Serial.println("GPIO QUERY: TODO");
}

void PinCtrl::handle_pwm_set() {
    const unsigned int number_of_bytes = static_cast<unsigned int>(_uart->available());

    if (number_of_bytes < sizeof(PwmSet)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<PwmSet>();
    // fix endianness for multi-byte pieces of data
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);

    DBG_LOG("PWM_SET: ");
    DBG_LOG(params.gpio_bitset, HEX);
    DBG_LOG(" ");
    DBG_LOG_LINE(static_cast<int>(params.intensity));

    /* Go through each bit and set PWM on appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            analogWrite(pin, params.intensity);
        }
    }
}

void PinCtrl::handle_query_state() {
    Serial.println("QUERY STATE: TODO");
}

void PinCtrl::service_gpio_pulse() {
    /* Do nothing if no pulsing is ongoing */
    if (!_pins_to_pulse) {
        return;
    }

    /* Do nothing if pulse time hasn't elapsed yet */
    if (millis() - _pulse_start_ms < _pulse_dur_ms) {
        return;
    }

    /* Set the pin low */
    int pin = PinCtrl::get_highest_bit(_pins_to_pulse);
    if (pin < 0) { // note - should never happen
        Serial.println("!!! Pulse active with no pin set");
        return;
    }
    
    digitalWrite(pin, LOW);
    PinCtrl::clear_highest_bit(_pins_to_pulse);

    /* If there's nothing left to do, stop */
    if (!_pins_to_pulse) {
        DBG_LOG("Done with pulsing");
        _pulse_start_ms = 0;
        return;
    }

    /* Start next pulse */
    pin = PinCtrl::get_highest_bit(_pins_to_pulse);
    if (pin < 0) { // note - should never happen
        Serial.println("!!! Next pulse starting with no pin set");
        return;
    }

    DBG_LOG("Pulsing pin ");
    DBG_LOG(pin);
    DBG_LOG(" for ");
    DBG_LOG_LINE(_pulse_dur_ms);

    digitalWrite(pin, HIGH);
    _pulse_start_ms = millis();
}

/** Helper to parse data from the UART buffer */
template <typename T> 
T PinCtrl::parse_bytes() {
    /* Read into a byte buffer */
    std::uint8_t read_buffer[sizeof(T)] = {};
    _uart->read(read_buffer, sizeof(read_buffer));
    
    /* Transform that byte buffer into the appropriate struct */
    T parameters = {};
    memcpy(&parameters, read_buffer, sizeof(parameters));
    
    return parameters;
}
