import argparse
import gnupg # pip3 install python-gnupg
import os
import random
import re
import stat
import string
import sys
import shutil
import datetime

# tested on MacOS

# ---------------------- constants -----------------------

# path to the credentials file containing all IDs and passwords
# will be created in this skript
# file is fomatted so can import it to keepass
CREDENTIALS_FILE = r"pgp-credentials.csv" 

# ephemeral home directory in which the keyrings will be created
KEYRING_DIR = r"pgp-keys"



# --------------------- helper function -----------------------

def pass_gen():
	alphabet = string.ascii_letters + "123456789"
	password = ""
	for _ in range(16):
		password += random.choice(alphabet)
	return password


# -------------------- main function --------------------

def main():
	
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("email_addresses", 
		help="file containing email adresses line by line")
	parser.add_argument("--out", 
		help="output directory for the pgp-keys (will be created)")
	args = parser.parse_args()

	# check if file containing the email-addresses exists
	if not os.path.exists(args.email_addresses):
		sys.exit("email-addresses: file does not exist.")

	# parse email addresses
	file = open(args.email_addresses, "r")
	email_addresses = file.readlines()

	# check if the user wants to create an output dir
	if args.out:

		# check if output dir already exists and
		if os.path.exists(args.out):
			if input("Directory {out} already exists. Delete contents and re-create? (y/n)"
				.format(out=args.out))=='y':
				shutil.rmtree(args.out)
			else:
				sys.exit("won't delete output dir.")

		# create output directory
		os.makedirs(args.out)

	# else set output dir to working dir
	else:
		args.out = '.'

	# create gpg singleton
	gpg = gnupg.GPG(gnupghome=args.out, verbose=True)

	# adjust permissions (avoids PGP warning)
	#os.chmod(args.out + '/' + KEYRING_DIR, stat.S_IRWXU)
	#os.chmod(args.out + '/' + KEYRING_DIR + "/private-keys-v1.d", stat.S_IRWXU)

	# create batch file for gpg key generation
	#file = open(args.out + '/' + BATCH_FILE, "w")

	# credentials file (can be imported to keepass)
	credentials_file = open(args.out + '/' + CREDENTIALS_FILE, "w")
	credentials_file.write('"Group","Title","Username","Password","URL","Notes"\n')

	# iterate on email addresses
	for email in email_addresses:

		# check if email address is valid
		regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
		if not re.search(regex, email):
			print ("skipping invalid mail address: " + email)
			continue
		
		# generate password
		passphrase = pass_gen()

		# generate key pair
		input_data = gpg.gen_key_input(
			name_email=email,
			passphrase=passphrase,
			expire_date=0,
			key_type="RSA",
			key_length=4096,
			subkey_type="RSA",
			subkey_length=4096
		)
		key = gpg.gen_key(input_data)
		
		# write credentials to file
		credentials_file.write('"pgp-keys",')					# group
		credentials_file.write('"{a}",'.format(a=email))		# title
		credentials_file.write('"{f}",'.format(f=key.fingerprint))		# username
		credentials_file.write('"{p}",'.format(p=passphrase))	# password
		credentials_file.write('"",')							# url
		credentials_file.write('"{t}",'.format(t=datetime.datetime.now()))	# notes

		print("2323232" + key.fingerprint)

		# export private key to file
		ascii_armored_private_keys = gpg.export_keys(
		    keyids=key.fingerprint,
		    secret=True,
		    passphrase=passphrase,
		)
		with open(args.out + '/' + email + "_secreta.asc", 'w') as f:
			f.write(ascii_armored_private_keys)

	# TODO: export all public keys

	credentials_file.close()

	print("done. Don't forget to clean up (save credentials to keepass, delete keyring...)\n")

# --------------- start of the skript ------------------

# when started as script, call main function
if __name__ == "__main__":
    main()