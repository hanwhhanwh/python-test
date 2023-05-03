# 클래스 변수 활용2
# date	2023-05-03
# author	hbesthee@naver.com

from __future__ import annotations

class ContactList(list["Contact"]):
	""" 검색 (search) 기능을 추가한 클래스 """
	def search(self, name) -> list["Contact"]:
		matching_list: list["Contact"] = []
		for contact in self:
			if (contact._name.find(name) >= 0):
				matching_list.append(contact)

		return matching_list


class Contact:
	allContacts = ContactList() # 클래스 변수 ; 모든 인스턴스에서 공유함
    
	def __init__(self, name: str, email: str) -> None:
		self._name = name
		self._email = email
		Contact.allContacts.append(self)

	def __repr__(self) -> str:
		return ( f'{self.__class__.__name__}({self._name}, {self._email})')


class Supplier(Contact):

	def order(self, order: "Order") -> Optional[str]:
		print(f'ordered...')


class Firend(Contact):

	def __init(self, name: str, email: str, phone: str) -> None:
		super().__init__(name, email)
		self._phone = phone


c1 = Contact('name1', 'email1')
c2 = Contact('name2', 'email2')
s = Supplier('Supplier', 'Supplier@email')
f = Firend('firend', 'firend@email')

print(Contact.allContacts)

s.order(1)

matching = Contact.allContacts.search('name')
print(matching)

"""
[Contact(name1, email1), Contact(name2, email2), Supplier(Supplier, Supplier@email), Firend(firend, firend@email)]
ordered...
[Contact(name1, email1), Contact(name2, email2)]
"""