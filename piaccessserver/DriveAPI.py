#!/usr/bin/python

'''
Original script by Wesley Chun, 
Heavily modified to fit purpose
http://wescpy.blogspot.ca/2015/12/migrating-to-new-google-drive-api-v3.html


'''

from __future__ import print_function
import os
import sys
import argparse
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

#parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", choices=["U", "D", "O"], help="Mode of the script either U for upload, D for download or O for update(overwrite).")
parser.add_argument("-f", "--file", nargs='+', help="File name to upload or path to download")	
parser.add_argument("-i", "--id", nargs='+', help="Id of file to download or update.")
args = parser.parse_args()

#function to associate the id with the file

def assoc(ids, files):
	num = 0
	idarr = []
	for id in ids:
		idarr.append((id,files[num]))
		num += 1
	print(idarr) 
	return idarr
	
def fileerr(local):
	if local:
		print("File not found, please make sure the file you are uploading has an extension and exists.")
	else:
		print("The file you are trying to download or update does not exist on the drive (Id not found)")
	
#define upload, download and overwrite functions.

def upload(files):
	for file in files:
		if os.path.isfile(file):
			metadata = {'name': os.path.split(file)[1]}
			
			res = DRIVE.files().create(body=metadata, media_body=file).execute()
			
			if res:
				print('Uploaded "%s" (%s)' % (file, res['mimeType']))
				print('ID: "%s"' % (res['id']))
		else: fileerr(True)
	
def download(ids, files):
	if args.id:		
		for id, file in assoc(ids, files):
			try:
				data = DRIVE.files().get_media(fileId=id).execute()
			
				if data:
					fn = file
					with open(fn, 'wb') as fh:
						fh.write(data)
					print('Downloaded "%s" ' % (fn))
			except:fileerr(False)
	else:
			print("usage: %s [-h] [-i ID] {U,D,O} file" % (os.path.basename(__file__)))
			print("%s: error: the following arguments are required: ID" % (os.path.basename(__file__)))

		
def overwrite(ids, files):
	if args.id:
		for id, file in assoc(ids, files):
			if os.path.isfile(file):
				try:
					res = DRIVE.files().update(fileId=id, media_body=file).execute()
					if res:
						print('Uploaded "%s" (%s)' % (file, res['mimeType']))
				except:fileerr(False)
			else: fileerr(True)
	else:
		print("usage: %s [-h] [-i ID] {U,D,O} file" % (os.path.basename(__file__)))
		print("%s: error: the following arguments are required: ID" % (os.path.basename(__file__)))
		
		
#connect and authenticate to google drive
flags = tools.argparser.parse_args(args=[])
SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
	creds = tools.run_flow(flow, store, flags)
			
DRIVE = build('drive', 'v3', http=creds.authorize(Http()))

if args.file:

	#choose mode and call function
	if args.mode == "U":
		upload(args.file)
	elif args.mode == "D":
		download(args.id, args.file)
	elif args.mode == "O":
		overwrite(args.id, args.file)
	else:
		print("usage: %s [-h] [-i ID] {U,D,O} file" % (os.path.basename(__file__)))
		print("%s: error: the following arguments are required: Mode (Choose between {U or D or O}" % (os.path.basename(__file__)))
else:
	print("usage: %s [-h] [-i ID] {U,D,O} file" % (os.path.basename(__file__)))
	print("%s: error: the following arguments are required: File" % (os.path.basename(__file__)))
	

