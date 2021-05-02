from abc import *

class AbstractCountry(metaclass=ABCMeta):
    """name = '국가명'
    population = '인구'
    capital = '수도'"""

    def show(self):
        print('국가 클래스의 메소드입니다.')

    @abstractmethod
    def show_capital(self):
        print('국가의 수도는?')

class Korea(AbstractCountry):

    def __init__(self, name,population, capital):
        self.name = name
        self.population = population
        self.capital = capital

    def show_name(self):
        print('국가 이름은 : ', self.name)

a = AbstractCountry()
a.show()
b = Korea("대한민국", 50000000, '서울')
b.show_name()
