from  waitress import serve
    
from myback.wsgi import application
    
if __name__ == '__main__':
    serve(application, host='192.168.5.23', port=80)