# ============================================================================
# FILE: questionnaires/management/commands/setup_question_types.py
# ============================================================================

from django.core.management.base import BaseCommand
from questionnaires.models import QuestionType

class Command(BaseCommand):
    help = 'Create default question types'

    def handle(self, *args, **options):
        question_types = [
            {
                'name': QuestionType.MULTIPLE_CHOICE,
                'description': 'Questions with four options (A, B, C, D) where only one is correct'
            },
            {
                'name': QuestionType.TRUE_FALSE,
                'description': 'Questions that can be answered with True or False'
            },
            {
                'name': QuestionType.IDENTIFICATION,
                'description': 'Questions requiring specific terms, names, or concepts as answers'
            },
            {
                'name': QuestionType.ESSAY,
                'description': 'Open-ended questions requiring detailed written responses'
            },
            {
                'name': QuestionType.FILL_BLANK,
                'description': 'Sentences or paragraphs with missing words to be filled in'
            },
            {
                'name': QuestionType.MATCHING,
                'description': 'Questions where items in two columns must be matched'
            },
        ]

        for qt_data in question_types:
            qt, created = QuestionType.objects.get_or_create(
                name=qt_data['name'],
                defaults={'description': qt_data['description']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created question type: {qt.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Question type already exists: {qt.get_name_display()}')
                )

        self.stdout.write(self.style.SUCCESS('\nSetup complete!'))