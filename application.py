import os
from os import environ
from FlaskWebProject import app

if __name__ == '__main__':
    # Force OAuth to work over local self-signed HTTPS
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    # debug=True is CRITICAL to see the real error message
    app.run(host=HOST, port=PORT, ssl_context='adhoc', debug=True)