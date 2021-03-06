from celery import Celery
from django.db import IntegrityError
from github3 import login
import requests

from .celery import app
from .models import Repo

from django.conf import settings


@app.task
def acquire_github_token_task(code, state):
    """
    Given a temporary Github code and the OAuth flow state token, get
    an access token and persist it with the correct repos.
    """
    response = requests.post(
        settings.GITHUB_OAUTH_TOKEN_URL,
        headers={'accept': 'application/json'},
        data={
            'client_id': settings.GITHUB_OAUTH_CLIENT_ID,
            'client_secret': settings.GITHUB_OAUTH_CLIENT_SECRET,
            'code': code,
            'redirect_uri': '',
            'state': state
        }
    )
    print response.status_code
    print response.content
    access_token = response.json()['access_token']
    gh = login(token=access_token)
    for repo in gh.iter_user_repos(gh.user().login, 'owner'):
        full_name = repo.full_name
        try:
            Repo.objects.create(access_token=access_token, full_name=full_name)
        except IntegrityError:
            print('Repo {full_name} already has an access token!'.format(full_name=full_name))
