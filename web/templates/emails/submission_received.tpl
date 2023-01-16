{# deprecated, see web.model.EmailNotificationText => TODO: remove #}

{% extends "mail_templated/base.tpl" %}

{% block subject %}
OE Week submission received
{% endblock %}

{% block body %}
Dear Open Education Week Collaborator,

We appreciate your contribution to Open Education Week (OE Week).  Your entry has been received and will be reviewed shortly by the OE Week Planning Committee.  We will notify you when your submission is approved and posted to the website. If you have questions, please reply to this message.

If you'd like to edit your entry, "{{ title }}", you can do so here: https://oeweek.oeglobal.org/edit/{{ uuid }}/

Open Education Week is a global effort built on everyone's contributions.  Please visit the website ( https://www.openeducationweek.org ) regularly for the latest updates and additions to the event.  Take advantage of the promotional materials available for you to download, reuse, remix, and redistributie to promote your own activities and events.

This year we invite you to share your OE Week experiences, curate resources, and participate in discussions in our OEG Connect community space for the event at https://connect.oeglobal.org/c/oeweek/33
If you have not created an account here we offer a unique invitation link so you can join https://connect.oeglobal.org/invites/jTtdVe5Qsx

Once again thank you for helping us make this event a global celebration of the Open Education movement. We look forward to seeing your participation throughout the week.

Many thanks,

Open Education Week Planning Committee
#OEWeek

{% endblock %}
