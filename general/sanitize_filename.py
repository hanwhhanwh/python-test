# -*- coding: utf-8 -*-
# 
# made : hbesthee@naver.com
# date : 2024-12-30


from os.path import splitext
from unicodedata import normalize

import re
from pathlib import Path

def sanitize_filename(filename: str, replace_char: str = "_") -> str:
    """ 문자열을 안전한 파일명으로 변환합니다.
    
    Args:
        filename (str): 변환할 원본 문자열
        replace_char (str): 허용되지 않는 문자를 대체할 문자 (기본값: '_')
        
    Returns:
        str: 안전한 파일명
    """
    filename = normalize('NFKC', filename) # 유니코드 정규화 (한글 자모 결합 등)
    
    # 윈도우즈에서 사용할 수 없는 예약어 리스트
    WINDOWS_RESERVED = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
                       'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    
    # 파일명에서 경로 부분 제거
    filename = Path(filename).name
    
    # 윈도우즈 예약어인 경우 접두어 추가
    base = filename.split('.')[0].upper()
    if base in WINDOWS_RESERVED:
        filename = f"_{filename}"
    
    # 허용되지 않는 문자 제거 또는 대체
    # < > : " / \ | ? * 및 제어 문자 제거
    filename = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', replace_char, filename)
    
    # 마침표로 시작하거나 끝나는 경우 제거
    filename = filename.strip('.')
    
    # 공백 문자를 지정된 대체 문자로 변환
    filename = re.sub(r'\s+', replace_char, filename)
    
    # 파일명이 비어있는 경우 기본값 지정
    if not filename:
        filename = "unnamed_file"
    
    # 최대 길이 제한 (윈도우즈 기준 255자)
    if len(filename) > 255:
        name, ext = splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename



if (__name__ == '__main__'):
    # 기본 사용
    safe_name = sanitize_filename("안녕! 세상?: file*name.txt")
    print(safe_name)  # "안녕_세상_file_name.txt"

    # 대체 문자 변경
    safe_name = sanitize_filename("hello:world.txt", replace_char="-")
    print(safe_name)  # "hello-world.txt"
