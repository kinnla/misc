import argparse
import gnupg # pip3 install python-gnupg
import os
import random
import re
import stat
import string

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
	
	# list of tuples (ID, pass) for all keys
	credentials = []

	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("mail_addresses", 
		help="file containing mail adresses line by line")
	parser.add_argument("out", 
		help="output directory for the pgp-keys (will be created)")
	args = parser.parse_args()

	# check if file containing the mail-adresses exists
	if not os.path.exists(args.mail_addresses):
		sys.exit("mail-addresses: file does not exist.")

	# parse mail addresses
	file = open(args.mail_addresses, "r")
	mail_addresses = file.readlines()

	# check if output dir already exists and
	if os.path.exists(args.out):
		if input("Directory {out} already exists. Delete contents and \
			re-create? (y/n)".format(out=arg.out))=='y':
			os.remove(args.out)
		else:
			sys.exit("won't delete output dir.")

	# create output directory
	os.makedirs(args.out + '/' + KEYRING_DIR)
	gpg = gnupg.GPG(gnupghome=KEYRING_DIR, verbose=True)

	# adjust permissions (avoids PGP warning)
	#os.chmod(args.out + '/' + KEYRING_DIR, stat.S_IRWXU)
	#os.chmod(args.out + '/' + KEYRING_DIR + "/private-keys-v1.d", stat.S_IRWXU)

	# create batch file for gpg key generation
	#file = open(args.out + '/' + BATCH_FILE, "w")

	# iterate on mail addresses
	for mail in mail_addresses:

		# check if email address is valid
		regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
		if not re.search(regex, mail):
			print ("skipping invalid mail address: " + mail)
			continue
		
		# generate password and write to credentials
		passphrase = pass_gen()
		credentials.append((mail, passphrase))

		# generate key pair
		key = gpg.gen_key(
			name_email=mail,
			passphrase=passphrase,
			expire_date=0,
			key_type="RSA",
			key_length=4096,
			subkey_type="RSA",
			subkey_length=4096
		)
		print(key)

		# export private key to file
		ascii_armored_private_keys = gpg.export_keys(
		    keyids=key.fingerprint,
		    secret=True,
		    passphrase='passphrase',
		)
		with open(mail + "_secreta.asc", 'w') as f:
			f.write(ascii_armored_private_keys)

	# export all public keys



	# --------------------- gpg commands ------------------

	

	# write credentials to file
	file = open(CREDENTIALS_FILE, "w")
	file.write('"Group","Title","Username","Password","URL","Notes"\n')
	for (email, passphrase) in credentials:
		file.write('"pgp-keys",')
		file.write('"{a}",'.format(a=email))

		file.write(a + " " + p + "\n")
	file.close()

	print("done. Don't forget to clean up (save credentials to keepass, delete keyring...)\n")

	print(status.ok)
	print(status.status)
	print(status.stderr)

# --------------- start of the skript ------------------

# when started as script, call main function
if __name__ == "__main__":
    main()