{% extends "mail_templated/base.tpl" %}

{% block subject %}
Your OE Week contribution is featured on the website!
{% endblock %}

{% block body %}
Dear {{ firstname }},

We appreciate your support and contribution to the Open Education Week.  Your entry "{{ title }}" has been approved and will be featured on the OE Week website ( https://oeweek.oeglobal.org ).

You may find it here:  https://oeweek.oeglobal.org/{{ slug1 }}/{{ year }}/{{ slug2 }}/

Please take a minute to review the information. If you have any questions or need to make changes or updates to your contribution, please notify us at info@openeducationweek.org

As you get ready for OEWeek …

Don’t forget to take advantage of the promotional kit available for download, reuse, remix, and redistribution here (  https://bit.ly/OEW22_materials ). These OEWeek-branded materials can help you to promote your own event. You’ll also find the official OEWeek Badge for your website.

Discuss all things Open Education and #oeweek highlights in OEG Connect at ( https://connect.oeglobal.org/c/oeweek/33 ). )! If you don’t have an account yet, join here: https://connect.oeglobal.org/invites/jTtdVe5Qsx .

Get social … Open Education Week is a global effort built on everyone’s contributions. Follow #OEWeek on social media to get updates!

• Twitter: https://twitter.com/OEWeek
• Facebook: https://www.facebook.com/openeducationwk

Open Education Week is a global effort built on everyone’s contributions. Please visit the website ( https://oeweek.oeglobal.org ) regularly for the latest updates, and join in on other events where you can! Check your inbox for email updates!

Thank you for joining us to make this 10 year anniversary a global celebration of the Open Education Movement. We look forward to seeing you throughout the week.

Many thanks,

The Open Education Week Planning Committee
#oeweek
{% endblock %}
