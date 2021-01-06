import requests
from celery import shared_task

from managebook.models import User
from managebook.utils import GitAuth


@shared_task
def refresh_git_reps_num():
    all_users = User.objects.all()
    for user in all_users:
        user.git_repos_num = GitAuth(user.git_username)
    User.objects.bulk_update(all_users, ['git_repos_num'])
