import re

from .models import BannedWord


def contains_banned_words(input_text):
    banned_words = BannedWord.objects.values_list('word', flat=True)
    if not banned_words:
        return False

    pattern = r'\b(' + '|'.join(re.escape(word) for word in banned_words) + r')\b'
    regex = re.compile(pattern, re.IGNORECASE)

    # Search the input text for any matches
    return bool(regex.search(input_text))
