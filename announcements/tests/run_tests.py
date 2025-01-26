#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import call_command

def run_tests():
    """Run all lost pets related tests"""
    # Add the project root directory to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    # Setup Django test environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Ensure the test database is created and migrated
    call_command('migrate')
    
    # Get the test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Run specific test modules
    test_modules = [
        'announcements.tests.test_lost_pets',
        'announcements.tests.test_notifications'
    ]
    
    print("Running Lost Pets Tests...")
    print("-" * 70)
    
    # Run the tests
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print("\nSome tests failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    run_tests() 