import requests
from celery import shared_task

from bookshop.settings import GIT_CLIENT_ID, GIT_CLIENT_SECRET, GIT_REDIRECT_URI
from managebook.models import User


@shared_task
def refresh_git_reps_num():
    url = f'https://github.com/login/oauth/access_token?client_id={GIT_CLIENT_ID}&client_secret={GIT_CLIENT_SECRET}&code={code}&redirect_uri={GIT_REDIRECT_URI}'
    data = requests.post(url)
    access_token = data.text.split("&")[0].split("=")[1]
    response = requests.get("https://api.github.com/user",
                            headers={
                                'Authorization': f'token {access_token}',
                                'Accept': 'application/json'
                            })
    login = response.json()['login']
    if login in User.git_username:
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
