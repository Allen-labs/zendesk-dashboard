# File Name:api.py
#
# This file is for connection to zenpy module.
#
# Copyright: 2016@nephoscale
#
# Start date: July 14th, 2016
#
# Dependancies:
#   zenpy:
#         Github:  https://github.com/facetoe/zenpy
#         Python: pip install zenpy
#   ndg-httpsclient:
#         pip install ndg-httpsclient

from   keystoneauth1          import identity
from   keystoneauth1          import session
from   zenpy.lib.api_objects  import Ticket, User, Comment, Attachment
from   zenpy.lib.exception    import APIException, RecordNotFoundException
from   django.conf            import settings
import keystoneclient
import logging as LOG

try:
    import json
except:
    import simlejson as json
import zenpy
import random, string
import pytz, tzlocal, datetime
import urllib

import os
class Zendesk:
    """ 
    Class which will be used to integrate with horizon
    """
    _request = _ks_user = _zenpy = _ks_tenant = _zendesk_admin = None
 
    def __init__(self, request):
        """ 
        # | Init function to configure the object
        # |
        # | @Arguments:
        # |    <ks_usher_id>: Keystone user id
        """
        
        #Checking the auth version and calling the create token method accordingly
        keystone_auth_version = getattr(settings, 'KEYSTONE_AUTH_VERSION', 'v3')        
        try:
            if keystone_auth_version == 'v3':
                self.keystone = self._manageV3(request)
            else:
                self.keystone = self._manageV2(request)
            self._request = request
        except Exception as e:
            LOG.error(str(e))
            if hasattr(e, 'http_status'):
                if e.http_status == 401:
                    raise ZendeskError(401, "Unable to login to horizon as admin.")
                if e.http_status == 404:
                    raise ZendeskError(404, "No user found in keystone with id " + keystone_user_id)

                # If some other error occured, then throw exception as unknown error
                # Because these errors are not relavant to the end user.
                raise ZendeskError(500, "Unknown error occured.")
            else:
                raise ZendeskError(500, "Unknown error occured.")
        zendesk_cred = {
            "email"     : getattr(settings, 'ZENDESK_ADMIN_EMAIL',    ''),    
            "password"  : getattr(settings, 'ZENDESK_ADMIN_PASSWORD', ''),
            "subdomain" : getattr(settings, 'ZENDESK_SUBDOMAIN'       '')
        }
        self._zenpy = zenpy.Zenpy(**zendesk_cred)
        
        # Currently as we are not supporting dynamic timezone,
        # so the following codes are commented. Later this codes will be
        # used.
        # Need to get the zendesk admin's timezone
        # get_admin = self._zenpy.search("email:" + getattr(settings, 'ZE

    def _manageV2(self, request):
        # | Function to manage the v2 login       
        # | 
        # | Arguments: Void
        # |
        # | Returns: None

        
        if request.session.get('zendesksupport', None):
             zendesksupport_session = request.session['zendesksupport']
#              if ( 'ks_user_email' in zendesksupport_session) and ('tenant_id' in zendesksupport_session):
#                  if zendesksupport_session['tenant_id'] == request.user.tenant_id:
#                     return self.keystones #None
        
        #Getting the details of the user
        tenant_id    = getattr(settings, 'KEYSTONE_ADMIN_TENANT_ID',    '')
        tenant_name  = getattr(settings, 'KEYSTONE_ADMIN_TENANT_NAME',  '')
        user_id      = getattr(settings, 'KEYSTONE_ADMIN_USER_ID',      '')
        user_name    = getattr(settings, 'KEYSTONE_ADMIN_USERNAME',    '')
        auth_url     = getattr(settings, 'KEYSTONE_ADMIN_AUTH_URL',     '')
        password     = getattr(settings, 'KEYSTONE_ADMIN_PASSWORD',     '')

        #Making the dictionary to save the data
        keystone_cred = {}
        
        #Saving the details to dictioanry
        if tenant_id:
            keystone_cred['tenant_id'] = tenant_id
        else:
            keystone_cred['tenant_name'] = tenant_name
        if user_id:
            keystone_cred['user_id'] = user_id
        else:
            keystone_cred['username'] = user_name
        keystone_cred['password'] = password
        keystone_cred['auth_url'] = auth_url
        auth = identity.v2.Password(**keystone_cred)
        sess = session.Session(auth=auth)
        keystone = keystoneclient.v2_0.client.Client(session=sess)
        #self.keystones = keystone
        #request.session['keystone_support'] = keystone
        user   = keystone.users.get(request.user.id)
        tenant = keystone.tenants.get(request.user.tenant_id)
        request.session['zendesksupport'] = {}
        request.session['zendesksupport']['tenant_id'] = tenant.id

        #Role related section
        roles = keystone.roles.roles_for_user(user=user.id, tenant=user.tenantId)
        set_role = ['admin', 'service']
        for role in roles:
            if role.name in set_role:
                request.session['role_check'] = True
            else:
                request.session['role_check'] = False    

        # If user has email store it in session
        if hasattr(user, 'email'):
            if user.email:
                request.session['zendesksupport']['ks_user_email'] = user.email
                request.session['zendesksupport']['ks_user_id'] = user.id
                
        #If the user have submitter id then saving it to session
        if hasattr(user, 'submitter_id'):
            request.session['zendesksupport']['submitter_id'] = user.submitter_id

        #Setting the default time zone
        user_timezone = 'UTC'
        all_tz = []
        for tz in pytz.all_timezones:
            # Get all the supported timezones,
            # which will be used to validate
            all_tz.append(tz)
                
        # If user has timezone, store it in session
        if hasattr(tenant, 'timezone'):
            if tenant.timezone in all_tz:
                user_timezone = tenant.timezone
        request.session['zendesksupport']['user_timezone'] = user_timezone
        request.session['zendesksupport']['timezone_offset'] = datetime.datetime.now(pytz.timezone(user_timezone)).strftime('%z')
        return keystone

    def _manageV3(self, request):
        # | Function to manage the v3 login
        # |
        # | Arguments: None
        # |
        # | Returns None
        if request.session.get('zendesksupport', None):
            zendesksupport_session = request.session['zendesksupport']
            if ( 'ks_user_email' in zendesksupport_session) and ('tenant_id' in zendesksupport_session):
                if zendesksupport_session['tenant_id'] == request.user.project_id:
                    return None
        proj_id            = getattr(settings, 'KEYSTONE_ADMIN_PROJECT_ID',           '')
        proj_name          = getattr(settings, 'KEYSTONE_ADMIN_PROJECT_NAME',         '')
        proj_domain_id     = getattr(settings, 'KEYSTONE_ADMIN_PROJECT_DOMAIN_ID',    '')
        proj_domain_name   = getattr(settings, 'KEYSTONE_ADMIN_PROJECT_DOMAIN_NAME',  '')
        user_id            = getattr(settings, 'KEYSTONE_ADMIN_USER_ID',              '')
        user_name          = getattr(settings, 'KEYSTONE_ADMIN_USERNAME',             '')
        user_domain_id     = getattr(settings, 'KEYSTONE_ADMIN_USER_DOMAIN_ID',       '')
        user_domain_name   = getattr(settings, 'KEYSTONE_ADMIN_USER_DOMAIN_NAME',     '')
        auth_url           = getattr(settings, 'KEYSTONE_ADMIN_AUTH_URL',             '')
        password           = getattr(settings, 'KEYSTONE_ADMIN_PASSWORD',     '')

        keystone_cred = {}

        if proj_id:
            keystone_cred['project_id'] = proj_id
        else:
            keystone_cred['project_name'] = proj_name

        if user_id:
            keystone_cred['user_id'] = user_id
        else:
            keystone_cred['username'] = user_name

        if proj_domain_id:
            keystone_cred['project_domain_id'] = proj_domain_id
        else:
            keystone_cred['project_domain_name'] = proj_domain_name

        if user_domain_id:
             keystone_cred['user_domain_id'] = user_domain_id
        else:
             keystone_cred['user_domain_name'] = user_domain_name
        keystone_cred['auth_url'] = auth_url
        keystone_cred['password'] = password
        auth = identity.v3.Password(**keystone_cred)
        sess = session.Session(auth=auth)
        keystone = keystoneclient.v3.client.Client(session=sess)
        #self.keystones = keystone
        user = keystone.users.get(request.user.id)
        project = keystone.projects.get(request.user.project_id)

        request.session['zendesksupport'] = {}
        request.session['zendesksupport']['tenant_id'] = request.user.project_id
        
        #Role related section
        roles = keystone.roles.list(user=user.id, project=user.default_project_id)
        set_role = ['admin', 'service']
        for role in roles:
            if role.name in set_role:
                request.session['role_check'] = True
            else:
                request.session['role_check'] = False    

        # If user has email store it in session
        if hasattr(user, 'email'):
            if user.email:
                request.session['zendesksupport']['ks_user_email'] = user.email
                request.session['zendesksupport']['ks_user_id'] = user.id
        
        user_timezone = 'UTC'
        all_tz = []
        for tz in pytz.all_timezones:
            # Get all the supported timezones,
            # which will be used to validate
            all_tz.append(tz)

        # If user has timezone, store it in session
        if hasattr(project, 'timezone'):
            if project.timezone in all_tz:
                user_timezone = project.timezone
        request.session['zendesksupport']['user_timezone'] = user_timezone
        request.session['zendesksupport']['timezone_offset'] = datetime.datetime.now(pytz.timezone(user_timezone)).strftime('%z')
        return keystone

    def _get_zendesk_user_id(self, selected_user= None):
        """
        # | Function to get keystone user detail.
        # | Also this function will create a user with random password
        # | if no user found.
        # |
        # | Arguments: None
        # |
        # | Return Type: User object
        """
        
        #Checking the user is selected
        user_selected = False
        if selected_user != None: 
            if selected_user['user'] != '':
                user_selected = True
                user_data = selected_user['user']
                user_data = user_data.split('--')
                email = user_data[1]
                zend_name = user_data[2]
                ks_id = user_data[0]
            else:
                email = self._request.session['zendesksupport']['ks_user_email']
        else:
            if 'zendesk_user_id' in self._request.session['zendesksupport']:
                return self._request.session['zendesksupport']['zendesk_user_id']

            if not self._user_has_email():
                # | If there is no email, then there is
                # | no point to check the user, simple return False
                raise False
    
            email = self._request.session['zendesksupport']['ks_user_email']
        users = self._zenpy.search("email:" + email, type="user")

        # Search user by email, will result maximum one user oly
        if users.count != 1:
            
            # | If no user found, then  create a new user
            if user_selected:
                pass
            else:
                zend_name = self._request.user

            #Creating new user with the details set
            new_user = User(name=str(zend_name), email=email, password=self._random_pass()) 
            #uid = self._zenpy.users.create(new_user).id
            uid = self._zenpy.users.create_or_update(new_user).id
            self._request.session['zendesksupport']['zendesk_user_id'] = uid
            extra = {"submitter_id": uid}
            if user_selected:
                self.keystone.users.update(ks_id, **extra)
            else:
                self.keystone.users.update(self._request.session['zendesksupport']['ks_user_id'], **extra)
            return uid

        for user in users:
            # | As there will be only one user
            # | so return at first attempt itself.
            self._request.session['zendesksupport']['zendesk_user_id'] = user.id
            return user.id
        
    
    def _random_pass(self):
        """
        # | Function to create a random password
        # |
        # | Arguments: None
        # |
        # | Returns: Random 13 charcter password
        """
        pass_length = 13
        chars = string.ascii_letters + string.digits + '!@#$%^&*()'
        rnd = random.SystemRandom()
        return "".join(rnd.choice(chars) for i in range(pass_length))

    def create_attachment(self, tfile):
        """
        # | Function to add attachment (Currently this is only for upload)
        # | 
        # | @Arguments: Uploaded File
        # |
        # | @Created tocken
        # | Currently this func is not working
        """
        attach = Attachment(tfile)
        #return self._zenpy.attachments.upload(tfile)
        return self._zenpy.attachments.upload(attach)

    def list_tickets(self, search_query = {}):
        """
        # | Function to get the available tickets of the user
        # |
        # | @Arguments: Void
        # |
        # | @Return Type: Result Generator object
        """
        if not self._user_has_email():
            LOG.error("No email address found for the user")
            raise ZendeskError(403, "No email address found for the user")

        try:
            search_query['requester'] = self._request.session['zendesksupport']['ks_user_email']
            search_query_str = ""
            for query in search_query:
                search_query_str += "%s:%s," % (urllib.quote(query), urllib.quote(search_query[query]))
            search_query_str = search_query_str.strip(",")
            LOG.info("query string for zendesk => %s" % search_query_str)
            tickets = self._zenpy.search(search_query_str, type="ticket")
            modified_list = {}
            
            # Okay now we got the tickets from zendesk
            # But it's time is not human readable. So we need to convert
            # it to human readable. For this we need the user's timezone, which is 
            # stored in project table in extra field
            user_timezone = 'UTC'
            admin_timezone = getattr(settings, 'ZENDESK_ADMIN_TIMEZONE', 'UTC')
            all_tz = []
            for tz in pytz.all_timezones:
                # Get all the supported timezones,
                # which will be used to validate
                all_tz.append(tz)

            if admin_timezone not in all_tz:
                # If the deployer has not provided proper
                # timezone, then we need to make it UTC
                admin_timezone = 'UTC'

            timezone = self._request.session['zendesksupport']['user_timezone'].strip()
            if timezone in all_tz:
               user_timezone = timezone
        
            user_timezone = getattr(settings, 'ZENDESK_ADMIN_TIMEZONE', 'UTC') #'US/Pacific'
            
            modified_list['count'] = tickets.count
            modified_list['tickets'] = []
            for t in tickets:
                print 'tickets:', tickets, t.submitter_id 
                # As tickets is an generator sting,
                # so we will modify the properties and will store them in a list
                created_at = self._get_target_datetime_obj(t.created_at, '%Y-%m-%dT%H:%M:%SZ', admin_timezone, user_timezone)
                updated_at = self._get_target_datetime_obj(t.updated_at, '%Y-%m-%dT%H:%M:%SZ', admin_timezone, user_timezone)
                t.formatted_created_at     = str(created_at)
                t.formatted_created_at_str = self._ago_calculate(created_at, user_timezone)
                t.formatted_updated_at     = str(updated_at)
                t.formatted_updated_at_str = self._ago_calculate(updated_at, user_timezone)
                modified_list['tickets'].append(t)
            return modified_list
        except APIException as e:
            LOG.error("ZENDESK SAYS:"+ str(e))
            e = json.loads(str(e))
            if e['error'] == "Couldn't authenticate you":
                raise ZendeskError(401, "ZENDESK SAYS: Couldn't authenticate you")
            else:
                raise ZendeskError(500, "ZENDESK SAYS:"+ str(e))
    
    def create_ticket(self, data, request):
        """
        # | Function to create a ticket. 
        # |
        # | Arguments:
        # | Data in dictionary, required to create a ticket
        # |
        # | Return Type: Ticket object
        """

        #Checking the user have the email, if no then error message need to show
        if not self._user_has_email():
            LOG.error("No email address found for the user")
            raise ZendeskError(403, "No email address found for the user")
        try:
            zendesk_user_id = self._get_zendesk_user_id(data)
            data['requester_id'] = zendesk_user_id
            
            #if the submitter selected the user from the list 
            if data['user'] != '':
                data['submitter_id'] = zendesk_user_id
                
            #Creating the ticket using the data
            ticket = Ticket(**data)
            created_ticket = self._zenpy.tickets.create(ticket)
            return created_ticket
        except Exception as e:
            LOG.error(str(e))
            raise ZendeskError(500, str(e))

    def create_comment(self, ticket_id, desc, privacy, files=[]):
        """
        # | Function to create comment for the given ticket id
        # |
        # | Arguments:
        # | <ticket_id>: Ticket id
        # | <desc>: description, Comment description
        # | 
        # | Returns: Comment object
        """
        user_id = self._get_zendesk_user_id()
        
        if not user_id:
            # | If user is False, then there is no email for the user
            # | in that case throw error
            raise ZendeskError(403, "No email address found for the user")
        
        author_id = user_id

        #Initializing
        token_list = []
        
        #Looping through each file and uploading them
        for f in files:
            name = os.path.basename(f)
            upload_instance = self._zenpy.attachments.upload(fp=f, target_name = name)
            token_list.append(upload_instance.token)

            #Delete the file after upload since it's of no further use
            os.remove(f)

        #Passing the contents for comment creation
        #We set the comment privacy via the public option(Privacy options are Public reply/Internal Note) 
        data = {
            "author_id": author_id,
            "body"     : desc,
            "public"   : privacy,
            "uploads"  : token_list
        }

        try:
            comment = Comment(**data)
            ticket  = Ticket(id=ticket_id)
            ticket.comment  = comment
            created_comment = self._zenpy.tickets.update(ticket)
            return created_comment
        except Exception as e:
            LOG.error(str(e))
            raise ZendeskError(str(e))
 
    def get_ticket_detail(self, ticket_id):
        """
        # | Function to get ticket detail
        # |
        # | Arguments: ticket_id
        # |
        # | Returns: Ticket Object
        """
        if not self._user_has_email():
            LOG.error("No email address found for the user")
            raise ZendeskError(403, "No email address found for the user")
        try:
            ticket = self._zenpy.tickets(id=ticket_id)
            return ticket
        except RecordNotFoundException as err:
            LOG.error(str(err))
            raise ZendeskError(404, "Ticket Not Found")
    
    # | Function to get the comments, of a given ticket
    # |    
    # | Arguments:
    # | <ticket_id>: Ticket id, whose comments need to fetached
    # |
    # | Returns: Comments Object
    def get_ticket_comments(self, ticket_id):
        #self.zendesk.delete_cache('user')
        comments = self._zenpy.tickets.comments(ticket_id)
        return comments

    def _user_has_email(self):
        """
        # | Function to check wheather the 
        # | current user has email or not
        # |
        # | Arguments: None
        # |
        # | Returns: Boolean
        """
        if self._request.session.get('zendesksupport', None):
            if "ks_user_email" not in self._request.session['zendesksupport']:
                return False
            return True
        return False

    def _get_target_datetime_obj(self, source_datetime_str, source_datetime_format, source_timezone, target_timezone):
        """
        # | Function to convert a given datetime  in one timezone to another timezone
        # |
        # | Arguments:
        # |     <source_datetime_str>:    Source datetime in string
        # |     <source_datetime_format>: Source datetime is in which formatLike "%Y-%m-%d"
        # |     <source_timezone>:        From which timezone. It should be one of the pytz timezone
        # |     <target_timezone>:        To which timezone. It should be one of the pytz timezone
        # |
        # | Returns datetime object
        """
        system_offset_str = pytz.timezone(str(tzlocal.get_localzone())).localize(datetime.datetime.now()).strftime('%z')
        source_offset_str = pytz.timezone(str(source_timezone)).localize(datetime.datetime.now()).strftime('%z')
        target_offset_str = pytz.timezone(str(target_timezone)).localize(datetime.datetime.now()).strftime('%z')

        system_offset_in_min = int(str(system_offset_str[0]) + str(int(system_offset_str[-4:-2])*60 + int(system_offset_str[-2:])))
        target_offset_in_min = int(str(target_offset_str[0]) + str(int(target_offset_str[-4:-2])*60 + int(target_offset_str[-2:])))
        source_offset_in_min = int(str(source_offset_str[0]) + str(int(source_offset_str[-4:-2])*60 + int(source_offset_str[-2:])))

        source_datetime_obj = datetime.datetime.strptime(source_datetime_str, source_datetime_format)
        system_datetime_obj = source_datetime_obj + datetime.timedelta(minutes=(system_offset_in_min - source_offset_in_min))
        target_detetime_obj = system_datetime_obj + datetime.timedelta(minutes=(target_offset_in_min - system_offset_in_min))
        return target_detetime_obj

    def _ago_calculate(self, source_obj, timezone):
        """
        # | Function to display the human readable string
        # |
        # | Arguments: 
        # |     <source_obj>: [datetime object] A date time object for which the calculation  will be done
        # |
        # | Returns: String
        """
        #current_time = datetime.datetime.now(pytz.timezone(timezone))
        current_time = datetime.datetime.now()
        date1 = datetime.datetime(source_obj.year, source_obj.month, source_obj.day, source_obj.hour, source_obj.minute, source_obj.second)
        date2 = datetime.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute, current_time.second)
        diff = date2 - date1
        total_seconds = diff.total_seconds()
        minute = 60
        hour   = 60 * 60
        day    = 60 * 60 * 24
        month  = 60 * 60 * 24 * 30
        year   = 60 * 60 * 24 * 30 * 12

        year_diff  = int(total_seconds / year)
        remain  = total_seconds % year
        month_diff = int (remain / month)
        remain = remain % month
        day_diff = int (remain / day)
        remain = remain % day
        hour_diff = int(remain / hour)
        remain = remain % hour
        minute_diff = int(remain/minute)
        second_diff = int(remain % minute)

        if year_diff >= 1:
            if year_diff == 1:
                return "about 1 year ago"
            return "about " + str(year_diff) + " years ago"
        elif month_diff >= 1:
            if month_diff == 1:
                return "about 1 month ago"
            return "about " + str(month_diff) + " months ago"
        elif day_diff >= 1:
            if day_diff == 1:
                return "about 1 day ago"
            return "about "+ str(day_diff) + " days ago"
        elif hour_diff >= 1:
            if hour_diff == 1:
                return "about 1 hour ago"
            return "about " + str(hour_diff) + " hours ago"
        elif minute_diff >= 1:
           if minute_diff == 1:
               return "about 1 minute ago"
           return "about " + str(minute_diff) + " minutes ago"
        else:
           return "Just now"

class ZendeskError(Exception):
    code = None
    title = None
    message = None
    http_codes = {
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "500": "Internal Error"
    }
    def __init__(self, code, message):
        self.code = code
        self.title = self.http_codes[str(code)]
        self.message = self.message
