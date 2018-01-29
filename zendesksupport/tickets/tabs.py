# File Name: tabs.py
#
# @Software: Openstack Horizon
#
# @version: Liberty
#
# @Package: zendesksupport
#
# Start Date: 14th July 2016
from django.utils.translation import ugettext_lazy as _
from horizon import tabs, exceptions, forms
from openstack_dashboard.dashboards.zendesksupport.tickets import tables
from django.core.urlresolvers import reverse_lazy, reverse
from horizon.utils import memoized
from openstack_dashboard.dashboards.zendesksupport.tickets import forms as ticket_form
from openstack_dashboard.dashboards.zendesksupport import api as zendesk_api
from django.conf import settings

class TicketListingTab(tabs.TableTab):
    """
    Class to handel the zendeskticket listing
    """
    name = _("My Tickets Tab")
    slug = "my_tickets"
    table_classes = (tables.TicketListTable, )
    template_name = ("horizon/common/_detail_table.html")
    preload = False
    _has_more_data = False
    _has_prev_data = False

    def get_tickets_data(self):
        """
        # | Function to get the ticket list for the given user
        # |
        # | @Arguments: None
        # |
        # | @Return Type: Dictionary
        """
        try:
            field_name = self.request.POST.get("tickets__ticketfilter__q_field", "")
            subject = status = priority = updated_at = created_at = None
            if field_name == "subject":
                subject = self.request.POST['tickets__ticketfilter__q']
            if field_name == 'priority':
                priority = self.request.POST['tickets__ticketfilter__q']
            if field_name == "status":
                status = self.request.POST['tickets__ticketfilter__q']

            search_query = {}

            # Prepare the search query
            if subject:
                search_query['subject'] = subject
            if priority:
                search_query['priority'] = str(priority).lower()
            if status:
                search_query['status'] = str(status).lower()

            zendesk = zendesk_api.Zendesk(self.request)
            tickets = zendesk.list_tickets(search_query)
            return tickets['tickets']
        except zendesk_api.ZendeskError as e:
            if e.code == 403:
                exceptions.handle(self.request, "It seems you do not have email address registered. Please update your profile.")
                return []
            else:
                exceptions.handle(self.request, "Unable to fetch tickets.")
                return []
        except Exception as err:
            error_message = _(str(err))
            exceptions.handle(self.request, error_message)
            return []

class MyTicketsTab(tabs.TabGroup):
    slug = "mytickets_tab"
    tabs = (TicketListingTab,)
    sticky = True

