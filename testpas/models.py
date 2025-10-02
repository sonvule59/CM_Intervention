# type: ignore
import datetime
from django.db import models, migrations
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta
from testpas import settings
import string
import random
import uuid
from django.core.mail import send_mail
from django.conf import settings
from testpas import settings

class Survey(models.Model):
    """ Defines a survey so when one is created in the code, each survey has the attributes: title, description, and the date created """
    title = models.CharField(max_length=255)
    description = models.TextField()
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return self.title

class Question(models.Model):
    """ Defines a question in a survey based on the survey key (id), and stores the question text and date created """
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question_text

class CustomUser(AbstractUser):
    """ A custom user that an admin can make with permissions and attributes that the admin can control """
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    registration_code = models.CharField(max_length=15, null=True, blank=True)
    consented = models.BooleanField(null=True, blank=True)
    consent_response = models.TextField(null=True, blank=True)

    # Avoid conflicts with default 'User' model by adding related_name
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user.",
    )
class Response(models.Model):
    """ Records the user that made the response, the question, and the answer they gave to the question """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=255)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"{self.user} - {self.question}"
class EmailTemplate(models.Model):
    """ Defines an email template with its name, subject, and body so it is easy to create an email to send no matter what it is for """
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="Use {participant_id} as placeholder.")
    def __str__(self):
        return self.name
class UserSurveyProgress(models.Model):
    """ Records the progress of a user. This connects the users with the status of their start and end times, progress, first day, elgibility, etc. """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    progress = models.IntegerField(default=0)
    day_1 = models.DateField(null=True, blank=True)  # Represents Day 1 (date of consent)
    survey_completed = models.BooleanField(default=False)
    eligible = models.BooleanField(default=False)
    eligibility_reason = models.TextField(null=True, blank=True)  # Reason for eligibility or ineligibility
    consent_given = models.BooleanField(default=False)  # Whether consent has been provided
    progress_percentage = models.IntegerField(null=True, blank=True)  # Percentage of survey completed

    ### Jun 25: Add in email log
    email_log = models.TextField(default="", blank=True) 
    ### Jun 25: Add in email log date
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Timeline reference for time compression testing
    timeline_reference_timestamp = models.DateTimeField(null=True, blank=True)
    
    # def __str__(self):
    #     return f"{self.user} - {self.survey} - {self.progress}%"

    def __str__(self):
        return self.user.username
    
def generate_confirmation_token():
    """ Function for generating the token (or code) that gives every user a unique token that is used to confirm their account """
    return uuid.uuid4().hex

class Participant(models.Model):
    """ Defines a participant so when one is created, all of the important information about a participant is recorded (i.e user, age, phase, group, phone number, start date, etc.) also
    includes functions,, one for each of the different emails that the participant recieves over the course of the study."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    code_entered = models.BooleanField(default=False)
    code_entry_date = models.DateField(null=True, blank=True)
    ### Jun 25: Add in code entry day
    code_entry_day = models.IntegerField(null=True, blank=True)
    email_send_date = models.DateField(null=True, blank=True)  # store email send date
    email_status = models.CharField(max_length=50, default='pending')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    confirmation_token = models.CharField(max_length=255, unique=True)
    is_confirmed = models.BooleanField(default=False)
    token_expiration = models.DateTimeField(default=timezone.now)
    phase = models.CharField(max_length=100, blank=True, null=True)
    monitoring_start_date = models.DateField(blank=True, null=True)
    # Double-blind Randomization
    participant_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    group = models.IntegerField(null=True, blank=True)
    group_assigned = models.BooleanField(default=False)
    intervention_start_date = models.DateTimeField(null=True, blank=True)
    intervention_end_date = models.DateTimeField(null=True, blank=True)
    engagement_tracked = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)  
    wave1_survey_email_sent = models.BooleanField(default=False)
    wave2_survey_email_sent = models.BooleanField(default=False)
    wave2_monitoring_notice_sent = models.BooleanField(default=False)
    ## Wave 3
    wave3_survey_email_sent = models.BooleanField(default=False)
    wave3_code_entered = models.BooleanField(default=False)  # New field for Wave 3
    wave3_code_entry_date = models.DateField(null=True, blank=True)
    wave3_code_entry_day = models.IntegerField(null=True, blank=True)  # Add missing field
    wave3_monitor_ready_sent = models.BooleanField(default=False)
    wave3_missing_code_sent = models.BooleanField(default=False)
    wave3_survey_monitor_return_sent = models.BooleanField(default=False)
    wave3_survey_monitor_return_date = models.DateField(null=True, blank=True)
    randomized_group = models.IntegerField(null=True, blank=True)
    
    # Intervention tracking fields
    intervention_access_granted = models.BooleanField(default=False)
    intervention_access_date = models.DateTimeField(null=True, blank=True)
    intervention_login_count = models.IntegerField(default=0)
    challenges_completed = models.IntegerField(default=0)
    intervention_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Intervention game tracking
    intervention_points = models.IntegerField(default=0)
    challenge_25_completed = models.BooleanField(default=False)
    challenge_25_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Saves participant information
    def save(self, *args, **kwargs):
        if not self.confirmation_token:
            self.confirmation_token = uuid.uuid4().hex
            while Participant.objects.filter(confirmation_token=self.confirmation_token).exists():
                self.confirmation_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    # Sends email to the participant
    def send_email(self, template_name, extra_context=None, mark_as=None):
            template = EmailTemplate.objects.get(name=template_name)
            context = {'participant_id': self.participant_id, 'username': self.user.username}
            
            # Add survey links for survey-related emails
            if 'survey' in template_name:
                if 'wave1' in template_name:
                    context['survey_link'] = f"{settings.BASE_URL}/survey/wave1/"
                elif 'wave2' in template_name:
                    context['survey_link'] = f"{settings.BASE_URL}/survey/wave2/"
                elif 'wave3' in template_name or 'study_end' in template_name:
                    context['survey_link'] = f"{settings.BASE_URL}/survey/wave3/"
            
            if extra_context:
                context.update(extra_context)
            body = template.body.format(**context)
            try:
                send_mail(
                    template.subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [self.email or self.user.email, 'vuleson59@gmail.com', 'projectpas2024@gmail.com'],
                    fail_silently=False,
                )
                self.email_status = mark_as or 'sent'
                self.email_send_date = timezone.now().date()
                self.save()
            except Exception as e:
                self.email_status = 'failed'
                self.save()
                raise
    # Sends a confirmation email to the participant
    def send_confirmation_email(self):
        confirmation_link = f"{settings.BASE_URL}/confirm-account/{self.confirmation_token}/"
        self.send_email(
            'account_confirmation',
            extra_context={'confirmation_link': confirmation_link}
        )
    def __str__(self):
        return self.user.username
    
    """Info 12"""
    def send_code_entry_email(self):
        template = EmailTemplate.objects.get(name='wave1_code_entry')
        message = template.body.format(
            username=self.user.username,
            code_date=self.code_entry_date.strftime('%m/%d/%Y') if self.code_entry_date else '',
            start_date=(self.code_entry_date + timedelta(days=1)).strftime('%m/%d/%Y') if self.code_entry_date else '',
            end_date=(self.code_entry_date + timedelta(days=7)).strftime('%m/%d/%Y') if self.code_entry_date else ''
        )
    
        
    def send_wave1_survey_return_email(self):
        template = EmailTemplate.objects.get(name='wave1_survey_return')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(
            template.subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email, 'vuleson59@gmail.com', 'projectpas2024@gmail.com'],
            fail_silently=False,
        )
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

    def send_missing_code_email(self):  # Info 14
        template = EmailTemplate.objects.get(name='wave1_missing_code')
        message = template.body.format(username=self.user.username)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()
    def send_wave2_no_monitoring_email(self):  # Info 16 & 19
        template = EmailTemplate.objects.get(name='intervention_access_later' if self.group == 0 else 'wave2_no_monitoring')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

    def send_wave2_survey_email(self):  # Info 17 & 18
        template = EmailTemplate.objects.get(name='intervention_access_immediate' if self.group == 1 and self.intervention_start_date == timezone.now().date() else 'wave2_survey_ready')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

    def send_wave3_survey_email(self):  # Info 20
        template = EmailTemplate.objects.get(name='wave3_survey_ready')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()
    def send_wave3_monitoring_email(self):  # Info 21
        template = EmailTemplate.objects.get(name='wave3_monitoring_ready')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

    def send_wave3_code_entry_email(self):  # Info 23
        try:
            template = EmailTemplate.objects.get(name='wave3_code_entry')
            message = template.body.format(
                participant_id=self.participant_id, 
                code_date=self.wave3_code_entry_date.strftime('%m/%d/%Y') if self.wave3_code_entry_date else '', 
                start_date=(self.wave3_code_entry_date + timezone.timedelta(days=1)).strftime('%m/%d/%Y') if self.wave3_code_entry_date else '', 
                end_date=(self.wave3_code_entry_date + timezone.timedelta(days=7)).strftime('%m/%d/%Y') if self.wave3_code_entry_date else ''
            )
            send_mail(
                template.subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [self.user.email, 'vuleson59@gmail.com'], 
                fail_silently=False
            )
            self.email_status = 'sent'
            self.email_send_date = timezone.now().date()
            self.save()
            return True
        except Exception as e:
            print(f"Wave 3 code entry email error: {str(e)}")
            self.email_status = 'failed'
            self.save()
            return False

    def send_study_end_email(self):  # Info 24
        template = EmailTemplate.objects.get(name='study_end')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

    def send_wave3_missing_code_email(self):  # Info 25
        template = EmailTemplate.objects.get(name='wave3_missing_code')
        message = template.body.format(participant_id=self.participant_id)
        send_mail(template.subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, 'vuleson59@gmail.com'], fail_silently=False)
        self.email_status = 'sent'
        self.email_send_date = timezone.now().date()
        self.save()

#Testing
class ParticipantEntry(models.Model):
    participant_id = models.CharField(max_length=100)
    entry_date = models.DateTimeField(default=timezone.now)
    email = models.EmailField()

    def __str__(self):
        return self.participant_id

class EmailContent(models.Model):
    """ Stores the email contents """
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.subject

class MessageContent(models.Model):
    """ Stores the message contents that are shown on screen """
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sms_body = models.TextField()

    def __str__(self):
        return self.subject
    
class Challenge(models.Model):
    """ Stores user progress in a challenge """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    code = models.CharField(max_length=255, null=True, blank=True)  # For challenges requiring a code
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)

class SurveyProgress(models.Model):
    """ Stores user progress in a survey """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest_submitted = models.BooleanField(default=False)
    interested = models.BooleanField(null=True, blank=True)

    eligibility_submitted = models.BooleanField(default=False)
    is_eligible = models.BooleanField(null=True, blank=True)

    consent_submitted = models.BooleanField(default=False)
    consented = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"SurveyProgress for {self.user.username}"
    
class Token(models.Model):
    """ Stores token values, the user it is sent to, the date it was created, and if it was used by the user """
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Token for {self.recipient.username}"

    @staticmethod
    def generate_token(length=25):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)

class Content(models.Model):
    """Model for researcher-editable website content"""
    CONTENT_TYPES = [
        ('exit_screen', 'Exit Screen Content'),
        ('waiting_screen', 'Waiting Screen Content'),
        ('consent_form', 'Consent Form Content'),
        ('eligibility_interest', 'Eligibility Interest Page'),
        ('home_page', 'Home Page Content'),
    ]
    
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="HTML content that can be edited by researchers")
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_content_type_display()} - {self.title}"

""" The following classes are for storing responses to challenges from users and participants as well as when they created or update their responses. """

class Challenge5Response(models.Model):
    """Stores responses to Introductory Challenge 5 (Self-efficacy, 7 items, 0-4)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge5_responses')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='challenge5_responses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    q1 = models.PositiveSmallIntegerField()
    q2 = models.PositiveSmallIntegerField()
    q3 = models.PositiveSmallIntegerField()
    q4 = models.PositiveSmallIntegerField()
    q5 = models.PositiveSmallIntegerField()
    q6 = models.PositiveSmallIntegerField()
    q7 = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Challenge5Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class WorkRelatedChallenge8Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Easy-to-perform task
    answer2 = models.TextField(blank=True, null=True)  # Increasingly difficult task
    answer3 = models.TextField(blank=True, null=True)  # Specific plan
    answer4 = models.TextField(blank=True, null=True)  # Flexible habit

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WorkRelatedChallenge8Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class WorkRelatedChallenge11Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Past success experiences
    answer2 = models.TextField(blank=True, null=True)  # Mental rehearsal factors
    answer3 = models.TextField(blank=True, null=True)  # Prompts and cues plan
    answer4 = models.TextField(blank=True, null=True)  # General behavior goal
    answer5 = models.TextField(blank=True, null=True)  # Outcome goal
    answer6 = models.TextField(blank=True, null=True)  # Social support plan

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WorkRelatedChallenge11Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class TransportRelatedChallenge13Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Easy-to-perform task
    answer2 = models.TextField(blank=True, null=True)  # Increasingly difficult task
    answer3 = models.TextField(blank=True, null=True)  # Specific plan
    answer4 = models.TextField(blank=True, null=True)  # Flexible habit

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TransportRelatedChallenge13Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class TransportRelatedChallenge16Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Past success experiences
    answer2 = models.TextField(blank=True, null=True)  # Mental rehearsal factors
    answer3 = models.TextField(blank=True, null=True)  # Prompts and cues plan
    answer4 = models.TextField(blank=True, null=True)  # General behavior goal
    answer5 = models.TextField(blank=True, null=True)  # Outcome goal
    answer6 = models.TextField(blank=True, null=True)  # Social support plan

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TransportRelatedChallenge16Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class DomesticRelatedChallenge18Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Easy-to-perform task
    answer2 = models.TextField(blank=True, null=True)  # Increasingly difficult task
    answer3 = models.TextField(blank=True, null=True)  # Specific plan
    answer4 = models.TextField(blank=True, null=True)  # Flexible habit

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DomesticRelatedChallenge18Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class DomesticRelatedChallenge21Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Past success experiences
    answer2 = models.TextField(blank=True, null=True)  # Mental rehearsal factors
    answer3 = models.TextField(blank=True, null=True)  # Prompts and cues plan
    answer4 = models.TextField(blank=True, null=True)  # General behavior goal
    answer5 = models.TextField(blank=True, null=True)  # Outcome goal
    answer6 = models.TextField(blank=True, null=True)  # Social support plan

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DomesticRelatedChallenge21Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class LeisureRelatedChallenge23Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Easy-to-perform task
    answer2 = models.TextField(blank=True, null=True)  # Increasingly difficult task
    answer3 = models.TextField(blank=True, null=True)  # Specific plan
    answer4 = models.TextField(blank=True, null=True)  # Flexible habit

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"LeisureRelatedChallenge23Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class LeisureRelatedChallenge26Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    answer1 = models.TextField(blank=True, null=True)  # Past success experiences
    answer2 = models.TextField(blank=True, null=True)  # Mental rehearsal factors
    answer3 = models.TextField(blank=True, null=True)  # Prompts and cues plan
    answer4 = models.TextField(blank=True, null=True)  # General behavior goal
    answer5 = models.TextField(blank=True, null=True)  # Outcome goal
    answer6 = models.TextField(blank=True, null=True)  # Social support plan

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"LeisureRelatedChallenge26Response(user={self.user.username}, created_at={self.created_at:%Y-%m-%d %H:%M})"

class ChallengeCompletion(models.Model):
    """Track which challenges each user has completed"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    challenge_number = models.IntegerField(help_text="Challenge number (1-35)")
    challenge_name = models.CharField(max_length=100, help_text="Name of the challenge")
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'challenge_number']
        ordering = ['challenge_number']
    
    def __str__(self):
        return f"Challenge {self.challenge_number}: {self.challenge_name} - {self.user.username}"

