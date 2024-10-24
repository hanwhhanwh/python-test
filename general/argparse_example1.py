# 간단한 명령줄 인자 분석 예제
# make hbesthee@naver.com
# date 2024-10-24

import argparse
import sys

def parse_arguments():
    """ 명령줄 인자를 파싱하는 함수 """
    # ArgumentParser 인스턴스 생성
    parser = argparse.ArgumentParser(
        description = '파일 처리 프로그램 예제',
        formatter_class = argparse.RawDescriptionHelpFormatter
    )

    # 필수 인자
    parser.add_argument('input_file', 
                       help='처리할 입력 파일 경로')

    # 선택적 인자 (옵션)
    parser.add_argument('-o', '--output',
                       help='출력 파일 경로 (기본값: output.txt)',
                       default='output.txt')

    # 불리언 플래그
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='상세 출력 모드 활성화')

    # 숫자 인자
    parser.add_argument('-n', '--number',
                       type=int,
                       default=1,
                       help='처리할 횟수 (기본값: 1)')

    # 선택 인자
    parser.add_argument('-m', '--mode',
                       choices=['read', 'write', 'append'],
                       default='read',
                       help='파일 처리 모드 선택 (기본값: read)')

    # 여러 값을 받는 인자
    parser.add_argument('-f', '--filters',
                       nargs='+',
                       help='적용할 필터 목록')

    try:
        args = parser.parse_args()
        return args
    except Exception as e:
        parser.print_help()
        sys.exit(1)

def main():
    # 인자 파싱
    args = parse_arguments()

    # 파싱된 인자 사용 예시
    if args.verbose:
        print(f"입력 파일: {args.input_file}")
        print(f"출력 파일: {args.output}")
        print(f"처리 모드: {args.mode}")
        print(f"처리 횟수: {args.number}")
        print(f"필터 목록: {args.filters}")

    # 여기에 실제 파일 처리 로직 구현
    try:
        with open(args.input_file, 'r') as f:
            content = f.read()
            # 처리 로직...
            
        if args.verbose:
            print("파일 처리 완료")
            
    except FileNotFoundError:
        print(f"오류: 입력 파일 '{args.input_file}'을 찾을 수 없습니다.")
        sys.exit(1)


if (__name__ == "__main__"):
    main()