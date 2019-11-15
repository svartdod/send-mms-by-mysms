from requests import Request, Session
import json
import pandas as pd 
import os
import base64
import mimetypes

sess = Session()

def get_header():

	
	headers = {
		
		'Accept-Encoding': 'gzip, deflate, br',
		'Connection': 'keep-alive',
		'Host': 'app.mysms.com',
		'Content-Type': 'application/json',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
	}

	return headers

def login(number, password, apiKey,sess):
	url = 'https://app.mysms.com/json/user/login'
	data = '{"msisdn":'+str(number)+',"password":"'+password+'","apiKey":"'+apiKey+'"}'
	response = sess.post(url,data=data,headers=get_header())
	return response

def send(number,message,authToken,apiKey,sess,attachmentKey):
	url = 'https://app.mysms.com/json/remote/sms/send'
	message += ' '+'http://mysms.com/'+attachmentKey
	data = '{"recipients":["+'+str(number)+'"],"message":"'+message+'","dateSendOn":null,"encoding":0,"smsConnectorId":0,"store":true,"authToken":"'+authToken+'","apiKey":"'+apiKey+'"}'
	response = sess.post(url,data=data,headers=get_header())
	return response


def log_d(text):
	print ('[+]--',text,'--')


def log_e(text):
	print ('[-]--',text,'--')

def create_attachment(apiKey,authToken):
	url = 'https://app.mysms.com/json/attachment/create'
	data = '{"authToken":"'+authToken+'","apiKey":"'+apiKey+'"}'
	response = sess.post(url,data=data,headers=get_header())
	return response

def add_attachment(apiKey,authToken,attachmentKey,fileName):
	url = 'https://app.mysms.com/json/attachment/part/add'
	size = os.path.getsize(fileName)
	data = '{"authToken":"'+authToken+'","apiKey":"'+apiKey+'","attachmentKey":"'+attachmentKey+'","fileName":"'+fileName+'","fileSize":"'+str(size)+'","preview":"true","typeId":"2"}'
	response = sess.post(url,data=data,headers=get_header())
	return response

def upload(apiKey,authToken,attachmentKey):
	url = 'https://app.mysms.com/json/attachment/part/uploaded'
	data = '{"authToken":"'+authToken+'","apiKey":"'+apiKey+'","attachmentKey":"'+attachmentKey+'","partId":"1"}'
	response = sess.post(url,data=data,headers=get_header())
	return response

def encode_multipart_formdata(fields,file,fileName):
	BOUNDARY = '------WebKitFormBoundaryZXdAs8CNYvogQ4xz'
	CRLF = '\r\n'
	L = []
	for (key, value) in fields.items():
		if key == 'bucketName':
			continue	 
		L.append('--' + BOUNDARY)
		L.append('Content-Disposition: form-data; name="%s"' % key)
		L.append('')
		L.append(value)
	L.append('--' + BOUNDARY)
	L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % ('file', 'blob'))
	L.append('Content-Type: %s' % (mimetypes.guess_type(fileName)[0] or 'application/octet-stream'))
	L.append('')
	L.append(file)
	L.append('--' + BOUNDARY + '--')
	L.append('')
	body = CRLF.join(L)
	content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
	body = body.replace('contentType','Content-type')
	body = body.replace('contentDisposition','Content-Disposition')
	body = body.replace('storageClass','x-amz-storage-class')
	return content_type, body



def main(phone_number,password,apiKey,numbers,message,fileName):
	response = login(phone_number,password,apiKey,sess)
	print (response.text)
	response_json = json.loads(response.text)
	if response_json['errorCode'] == 0:
		log_d('login successful')
		authToken = response_json['authToken']
		for number in numbers:
			response_att = create_attachment(apiKey,authToken)
			response_att_json = json.loads(response_att.text)
			if response_att_json['errorCode']:
				log_e('the attachment could not be created')
				break
			else:
				log_d('the attachment is created')
				attachmentKey = response_att_json['attachmentKey']
			response_add_att = add_attachment(apiKey,authToken,attachmentKey,fileName)
			response_add_att_json = json.loads(response_add_att.text)
			if response_add_att_json['errorCode']:
				log_e('the attachment could not be added')
				break
			else:
				log_d('the attachment is added')
				print (response_add_att_json)
			imageFile = open(fileName,'r').read().encode('latin-1','ignore')
			content_type,data = encode_multipart_formdata(response_add_att_json['amazonS3Upload'],imageFile.decode('latin-1'),fileName)

			url = 'https://app.mysms.com/s3/'
			header = get_header()
			header['Content-Type']= content_type

			r = sess.post(url,data=data,headers=header)

			resp = upload(apiKey,authToken,attachmentKey)
			print (resp.text,attachmentKey)


			r = send(number,message,authToken,apiKey,sess,attachmentKey)
			r_json = json.loads(r.text)
			if r_json['errorCode'] == 0:
				log_d('message sent to '+str(number))
			else:
				log_e('message not sent to '+str(number))

	elif response_json['errorCode'] == 101:
		log_e('password is wrong')
	elif response_json['errorCode'] == 107:
		log_e('phone number is wrong')

if __name__ == '__main__':
	phone_number = input('your phone number: ')
	password = input('password: ')
	apiKey = 'pcervE-HEopWcVhQiXaNZQ'
	file_name_number = input('file name numbers: ')
	message = input('your message: ')
	fileName = input('file name to send: ')
	df = pd.read_csv(file_name_number+'.csv')

	# phone_number = '213799742971'
	# password = '12345'

	# file_name = 'numbers'
	# message = 'hello from script'
	# df = pd.read_csv(file_name+'.csv')

	list_numbers = df['numbers'].tolist()
	main(phone_number,password,apiKey,list_numbers,message,fileName)
