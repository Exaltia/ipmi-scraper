import re
from pynput.keyboard import Key, Controller
import paramiko
ssh = paramiko.SSHClient()
sshkey = paramiko.RSAKey.from_private_key_file('/home/exaltia/manager_ovh',
                                            password='La patate micro ondée se '
                                                     'transforme en diamant '
                                                     'miauleur')
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
kbd = Controller()
ssh.connect('1.sol-ssh.ipmi.ovh.net', username='ipmi', pkey=sshkey)
remote_con = ssh.invoke_shell()
stdin = remote_con.makefile('wb')
stdout = remote_con.makefile('rb')
stdin.write('\r\n')
kbd.release(Key.enter)
ignore_start = 424
# We ignore a few bytes before the bios is really displayed.
# We don't trash it, as it can probably be used to detect display type
# I hope every lanplus display in the same manner
trash = stdout.read(ignore_start)
page = stdout.read(6034)  # Todo: value is almost one page, need to be corrected
onepage = page
# Should be 80 characters * 24 lines
# If reading line per line, it's 80 bytes buffer
# onepage is binary, we need ascii to do str handling
onepage = onepage.decode('ascii')
onepage = onepage.split('\x1b[19;80H\x1b[0m\x1b[37m\x1b[40m\x1b[1m\x1b[37m\x1b[44m\x1b[01;')[1]
# We split the end of a page, because on some pages the SoL refresh the page once per second, making paramiko receive some data from the previous refresh
# This ensure that we work on a full page, not a partial + full page + another partial page due to the larger read buffer to compensate for that refresh

pagelist = onepage.split('\x1b')
# ssh.close()
almost_clean = []
number_to_name_and_values = {}
dict_association = {}
for each in pagelist:
    almost_clean.append(each.split('H'))
for each in almost_clean:
    for entry in each:
        if re.search(r'[0-9]{2}', entry):
            if ';04' in entry:  # each list has a lenght of 2
                lineid = re.search(r'[0-9]{2}', entry)
                lineid = lineid.group()
                position = entry[0].split(';')  # There is an [ in the first number, stripping it
                try:
                    if len(number_to_name_and_values[lineid]) <= 2:
                        number_to_name_and_values[lineid].append(['0|'+each[1]])
                except KeyError:
                    print('keyerror')
                    number_to_name_and_values[lineid] = (['0|'+each[1]])
            if ';31' in entry:
                print('in ;31 anyways')
                lineid = re.search(r'[0-9]{2}', entry)
                lineid = lineid.group()
                try:
                    if len(number_to_name_and_values[lineid]) <= 2:
                        number_to_name_and_values[lineid].append(['1|'+each[1]])
                        # Sometimes entries are in reverse order, we need to put
                        # it back in the correct order
                except KeyError:
                    number_to_name_and_values[lineid] = (['1|'+each[1]])
for key in number_to_name_and_values:
    if number_to_name_and_values[key][0].startswith('1|'):
        newkey = number_to_name_and_values[key][1][0]
        newkey = newkey.strip('0|')
        value = number_to_name_and_values[key][0]
        value = value.strip('1|')
        dict_association[newkey] = value
    else:
        if len(number_to_name_and_values[key]) == 2:
            # Some picked up entry are just title with no values
            newkey = number_to_name_and_values[key][0]
            newkey = newkey.strip('0|')
            value = number_to_name_and_values[key][1][0]
            value = value.strip('1|')
            dict_association[newkey] = value
print(dict_association)

ssh.close()
