import re
import sys

from pynput.keyboard import Key, Controller
import paramiko
from time import sleep
# This code was tested on ns3104631 (rise 1) with intel motherboard
# At this stage, no guarantees that it will work elsewere, this is a PoC/PoV


# onepage is binary, we need ascii to do str handling

# We split the end of a page, because on some pages the SoL refresh the page
# once per second, making paramiko receive some data from the previous refresh
# This ensure that we work on a full page, not a partial + full page + another
# partial page due to the larger read buffer to compensate for that refresh
def page_process(page, stdin, stdout):
    stdin.write(b'\x1b[')
    sleep(3) # Because internet at home is slow.
    stdin.write('\r\n')
    if len(page) == 0:
        number_to_name_and_values = {}
        dict_association = {}
        page = stdout.read(6034)
        onepage = page
        onepage = onepage.split(
            b'\x1b[0m\x1b[37m\x1b[40m\x1b[1m\x1b[37m\x1b[44m\x1b[01;')
        try:
            onepage = onepage[1]
        except:
            pass
        onepage = onepage.decode('ascii')

    while onepage.find('\x1b[20;56Hv') >= 1:
        # \x1b[20;56Hv is the ansi code for a red v on the page, meaning we can scroll
        # We scroll after the first processing because we want all options in a page
        # We split and convert again only after the first data buffer reception

        # Should be 80 characters * 24 lines
        # onepage is binary, we need ascii to do str handling
        pagelist = onepage.split('\x1b')
        for each in pagelist:
            almost_clean.append(each.split('H'))
        for each in almost_clean:
            for entry in each:
                if re.search(r'[0-9]{2}', entry):
                    if ';04' in entry:  # each list has a lenght of 2
                        lineid = re.search(r'[0-9]{2}', entry)
                        lineid = lineid.group()
                        position = entry.split(
                            ';')  # There is an [ in the first number, stripping it
                        try:
                            if len(number_to_name_and_values[lineid]) <= 2:
                                number_to_name_and_values[lineid].append(
                                    ['0|' + each[1]])
                        except KeyError:
                            number_to_name_and_values[lineid] = (['0|' + each[1]])
                    if ';31' in entry:
                        lineid = re.search(r'[0-9]{2}', entry)
                        lineid = lineid.group()
                        try:
                            if len(number_to_name_and_values[lineid]) <= 2:
                                number_to_name_and_values[lineid].append(
                                    ['1|' + each[1]])
                                # Sometimes entries are in reverse order, we need to put
                                # it back in the correct order
                        except KeyError:
                            number_to_name_and_values[lineid] = (['1|' + each[1]])
                        except:
                            print(sys.exc_info())
        stdin.write(b'\x1b[B')
        stdin.write('a')
        page = stdout.read(6034)
        onepage = page
        onepage = onepage.split(
            b'\x1b[0m\x1b[37m\x1b[40m\x1b[1m\x1b[37m\x1b[44m\x1b[01;')
        # We split the end of the page to get right one page, no more, no less
        try:
            # In some case, the list is len 1, then we don't need to split it
            onepage = onepage[1]
        except:
            onepage = onepage[0]
        onepage = onepage.decode('ascii')
        sleep(0.5)
    for key in number_to_name_and_values:
        if len(number_to_name_and_values[key]) >2:
            number_to_name_and_values[key].pop(2)
        if number_to_name_and_values[key][0].startswith('1|'):
            newkey = number_to_name_and_values[key][1][0]
            newkey = newkey.strip('0|')
            value = number_to_name_and_values[key][0]
            value = value.strip('1|')
            try:
                dict_association[newkey] = value
            except:
                print(sys.exc_info())
        if len(number_to_name_and_values[key]) == 2:
            # Some picked up entry are just title with no values
            newkey = number_to_name_and_values[key][0]
            newkey = newkey.strip('0|')
            value = number_to_name_and_values[key][1][0]
            value = value.strip('1|')
            try:
                dict_association[newkey] = value
            except:
                print(sys.exc_info())
    stdin.write(b'\x1b[')
    stdin.write('\r\n')
    return dict_association
if __name__ == "__main__" :
    ssh = paramiko.SSHClient()
    sshkey = paramiko.RSAKey.from_private_key_file('/path/to/key',
                                                   password='key_password')
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kbd = Controller()
    ssh.connect('1.sol-ssh.ipmi.ovh.net', username='ipmi', pkey=sshkey)
    remote_con = ssh.invoke_shell()
    stdin = remote_con.makefile('wb')
    stdout = remote_con.makefile('rb')
    stdin.write(b'\x1b[')
    sleep(3)
    stdin.write('\r\n')
    kbd.release(Key.enter)
    ignore_start = 424
    # We ignore a few bytes before the bios is really displayed,
    # OVH and lanplus banner.
    # We don't trash it, as it can probably be used to detect display type
    # I hope every lanplus display react in the same manner
    trash = stdout.read(ignore_start)
    if trash.find(b'error') >=1:
        print(trash)
        sys.exit(1)
    almost_clean = []
    page = ''
    result_dict = page_process(page, stdin, stdout)
    # Cleaning dict at the very last
    final_dict = {}
    for i, (key, value) in enumerate(result_dict.items()):
        if key[1:2] != '|':
            key = key.strip(' ')
            if value[1:2] != '|':
                value = value.strip(' ')
                final_dict[key] = value
    print(final_dict)
    ssh.close()
