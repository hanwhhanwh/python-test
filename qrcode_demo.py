import qrcode 

# 첫번째 예제
img = qrcode.make("굿바이2020!! 내년에는 코로나 없는 세상이 다시 찾아왔으면 좋겠습니다.")
img.save("C:/temp/goodbye2020.png")
print(type(img))
print(img.size)


# 두번째 예제
img_url = qrcode.make("https://hbesthee.tistory.com/")
img_url.save("C:/temp/hbesthee.png")
print(img_url.size)

"""
실행결과
<class qrcode.image.pil.PilImage'>
(490, 490)
(370, 370)
"""