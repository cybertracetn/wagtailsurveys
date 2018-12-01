from django.conf.urls import include, url
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.core import hooks
from wagtail.admin.menu import MenuItem

from wagtailsurveys import admin_urls
from wagtailsurveys.models import get_surveys_for_user


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^surveys/', include(admin_urls, namespace='wagtailsurveys')),
    ]


class SurveysMenuItem(MenuItem):
    def is_shown(self, request):
        # show this only if the user has permission to retrieve submissions for at least one form
        return get_surveys_for_user(request.user).exists()


@hooks.register('register_admin_menu_item')
def register_surveys_menu_item():
    return SurveysMenuItem(
        _('Surveys'),
        reverse('wagtailsurveys:index'),
        name='surveys',
        classnames='icon icon-group',
        order=300
    )
