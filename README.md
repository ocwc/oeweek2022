# Django app for Open Education Week

## Installation / deployment

See [README in ansible subdirectory](ansible/README.md) (need to `apt install` several packages for the screenshot functionality to work -- without it, the installation will crash).

### Special case: front-end only

In case you are going to do only local development focused on front-end (e.g. no need for scheduled tasks like screenshot fetching. etc.)
then above mentioned `ansible/README.md` still applies but:

* `localsettings.py`: add following

```
FE_DEPLOYMENT = True
```

* `pip install -r requirements.txt`: do following instead after `BASE_DIR = ...`

```
pip install -r requirements-fe.txt
```

The rest should be the same.

## Notes

* In 2022, images were hosted through the Internet Archive and were uploaded to https://archive.org/upload/?identifier=oeweek2022 -> and available via https://archive.org/download/oeweek2022/MYFILENAME.png

* Starting with 2023, images can be uploaded as a part of the submission process or created using

* debug with local server ```DEBUG=True python manage.py runserver 4201 --insecure```

* no debug with local server: ```python manage.py runserver 4201 --insecure```

## Development

Branches, pull-requests, releases, etc.: according to [git-flow](http://danielkummer.github.io/git-flow-cheatsheet/) but ...

... in order to allow better overview for current and future contributors, we'd like to conclude features with pull-requests,
i.e. instead of `git flow feature finish MYFEATURE` do following:

1. `git flow feature publish MYFEATURE`
2. go to GitLab/GitHub and open pull-request from your feature branch to `develop`
3. review + adjustments
4. merge + delete branch after merge

### Git hooks

For source code formatting, etc.:

`pre-commit install`

