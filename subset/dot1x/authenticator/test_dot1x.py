import sys

write_file = sys.argv[1]
print('Writing to file %s' % write_file)
result ='Authentication for <mac> successful.'
with open(write_file,  'w') as w_file:
    w_file.write(result)
