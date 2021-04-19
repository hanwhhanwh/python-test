class Language:
    default_language = "English"

    def __init__(self):
        self.show = '나의 언어는 ' + self.default_language

    @classmethod
    def class_my_language(cls):
        return cls()

    @staticmethod
    def static_my_language():
        return Language()

    def print_language(self):
        print(self.show)


class KoreanLanguage(Language):
    default_language = "한국어"


a = KoreanLanguage.static_my_language()
b = KoreanLanguage.class_my_language()

a.print_language()
b.print_language()

""" 실행결과 >>>
나의 언어는 English
나의 언어는 한국어
"""