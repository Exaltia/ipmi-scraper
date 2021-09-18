import re

import paramiko
# from keyboard import press
from time import sleep
ssh = paramiko.SSHClient()
key = paramiko.RSAKey.from_private_key_file('/home/exaltia/manager_ovh',
                                            password='La patate micro ondée se '
                                                     'transforme en diamant '
                                                     'miauleur')
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('1.sol-ssh.ipmi.ovh.net', username='ipmi', pkey = key )

#stdin, stdout, stderr = ssh.exec_command('')
remote_con = ssh.invoke_shell()
stdin = remote_con.makefile('wb')
stdout = remote_con.makefile('rb')
stdin.write('\r\n')
#sleep(10)
#output = remote_con.recv(10000)
ignore_start = 424
trash = stdout.read(ignore_start)
onepage = stdout.read(15360) #Todo: value is almost one page, need to be corrected
#Should be 80 characters * 24 lines * 8 bytes
#If reading line per line, it's 80*8 bytes buffer
#onepage is binary, we need ascii to do str handling
onepage = onepage.decode('ascii')
# onepage = onepage.strip("b'")
pagelist = onepage.split('\x1b')

almost_clean = []
dict_association = {}
for each in pagelist:
    almost_clean.append(each.split('H'))
for each in almost_clean:
    for entry in each:
        if re.search(r'[0-9]{2}', entry):
            if ';' in each[0]: # each list has a lenght of 2
                lineid = each[0].split(';', 1)[0].strip('[')
                position = each[0].split(';') #There is an [ in the first number, stripping it
                position[0] = ''.join(position[0].strip('['))
                if position[1] == '04':
                    dictkey = each[1].rstrip(' ')
                if lineid == position[0]:
                    #Line id and next entry in the list are the same line, we can construct the dict entry
                    if position[1] == '31':
                        #if position is not 31, this is not an interesting value
                        try:
                            if dictkey not in dict_association.keys():
                                dict_association[dictkey] = each[1].rstrip(' ')
                        except:
                            pass
                            # Dict key variable may have not been created, but we don't care
print(dict_association)
ssh.close()