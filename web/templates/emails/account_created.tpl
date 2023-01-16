{# deprecated, see web.model.EmailNotificationText => TODO: remove #}

{% extends "mail_templated/base.tpl" %}

{% block subject %}
OEW: Your account to edit submission(s)
{% endblock %}

{% block body %}
Dear OEW Collaborator,

Please click on the following link to login and edit your submissions to Open Education Week:

https://www.openeducationweek.org/user-login/?user={{user.username}}&key={{key}}


Many thanks,
OEW Planning Committee

{% endblock %}
