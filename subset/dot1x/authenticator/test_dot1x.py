import sys


def main():
    write_file = sys.argv[1]
    result ='Authentication for <mac> successful.'
    with open(write_file,  'w') as w_file:
        w_file.write(result)


if __name__ == '__main__':
    main()
