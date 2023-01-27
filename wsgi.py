"""
WSGI config for myback project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
import sys

import site

sys.path.append('C:/myback_dev/myback')
sys.path.append('C:/myback_dev/myback/serviceback')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myback.settings')
os.environ['DJANGO_SETTINGS_MODULE'] = 'myback.settings'
application = get_wsgi_application()



# import sys

# def application(environ, start_response):
#     status = '200 OK'
#     output = b'Hello World!'

#     response_headers = [('Content-type', 'text/plain'),
#                         ('Content-Length', str(len(output)))]
#     start_response(status, response_headers)


#     return [output]