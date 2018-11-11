# -*- coding: utf-8 -*-
import time
import sys
import os
import argparse
import imagehash
from PIL import Image
import getopt

import pymysql

import logging


'''
	가로 1.77 : 세로 1 (height X 0.128 = 블랙박스) 
	1280 X 720
	1920 X 1080

	가로 1.5 : 세로 1 (height ㅌ 0.094 = 블랙박스)
	720 X 480 

'''
def crop_img(img):
	
	img_width, img_height = img.size
	crop_img = ''

	#0.093 ~ 0.095
	if (img_width == 720 and img_height == 480):
		crop_img = img.crop(( int(img_width//2) - int(img_width/10) , 0, int(img_width//2) + int(img_width/10) , int(img_height * 0.092)))
	
	#0.127 ~ 0.128
	elif ( (img_width == 1280 and img_height == 720) or (img_width == 1920 and img_height == 1080)): 
		crop_img = img.crop(( int(img_width//2) - int(img_width/10) , 0, int(img_width//2) + int(img_width/10) , int(img_height * 0.126)))

	elif (img_width == 1280 and img_height == 692):
		crop_img = img.crop((img_width//2 - 150, 0, img_width//2 + 150, 75))
	
	return crop_img


'''
	Returns flag whether black box exists 
'''
def black_box_check(file_path):

	black_box_list = []
	black_flag = 1
	count = 0
	try :
		for filename in os.listdir(file_path): #원본 이미지에서 검정박스 여부 확인
			#If the extension is an image file
			if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.bmp') :
				img = Image.open(file_path + "/" + filename)
				cropped_img = crop_img(img)
				extrema = cropped_img.convert("L").getextrema()
				
				if sum(extrema) in range(0,30):
					black_box_list.append("O")
					count = count + 1		
				else:
					black_box_list.append("X")
					count = count + 1

				if (count >= 100):
					break
	except OSError as os_error:
		print ("OSError" ,os_error)
		pass

	for black_box in black_box_list:
		if (black_box == "X"):
			black_flag = 0
			break

	return black_flag


'''
	make Image Hash
'''

def do_work(path, db_insert):
	org_dic ={}
	count = 0
	img_count = 0
	try :
		black_flag = black_box_check(path)

		img_count = len(os.listdir(path))

		print ("================== extract imghash ==================")
		print ("")
		for filename in os.listdir(path):
			if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.bmp') :
				count = count + 1
				org_img = Image.open(path + "/" + filename)
				phash = img_resize(org_img, black_flag)
				org_dic[phash] = filename
				printProgress(count, img_count, "", "",1, 50)

		print ("")
		print ("=============== save imagehash info ==================")
		print ("")
		f = open ("image_hash.txt","w")

		for keys,values in org_dic.items():
			if (db_insert):
				input_db(keys, values)

			else :
				f.write(str(keys) + " : " + str(values)+ "\n")
			# print (str(keys) + " : " + str(values))
			# print (values)
		f.close()
		# os.system("")
	except OSError as os_error:
		print ("OSError : " ,os_error)



'''
	CREATE TABLE hash (
	dept_no INT(11) AUTO_INCREMENT PRIMARY KEY,
	phash VARCHAR(32) NOT NULL,
	image_name VARCHAR(32) NOT NULL
	);
'''
def input_db(keys, values):

	conn = pymysql.connect(host='localhost', user='root', password='ms0203rlA!',
                           db='hash_test', charset='utf8')

	curs = conn.cursor()
 #    insert into cert(date, bank_info, account_number, country, IP) values ('2018-08-28', '', 1, '', '' );
	sql = """insert into hash(phash, image_name) values ( %s, %s)"""
	curs.execute(sql, (str(keys), str(values)))
	conn.commit()

'''

'''
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100): 
	formatStr = "{0:." + str(decimals) + "f}" 
	percent = formatStr.format(100 * (iteration / float(total))) 
	filledLength = int(round(barLength * iteration / float(total))) 
	bar = '#' * filledLength + '-' * (barLength - filledLength) 
	sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)), 

	if iteration == total: 
		sys.stdout.write('\n') 
	sys.stdout.flush() 

#이미지 리사이즈하기
def img_resize(img, img_black_flag):
	#검정 박스가 있는 경우
	width, height = img.size

	#이미지 크기가 1920, 1080 인 경우

	#이미지의 검정 박스가 존재하는 경우
	if img_black_flag :
		#TODO 1920 X 1080 / 1280 X 720
		#1920 X 1080 해상도 (박스 높이 137) 1280 X 720 해상도 (박스 높이 92)
		if ( (width == 1920 and height == 1080) or (width == 1280 and height == 720) ):
			cropped_img = img.crop((0, int(height * 0.13), width, height - int(height * 0.13) ))
			cropped_img = cropped_img.resize((1920, 1080), Image.ANTIALIAS)
			phash = imagehash.phash(cropped_img)
		
		#1280 X 720 해상도 (박스 높이 92)
		# elif (width == 1280 and height == 720):
		# 	cropped_img = img.crop((0, int(height * 0.13) , width, height - int(height * 0.13) ))
		# 	cropped_img = cropped_img.resize((1920, 1080), Image.ANTIALIAS)
		# 	phash = imagehash.phash(cropped_img)

		#1280 X 720 해상도 (박스 높이 75 ~ 92)
		elif (width == 1280 and height == 692):
			cropped_img = img.crop((0, 90, width, height - 90))
			cropped_img = cropped_img.resize((1920, 1080), Image.ANTIALIAS)
			phash = imagehash.phash(cropped_img)

		#720 X 480 해상도 (박스 높이 35)
		elif (width == 720 and height == 480):
			#cropped_img = img.crop((width//2 - 250, height//2 - 150, width//2 + 250, height//2 + 150))
			cropped_img = img.crop((0,  40, width, height - 40))
			cropped_img = cropped_img.resize((1920, 1080), Image.ANTIALIAS)
			phash = imagehash.phash(cropped_img)

		#아직 구현 안됨
		else :
			print("wait 아직 구현 안됨")

	#이미지의 검정 박스가 존재하지 않는 경우
	else :
		img = img.resize((1920, 1080), Image.ANTIALIAS)
		phash = imagehash.phash(img)
	return phash


def get_imgfile_list (dir_path):

	imgdirList = []
	count = 0
	try:
		filenames = os.listdir(dir_path)
		for filename in filenames:
			 imgdirList.append(filename)
			 
		return imgdirList           
	except PermissionError:
		print ("permission Denided")
		return []

		
def compare():
	tar_dic = {}
	org_dic = {}
	with open('image_hash.txt', 'r') as f:
		rls = f.readlines()
		for i in rls:
			tar_hash = imagehash.hex_to_hash(i.split(' : ')[0])
			tar_img_name = i.split(' : ')[1]
			tar_dic[tar_hash] = tar_img_name

	conn = pymysql.connect(host='localhost', user='root', password='ms0203rlA!',
                           db='hash_test', charset='utf8')
	curs = conn.cursor()
	curs.execute("SELECT phash, image_name FROM hash")
	result = curs.fetchall()
	
	for i in result:
		org_hash = imagehash.hex_to_hash(str(i).split("'")[1])
		org_img_name = str(i).split("'")[3]
		org_dic[org_hash] = org_img_name

	resultList = []

	for oh, oin in org_dic.items():
		for th, tin in tar_dic.items(): 
			diff_hash = th-oh
			if diff_hash <= 3:
				resultList.append(tin[:-1] + " - " + oin + " : " + str(diff_hash))
				print(tin[:-1] + " - " + oin + " : " + str(diff_hash))
			elif diff_hash <= 6 and diff_hash >= 4 :
				resultList.append(tin[:-1] + " - " + oin + " : " + str(diff_hash))
				print(tin[:-1] + " - " + oin + " : " + str(diff_hash))
			elif diff_hash <= 10 and diff_hash >= 7 :
				resultList.append(tin[:-1] + " - " + oin + " : " + str(diff_hash))
				print(tin[:-1] + " - " + oin + " : " + str(diff_hash))

	f = open("\\result.txt", "w")
	for reList in resultList :
		f.write(reList + "\n")
	f.close()


# help alert
def help():
	print ("print help usage")
	print ("[-d] is input image saved directory")
	print ("[-o] is input image saved directory")
	print ("	\"1\"  is use database  ")
	print ("	\"0\"  is use file save ")
	print (" None use -o option default is 0(use file save) ")
	print ("[-c] is compare ")
	print ("[-h][--help] is help option ")






if __name__ == '__main__':
	db_flag = 0

	try:
		# 여기서 입력을 인자를 받는 파라미터는 단일문자일 경우 ':' 긴문자일경우 '='을끝에 붙여주면됨
		opts, args = getopt.getopt(sys.argv[1:],"d:o:h:c",["help"])
	
	except getopt.GetoptError as err:
		print (str(err))
		help()
		sys.exit(1)

	file_ext = None
	name = None
	search_list = None
	
	if opts == [] :
		help()
		sys.exit(1)
	start_time = time.time()
	for opt,arg in opts:
		#print ("arg is : " +str(arg))

		if (opt == '-d'):
			origin = arg
		elif (opt == '-o'):
			db_flag = arg
		elif (opt == '-c'):
			compare()
		elif ( opt == "-h") or ( opt == "--help"):
			help()
			sys.exit(1)
	
	if opt == '-d' or opt == '-o':
		do_work(origin, db_flag)

	else:
		pass
	end_time = time.time()
	print("Elapsed time is "+str(end_time-start_time))