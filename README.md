# Django app for Open Education Week

Notes:

* Images are hosted through the Internet Archive. Images for OE Week 2022 are uploaded to https://archive.org/upload/?identifier=oeweek2022 -> and available via https://archive.org/download/oeweek2022/MYFILENAME.png
  * or uploaded during submission process

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


## Deployment

see [README in ansible subdirectory](ansible/README.md)
