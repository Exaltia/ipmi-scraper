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
number_to_name_and_values = {}
dict_association = {}
for each in pagelist:
    almost_clean.append(each.split('H'))
for each in almost_clean:
    # # result = re.search(r'[0-9{2}]', each[0])
    # if ';04' in each[0][4:5]:
    #     number_to_name_and_values[each[0][1:2]] = each[1]
    # if ';31' in each[0][4:5]:
    #     number_to_name_and_values[each[0][1:2]] = each[1]
    for entry in each:
        if re.search(r'[0-9]{2}', entry):
            if ';04' in entry: # each list has a lenght of 2
                lineid = re.search(r'[0-9]{2}', entry)
                lineid = lineid.group()

                position = entry[0].split(';') #There is an [ in the first number, stripping it
                # position[0] = ''.join(position[0].strip('['))
                # if lineid not in number_to_name_and_values.keys():
                #     print('key not found', lineid, each[1])
                try:
                    if len(number_to_name_and_values[lineid]) <= 2:
                        number_to_name_and_values[lineid].append(['0|'+each[1]])
                except KeyError:
                    print('keyerror')
                    number_to_name_and_values[lineid] = (['0|'+each[1]])
                # else:
                #     if len(number_to_name_and_values[lineid]) < 2:
                #         number_to_name_and_values[lineid].append(each[1])
            if ';31' in entry:
                print('in ;31 anyways')
                lineid = re.search(r'[0-9]{2}', entry)
                lineid = lineid.group()
                # if lineid in number_to_name_and_values.keys():
                #     if len(number_to_name_and_values[lineid]) < 2:
                #         number_to_name_and_values[lineid].append(each[1])
                try:
                    if len(number_to_name_and_values[lineid]) <= 2:
                        number_to_name_and_values[lineid].append(['1|'+each[1]])
                        #Sometimes entries are in reverse order, we need to put it back in the correct order
                except KeyError:
                    number_to_name_and_values[lineid] = (['1|'+each[1]])
                # else:
                #     tempdict ={'lineid': each[1]}
                # if lineid == position[0]:
                #     #Line id and next entry in the list are the same line, we can construct the dict entry
                #     if position[1] == '31':
                #         #if position is not 31, this is not an interesting value
                #         try:
                #             if dictkey not in dict_association.keys():
                #                 dict_association[dictkey] = each[1].rstrip(' ')
                #         except:
                #             pass
                            # Dict key variable may have not been created, but we don't care
for key in number_to_name_and_values:
    # try:
    #     if len(number_to_name_and_values[key]) > 2:
    #         number_to_name_and_values[key].pop(2)
    #     #Not all keys have values
    #
    # except:
    #     #We don't want to do anything with those missing values
    #     pass
    if number_to_name_and_values[key][0].startswith('1|'):
        newkey = number_to_name_and_values[key][1][0]
        newkey = newkey.strip('0|')
        value = number_to_name_and_values[key][0]
        value = value.strip('1|')
        dict_association[newkey] = value
    else:
        newkey = number_to_name_and_values[key][0]
        newkey = newkey.strip('0|')
        value = number_to_name_and_values[key][1][0]
        value = value.strip('1|')
        dict_association[newkey] = value
    # dict_association[number_to_name_and_values[key][0]] = number_to_name_and_values[key][1]
print(dict_association)
ssh.close()