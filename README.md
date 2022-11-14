# Django app for Open Education Week

Notes:

* Images are hosted through the Internet Archive. Images for OE Week 2022 are uploaded to https://archive.org/upload/?identifier=oeweek2022 -> and available via https://archive.org/download/oeweek2022/MYFILENAME.png

* debug with local server ```DEBUG=True python manage.py runserver 4201 --insecure```

* no debug with local server: ```python manage.py runserver 4201 --insecure```


## Development

Branches, pull-requests, releases, etc.: according to [git-flow](http://danielkummer.github.io/git-flow-cheatsheet/)


### Git hooks

For source code formatting, etc.:

`pre-commit install`


## Deployment

see [README in ansible subdirectory](ansible/README.md)
