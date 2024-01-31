from email.mime import base
import requests
from bs4 import BeautifulSoup
import PIL.Image
import time
import io
import base64
import sqlite3
import pdb
import random

'''
SQLite 3 Database Create Statments! 

CREATE TABLE "scraped" (
	"id"	INTEGER,
	"img_number"	INTEGER UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
)

CREATE TABLE "scrapes" (
	"id"	INTEGER,
	"url"	TEXT UNIQUE,
	"img_base64"	BLOB,
	"params"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
'''

# Connect to DB.
conn = sqlite3.connect('CivitAI.db')

# Empty list "scraped", to be populated in-memory. 
scraped = []

# Collect a list of image #s from DB which have already been scraped.
cur = conn.execute('SELECT img_number FROM scraped')
for _r in  cur.fetchall():
	scraped.append(_r[0])

# Range of IDs, randomized.
while True:

	_range = random.randrange(5000000, 5634010)
	if _range not in scraped:

		try:
			_r = requests.get(f"https://civitai.com/images/{_range}")

			# IF our request is 200 OK:
			if _r.status_code == 200:
				
				soup = BeautifulSoup(_r.text, "html.parser")
				viewport = soup.find("div", {"class": "mantine-ScrollArea-viewport"})

				# Grab image URL.
				for _v in viewport:
					imgs = soup.find_all("img")
					for _i in imgs:
						
						# Find the URL of original image, containing the EXIF.
						if "original=true" in _i.get("src"):
							generated_image_url = _i.get('src')

							# Replace text to pull 320x width version for DB storage.
							generated_image_thumb_url = _i.get('src').replace('original=true', 'width=320')	

						# If we can't find the original image URL, skip.
						else:
							# print(f"[Error] {_r.url}, 'Original' image not found.")
							continue

					# Download image.
					_r = requests.get(generated_image_url)

					# Convert to Base64-encoded for DB storage.
					base64_img = base64.b64encode(_r.content)

					# Grab generation parameters from EXIF data.
					pil_img = PIL.Image.open(io.BytesIO(_r.content))
					params = pil_img.info['parameters']

					if params:

						# Grab thumbnail copy of image (without EXIF).
						_thumb_req = requests.get(generated_image_thumb_url)
						_thumb_b64 = base64.b64encode(_thumb_req.content)
						
						# Write resulting data to SQLite3.
						conn.execute('INSERT INTO scrapes (url, img_base64, params) VALUES (?, ?, ?)', (_r.url, sqlite3.Binary(_thumb_b64), params))
						conn.commit()

						# Record the image # that has been scraped....
						conn.execute('INSERT INTO scraped (img_number) VALUES (?)', (_range,))
						conn.commit()

						# Add image ID to in-memory dict, to avoid re-requesting the URL.
						scraped.append(str(_range))

						print(f"[D/L] {_r.url}")

					else:
						# print(f"[Error] {_r.url}, 'params' not found.")
						pass

					# Sleep for 1 second.
					time.sleep(random.uniform(1.3,1.1832))
			else:
				print(f"Request to [https://civitai.com/images/{_range}] failed! ")

		# Error Handling
		except Exception as e:
			
			# Add image ID to in-memory dict, to avoid re-requesting the URL.
			scraped.append(str(_range))
			
			# Record to DB the image # which produced an error...
			try:
				conn.execute('INSERT INTO scraped (img_number) VALUES (?)', (_range,))
				conn.commit()

			except Exception as e:
				# UNIQUE constraint, terminating script and re-starting will be the excluded img #s from DB and store in our "scraped" dict.
				print(f"[Error] Failed to insert image # {_range} into DB. Error: {e}")
				pass


	else:
		print(f"[Skip] (https://civitai.com/images/{_range})")

# Close DB.
conn.close()