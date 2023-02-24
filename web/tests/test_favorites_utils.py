# -*- coding: utf-8 -*-
import pytest

from django.conf import settings

from web.favorites_utils import decode_favorites, encode_favorites, toggle_favorite


TEST_OK_SIZES = [(3), (settings.MAX_FAVORITES)]


@pytest.mark.parametrize("size", TEST_OK_SIZES)
def test_ok_encode_decode(size):
    favorites = []
    for id in range(size):
        favorites.append(id)

    encoded = encode_favorites(favorites)
    decoded = decode_favorites(encoded)

    assert len(favorites) == len(decoded)

    for i in range(size):
        assert favorites.pop(0) == decoded.pop(0), "items at %d not same" % i


def test_nok_toggle_decode():
    buffer = "X" * (settings.MAX_FAVORITES * 8 + 1)
    with pytest.raises(ValueError) as e_info:
        decoded = decode_favorites(buffer)


def test_nok_toggle_favorite():
    favorites = []
    for id in range(settings.MAX_FAVORITES):
        favorites.append(id)
    result = toggle_favorite(favorites, settings.MAX_FAVORITES + 1)
    assert result == "error"
