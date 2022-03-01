{% extends "mail_templated/base.tpl" %}

{% block subject %}
Your OE Week submission is featured on the website!
{% endblock %}

{% block body %}
Dear {{ firstname }},

We appreciate your support and contribution to the Open Education Week.  Your entry "{{ title }}" has been approved and will be featured on the OE Week website ( https://oeweek.oeglobal.org ).

You may find it here:  https://oeweek.oeglobal.org/{{ year }}/{{ slug }}/

Please take a minute to review the information. If you have any questions or need to make changes or updates to your submission, please notify us at info@openeducationweek.org

As you get ready for OEWeek …

Don’t forget to take advantage of the promotional kit available for download, reuse, remix, and redistribution to promote your own events and to promote Open Education Week. Here you’ll find the official OEWeek Badge to display on your website.

Discuss all things Open Education and #oeweek highlights in OEG Connect at ( https://connect.oeglobal.org/c/oeweek/33 )! and look out for email updates on the OEWeek activities around the world! If you don’t have an account yet, join here: https://connect.oeglobal.org/invites/jTtdVe5Qsx

Get social … Open Education Week is a global effort built on everyone’s contributions. Follow #OEWeek on social media to get updates!

• Twitter: https://twitter.com/OEWeek
• Facebook: https://www.facebook.com/openeducationwk

Open Education Week is a global effort built on everyone’s contributions. Please visit the website ( https://www.openeducationweek.org ) regularly for the latest updates, and join in on other events where you can!

Thank you for joining us to make this 10 year anniversary a global celebration of the Open Education Movement. We look forward to seeing you throughout the week.

Many thanks,

The Open Education Week Planning Committee
#oeweek
{% endblock %}
