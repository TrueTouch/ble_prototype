/**
 * truetouch.hpp - a simple protocol written on top of a BLE UART for controlling pins on
 *                 the TrueTouch device.
 *
 * Copyright (c) 2021 TrueTouch
 * Distributed under the MIT license (see LICENSE or https://opensource.org/licenses/MIT)
 */

#pragma once

#include <climits>
#include <cstdint>

#include <bluefruit.h>

class TrueTouch {
public:
////////////////////////////////////////////////////////////////////////////////////////////////////
// Public Types
////////////////////////////////////////////////////////////////////////////////////////////////////
    /** The type constituting a bitset. */
    using Bitset = std::uint32_t;

    /** Types of commands. */
    enum class Command : std::uint8_t {
        SOLENOID_WRITE = 0x01,  /*!< Digital write to the given fingers' solenoids. */
        SOLENOID_PULSE = 0x02,  /*!< Pulse given fingers' solenoids for so many ms. */
        ERM_SET = 0x03,         /*!< Set PWM on given fingers' ERM motors. */
    };

    /** Fingers the TrueTouch device is connected to. */
    enum class Finger : std::uint8_t {
        THUMB = 0,
        INDEX = 1,
        MIDDLE = 2,
        RING = 3,
        PINKY = 4,
        PALM = 5,
    };

    /** Solenoid write options. */
    enum class GpioOutput : std::uint8_t {
        OUT_LOW = 0,
        OUT_HIGH = 1
    };

    /** Solenoid write parameters. */
    struct __attribute__((packed)) SolenoidWrite {
        Command command;
        Bitset finger_bitset; // n-th bit set configures n-th finger in the Finger enum
        GpioOutput output;
    };

    /** Solenoid pulse parameters. */
    struct __attribute__((packed)) SolenoidPulse {
        Command command;
        Bitset finger_bitset; // n-th bit set configures n-th finger in the Finger enum
        std::uint32_t duration_ms; // duration of pulse per gpio in ms
    };

    /** ERM set parameters. */
    struct __attribute__((packed)) ErmSet {
        Command command;
        Bitset finger_bitset; // n-th bit set configures n-th finger in the Finger enum
        std::uint8_t intensity; // 0-255
    };

////////////////////////////////////////////////////////////////////////////////////////////////////
// Public Constants
////////////////////////////////////////////////////////////////////////////////////////////////////
    /** Max number of bits in a bitset. */
    static constexpr std::size_t BITSET_BIT_COUNT{sizeof(Bitset) * CHAR_BIT};

    /** Number of solenoids in the system. */
    static constexpr int SOLENOID_COUNT{5};

    /** Number of ERM motors in the system. */
    static constexpr int ERM_COUNT{6};

////////////////////////////////////////////////////////////////////////////////////////////////////
// Public Functions
////////////////////////////////////////////////////////////////////////////////////////////////////

    /**
     * Initializes hardware used for TrueTouch. BLE should be initialized before this is called.
     *
     * @param[in] uart          BLEUart instance to be used by the TrueTouch device
     * @param[in] solenoid_pins pointer to array containing 5 pins corresponding to where the solenoids are connected
     * @param[in] erm_pins      pointer to array containing 6 pins corresponding to where the ERM motors are connected
     */
    TrueTouch(BLEUart *uart, const int *solenoid_pins, const int *erm_pins);

    virtual ~TrueTouch();

    /** Services any pending data read by this device. */
    void service();

private:
////////////////////////////////////////////////////////////////////////////////////////////////////
// Internal Data
////////////////////////////////////////////////////////////////////////////////////////////////////

    BLEUart *_uart;                 /*!< Pointer to BLE UART instance */
    std::uint32_t _fingers_to_pulse;   /*!< Bit mask of pins to pulse */
    std::uint32_t _pulse_dur_ms;    /*!< Current pulse activity delay in ms */
    std::uint32_t _pulse_start_ms;  /*!< Time the current pulse started in ms */

    int _solenoid_pins[SOLENOID_COUNT];
    int _erm_pins[ERM_COUNT];

////////////////////////////////////////////////////////////////////////////////////////////////////
// Internal Functions
////////////////////////////////////////////////////////////////////////////////////////////////////

    /** Functions to handle commands */
    void handle_solenoid_write();

    void handle_solenoid_pulse();

    void handle_erm_set();

    /* Service any ongoing pulse command */
    void service_gpio_pulse();

    /* Copy bytes from the BLE UART byte buffer into the type T */
    template<typename T>
    T parse_bytes() {
        if (static_cast<unsigned>(_uart->available()) < sizeof(T)) {
            Serial.println("Trying to parse without enough bytes!");
            return T{};
        };

        /* Read into a byte buffer */
        std::uint8_t read_buffer[sizeof(T)] = {};
        _uart->read(read_buffer, sizeof(read_buffer));

        /* Transform that byte buffer into the appropriate struct */
        T ret = {};
        memcpy(&ret, read_buffer, sizeof(ret));

        return ret;
    }
};
