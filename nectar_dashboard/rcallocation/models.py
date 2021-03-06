# Models for the ResearchCloud Allocations portal
# Original: Tom Fifield <fifieldt@unimelb.edu.au> - 2011-10
# Modified by Martin Paulo
import datetime
from dateutil.relativedelta import relativedelta
import logging

from django.core.mail import EmailMessage
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

import for_choices
from allocation_home_choices import ALLOC_HOME_CHOICE
from project_duration_choices import DURATION_CHOICE
from grant_type import GRANT_TYPES

LOG = logging.getLogger(__name__)


#############################################################################
#
# Requests are created by Users who wish to receive Allocations
#
#############################################################################


def _six_months_from_now():
    return datetime.date.today() + datetime.timedelta(
        days=30 * 6),


class AllocationRequest(models.Model):
    REQUEST_STATUS_CHOICES = (
        # Request created but nothing else
        # User can: Submit
        ('N', 'New'),

        # Request has been emailed
        # Admin can: Approve, Reject, Edit
        # User can: Edit
        ('E', 'Submitted'),

        # Admin has approved the request
        # Admin can: Provision, Edit
        # User can: Amend, Extend
        ('A', 'Approved'),

        # Admin has rejected the request
        # User can: Edit, Submit
        ('R', 'Declined'),

        # User has requested an extension
        # Admin can: Approve, Reject, Edit
        # User can: Edit
        ('X', 'Update/extension requested'),

        # Admin has rejected an extension
        # User can: Edit, Extend
        ('J', 'Update/extension declined'),

        # Admin has provisioned an approved request
        # User can: Amend, Extend
        ('P', 'Provisioned'),

        # Requests in above status can be viewed by both user
        # and admin at all times.

        # Not visible to users
        ('L', 'Legacy submission'),

        # Avoid sending emails for legacy approvals/rejections.
        # Set to A/R during model save.
        ('M', 'Legacy approved'),
        ('O', 'Legacy rejected'),
    )
    parent_request = models.ForeignKey('AllocationRequest', null=True,
                                       blank=True)

    status = models.CharField(max_length=1, blank=False,
                              choices=REQUEST_STATUS_CHOICES,
                              default='N')

    status_explanation = models.TextField(
        null=True, blank=True,
        verbose_name="Reason",
        help_text="A brief explanation of the reason the request has been "
                  "sent back to the user for changes")

    created_by = models.CharField(null=False, blank=False, max_length=100)

    submit_date = models.DateField('Submission Date',
                                   default=datetime.date.today)
    modified_time = models.DateTimeField('Modified Date',
                                         default=datetime.datetime.utcnow)

    # The ordering of the following fields are important, as it
    # governs the order they appear on the forms
    tenant_name = models.CharField(
        'Project identifier',
        max_length=64,
        blank=True,
        null=True,
        help_text='A short name used to identify your project.<br>'
                  'Must contain only letters and numbers.<br>'
                  '16 characters max.')

    project_name = models.CharField(
        'Project allocation title',
        max_length=200,
        help_text='A human-friendly descriptive name for your research '
                  'project.')

    contact_email = models.EmailField(
        'Contact e-mail', blank=True,
        help_text="""The e-mail address provided by your IdP which
                     will be used to communicate with you about this
                     allocation request.  <strong>Note:</strong> <i>if
                     this is not a valid e-mail address you will not
                     receive communications on any allocation request
                     you make</i>. If invalid please contact your IdP
                     and ask them to correct your e-mail address!"""
    )

    start_date = models.DateField(
        'Start date',
        default=datetime.date.today,
        help_text="""The day on which you want your Project Allocation to
                     go live. Format: yyyy-mm-dd""")

    end_date = models.DateField(
        'Estimated end date',
        editable=False,
        default=_six_months_from_now,
        help_text='The day on which your project will end.')

    estimated_project_duration = models.IntegerField(
        'Estimated project duration',
        choices=DURATION_CHOICE,
        blank=False,
        null=False,
        default=1,
        help_text="""Resources are approved for at most 12-months,
                    but projects can extend a request for resources
                    once it has been approved.""")

    convert_trial_project = models.BooleanField(
        'Convert trial project?',
        default=False,
        help_text='If selected, your existing trial project pt- will be '
                  'renamed so any resources inside it will become part of '
                  'this new allocation. A new trial project will be created '
                  'in its place.')

    INSTANCE_TYPE_CHOICES = (
        ('S', 'm1.small'),
        ('M', 'm1.medium'),
        ('B', 'm1.large'),
        ('L', 'm1.xlarge'),
        ('X', 'm1.xxlarge'),
    )

    primary_instance_type = models.CharField(
        max_length=1,
        blank=True,
        choices=INSTANCE_TYPE_CHOICES,
        default=' ',
        help_text="""
        This is the typical VM size you expect to use. Five basic
        types of primary instance are available:
        <table class="text-left table-condensed">
          <tr><th>Name</th><th>VCPUs</th><th>RAM</th><th>Local Disk</th></tr>
          <tr><td><b>m1.small</b></td><td>1</td><td>4GB</td><td>30GB</td></tr>
          <tr>
              <td><b>m1.medium</b></td><td>2</td><td>8GB</td><td>60GB</td>
          </tr>
          <tr>
              <td><b>m1.large</b></td><td>4</td><td>16GB</td><td>120GB</td>
          </tr>
          <tr>
              <td><b>m1.xlarge</b></td><td>8</td><td>32GB</td><td>240GB</td>
          </tr>
          <tr>
              <td><b>m1.xxlarge</b></td><td>16</td><td>64GB</td><td>480GB</td>
          </tr>
        </table>

        Compute resources are subject to availability and from time to
        time some flavors will not be available.  It is recommended
        that you consider using 4 and 2 core instances to distribute
        your work load.
        """)

    instances = models.IntegerField(
        'Number of instances', default=2,
        help_text='The maximum number of instances that '
                  'you think your project will require at any one time.')

    cores = models.IntegerField(
        'Number of cores',
        default=2,
        help_text="""This is the maximum number of cores you'd
                    like to use at any one time across all instances.
                    For example, if you'd like to be able to run two
                    "XXL Sized" instances at once (each has 16 CPU cores),
                    you should specify 32 here.""")

    core_hours = models.IntegerField(
        'Number of core hours',
        default=744,
        help_text="""<p>
                    Core hours is the number of hours multiplied by the
                    number of cores in use. The default value in this field
                    is half of the core hours required to run all of the
                    cores requested over the estimated project period.
                    This should be adjusted up or down as required.
                    </p>
                     For example:
                     <ul>
                       <li>
                           * A 1-core Virtual Machine will use 24 core hours
                           each day it is used
                       </li>
                       <li>
                           * A 2-core Virtual Machine will use 48 core hours
                           each day it is used
                       </li>
                       <li>
                           * A 4-core Virtual Machine will use 96 core hours
                           each day it is used
                       </li>
                       <li>
                           * A 8-core Virtual Machine will use 192 core hours
                           each day it is used
                       </li>
                     </ul>
                     """)

    instance_quota = models.IntegerField('Instance count quota', default='0')

    ram_quota = models.IntegerField('Maximum RAM usage quota', default='0')

    core_quota = models.IntegerField('Maximum number of cores available',
                                     default='0')

    approver_email = models.EmailField('Approver email', blank=True)

    volume_zone = models.CharField(
        "Persistent Volume location",
        blank=True,
        null=True,  # To work around south/sqlite failures.
        default='',
        max_length=64,
        help_text="""Optional. Select a location here if you need volumes
                     located at a specific node.""")

    object_storage_zone = models.CharField(
        "Object Storage location",
        blank=True,
        null=True,  # To work around south/sqlite failures.
        default='',
        max_length=64,
        help_text="""Optional. Select a location here if you need
                     object storage located at a specific node.""")

    use_case = models.TextField(
        "Research use case",
        max_length=4096,
        help_text="""A short write up on how you intend to to use your
        cloud instances will help us in our decision making.""")

    usage_patterns = models.TextField(
        "Instance, Object Storage and Volumes Storage Usage Patterns",
        max_length=1024, blank=True,
        help_text="""Will your project have many users and small data
                sets? Or will it have large data sets with a small
                number of users? Your answers here will help us.""")

    allocation_home = models.CharField(
        "Allocation home location",
        choices=ALLOC_HOME_CHOICE,
        blank=False,
        null=False,
        default='national',
        max_length=128,
        help_text="""You can provide a primary location where you expect to
                use most resources, effectively the main NeCTAR node for your
                allocation. Use of other locations is still possible.
                This can also indicate a specific arrangement with a
                NeCTAR Node, for example where you obtain support, or if
                your institution is a supporting member of that Node.
                """
    )

    geographic_requirements = models.TextField(
        max_length=1024,
        blank=True,
        verbose_name="Additional location requirements",
        help_text="""Indicate to the allocations committee any special
                geographic requirements that you may need?  Please note
                that the ability to run virtual machines at specified
                locations is normal functionality and not a
                special requirement.""")

    tenant_uuid = models.CharField(max_length=36, blank=True, null=True)

    estimated_number_users = models.IntegerField(
        'Estimated number of users',
        default='1',
        validators=[MinValueValidator(1), ],
        error_messages={
            'min_value': 'The estimated number of users must be great than 0'},
        help_text="""Estimated number of users, researchers and collaborators
        to be supported by the allocation.""")

    FOR_CHOICES = for_choices.FOR_CHOICES
    PERCENTAGE_CHOICES = (
        (0, '0%'),
        (10, '10%'),
        (20, '20%'),
        (30, '30%'),
        (40, '40%'),
        (50, '50%'),
        (60, '60%'),
        (70, '70%'),
        (80, '80%'),
        (90, '90%'),
        (100, '100%'),
    )

    field_of_research_1 = models.CharField(
        "First Field Of Research",
        choices=FOR_CHOICES,
        blank=True,
        null=True,
        max_length=6
    )

    for_percentage_1 = models.IntegerField(
        choices=PERCENTAGE_CHOICES, default=100,
        help_text="""The percentage""")

    field_of_research_2 = models.CharField(
        "Second Field Of Research",
        choices=FOR_CHOICES,
        blank=True,
        null=True,
        max_length=6
    )

    for_percentage_2 = models.IntegerField(
        choices=PERCENTAGE_CHOICES, default=0,
        help_text="""The percentage""")

    field_of_research_3 = models.CharField(
        "Third Field Of Research",
        choices=FOR_CHOICES,
        blank=True,
        null=True,
        max_length=6
    )

    for_percentage_3 = models.IntegerField(
        choices=PERCENTAGE_CHOICES, default=0)

    nectar_support = models.CharField(
        'List any NeCTAR Virtual Laboratories supporting this request',
        blank=True,
        max_length=255,
        help_text="""Specify any NeCTAR Virtual Laboratories
                    supporting this request.""")

    ncris_support = models.CharField(
        'List NCRIS capabilities supporting this request',
        blank=True,
        max_length=255,
        help_text="""Specify NCRIS capabilities supporting this request.""")

    funding_national_percent = models.IntegerField(
        'Nationally Funded Percentage [0..100]',
        default='100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        error_messages={'min_value': 'The minimum percent is 0',
                        'max_value': 'The maximum percent is 100'},
        help_text="""Percentage funded under the National
                    Allocation Scheme.""")

    funding_node = models.CharField(
        "Node Funding Remainder (if applicable)",
        choices=ALLOC_HOME_CHOICE[1:],
        blank=True,
        null=True,
        max_length=128,
        help_text="""You can choose the node that complements
                    the National Funding."""
    )

    def set_status(self, status):
        status = status.upper()
        status_abbreviations = [abbr for abbr, full_name in
                                self.REQUEST_STATUS_CHOICES]
        if status not in status_abbreviations:
            raise Exception()

        self.status = status

    def is_active(self):
        """
        Return True if the allocation has either been accepted or provisioned,
        false otherwise.
        """
        return self.status.lower() in ('a', 'p')

    def is_decided(self):
        """
        Return True if the allocation has either been accepted or
        rejected, false otherwise.
        """
        return self.is_active()

    def is_rejected(self):
        """
        Return True if the allocation has either been accepted or
        rejected, false otherwise.
        """
        return self.status.lower() in ('r', 'j')

    def is_requested(self):
        return self.status.lower() in ('e', 'n', 'l')

    def amendment_requested(self):
        """
        Return True if the user has requested an extention
        """
        return self.status.lower() in ('x', 'j')

    def is_archived(self):
        return self.parent_request is not None

    def can_be_amended(self):
        return self.is_active() and not self.is_archived()

    def can_be_extended(self):
        return self.can_be_amended() and not self.is_archived()

    def can_be_edited(self):
        return not self.is_active() and not self.is_archived()

    def can_admin_edit(self):
        return self.status.lower() not in ('p', 'a') and not self.is_archived()

    def can_user_edit(self):
        return self.status.lower() in (
            'e', 'r', 'n', 'l') and not self.is_archived()

    def can_user_edit_amendment(self):
        return self.amendment_requested() and not self.is_archived()

    def can_be_rejected(self):
        return self.is_requested() and not self.is_archived()

    def can_be_approved(self):
        return self.is_requested() and not self.is_archived()

    def can_reject_change(self):
        return self.can_approve_change()

    def can_approve_change(self):
        return self.amendment_requested() and not self.is_archived()

    def can_be_provisioned(self):
        return self.status.lower() == 'a' and not self.is_archived()

    def notify_via_e_mail(self, sender, recipient_list, template, cc_list=[],
                          bcc_list=[], reply_to=None):
        """
        Send an email to the requester notifying them that their
        allocation has been processed.
        """
        if not sender and recipient_list:
            # TODO (shauno): log this problem
            raise Exception

        plaintext = get_template(template)
        ctx = Context({"request": self})
        text = plaintext.render(ctx)
        subject, body = text.split('')
        email = EmailMessage(
            subject.strip(),
            body,
            sender,
            recipient_list,
            cc=cc_list
        )

        if bcc_list:
            email.bcc = bcc_list

        if reply_to:
            email.extra_headers = {'Reply-To': reply_to}

        email.send()

    def notify_provisioner(self):
        if not self.can_be_provisioned():
            return
        template = get_template('rcallocation/email_provision.txt')
        ctx = Context({'request': self})
        text = template.render(ctx)
        to = [settings.ALLOCATION_EMAIL_PROVISIONER]
        cc = [self.contact_email]
        sender = self.approver_email
        subject, body = text.split('')
        email = EmailMessage(subject.strip(), body, sender, to, cc=cc)
        email.send()

    def notify_user(self, template):
        to = [self.contact_email]
        cc = settings.ALLOCATION_EMAIL_RECIPIENTS
        sender = settings.ALLOCATION_EMAIL_FROM
        reply_to = settings.ALLOCATION_EMAIL_REPLY_TO
        self.notify_via_e_mail(
            template=template,
            sender=sender,
            recipient_list=to,
            cc_list=cc,
            reply_to=reply_to,
        )

    def notify_admin(self, template):
        self.notify_via_e_mail(
            sender=settings.ALLOCATION_EMAIL_FROM,
            recipient_list=settings.ALLOCATION_EMAIL_RECIPIENTS,
            template=template,
            cc_list=[self.contact_email],
            bcc_list=settings.ALLOCATION_EMAIL_BCC_RECIPIENTS,
            reply_to=settings.ALLOCATION_EMAIL_REPLY_TO,
        )

    def send_notifications(self):
        status = self.status.lower()
        if status in ['n', 'e', 'x']:
            if status == 'n':
                template = 'rcallocation/email_alert_acknowledge.txt'
            else:
                template = 'rcallocation/email_alert.txt'
            self.notify_admin(template)
            if status == 'n':
                # N is a special state showing that the
                # request has been created but no email has
                # been sent. Progress it once it's been sent.
                self.status = 'E'
        elif self.can_be_provisioned():
            # User is cc'd on the support email to create the tenant.
            self.notify_provisioner()
        elif self.is_rejected():
            template = 'rcallocation/email_alert_rejected.txt'
            self.notify_user(template)

    def save(self, *args, **kwargs):
        # calculate the end date based on the start date and duration
        duration_relativedelta = relativedelta(
            months=self.estimated_project_duration)
        self.end_date = self.start_date + duration_relativedelta
        if not kwargs.get('provisioning'):
            if not self.is_archived():
                self.modified_time = datetime.datetime.utcnow()
                try:
                    self.send_notifications()
                except:
                    LOG.error(
                        'Could not send notification email for allocation %s.'
                        % self.project_name)
                    if settings.DEBUG:
                        raise
        if self.status == 'M':
            self.status = 'A'
        elif self.status == 'O':
            self.status = 'R'
        if 'provisioning' in kwargs:
            del kwargs['provisioning']
        super(AllocationRequest, self).save(*args, **kwargs)

    def get_all_fields(self):
        """
        Returns a list of all non None fields, each entry containing
        the fields label, field name, and value (if the display value
        exists it is preferred)
        """
        fields = []
        for f in self._meta.fields:
            if f.editable:
                field_name = f.name

                # resolve picklists/choices, with get_xyz_display() function
                try:
                    get_choice = 'get_' + field_name + '_display'
                    if hasattr(self, get_choice):
                        value = getattr(self, get_choice)()
                    else:
                        value = getattr(self, field_name)
                except AttributeError:
                    value = None

                # only display fields with values and skip some fields entirely
                if not (value is None or field_name in ('id', 'status')):
                    fields.append(
                        {
                            'label': f.verbose_name,
                            'name': field_name,
                            'value': value,
                        }
                    )
        return fields

    def __unicode__(self):
        return '"{0}" {1}'.format(self.project_name, self.contact_email)


class Quota(models.Model):
    allocation = models.ForeignKey(AllocationRequest, related_name='quotas')

    resource = models.CharField(
        choices=getattr(settings, 'ALLOCATION_QUOTA_TYPES', ()),
        max_length=64,
    )

    zone = models.CharField(
        "Availability Zone",
        max_length=64,
        help_text="""The location to of the resource.""")

    requested_quota = models.IntegerField(
        'Requested quota',
        default='0')

    quota = models.IntegerField(
        "Allocated quota",
        default='0')

    units = models.CharField(
        "The units the quota is stored in.",
        default='GB',
        max_length=64)

    class Meta:
        unique_together = ("allocation", "resource", "zone")

    def __unicode__(self):
        return '{0} {1} {2}'.format(self.allocation.id,
                                    self.resource, self.zone)


class ChiefInvestigator(models.Model):
    allocation = models.ForeignKey(AllocationRequest,
                                   related_name='investigators')

    title = models.CharField(
        'Title',
        blank=False,
        max_length=60,
        help_text="""The chief investigator's title"""
    )

    given_name = models.CharField(
        'Given name',
        blank=False,
        max_length=200,
        help_text="""The chief investigator's given name"""
    )

    surname = models.CharField(
        'Surname',
        blank=False,
        max_length=200,
        help_text="""The chief investigator's surname"""
    )

    email = models.EmailField(
        'Institutional email address',
        blank=False,
        help_text="""Email address must belong the university or
            organisation for accountability."""
    )

    institution = models.CharField(
        'Institution',
        blank=False,
        max_length=200,
        help_text="""The name of the institution or university of
                    the chief investigator including the schools,
                    faculty and/or department."""
    )

    additional_researchers = models.TextField(
        'Please list all other primary investigators, partner investigators '
        'and other research collaborators',
        blank=True,
        max_length=1000,
        default='',
        help_text="""Please list all other primary investigators, partner
        investigators and other research collaborators"""
    )

    def __unicode__(self):
        return '{0} {1} {2}'.format(self.title, self.given_name, self.surname)


class Institution(models.Model):
    name = models.CharField(
        'Supported institutions',
        max_length=200,
        help_text="""List the Australian research institutions and
                    universities supported by this application. If this
                    application is just for you, just write the name of
                    your institution or university. If you are running a
                    public web service list the Australian research
                    institutions and universities that
                    you think will benefit most.""")

    allocation = models.ForeignKey(AllocationRequest,
                                   related_name='institutions')

    class Meta:
        unique_together = ("allocation", "name")

    def __unicode__(self):
        return self.name


class Publication(models.Model):
    publication = models.CharField(
        'Publication/Output',
        max_length=255,
        help_text="""Please provide any traditional and non-traditional
                research outputs using a citation style text reference
                for each. eg. include article/title, journal/outlet, year,
                DOI/link if available.""")

    allocation = models.ForeignKey(AllocationRequest,
                                   related_name='publications')

    class Meta:
        unique_together = ("allocation", "publication")

    def __unicode__(self):
        return self.publication


class Grant(models.Model):
    grant_type = models.CharField(
        "Type",
        choices=GRANT_TYPES,
        blank=False,
        null=False,
        default='arc',
        max_length=128,
        help_text="""Choose the grant type from the dropdown options."""
    )

    funding_body_scheme = models.CharField(
        "Funding body and scheme",
        blank=False,
        max_length=255,
        help_text="""For example, ARC Discovery Project."""
    )

    grant_id = models.CharField(
        'Grant ID',
        blank=True,
        max_length=200,
        help_text="""Specify the grant id."""
    )

    first_year_funded = models.IntegerField(
        'First year funded',
        blank=False,
        default=datetime.datetime.now().year,
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
        error_messages={
            'min_value': 'Please input a year between 1970 ~ 3000',
            'max_value': 'Please input a year between 1970 ~ 3000'},
        help_text="""Specify the first year funded"""
    )

    total_funding = models.FloatField(
        'Total funding (AUD)',
        validators=[MinValueValidator(1)],
        help_text="""Total funding amount in AUD"""
    )

    allocation = models.ForeignKey(AllocationRequest, related_name='grants')

    class Meta:
        unique_together = ("allocation", "grant_type", "funding_body_scheme",
                           "grant_id", "first_year_funded", "total_funding")

    def __unicode__(self):
        return "Funding : {0} , total funding: {1}".format(self.funding_body,
                                                           self.total_funding)
