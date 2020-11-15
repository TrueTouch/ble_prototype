/* bleuart_pin_ctrl.cpp
 * A simple pin control class that utilizes BLE UART to control pins on this device.
 * Functionality:
 *      - Control GPIO (set, clear, toggle)
 *      - Control PWM (0-255)
 *      - Get status
 */

#include "bleuart_pin_ctrl.h"

using namespace BleUartPinCtrl;

static void handle_gpio_configure(BLEUart *uart);
static void handle_gpio_write(BLEUart *uart, bool high);
static void handle_gpio_query(BLEUart *uart);
static void handle_pwm_set(BLEUart *uart);
static void handle_query_state(BLEUart *uart);

/** Helper to perform endian fix on data */
static std::uint32_t byte_swap32(std::uint32_t input) {
    return __builtin_bswap32(input);
}

/** Helper to tell if the nth bit of a 32-bit number is set */
static bool is_set(std::uint32_t value, unsigned int n) {
    /* Assert no overflow */
    if (n > 31) {
        return false;
    }

    return value & (1UL << n);
}

/** Helper to parse data from the UART buffer */
template <typename T> 
T parse_bytes(BLEUart *uart) {
    /* Read into a byte buffer */
    std::uint8_t read_buffer[sizeof(T)] = {};
    uart->read(read_buffer, sizeof(read_buffer));
    
    /* Transform that byte buffer into the appropriate struct */
    // TODO CMK (11/14/20): anticipate endianness issues
    T parameters = {};
    memcpy(&parameters, read_buffer, sizeof(parameters));
    
    return parameters;
}

void BleUartPinCtrl::service(BLEUart *uart) {
    /* Is there data? */
    if (uart->available() <= 0) {
        return;
    }

    /* First byte is command, peek that */
    const Command command = static_cast<Command>(uart->peek());
    
    /* Perform command-specific processing (break if all data bytes aren't recieved yet) */
    switch (command) {
        case Command::GPIO_CONFIGURE: {
            handle_gpio_configure(uart);
        } break;

        case Command::GPIO_SET: {
            handle_gpio_write(uart, true);
        } break;

        case Command::GPIO_CLEAR: {
            handle_gpio_write(uart, false);
        } break;

        case Command::GPIO_QUERY: {
            handle_gpio_query(uart);
            // TODO CMK (11/14/20): implement
        } break;

        case Command::PWM_SET: {
            handle_pwm_set(uart);
        } break;

        case Command::QUERY_STATE: {
            handle_query_state(uart);
            // TODO CMK (11/14/20): implement
        } break;
    }
}

static void handle_gpio_configure(BLEUart *uart) {
    const unsigned int number_of_bytes = static_cast<unsigned int>(uart->available());

    if (number_of_bytes < sizeof(GpioConfigure)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<GpioConfigure>(uart);
    // fix endianness
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);

    // TODO CMK (11/14/20): TODO remove, debug
    Serial.print("GPIO_CONFIGURE: ");
    Serial.print(params.gpio_bitset, HEX);
    Serial.print(" ");
    Serial.println(static_cast<int>(params.gpio_direction));

    /* Go through each bit and configure appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            if (params.gpio_direction == 0) { // TODO CMK type stuff
                pinMode(pin, INPUT);
            } else {
                pinMode(pin, OUTPUT);
            }
        }
    }
}

// TODO CMK (11/14/20): if using one method for both, does it make sense to have them be separate commands?
static void handle_gpio_write(BLEUart *uart, bool high) {
    const unsigned int number_of_bytes = static_cast<unsigned int>(uart->available());

    if (number_of_bytes < sizeof(GpioSet)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<GpioSet>(uart);
    // fix endianness
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);
    
    // TODO CMK (11/14/20): TODO remove, debug
    Serial.print("GPIO_SET: ");
    Serial.println(params.gpio_bitset, HEX);

    /* Go through each bit and set appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            digitalWrite(pin, high);
        }
    }
}

static void handle_gpio_query(BLEUart *uart) {
    Serial.println("GPIO QUERY: TODO");
}

static void handle_pwm_set(BLEUart *uart) {
    const unsigned int number_of_bytes = static_cast<unsigned int>(uart->available());

    if (number_of_bytes < sizeof(PwmSet)) {
        return; // missing bytes
    }

    /* Parse byte buffer into the struct */
    auto params = parse_bytes<PwmSet>(uart);
    // fix endianness
    params.gpio_port = byte_swap32(params.gpio_port);
    params.gpio_bitset = byte_swap32(params.gpio_bitset);

    // TODO CMK (11/14/20): TODO remove, debug
    Serial.print("PWM_SET: ");
    Serial.print(params.gpio_bitset, HEX);
    Serial.print(" ");
    Serial.println(static_cast<int>(params.intensity));

    /* Go through each bit and set PWM on appropriate pins */
    for (int pin = 0; pin < 32; ++pin) {
        if (is_set(params.gpio_bitset, pin)) {
            analogWrite(pin, params.intensity);
        }
    }
}

static void handle_query_state(BLEUart *uart) {
    Serial.println("QUERY STATE: TODO");
}
