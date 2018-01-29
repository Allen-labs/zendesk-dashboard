# _______________________________________________________________
# |  File Name: urls.py                                         |
# |                                                             |
# | Software: Openstack Horizon Dashboard ['liberty']          |
# |_____________________________________________________________|
# |                                                             |
# | Dashboard Name: zendesksupport                             |
# |                                                             |
# | Copyright: 2016@nephoscale.com                              |
# |_____________________________________________________________|
from django.conf.urls import patterns
from django.conf.urls import url
from openstack_dashboard.dashboards.zendesksupport.tickets import views

urlpatterns = patterns(
    '',
    url(r'^$',                      views.IndexView.as_view(),        name='index'),
    url(r'^create_ticket/$',        views.CreateTicketView.as_view(), name='create_ticket'),
    url(r'^(?P<ticket_id>[^/]+)/$', views.get_ticket_detail,          name="ticket_detail")
)

