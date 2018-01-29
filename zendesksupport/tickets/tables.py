# File Name: tables.py
#
# Package Name: Openstack Horizon [liberty]
#
# Dashboard:  zendesksupport
#
# Start Date: July 14th, 2016
#
# Copyright: 2016@nephoscale.com
from django.utils.translation import ugettext_lazy as _
from horizon import tables
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.safestring import mark_safe

class CreateTicketAction(tables.LinkAction):
    name = "create_ticket"
    verbose_name = _("Create Ticket")
    url = reverse_lazy("horizon:zendesk_support_dashboard:tickets:create_ticket")
    classes = ("ajax-modal", "btn-primary")
    icon = "envelope"


def transform_status(ticket):
    """
    # | Function to transform the status to uppercase
    # | 
    # | Ticket object
    # |
    # | Returns string
    """
    if not ticket.status:
        return '-'
    return str(ticket.status).upper()

def transform_priority(ticket):
    """
    # | Transforming the priority trext into uppercase
    # |
    # | Argument: Ticket Object
    # |
    # | Returns String
    """
    if not ticket.priority:
        return '-'
    return str(ticket.priority).upper()

def transform_created_at(ticket):
    """
    # | Transforming the created_at date
    # |
    # | Arguments: Ticket Object
    # |
    # | Returns the string
    """
    return mark_safe('<span style="cursor:pointer;" title="' + ticket.formatted_created_at + '">' + ticket.formatted_created_at_str + '</span>')


def transform_updated_at(ticket):
     """
     # | Transforming the updated_at date
     # |
     # | Arguments: Ticket Object
     # |
     # | Returns the string
     """
     return mark_safe('<span style="cursor:pointer;" title="' + ticket.formatted_updated_at + '">' + ticket.formatted_updated_at_str + '</span>')


class TicketFilterAction(tables.FilterAction):
    """
    # | Class to filtering the tickets
    """
    name = "ticketfilter"
    filter_type = "server"
    verbose_name = _("Filter Tickets")
    needs_preloading = True
    filter_choices = (("subject", _("Subject contains "), True),
                     ('priority', _("Priority ="),        True),
                     ('status',   _("Status ="),          True))

class TicketListTable(tables.DataTable):
    """ 
    TABLE TO LIST THE TICKETS
    """
    subject = tables.Column(
        'subject',
        verbose_name=_("Subject"),
        link=lambda obj: reverse('horizon:zendesk_support_dashboard:tickets:ticket_detail', args=[obj.id]),
        sortable = True
    )
    status     = tables.Column(transform_status,     verbose_name=_("Status"),       sortable=True)
    priority   = tables.Column(transform_priority,   verbose_name=_("Priority"),     sortable=True)
    created_at = tables.Column(transform_created_at, verbose_name=_("Created At"),   sortable=True)
    updated_on = tables.Column(transform_updated_at, verbose_name=_('Last Updated'), sortable=True)

    class Meta:
        name = "tickets"
        verbose_name = _("My Tickets")
        table_actions = (CreateTicketAction,TicketFilterAction)

