import gnupg # pip3 install python-gnupg
import os
import random
import stat
import string

# sudo apt install xclip

# ---------------------- constants -----------------------

# This skript will create a PGP key for each email-address
# Add or edit addresses, one address per line
EMAIL_ADDRESSES = """
"""

# path to the batch file containing all commands and paramters for gpg
BATCH_FILE = r"gpg-batch" 

# path to the credentials file containing all IDs and passwords
# file is fomatted  so can import it to keepass
CREDENTIALS_FILE = r"gpg-credentials.csv" 

# ephemeral home directory in which the keyrings will be created
KEYRING_DIR = r"pgp-keys"


# --------------------- variables -----------------------

# list of tuples (ID, pass) for all keys
credentials = []


# --------------------- functions -----------------------

def pass_gen():
	alphabet = string.ascii_letters + "123456789"
	password = ""
	for _ in range(16):
		password += random.choice(alphabet)
	return password


# --------------- start of the skript ------------------

# create batch file for gpg key generation
file = open(BATCH_FILE,"w")
for a in iter(EMAIL_ADDRESSES.strip().splitlines()):

	# create password and write to credentials
	p = pass_gen()
	credentials.append((a,p))
	file.write ("Key-Type: eddsa\n")
	file.write ("Key-Curve: Ed25519\n")
	file.write ("Key-Usage: sign\n")
	file.write ("Subkey-Type: ecdh\n")
	file.write ("Subkey-Curve: Curve25519\n")
	file.write ("Subkey-Usage: encrypt\n")
	file.write ("Name-Email: " + a + "\n")
	file.write ("Passphrase: " + p + "\n")
	file.write ("Expire-Date: 0\n")
	file.write ("%commit\n")
file.close()

# create the keyring directory, if it not yet exists
if not os.path.exists(KEYRING_DIR):
	os.makedirs(KEYRING_DIR)

# create the private keys subdirectory, if it not yet exists
if not os.path.exists(KEYRING_DIR + "/private-keys-v1.d"):
	os.makedirs(KEYRING_DIR + "/private-keys-v1.d")

# adjust permissions (avoids PGP warning)
os.chmod(KEYRING_DIR, stat.S_IRWXU)
os.chmod(KEYRING_DIR + "/private-keys-v1.d", stat.S_IRWXU)

# --------------------- gpg commands ------------------

# generate keys
command = "gpg --batch --generate-key --homedir {k} {f}".format(
	k=KEYRING_DIR, f=BATCH_FILE)
#print(command)
stream = os.popen(command)
print (stream.read())
stream.close()

# export public keys, all in one file
command = "gpg --armor --output allpubkeys.asc --export --homedir " + KEYRING_DIR
#print(command)
stream = os.popen(command)
print (stream.read())
stream.close()

print ("exporting private keys one by one. Password will be in the clipboard")

# iterate on all email addresses
for (a, p) in credentials:

	# Copy passphrase to clipboard
	command = "echo {p} | tr -d '\n' | xclip -selection c".format(p=p)
	stream = os.popen(command)
	stream.close()

	# export private keys to individual file
	command = "gpg --batch --yes --homedir {k} --armor --output {f} --export-secret-keys {a}".format(
		a=a, f=a + "_secreta.asc", k=KEYRING_DIR)
	stream = os.popen(command)
	stream.close()

# write credentials to file
file = open(CREDENTIALS_FILE, "w")
file.write('"Group","Title","Username","Password","URL","Notes"\n')
for (a, p) in credentials:
	file.write('"pgp-keys",')
	file.write('"{a}",'.format(a=a))

	file.write(a + " " + p + "\n")
file.close()

# delete batchfile
os.remove(BATCH_FILE) 

print("done. Don't forget to clean up (save credentials to keepass, delete keyring...)\n")