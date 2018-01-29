# File Name: dashboard.py
#
# Software: Openstack Horizon [liberty]
#
# Start Date: 14th July 2016
#
# Copyright: 2016@nephoscale.com

from django.utils.translation import ugettext_lazy as _
import horizon

class ZendeskSupportDashboard(horizon.Dashboard):
    """ 
    Class to register the Customer Support dashboard to horizon
    """
    name   = _("Customer Support")
    slug   = "zendesk_support_dashboard"
    panels = ('tickets',) 
    default_panel = 'tickets'

horizon.register(ZendeskSupportDashboard)

