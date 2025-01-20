from sys import argv

if __name__ == '__main__':
    if len(argv) < 2:
        print('Usage: python main.py <instance>')
        exit(1)
    
    instance = argv[1]
    
    print(instance)