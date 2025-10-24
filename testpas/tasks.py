# from bz2 import compress
from datetime import timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command
from testpas import settings
from django.utils import timezone
import random
from testpas.models import Participant, EmailTemplate, UserSurveyProgress
import logging
from testpas.management.commands.seed_email_template import EMAIL_TEMPLATES
from testpas.utils import get_current_time
from .models import User
from .timeline import get_study_day
logger = logging.getLogger(__name__)
from .timeline import get_timeline_day
### Jun 11: Add in run_daily_timeline_checks task among other tasks
@shared_task
def run_daily_timeline_checks():
    for user in User.objects.all():
        daily_timeline_check(user)

## Jun 11: Add in run_daily_timeline_checks task among other tasks. 
## This is rewritten send_scheduled_emails() function.
def daily_timeline_check(user):
    seconds_per_day = getattr(settings, 'SECONDS_PER_DAY', 86400)
    compressed = getattr(settings, 'TIME_COMPRESSION', False)

    """----------------------This is real time. Turn this one ON in production----------------------------------"""
    # today = get_timeline_day(user, compressed=settings.TIME_COMPRESSION, seconds_per_day=settings.SECONDS_PER_DAY)
    """---------------------------------------------------------------------------------------------------------"""
    
    """----------------------This is TIME COMPRESSION TESTING. Turn this one OFF in production------------------"""
    now = get_current_time()
    
    # Get user progress to use the same day_1 as frontend
    user_progress = UserSurveyProgress.objects.filter(
        user=user, 
        survey__title="Eligibility Criteria"
    ).first()
    
    if user_progress and user_progress.day_1:
        today = get_study_day(
            user_progress.day_1,
            now=now,
            compressed=compressed,
            seconds_per_day=seconds_per_day,
            reference_timestamp=user_progress.timeline_reference_timestamp
        )
    else:
        # Fallback to user.date_joined if no progress found
        today = get_timeline_day(
            user, 
            now=now,
            compressed=compressed,
            seconds_per_day=seconds_per_day,
            )
    """---------------------------------------------------------------------------------------------------------"""
    participant = getattr(user, 'participant', None)
    if not participant:
        print(f"[SKIP] No participant for user {user.id}")
        return
    
    # Skip participants who have completed the study (Day 112+)
    if today and today > 112:
        print(f"[SKIP] User {user.id} completed study (Day {today} > 112)")
        return
        
    # study_day = get_timeline_day(user, compressed=settings.TIME_COMPRESSION, seconds_per_day=settings.SECONDS_PER_DAY)
    print(f"[CHECK] User {user.id}, Day {today}, Status: {participant.email_status}")

    # Info 9 – Day 1: Wave 1 Online Survey Ready
    if today and today == 1 and participant.email_status != 'sent_wave1_survey':
        participant.send_email("wave1_survey_ready", mark_as='sent_wave1_survey')

    # Info 10 – Day 8: Wave 1 Physical Activity Monitoring – Ready
    # Send at 7 AM CT in real-time mode; in time-compression, send immediately when day==8
    if today and today == 8 and not participant.code_entry_date and participant.email_status != 'sent_wave1_monitor':
        if not settings.TIME_COMPRESSION:
            # Enforce 7 AM Central Time (CT) for real-time mode
            from pytz import timezone as tz
            ct = tz('US/Central')
            now_ct = timezone.now().astimezone(ct)
            if now_ct.hour == 7:
                participant.send_email("wave1_monitor_ready", mark_as='sent_wave1_monitor')
        else:
            participant.send_email("wave1_monitor_ready", mark_as='sent_wave1_monitor')

    # Info 14 – Day 22: Missing Code Entry (Wave 1)
    if today and today == 22 and not participant.code_entered and participant.email_status != 'sent_wave1_missing':
        participant.send_email("wave1_missing_code")
        participant.email_status = 'sent_wave1_missing'
        participant.save()

    # Info 13 – 7 days after code entry: Return Monitor (Wave 1)
    if participant.code_entry_day is not None:
        code_day = participant.code_entry_day  # Use stored timeline day directly
        if today == code_day + 7 and participant.email_status != 'sent_wave1_survey_return':
            print(f"[SEND] Info 13 (Return Monitor) to user {user.id}")
            participant.send_email("wave1_survey_return")
            participant.email_status = 'sent_wave1_survey_return'
            participant.save()

    # Info 15 – Day 29: Randomization
    """
    The following Python code is checking if today is the 29th day of the month and if the participant's
    # randomized_group is None. If these conditions are met, it then randomizes the participant, sets
    # the randomized_group, and saves the changes.
    Information 15: (Website) Double-Blind Randomization
 	On Day 29, randomize (i.e., equal chance of being assigned to either group) the participants into either Group 0 (usual care group [i.e., control group]) or Group 1 (intervention group) at 7 AM Central Time (CT).
 
	    Group 0 (i.e., the usual care group) will be given the access to the intervention after the data collection is done from Day 113. 
    There will be no expiration date for the access for Group 0. We will not track their engagement with the intervention (e.g., the number of challenges completed) from Group 0.

    	Group 1 (i.e., the intervention group) will be given the access to the intervention from Day 29 to Day 56. We will track their engagement with the intervention (e.g., the number of challenges completed) from Group 1.
    """
    # # Info 15 – Day 29: Randomization
    # # On Day 29, randomize participants into Group 0 (control) or Group 1 (intervention) if not already randomized.
    # if today and 29 <= today <= 30 and participant.randomized_group is None:
    #     import random
    #     group = random.choice([0, 1])
    #     participant.randomized_group = group
    #     participant.group = group  # Also set the group field for consistency
    #     participant.group_assigned = True  # Mark as assigned
    #     participant.save()
    #     print(f"[RANDOMIZE] User {user.id} assigned to Group {group}")

    #     if participant.randomized_group == 0:
    #         participant.send_email("intervention_access_later", extra_context={
    #             "username": user.username
    #         })
    #     elif participant.randomized_group == 1:
    #         participant.send_email("intervention_access_immediate", extra_context={
    #             "username": user.username,
    #             "login_link": settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "https://your-login-page.com" ## to be updated with the actual login page in production.
    #         })
    ############### NEW DOUBLE BLIND RANDOMIZATION MECHANICS STARTS HERE ######################
    #Pair 1: TEST001 (Position 1) + TEST002 (Position 2)
    #Pair 2: TEST003 (Position 1) + TEST004 (Position 2) #########################################
    
    # Info 15 – Day 29: 2-Block Randomization
    # On Day 29, randomize participants using 2-block randomization procedure
    if today and today == 29 and not participant.randomization_completed:
        # Check if we need to assign this participant to a pair
        if participant.randomization_pair_id is None:
            # Find the next available pair or create a new one
            last_pair = Participant.objects.filter(
                randomization_pair_id__isnull=False
            ).order_by('-randomization_pair_id').first()
            
            if last_pair is None:
                # First participant ever
                pair_id = 1
                position = 1
            else:
                # Check if the last pair is complete (has 2 participants)
                pair_participants = Participant.objects.filter(
                    randomization_pair_id=last_pair.randomization_pair_id
                ).count()
                
                if pair_participants < 2:
                    # Join the existing incomplete pair
                    pair_id = last_pair.randomization_pair_id
                    position = 2
                else:
                    # Create a new pair
                    pair_id = last_pair.randomization_pair_id + 1
                    position = 1
            
            participant.randomization_pair_id = pair_id
            participant.randomization_position = position
            participant.save()
        
        # Now perform the 2-block randomization
        pair_participants = Participant.objects.filter(
            randomization_pair_id=participant.randomization_pair_id
        ).order_by('id')  # Order by enrollment time (earlier ID = earlier enrollment)
        
        if len(pair_participants) == 2:
            # Both participants in the pair are ready for randomization
            import random
            
            # First participant (earlier enrollment) gets random assignment
            first_participant = pair_participants[0]
            second_participant = pair_participants[1]
            
            # Fair coin flip for first participant
            first_group = random.choice([0, 1])
            second_group = 1 - first_group  # Opposite group
            
            # Assign groups
            first_participant.randomized_group = first_group
            first_participant.group = first_group
            first_participant.group_assigned = True
            first_participant.randomization_completed = True
            first_participant.save()
            
            second_participant.randomized_group = second_group
            second_participant.group = second_group
            second_participant.group_assigned = True
            second_participant.randomization_completed = True
            second_participant.save()
            
            print(f"[2-BLOCK RANDOMIZE] Pair {participant.randomization_pair_id}: "
                  f"First participant (ID {first_participant.id}) -> Group {first_group}, "
                  f"Second participant (ID {second_participant.id}) -> Group {second_group}")
            
            # Send notification emails
            if first_participant.randomized_group == 0:
                first_participant.send_email("intervention_access_later", extra_context={
                    "username": first_participant.user.username
                })
            elif first_participant.randomized_group == 1:
                first_participant.send_email("intervention_access_immediate", extra_context={
                    "username": first_participant.user.username,
                    "login_link": settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "https://your-login-page.com"
                })
            
            if second_participant.randomized_group == 0:
                second_participant.send_email("intervention_access_later", extra_context={
                    "username": second_participant.user.username
                })
            elif second_participant.randomized_group == 1:
                second_participant.send_email("intervention_access_immediate", extra_context={
                    "username": second_participant.user.username,
                    "login_link": settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "https://your-login-page.com"
                })
        else:
            print(f"[2-BLOCK RANDOMIZE] Pair {participant.randomization_pair_id} waiting for second participant")
    ############### NEW DOUBLE BLIND RANDOMIZATION MECHANICS ENDS HERE ######################
    """
    Information 18: Day 57: Wave 2 Survey Ready
    (Email) Wave 2 Online Survey Set – Ready. On Day 57, send this email to every participant from any group.  
    """
    if today and today == 57 and not participant.wave2_survey_email_sent:
        participant.send_email(
            "wave2_survey_ready",
            extra_context={
                # "participant_id": participant.participant_id,
                "username": participant.user.username,
            }
        )
        participant.wave2_survey_email_sent = True
        participant.save()

    """
    Information 21: Day 67 – Send No Wave 2 Monitoring Email
    (Email) Wave 2 No Monitoring Email – Ready. On Day 67, send this email to every participant from any group.  
    """
    # Day 67 – Send No Wave 2 Monitoring Email
    if today and 67 <= today <= 68 and not participant.wave2_monitoring_notice_sent:
        participant.send_email(
            "wave2_no_monitoring",
            extra_context={
                # "participant_id": participant.participant_id,
                "username": participant.user.username,
            }
        )
        participant.wave2_monitoring_notice_sent = True
        participant.save()

    """
    Information 21: Day 113: Wave 3 Survey Ready
    (Email) Wave 3 Online Survey Set – Ready. On Day 113, send this email to every participant from any group.  
    """
    if today and today == 113 and not participant.wave3_survey_email_sent:
        participant.send_email(
            "wave3_survey_ready", 
            extra_context={
                "username": user.username})
        participant.wave3_survey_email_sent = True
        participant.save()

    """
    Information 23: Day 120: Wave 3 Monitoring Ready
    (Email) Wave 3 Physical Activity Monitoring Ready. On Day 120, send this email to every participant from any group.  
    """
    if today and today == 120 and not participant.wave3_monitor_ready_sent:
        participant.send_email("wave3_monitoring_ready", extra_context={"username": user.username})
        participant.wave3_monitor_ready_sent = True
        participant.save()

    # Info 27 – Day 134: Missed Wave 3 Code Entry (Study End)
    if today and today == 134 and not participant.wave3_code_entered and not participant.wave3_missing_code_sent:
        participant.send_email("wave3_missing_code")
        participant.wave3_missing_code_sent = True
        participant.save()

    # Info 24 – 8 days after Wave 3 code entry: Study End Survey & Monitor Return
    if hasattr(participant, 'wave3_code_entry_day') and participant.wave3_code_entry_day is not None:
        wave3_code_day = participant.wave3_code_entry_day
        if today and today >= wave3_code_day + 8 and not participant.wave3_survey_monitor_return_sent:
            participant.send_email("study_end")
            participant.wave3_survey_monitor_return_sent = True
            participant.wave3_survey_monitor_return_date = timezone.now().date()
        participant.save()

@shared_task
def send_wave1_survey_return_email(participant_id):
    """Information 13: Survey by Today & Return Monitor (Wave 1)"""
    try:
        participant = Participant.objects.get(id=participant_id)
        if participant.email_status == 'sent_wave1_survey_return':
            logger.info(f"Skipping wave1_survey_return for {participant.email}: already sent")
            return
        # Schedule 8 days after code_entry_date at 7 AM CT
        now = timezone.now()
        send_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now.hour >= 7:
            send_time += timedelta(days=1)
        participant.send_email('wave1_survey_return', extra_context={'username': participant.user.username})
        participant.email_status = 'sent_wave1_survey_return'
        participant.save()
        logger.info(f"Sent wave1_survey_return to {participant.email}")
    except Participant.DoesNotExist:
        logger.error(f"Participant {participant_id} not found for wave1_survey_return")
    except Exception as e:
        logger.error(f"Error sending wave1_survey_return for participant {participant_id}: {str(e)}")

@shared_task
def send_wave1_code_entry_email(participant_id):
    """Information 12: Physical Activity Monitoring Tomorrow (Wave 1)"""
    try:
        participant = Participant.objects.get(id=participant_id)
        # Check email_status to prevent duplicates
        if participant.email_status == 'sent_wave1_code':
            logger.info(f"Skipping wave1_code_entry for {participant.email}: already sent")
            return
        code_date = participant.code_entry_date
        if not code_date:
            logger.error(f"No code entry date for participant {participant_id}")
            return
        start_date = code_date + timedelta(days=1)
        end_date = code_date + timedelta(days=7)
        # Send immediately at 7 AM CT
        now = timezone.now()
        send_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now.hour >= 7:
            send_time += timedelta(days=1)
        participant.send_email(
            'wave1_code_entry',
            extra_context={
                'username': participant.user.username,
                'code_date': code_date.strftime('%m/%d/%Y'),
                'start_date': start_date.strftime('%m/%d/%Y'),
                'end_date': end_date.strftime('%m/%d/%Y'),
            }
        )
        participant.email_status = 'sent_wave1_code'
        participant.save()
        logger.info(f"Sent wave1_code_entry to {participant.email}")
    except Participant.DoesNotExist:
        logger.error(f"Participant {participant_id} not found for wave1_code_entry")
    except Exception as e:
        logger.error(f"Error sending wave1_code_entry for participant {participant_id}: {str(e)}")

@shared_task
def send_wave1_monitoring_email(participant_id):
    """Send Wave 1 Physical Activity Monitoring email to participant."""
    """Information 10: Wave 1 Physical Activity Monitoring Ready"""
    try:
        participant = Participant.objects.get(id=participant_id)
        template = EmailTemplate.objects.get(name='wave1_monitor_ready')
        context = {'participant_id': participant.participant_id}
        body = template.body.format(**context)
        send_mail(
            template.subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [participant.email or participant.user.email, 'svu23@iastate.edu', 'vuleson59@gmail.com', 'projectpas2024@gmail.com'],
            fail_silently=False,
        )
        participant.email_status = 'sent'
        participant.email_send_date = timezone.now().date()
        participant.save()
        logger.info(f"Sent Wave 1 monitoring email to {participant.participant_id}")
    except Participant.DoesNotExist:
        logger.error(f"Participant {participant_id} not found")
    except EmailTemplate.DoesNotExist:
        logger.error("Wave 1 monitor ready email template not found")
    except Exception as e:
        logger.error(f"Failed to send Wave 1 monitoring email to {participant_id}: {e}")

@shared_task
def send_wave3_code_entry_email(participant_id):
    """Information 23: Physical Activity Monitoring Tomorrow (Wave 3)"""
    try:
        participant = Participant.objects.get(id=participant_id)
        
        # Calculate dates
        code_date = participant.wave3_code_entry_date
        if not code_date:
            logger.error(f"No Wave 3 code entry date for participant {participant_id}")
            return
            
        start_date = code_date + timedelta(days=1)
        end_date = code_date + timedelta(days=7)
        
        participant.send_email(
            'wave3_code_entry',
            extra_context={
                'code_date': code_date.strftime('%m/%d/%Y'),
                'start_date': start_date.strftime('%m/%d/%Y'),
                'end_date': end_date.strftime('%m/%d/%Y'),
            }
        )
        logger.info(f"Sent Wave 3 code entry email to {participant.participant_id}")
    except Exception as e:
        logger.error(f"Error sending Wave 3 code entry email: {str(e)}")

@shared_task
def send_study_end_email(participant_id):
    """Information 24: Survey and Monitor Return Email (Study End)"""
    try:
        participant = Participant.objects.get(id=participant_id)
        
        # Check if already sent
        if participant.wave3_survey_monitor_return_sent:
            logger.info(f"Study end email already sent for participant {participant_id}")
            return
            
        participant.send_email('study_end')
        participant.wave3_survey_monitor_return_sent = True
        participant.wave3_survey_monitor_return_date = timezone.now().date()
        participant.save()
        
        logger.info(f"Sent study end email to {participant.participant_id}")
    except Exception as e:
        logger.error(f"Error sending study end email: {str(e)}")

@shared_task
def send_wave3_missing_code_email(participant_id):
    """Information 25: Missing Code Entry Email (Study End)"""
    try:
        participant = Participant.objects.get(id=participant_id)
        
        # Check if already sent
        if participant.wave3_missing_code_sent:
            logger.info(f"Wave 3 missing code email already sent for participant {participant_id}")
            return
            
        participant.send_email('wave3_missing_code')
        participant.wave3_missing_code_sent = True
        participant.save()
        
        logger.info(f"Sent Wave 3 missing code email to {participant.participant_id}")
    except Exception as e:
        logger.error(f"Error sending Wave 3 missing code email: {str(e)}")


@shared_task
def run_randomization():
    call_command('randomize_participants')
