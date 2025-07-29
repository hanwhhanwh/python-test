# -*- coding: utf-8 -*-
# ForwardRef의 실제 대상 클래스 타입 구하기
# made : hbesthee@naver.com
# date : 2025-07-29

# Original Packages
from dataclasses import dataclass, fields, is_dataclass
from typing import get_origin, get_args, Optional, Union, ForwardRef, get_type_hints

import sys


def resolve_dataclass_type(annot, globalns=None, localns=None):
    """
    필드 타입(annotation)에서 실제 데이터 클래스 타입을 찾아 반환합니다.
    Optional[T], ForwardRef('T') 등도 처리합니다.
    """
    origin = get_origin(annot)
    # Optional[T] 또는 Union[T, NoneType]
    if origin is Union:
        for arg in get_args(annot):
            if arg is type(None):
                continue
            resolved = resolve_dataclass_type(arg, globalns, localns)
            if resolved:
                return resolved
    # ForwardRef 처리
    if isinstance(annot, ForwardRef):
        # ForwardRef('Node') → 실제 클래스 객체
        resolved = eval(annot.__forward_arg__, globalns or sys.modules['__main__'].__dict__, localns)
        if is_dataclass(resolved):
            return resolved
    # 일반 데이터 클래스
    if is_dataclass(annot):
        return annot
    return None


@dataclass
class NextNode:
	next_value: int


@dataclass
class Node:
	value: int
	NextNode: Optional['NextNode'] = None  # ForwardRef + Optional

# 필드 타입 해석
f = fields(Node)[1]
resolved = resolve_dataclass_type(f.type, globals())
print(resolved)


type_hints = get_type_hints(Node)
print(type_hints)
print(type_hints.get("NextNode"), type(type_hints.get("NextNode")))
print(get_args(type_hints.get("NextNode")))
print(get_args(type_hints.get("NextNode"))[0])
print(get_args(type_hints.get("NextNode"))[0](4))


"""Result:
<class '__main__.NextNode'>
{'value': <class 'int'>, 'NextNode': typing.Optional[__main__.NextNode]}
typing.Optional[__main__.NextNode] <class 'typing._UnionGenericAlias'>
(<class '__main__.NextNode'>, <class 'NoneType'>)
<class '__main__.NextNode'>
NextNode(next_value=4)
"""