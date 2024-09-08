_ORDINAL_SUFFIX_LIST = ['th', 'st', 'nd', 'rd', 'th']


def make_ordinal(n: int):
    """
    Convert an integer into its ordinal representation.

    make_ordinal(0)   => '0th'
    make_ordinal(3)   => '3rd'
    make_ordinal(122) => '122nd'
    make_ordinal(213) => '213th'

    :param n: the integer to convert.
    :return: the ordinal representation of ``n``.
    """
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = _ORDINAL_SUFFIX_LIST[min(n % 10, 4)]

    return str(n) + suffix
