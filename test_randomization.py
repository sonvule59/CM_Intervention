#!/usr/bin/env python
"""
Test script for 2-block randomization system
Run this to test the randomization logic
"""
    #Pair 1: TEST001 (Position 1) + TEST002 (Position 2)
    #Pair 2: TEST003 (Position 1) + TEST004 (Position 2) #########################################
import os
import sys
import django
from datetime import datetime, timedelta
import pytz

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testpas.settings')
django.setup()

from django.contrib.auth.models import User
from testpas.models import Participant, UserSurveyProgress
from testpas.tasks import daily_timeline_check
from testpas.utils import get_current_time

def create_test_participants():
    """Create test participants for randomization testing"""
    print("Creating test participants...")
    
    # Create 4 test users
    test_users = []
    for i in range(1, 5):
        username = f"test_randomization_{i}"
        email = f"projectpas2024@gmail.com"
        
        # Create user if doesn't exist
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"Created user: {username}")
        else:
            print(f"User already exists: {username}")
        
        test_users.append(user)
    
    # Create participants and progress for each user
    participants = []
    for i, user in enumerate(test_users):
        # Create participant
        participant, created = Participant.objects.get_or_create(
            user=user,
            defaults={
                'participant_id': f'TEST{i+1:03d}',
                'age': 30 + i,
                'dominant_hand': 'right',
                'confirmation_token': f'token_{i}',
                'is_confirmed': True
            }
        )
        
        # Create user progress with Day 1 set to trigger randomization
        from testpas.models import Survey
        survey, _ = Survey.objects.get_or_create(
            title="Eligibility Criteria",
            defaults={'description': 'Test survey for randomization'}
        )
        # # Set Day 1 to be 29 days ago to simulate Day 29
        # # Day 29 means 28 days have passed since Day 1
        # day_1_date = datetime.now(pytz.timezone('America/Chicago')).date() - timedelta(days=28)
        # Set Day 1 to be today
        day_1_date = datetime.now(pytz.timezone('America/Chicago')).date()
        
        # Set reference timestamp to be exactly 28 days ago to simulate Day 29
        # With time compression (10 seconds = 1 day), we need 28 * 10 = 280 seconds ago
        reference_timestamp = get_current_time() - timedelta(seconds=280)  # 28 days * 10 seconds
        
        progress, created = UserSurveyProgress.objects.get_or_create(
            user=user,
            survey=survey,
            defaults={
                'eligible': True,
                'consent_given': True,
                'day_1': day_1_date,
                'timeline_reference_timestamp': reference_timestamp
            }
        )
        
        # If not created, update both day_1 and reference timestamp
        if not created:
            progress.day_1 = day_1_date
            progress.timeline_reference_timestamp = reference_timestamp
            progress.save()
        
        participants.append(participant)
        print(f"Created participant: {participant.participant_id}")
    
    return participants

def test_randomization():
    """Test the 2-block randomization system"""
    print("\n" + "="*60)
    print("TESTING 2-BLOCK RANDOMIZATION SYSTEM")
    print("="*60)
    
    # Create test participants
    participants = create_test_participants()
    
    # Show initial state
    print(f"\nInitial state - {len(participants)} participants:")
    for p in participants:
        print(f"  {p.participant_id}: Group={p.randomized_group}, Pair={p.randomization_pair_id}, Position={p.randomization_position}")
    
    # Simulate Day 29 by running the daily timeline check for each participant
    print(f"\nSimulating Day 29 randomization...")
    
    for participant in participants:
        print(f"\nProcessing {participant.participant_id}...")
        
        # Check the current study day before processing
        from testpas.timeline import get_study_day
        from testpas.models import UserSurveyProgress
        from testpas import settings
        
        user_progress = UserSurveyProgress.objects.filter(user=participant.user).first()
        if user_progress:
            current_day = get_study_day(
                user_progress.day_1,
                now=get_current_time(),
                compressed=settings.TIME_COMPRESSION,
                seconds_per_day=settings.SECONDS_PER_DAY,
                reference_timestamp=user_progress.timeline_reference_timestamp
            )
            print(f"  Current study day: {current_day}")
        
        try:
            daily_timeline_check(participant.user)
            
            # Refresh from database
            participant.refresh_from_db()
            print(f"  Result: Group={participant.randomized_group}, Pair={participant.randomization_pair_id}, Position={participant.randomization_position}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show final state
    print(f"\nFinal state after randomization:")
    for p in participants:
        print(f"  {p.participant_id}: Group={p.randomized_group}, Pair={p.randomization_pair_id}, Position={p.randomization_position}")
    
    # Verify 2-block randomization
    print(f"\nVerifying 2-block randomization:")
    pairs = {}
    for p in participants:
        if p.randomization_pair_id:
            if p.randomization_pair_id not in pairs:
                pairs[p.randomization_pair_id] = []
            pairs[p.randomization_pair_id].append(p)
    
    for pair_id, pair_participants in pairs.items():
        if len(pair_participants) == 2:
            p1, p2 = pair_participants
            if p1.randomized_group != p2.randomized_group:
                print(f"  ✓ Pair {pair_id}: {p1.participant_id} (Group {p1.randomized_group}) vs {p2.participant_id} (Group {p2.randomized_group}) - CORRECT")
            else:
                print(f"  ✗ Pair {pair_id}: {p1.participant_id} (Group {p1.randomized_group}) vs {p2.participant_id} (Group {p2.randomized_group}) - ERROR: Same group!")
        else:
            print(f"  ! Pair {pair_id}: Only {len(pair_participants)} participants (should be 2)")
    
    # Check overall balance
    group_0_count = sum(1 for p in participants if p.randomized_group == 0)
    group_1_count = sum(1 for p in participants if p.randomized_group == 1)
    print(f"\nOverall balance:")
    print(f"  Group 0 (Control): {group_0_count} participants")
    print(f"  Group 1 (Intervention): {group_1_count} participants")
    print(f"  Ratio: {group_0_count}:{group_1_count}")

def cleanup_test_data():
    """Clean up test data"""
    print(f"\nCleaning up test data...")
    
    # Delete test users and their associated data
    test_users = User.objects.filter(username__startswith='test_randomization_')
    count = test_users.count()
    test_users.delete()
    
    print(f"Deleted {count} test users and associated data")

if __name__ == "__main__":
    try:
        test_randomization()
        
        # Clean up test data
        print("\nCleaning up test data...")
        cleanup_test_data()
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
