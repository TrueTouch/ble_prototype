/*
 * util.hpp - common utility functions
 *
 * Copyright (c) 2021 TrueTouch
 * Distributed under the MIT license (see LICENSE or https://opensource.org/licenses/MIT)
 */

#pragma once

#include <cstdint>


namespace util {

    /* Perform a 32-bit byte swap. */
    inline std::uint32_t byte_swap32(std::uint32_t input) {
        return __builtin_bswap32(input);
    }

    /* Check if bit n is set in the mask */
    inline bool is_set(std::uint32_t mask, unsigned int n) {
        if (n > 31) {
            return false;
        }
        return mask & (1UL << n);
    }

    /* Return the bit position of the highest set bit (-1 if no bits are set) */
    inline int get_highest_bit(std::uint32_t mask) {
        for (int i = 31; i >= 0; --i) {
            if (mask & (1UL << i)) {
                return i;
            }
        }
        return -1;
    }

    /* Clears the bit position of the highest set bit */
    inline void clear_highest_bit(std::uint32_t &mask) {
        int n = get_highest_bit(mask);
        if (n >= 0) {
            mask &= ~(1UL << n);
        }
    }

}  // namespace util
