while True:
    user_input = input('Give the file name: ')

    try:
        with open(user_input, 'r') as file:
            file_content = file.read()
        

        try:
            result = int(file_content) / 1000
            print('The result was', result)
        except Exception:
            print('The file contents were unsuitable.')
    except Exception:
        print('There seems to be no file with that name.')
        
    


        