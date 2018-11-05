import dpkt
import datetime
import socket
import os
import sys

import time
import struct


# import system

pcap_size = 2030 #-- 2029


one_piece = ''
bitTorrent_list = []
torrent_size = 0


idx_list = []
compare_idx = None
compare_list = [] # idx,  


# https://dpkt.readthedocs.io/en/latest/_modules/dpkt/tcp.html
'''
	tcp = ip.data
	print ("s port : ", tcp.sport)
	print ("d port : ", tcp.dport)
	print ("seq : ", tcp.seq)
	print ("ack : ", tcp.ack)
	print ("_off : ", tcp._off)
	print ("flag : ", tcp.flags)
	print ("window  : ", tcp.win)
	print ("urp : ", tcp.urp)
'''



def mac_addr(address):

# 	return address
	return ':'.join('%02x' % b for b in address)


#handshake flag
def bitTorrent_handshake_check ():
	print ("check")


def rest_variable():
	'''
		src_ip, dst_ip, src_port, dst_port, handshake_flag, packet_count
	'''
	return '', '', '', '', 0, 0


def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    """
    return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()


def print_string (input_text):
	print ("packet is all saved")
	print (input_text)
	print (len(input_text))


#get packet
def read_packet(pcak):

	'''
		src ip는 토렌트로 파일을 받는 IP 주소
	'''

	src_ip, dst_ip, src_port, dst_port, handshake_flag, packet_count = rest_variable()

	handshake_flag = 0
	handshake_list = []
	
	count = 0
#180915_seeder(2).pcapng

	# with open('180914_tcp_seeder.pcap', 'rb') as f:
	with open('180915_seeder(2).pcap', 'rb') as f:
		pcap = dpkt.pcap.Reader(f)

		for timestamp, buf in pcap:
			eth = dpkt.ethernet.Ethernet(buf)
			
			#Ethernet IPv4
			if (eth.type == 0x0800):
				ip = eth.data

				#IP Protocol TCP
				if (ip.p == 0x06):
					tcp = ip.data

					try :
						if (len(tcp.data) != 0):

							count = count + 1

							if (handshake_flag):
								packet_count = packet_count + 1 #

							bit = tcp.data
							# print (bit)
							bit_len = bit[0] # Hand_shake_flag
							bit_flag_size = bit[0:4] # bitTorrnet flag
							bit_handshake = bit[1:bit_len+1].decode("utf-8")	

							#1. BitTorrnet HandShake Protocol
							if (bit_len == 19 and bit_handshake == "BitTorrent protocol") :
								print ('IP: %s -> %s len=%d' % (socket.inet_ntoa(ip.src), socket.inet_ntoa(ip.dst), ip.len))
								print ('BitTorrent Handshake Protocol')
								if (src_ip == '' and dst_ip == ''):
									src_ip = socket.inet_ntoa(ip.src)
									dst_ip = socket.inet_ntoa(ip.dst)

									src_port = tcp.sport
									dst_port = tcp.dport

									handshake_flag = 1
								
								elif (src_ip != '' and dst_ip != '' and handshake_flag == 1) :
									if (src_ip == socket.inet_ntoa(ip.dst) and
										dst_ip == socket.inet_ntoa(ip.src) and
										src_port == tcp.dport and
										dst_port == tcp.sport):
										
										#TODO hanshake list ip compare code 
										handshake_list.append([src_ip, dst_ip, src_port, dst_port])
										
										src_ip, dst_ip, src_port, dst_port, handshake_flag, packet_count = rest_variable()

										# print (handshake_list)


							#Not match handshake #TODO packet count but.. timeout
							elif (packet_count >=10):								
								src_ip, dst_ip, src_port, dst_port, handshake_flag, packet_count = rest_variable()

							else :
								# if (count > pcap_size): ##288 start!!! -- 290 -- 350 878 1000
								# 	sys.exit(1)

								for handshake in handshake_list :
									#TODO If more than one peer exists, the algorithm must be implemented.
									# print ("handsahke : ",handshake)
									packet_analysis(handshake, bit, tcp, ip)
	
					except UnicodeDecodeError as un_err :
						print ("UnicodeDecodeError : ", un_err)
						pass	



def packet_analysis(handshake, bit, tcp, ip):
	start = 0

	# print (len(bit))
	# print (socket.inet_ntoa(ip.dst))
	# print (socket.inet_ntoa(ip.src))
	# print (tcp.dport)
	# print (tcp.sport)
	# print (handshake)
	global bitTorrent_list
	global torrent_size

	f = open ("result.txt",'a')

	fa = open ("a_data.txt",'a')

	# bitTorrent_list = []
	try :

		
		if (handshake[0] == socket.inet_ntoa(ip.dst) and 
			handshake[1] == socket.inet_ntoa(ip.src) and 
			handshake[2] == tcp.dport and 
			handshake[3] == tcp.sport):

			# print ("1")
			get_bitTorrent_info(start, tcp, bit, ip)

			"""
				[16384, 7, 26, 0, 0, '']
			"""
			for i in range(0, len (bitTorrent_list)):

				if (bitTorrent_list[i][4] == 0):

					bitTorrent_list[i][4] = bitTorrent_list[i][4] + len(tcp.data[13:])
					bitTorrent_list[i][5] = bitTorrent_list[i][5] + tcp.data[13:].decode("utf-8")

				elif (bitTorrent_list[i][4] != 0):

					tmp_sum = bitTorrent_list[i][4] + len(tcp.data)

					if (bitTorrent_list[i][0] > tmp_sum):
						
						# one_piece = one_piece + tcp.data.decode("utf-8")
						bitTorrent_list[i][4] = bitTorrent_list[i][4] + len(tcp.data)
						bitTorrent_list[i][5] = bitTorrent_list[i][5] + tcp.data.decode("utf-8")
						break

					elif (bitTorrent_list[i][0] == tmp_sum):

						bitTorrent_list[i][4] = bitTorrent_list[i][4] + len(tcp.data)
						bitTorrent_list[i][5] = bitTorrent_list[i][5] + tcp.data.decode("utf-8")
						print ("")
						print ("")
						print ("piece saved (equals)")
						print ("piece_index : " + str(bitTorrent_list[i][2]) + "(" +str(hex(bitTorrent_list[i][2])) + ")"  + " start_idx : " 
							+ str(bitTorrent_list[i][3]) + "(" +str(hex(bitTorrent_list[i][3])) + ")"  + " size : " + str (len(str(bitTorrent_list[i][5]))) + "\n")
						# print (len(bitTorrent_list[i][8]))
						"""
							[16384, 7, 26, 0, 0, '']
						"""
						f.write("piece_index : " + str(bitTorrent_list[i][2]) + "(" +str(hex(bitTorrent_list[i][2])) + ")"  + " start_idx : " 
							+ str(bitTorrent_list[i][3]) + "(" +str(hex(bitTorrent_list[i][3])) + ")"  + " size : " + str (len(str(bitTorrent_list[i][5]))) + "\n")
						fa.write(bitTorrent_list[i][5])
						print (bitTorrent_list)
						f.close()
						fa.close()
						torrent_size = torrent_size + bitTorrent_list[i][0]
						del bitTorrent_list[i]
						break

					#elif a <= : packet save
					elif (bitTorrent_list[i][0] < tmp_sum):
						
						last_size = bitTorrent_list[i][0] - bitTorrent_list[i][4]
						
						print ("last size : " ,last_size)

						bitTorrent_list[i][4] = bitTorrent_list[i][4] + len(tcp.data[0:last_size])
						bitTorrent_list[i][5] = bitTorrent_list[i][5] + tcp.data[0:last_size].decode("utf-8")

						print ("")
						print ("")
						print ("piece saved (not equals)")
						print ("piece_index : " + str(bitTorrent_list[i][2]) + "(" +str(hex(bitTorrent_list[i][2])) + ")"  + " start_idx : " 
							+ str(bitTorrent_list[i][3]) + "(" +str(hex(bitTorrent_list[i][3])) + ")"  + " size : " + str (len(str(bitTorrent_list[i][5]))) + "\n")
						# print (len(bitTorrent_list[i][8]))
						"""
							[16384, 7, 26, 0, 0, '']
						"""
						f.write("piece_index : " + str(bitTorrent_list[i][2]) + "(" +str(hex(bitTorrent_list[i][2])) + ")"  + " start_idx : " 
							+ str(bitTorrent_list[i][3]) + "(" +str(hex(bitTorrent_list[i][3])) + ")"  + " size : " + str (len(str(bitTorrent_list[i][5]))) + "\n")
						fa.write(bitTorrent_list[i][5])
						print (bitTorrent_list[i])
						f.close()
						fa.close()
						torrent_size = torrent_size + bitTorrent_list[i][0]
						del bitTorrent_list[i]
						
						# #remainder piece
						get_bitTorrent_info(start, tcp, tcp.data[last_size:], ip)

						if (bitTorrent_list != []):
							for j in range(0, len (bitTorrent_list)):
								bitTorrent_list[j][4] = bitTorrent_list[j][4] + len(tcp.data[last_size+13 :])
								bitTorrent_list[j][5] = bitTorrent_list[j][5] + tcp.data[last_size+13 :].decode("utf-8")
								break
						# # tmp_idx, tmp_piece = get_inside_piece(0, tcp.data[last_size:])

						
						# for j in range(0, len(bitTorrent_list)):
						# 	if (tmp_idx == bitTorrent_list[j][2] and
						# 		tmp_piece == bitTorrent_list[j][3]):
								
						# 		bitTorrent_list[j][5] = tcp.ack
						# 		bitTorrent_list[j][6] = tcp.seq + len(tcp.data)
						# 		bitTorrent_list[j][7] = bitTorrent_list[i][7] + len(tcp.data[last_size+13 :])
						# 		bitTorrent_list[j][8] = bitTorrent_list[i][8] + tcp.data[last_size+13 :].decode("utf-8")
						# 		break

						# break

	except ValueError as ve :
			print ("invalid literal for int() with base 10 : ", ve)
			return

	# except TypeError as te :
	# 		print ("None Type : ", te)
	# 		return

	except IndexError as ee :
			print ("index error : ", ee)
			return
			# return
			#return

def get_inside_piece(start, remain_bit):

	try :
		if (start >= (len(remain_bit) - 1)):
			# return bitTorrent_list
			return -1, -1
		else :
			# print("1")
			# print ("1111 : ",len(remain_bit)) # 1123 + 337
			# print (remain_bit)
			size = remain_bit[start: start + 4]
			start = start + 4
			size_value = struct.unpack('>L', size)[0]
			flag = remain_bit[start : start + 1]
			flag_value = struct.unpack('>b', flag)[0]
			start = start + 1
			print("2", flag_value)

			if (flag_value == 65):
				print (remain_bit)
			# print (remain_bit)
			if (flag_value == 7):
				# print("2")
				piece_index = remain_bit[start : start + 4] 
				piece_index_value = struct.unpack('>L', piece_index)[0]
				start = start + 4

				begin_off_piece = remain_bit[start : start + 4] 
				begin_off_piece_value = struct.unpack('>L', begin_off_piece)[0]
				start = start + 4

				print ("BitTorrent piece (inside_info) : ", size_value)
				print ("piece_index_value : ",piece_index_value)
				print ("begin_off_piece_value : ",begin_off_piece_value)
				# bitTorrent_list.append([size_value, flag_value, piece_index_value, begin_off_piece_value, '', tcp.ack, ''])
				# bitTorrent_list.append(tmp_list)
				return piece_index_value, begin_off_piece_value
			else :
				return -1, -1
	
	except : 
		return -1, -1

#bittTorrnet info
#TODO return value is list?
def get_bitTorrent_info (start, tcp, bit, ip):
	global bitTorrent_list
	tmp_list = []
	try :
		if (start >= (len(bit) - 1)):
			# return bitTorrent_list
			return
		else :
			
			size = bit[start: start + 4]
			start = start + 4
			size_value = struct.unpack('>L', size)[0]
			flag = bit[start : start + 1]
			flag_value = struct.unpack('>b', flag)[0]
			start = start + 1
			
			#Unchoke
			if (flag_value == 1):
				# print ('IP: %s -> %s len=%d' % (socket.inet_ntoa(ip.src), socket.inet_ntoa(ip.dst), ip.len))
				print ('BitTorrent Unchoke Protocol : ',size_value)

			#Piece
			elif (flag_value == 7):

				piece_index = bit[start : start + 4] 
				piece_index_value = struct.unpack('>L', piece_index)[0]
				start = start + 4

				begin_off_piece = bit[start : start + 4] 
				begin_off_piece_value = struct.unpack('>L', begin_off_piece)[0]
				start = start + 4

				print ("BitTorrent piece : ", size_value)

				bitTorrent_list.append([size_value - 9 , flag_value, piece_index_value, begin_off_piece_value, 
					 0, ''])
				# bitTorrent_list.append([size_value, flag_value, piece_index_value, begin_off_piece_value, '', tcp.ack, ''])
				# bitTorrent_list.append(tmp_list)
				return			
			else :
				return
			# start = start + size_value

			get_bitTorrent_info(start, tcp, bit, ip)

	except struct.error :
		#Not BitTorrent Protocol
		return




if __name__ == '__main__':
	os.system("del result.txt")
	# os.system("del ata.txt")
	with open('180915_seeder(2).pcap', 'rb') as f:
		pcap = dpkt.pcap.Reader(f)
		read_packet(pcap)

	print ("result : ",torrent_size)
	print ("result : ", torrent_size / 1024 * 1024)