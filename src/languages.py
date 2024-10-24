from lingua import Language, LanguageDetectorBuilder

SUPPORTED_LANGUAGES = [Language.ENGLISH,
                       Language.SPANISH,
                       Language.FRENCH,
                       Language.GERMAN,
                       Language.DUTCH,
                       Language.ITALIAN,
                       Language.SWEDISH,
                       Language.JAPANESE,
                       Language.KOREAN,
                       Language.CHINESE]

LANGUAGE_MAP = {'eng': Language.ENGLISH,
                'spa': Language.SPANISH,
                'fre': Language.FRENCH,
                'ger': Language.GERMAN,
                'dut': Language.DUTCH,
                'ita': Language.ITALIAN,
                'swe': Language.SWEDISH,
                'jpn': Language.JAPANESE,
                'kor': Language.KOREAN,
                'chi': Language.CHINESE}


def detect_language(text):
    detector = LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES).build()
    language = detector.detect_language_of(text)
    return language


def matches_prediction(language: Language, predicted: str):
    return LANGUAGE_MAP[predicted] == language


class Languages:
    @classmethod
    def get_language_name(cls, lang_code):
        if len(str(lang_code)) == 3:
            lang_name = str(LANGUAGE_MAP[lang_code])
        else:
            lang_name = str(lang_code)
        return lang_name.split('.')[-1].lower()

    @classmethod
    def get_language_code(cls, language_name):
        reversed_dict = {value: key for key, value in LANGUAGE_MAP.items()}
        return reversed_dict[language_name]
