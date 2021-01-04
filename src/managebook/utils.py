import json
import requests
import webbrowser
import base64
from bookshop.settings import XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_SCOPE, XERO_REDIRECT_URL, GIT_CLIENT_ID, \
    GIT_CLIENT_SECRET, GIT_REDIRECT_URI, GIT_SCOPE

b64_id_secret = base64.b64encode(bytes(XERO_CLIENT_ID + ':' + XERO_CLIENT_SECRET, 'utf-8')).decode('utf-8')


def XeroFirstAuth():
    # 1. Send a user to authorize your app
    auth_url = ('''https://login.xero.com/identity/connect/authorize?''' +
                '''response_type=code''' +
                '''&client_id=''' + XERO_CLIENT_ID +
                '''&redirect_uri=''' + XERO_REDIRECT_URL +
                '''&scope=''' + XERO_SCOPE +
                '''&state=123''')
    webbrowser.open_new(auth_url)

    # 2. Users are redirected back to you with a code
    auth_res_url = input('What is the response URL? ')
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    print(auth_code)
    print('\n')

    # 3. Exchange the code
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url,
                             headers={
                                 'Authorization': 'Basic ' + b64_id_secret
                             },
                             data={
                                 'grant_type': 'authorization_code',
                                 'code': auth_code,
                                 'redirect_uri': XERO_REDIRECT_URL
                             })
    json_response = response.json()
    print(json_response)
    print('\n')

    # 4. Receive your tokens
    return [json_response['access_token'], json_response['refresh_token']]


def GitAuth(code):
    url = f'https://github.com/login/oauth/access_token?client_id={GIT_CLIENT_ID}&client_secret={GIT_CLIENT_SECRET}&code={code}&redirect_uri={GIT_REDIRECT_URI}'
    data = requests.post(url)
    access_token = data.text.split("&")[0].split("=")[1]
    response = requests.get("https://api.github.com/user",
                            headers={
                                'Authorization': f'token {access_token}',
                                'Accept': 'application/json'
                            })
    login = response.json()['login']
    data = requests.get(f'https://api.github.com/users/{login}/repos?page=1')
    rep_num = len(data.json())
    total_rep_num = rep_num
    page_num = 2
    while rep_num == 30:
        data = requests.get(f'https://api.github.com/users/{login}/repos?page={page_num}')
        page_num += 1
        rep_num = len(data.json())
        total_rep_num += rep_num
    return total_rep_num
