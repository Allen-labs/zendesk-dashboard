# _______________________________________________________________________
# | File Name: forms.py                                                 |
# |                                                                     |
# | This file is for handling the forms of zendesk support              |
# |_____________________________________________________________________|
# | Start Date: July 7th, 2016                                          |
# |                                                                     |
# | Package: Openstack Horizon Dashboard [liberty]                     |
# |                                                                     |
# | Copy Right: 2016@nephoscale                                         |
# |_____________________________________________________________________|

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django  import forms as django_forms
from horizon import exceptions
from horizon import forms
from openstack_dashboard.dashboards.zendesksupport import api as zendesk_api
from django.shortcuts import render, redirect
from openstack_dashboard import api
from keystoneclient.v2_0 import client as kclient_v2
from keystoneclient.v3 import client as kclient_v3
from keystoneauth1 import identity
from keystoneauth1 import session
from django.conf import settings
from keystoneclient.v2_0.tenants import Tenant
import os
from django.core.files.base import ContentFile

#Setting the ticket priority choices
TICKET_PRIORITY_CHOICES = (
    ('low',    'Low'),
    ('normal', 'Normal'),
    ('high',   'High'),
    ('urgent', 'Urgent')
)

# Checking the auth version
keystone_auth_version = getattr(settings, 'KEYSTONE_AUTH_VERSION', 'v2.0')

#Creating Keystone connections based on the version
if keystone_auth_version == 'v3':
    kwargs = {
        "project_name":           getattr(settings, 'KEYSTONE_ADMIN_PROJECT_NAME', ''),
        "project_domain_name":    getattr(settings, 'KEYSTONE_ADMIN_PROJECT_DOMAIN_NAME', ''),
        "username":           getattr(settings, 'KEYSTONE_ADMIN_USERNAME', ''),
        "user_domain_name":    getattr(settings, 'KEYSTONE_ADMIN_USER_DOMAIN_NAME', ''),
        "auth_url":            getattr(settings, 'KEYSTONE_ADMIN_AUTH_URL', ''),
        "password":            getattr(settings, 'KEYSTONE_ADMIN_PASSWORD', ''),
    }

    auth = identity.v3.Password(**kwargs)
    sess = session.Session(auth=auth)
    keystone = kclient_v3.Client(session=sess)  
    tenantVal = 'default_project_id'
    
else:
    kwargs = {
        "username":    getattr(settings, "KEYSTONE_ADMIN_USERNAME"),
        "password":    getattr(settings, "KEYSTONE_ADMIN_PASSWORD"),
        "auth_url":    getattr(settings, "KEYSTONE_ADMIN_AUTH_URL"),
        "tenant_name": getattr(settings, "KEYSTONE_ADMIN_TENANT_NAME"),
    }
    
    auth = identity.v2.Password(**kwargs)
    sess = session.Session(auth=auth)
    keystone = kclient_v2.Client(session=sess)
    tenantVal = 'tenantId'

class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)

        # Populate project choices
        user_choices = []
        
        #Initializing
        role_check = False
        # If the user is already set (update action), list only projects which
        # the user has access to.
        try:

            # Getting the user list
            users = keystone.users.list()
            for user in users:

                # checking the tenant id and the user id values to verify the role of permission               
                if hasattr(user, tenantVal):
                    if  user.id == request.user.id:
                        try:                         
                            if keystone_auth_version == 'v3':
                                
                                # Getting the role of user
                                roles = keystone.roles.list(user=user.id, project=user.default_project_id)
                            else:
                                
                                # Getting the role of user
                                roles = keystone.roles.roles_for_user(user=user.id, tenant=user.tenantId)
                                      
                            # Getting the role which have the create permission
                            # set_role = getattr(settings, 'ZENDESK_ROLE', 'admin')
                            set_role = ['admin', 'service']
                            for role in roles:
                                if role.name in set_role:
                                    role_check = True
                        except Exception, e:
                            print 'error in the role for user', e

                # Checking the user have email
                has_email = hasattr(user, 'email')
                if user.enabled and user.id != request.user.id and has_email:
                
                    # Only users with an email will be listed in the dropdown
                    if (getattr(user, 'email') != '') and (getattr(user, 'email') is not None):
                        
                        # Creating the dropdown value (user id, email and name)
                        user_value = str(user.id) + '--' + str(user.email) + '--' + str(user.name)
                        user_choices.append((user_value, user.name))
                
            # to show the drop down first element.
            if not user_choices:
                user_choices.insert(0, ('', _("No available users")))
                self.fields['user'].widget = forms.HiddenInput()
            elif len(user_choices) > 1:
                user_choices.insert(0, ('', _("Select a user")))
        except Exception, e:
            
            # Hidding the user field for the users
            self.fields['user'].widget = forms.HiddenInput()
            user_choices.insert(0, ('', _("No available users")))
        self.fields['user'].choices = user_choices
        if role_check == False:
            self.fields['user'].widget = forms.HiddenInput()
 

class CreateTicketForm(BaseUserForm):
    """
    # | Form Class to handel the ticket create form
    """
    
    #Creating the fields
    subject     = forms.CharField(  label=_("Subject of your issue"), required=True,  widget=forms.TextInput)
    priority    = forms.ChoiceField(label=_("Priority"),              required=True,  widget=forms.Select,   choices=TICKET_PRIORITY_CHOICES)
    description = forms.CharField(  label=_("Describe your issue"),   required=True,  widget=forms.Textarea ) 
    attachments = forms.FileField(  label=_("Attachments"),           required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user = forms.DynamicChoiceField(label=_("User list"), required=False,)

    def handle(self, request, data):
        """ 
        * Form to handle the create ticket request
        *
        * @Arguments:
        *   <request>: Request object
        *   <data>:    Data containg form data
        """
        subject     = data['subject']
        description = data['description']
        priority    = data['priority']
        user        = data['user']
        files       = request.FILES.getlist('attachments')

        folder    = 'zendesk_user_uploads'
        BASE_PATH = '/tmp/'

        #Initializing     
        attachment_list = []

        #Create the folder if it doesn't exist.
        try:
            os.mkdir(os.path.join(BASE_PATH, folder))
        except:
            pass

        #Looping through each file
        for file in files:
            uploaded_filename = file.name
            full_filename = os.path.join(BASE_PATH, folder, uploaded_filename)
            fout = open(full_filename, 'wb+')
            file_content = ContentFile(file.read())
                
            #Iterate through the chunks.
            for chunk in file_content.chunks():
               fout.write(chunk)
            fout.close()
            
            #Inserting the files to list
            attachment_list.append(str(full_filename))
        
        zenpy_obj = zendesk_api.Zendesk(request)

        # Okay, now we need to call our zenpy to create the 
        # ticket, with admin credential, on behalf of user
        try:
            zendesk = zendesk_api.Zendesk(self.request)

            #Setting the data to be passed for ticket creation
            api_data = {
                "subject": subject,
                "priority": priority,
                "description": description,
                "user": user
            }
            
            #Calling the method to create the tickets
            ticket_audit = zendesk.create_ticket(api_data, request)           
            ticket = ticket_audit.ticket

            #Enter loop only if attachments are present during ticket creation
            if attachment_list:
                
                #Get the count of attachments
                attachment_count = len(attachment_list)
                
                #Create an automated comment for adding the attachments 
                #(Only in the case of attachments added during initial ticket creation step)
                zendesk.create_comment(ticket.id, 'User has added %s attachments with this ticket.' % attachment_count, True, attachment_list)
            
            return redirect(reverse_lazy("horizon:zendesk_support_dashboard:tickets:ticket_detail", args=[ticket.id]))
        except Exception as err:
            error_message = _(str(err))
            exceptions.handle(request, error_message)
            return []

class AddCommentForm(django_forms.Form):
    """
    | * Class to add the comments to thye tickets
    """
    comment = forms.CharField(label = _('Add Comment'), required=True, widget=forms.TextInput)

