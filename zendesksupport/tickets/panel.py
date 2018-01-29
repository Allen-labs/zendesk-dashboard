# File Name: panel.py
#
# Software: Openstack Horizon [liberty]
#
# Dashboard Name: Customer Support
#
# Panel Name: tickets
#
# Start Date: 2016@nephoscale.com

from django.utils.translation import ugettext_lazy as _
from openstack_dashboard.dashboards.zendesksupport import dashboard
import horizon

class Tickets(horizon.Panel):
    name = _("Tickets")
    slug = "tickets"
dashboard.ZendeskSupportDashboard.register(Tickets)

