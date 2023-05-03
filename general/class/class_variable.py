# 클래스 변수 활용
# date	2023-05-03
# author	hbesthee@naver.com



class Contact:
	allContacts: list["Contact"] = [] # 클래스 변수 ; 모든 인스턴스에서 공유함
    
	def __init__(self, name: str, email: str) -> None:
		self._name = name
		self._email = email
		Contact.allContacts.append(self)

	def __repr__(self) -> str:
		return ( f'{self.__class__.__name__}({self._name}, {self._email})')


c1 = Contact('name1', 'email1')
c2 = Contact('name2', 'email2')

print(Contact.allContacts)

Contact.allContacts.append('4')

print(Contact.allContacts)

"""
[Contact(name1, email1), Contact(name2, email2)]
[Contact(name1, email1), Contact(name2, email2), '4']
"""