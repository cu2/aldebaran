def bytes_to_word(high, low):
    return 256 * high + low


def word_to_bytes(word):
    return (
        word / 256,
        word % 256,
    )


def byte_to_str(byte):
    return hex(byte)[2:].zfill(2).upper()


def word_to_str(word):
    return hex(word)[2:].zfill(4).upper()
