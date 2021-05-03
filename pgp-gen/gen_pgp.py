import argparse
import datetime
import gnupg # pip3 install python-gnupg
import os
import random
import re
import shutil
import string
import sys

# tested on MacOS

# ---------------------- constants -----------------------

# path to the csv file containing all IDs and passwords
# will be created by this skript
# file can be imported to a passwort manager, e.g. KeePassXC
CSV_FILE = r"pgp-credentials.csv" 

# notes to be included for each key in the CSV file
CSV_NOTES = "Created at " + datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")


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
	with open(args.email_addresses, 'r') as f:
	    email_addresses = f.read().splitlines() 

	# check if the user wants to create an output dir
	if args.out:

		# check if output dir already exists and
		if os.path.exists(args.out):
			if input("Directory '{out}' already exists. Delete contents and re-create? (y/n)"
				.format(out=args.out))=='y':
				shutil.rmtree(args.out)
			else:
				sys.exit("won't delete output dir.")

		# create output directory
		os.makedirs(args.out)

	# else set output dir to working dir
	else:
		args.out = '.'

	# create gpg instance (its a singleton :)
	# set 'verbose=True' for debugging
	gpg = gnupg.GPG(gnupghome=args.out, verbose=False)

	# credentials file (can be imported to keepass)
	csv_file = open(args.out + '/' + CSV_FILE, "w")
	csv_file.write('"Group","Title","Username","Password","URL","Notes"\n')

	# iterate on email addresses
	for email in email_addresses:

		# check if email address is valid
		regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
		if not re.search(regex, email):
			print ("skipping invalid email address: " + email)
			continue
		
		# generate passphrase
		passphrase = pass_gen()

		# generate PGP key pair
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
		csv_file.write('"pgp-keys",')					# group
		csv_file.write('"{s}",'.format(s=email))		# title
		csv_file.write('"{s}",'.format(s=key.fingerprint))		# username
		csv_file.write('"{s}",'.format(s=passphrase))	# password
		csv_file.write('"",')							# url
		csv_file.write('"{s}",'.format(s=CSV_NOTES))	# notes
		csv_file.write('\n')

		# export public key to file
		ascii_armored_public_keys = gpg.export_keys(key.fingerprint)
		with open(args.out + '/' + email + "_public.asc", 'w') as f:
			f.write(ascii_armored_public_keys)
		
		# export private key to file
		ascii_armored_private_keys = gpg.export_keys(
		    keyids=key.fingerprint,
		    secret=True,
		    passphrase=passphrase,
		)
		with open(args.out + '/' + email + "_private.asc", 'w') as f:
			f.write(ascii_armored_private_keys)

	# close csv file
	csv_file.close()

	# ToDo: export all public keys

	# end of program
	print("done.\n")

# --------------- start of the skript ------------------

# when started as script, call main function
if __name__ == "__main__":
    main()