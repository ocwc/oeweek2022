import struct

from cryptography.fernet import Fernet

from django.conf import settings

# ref:
# 1) https://cryptography.io/en/latest/fernet/
# 2) https://stackoverflow.com/a/8461913


def create_favorites():
    return []


def toggle_favorite(favorites, event_id):
    """
    :param favorites:    list of favorites to work with
    :param event_id:     ID if event for which to toggle "favorited" status
    :return:             True if event is favorited, False is it is not favorited, "error" on error
    """
    if event_id in favorites:
        favorites.remove(event_id)
        return False

    # We're going to encode that list into URL. To avoid URL getting too big, lets have some limit.
    if len(favorites) >= settings.MAX_FAVORITES:
        return "error"

    favorites.append(event_id)
    return True


def encode_favorites(favorites):
    fmt = "<%dI" % len(favorites)
    packed = struct.pack(fmt, *favorites)

    f = Fernet(settings.FAVORITES_CRYPTO_KEY)
    encrypted = f.encrypt(packed)

    return encrypted.decode("UTF-8")


def decode_favorites(data):
    # enforce some worst case (8-bytes per ID) limit
    if len(data) > (settings.MAX_FAVORITES * 8):
        raise ValueError("too big: %d" % len(data))

    encrypted = data.encode("UTF-8")

    f = Fernet(settings.FAVORITES_CRYPTO_KEY)
    decrypted = f.decrypt(encrypted)

    fmt = "<%dI" % (len(decrypted) // 4)
    favorites = list(struct.unpack(fmt, decrypted))

    return favorites
