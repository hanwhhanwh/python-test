# HTTP post method example
import requests

rest_api_url = 'https://postserver.com/api/v1.0/PostExample'

post_data = {
	'data_no':1
	, 'measure_date':'2020-12-10 14:49:38'
	, 'p1':55.76
	, 'p2':55.77
	, 'p3':55.78
	, 'n1':46.1
	, 'n2':46.2
	, 'n3':46.3
	, 's1':68.77
	, 's2':68.99
	, 's3':68.88
	, 'image_name':'201210_05-49-38.jpg'
}
res = requests.post(rest_api_url, data = post_data)

print(res)
