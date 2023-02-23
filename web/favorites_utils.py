from django.conf import settings


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
