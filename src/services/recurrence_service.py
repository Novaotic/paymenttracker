"""Service for generating recurring transaction instances."""

from datetime import date, timedelta
from typing import List
from dateutil.relativedelta import relativedelta

from src.models.transaction import Transaction, RecurrencePattern, TransactionType
from src.services.transaction_service import TransactionService


class RecurrenceService:
    """Service for generating recurring transaction instances from templates."""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Initialize recurrence service.
        
        Args:
            transaction_service: TransactionService instance
        """
        self.transaction_service = transaction_service
    
    def generate_instances(
        self,
        template: Transaction,
        start_date: date,
        end_date: date,
        regenerate_existing: bool = False
    ) -> List[Transaction]:
        """
        Generate recurring transaction instances from a template.
        
        Args:
            template: Template transaction (must have is_template=True)
            start_date: Start date for generation (inclusive)
            end_date: End date for generation (inclusive)
            regenerate_existing: If True, regenerate instances that already exist
            
        Returns:
            List of generated transaction instances
        """
        if not template.is_template:
            raise ValueError("Template transaction must have is_template=True")
        
        if template.recurrence_pattern is None:
            raise ValueError("Template must have a recurrence_pattern")
        
        # Generate dates based on pattern
        instance_dates = self._generate_dates(
            template.date,
            template.recurrence_pattern,
            start_date,
            end_date
        )
        
        # Filter out dates before template start date
        instance_dates = [d for d in instance_dates if d >= template.date]
        
        # Get existing instances
        existing_instances = self.transaction_service.get_transaction_instances(template.id)
        existing_dates = {inst.date for inst in existing_instances}
        
        generated = []
        for instance_date in instance_dates:
            # Skip if already exists and not regenerating
            if instance_date in existing_dates and not regenerate_existing:
                continue
            
            # Create instance
            instance = Transaction(
                date=instance_date,
                amount=template.amount,
                type=template.type,
                description=template.description,
                category=template.category,
                payee=template.payee,
                recurring_template_id=template.id,
                is_template=False,
                recurrence_pattern=None
            )
            
            generated.append(instance)
        
        return generated
    
    def _generate_dates(
        self,
        start_date: date,
        pattern: RecurrencePattern,
        range_start: date,
        range_end: date
    ) -> List[date]:
        """
        Generate dates for a recurrence pattern within a date range.
        
        Args:
            start_date: Starting date for the pattern
            pattern: Recurrence pattern
            range_start: Start of date range (inclusive)
            range_end: End of date range (inclusive)
            
        Returns:
            List of dates
        """
        dates = []
        current_date = start_date
        
        if pattern == RecurrencePattern.WEEKLY:
            # Move to first occurrence within range or start_date, whichever is later
            if start_date < range_start:
                # Calculate how many weeks to skip
                weeks_to_skip = (range_start - start_date).days // 7
                current_date = start_date + timedelta(weeks=weeks_to_skip)
                # Ensure we're at least at range_start
                if current_date < range_start:
                    current_date = current_date + timedelta(weeks=1)
            
            while current_date <= range_end:
                dates.append(current_date)
                current_date += timedelta(weeks=1)
        
        elif pattern == RecurrencePattern.BIWEEKLY:
            # Move to first occurrence within range or start_date, whichever is later
            if start_date < range_start:
                # Calculate how many biweeks to skip
                biweeks_to_skip = (range_start - start_date).days // 14
                current_date = start_date + timedelta(weeks=biweeks_to_skip * 2)
                # Ensure we're at least at range_start
                if current_date < range_start:
                    current_date = current_date + timedelta(weeks=2)
            
            while current_date <= range_end:
                dates.append(current_date)
                current_date += timedelta(weeks=2)
        
        elif pattern == RecurrencePattern.MONTHLY:
            # Check if start_date is the last day of its month
            start_month = start_date.month
            start_year = start_date.year
            if start_month == 12:
                next_month_start = date(start_year + 1, 1, 1)
            else:
                next_month_start = date(start_year, start_month + 1, 1)
            start_month_last_day = (next_month_start - timedelta(days=1)).day
            use_last_day = (start_date.day == start_month_last_day)
            
            # Move to first occurrence within range or start_date, whichever is later
            current_date = max(start_date, range_start)
            # If current_date is not the same day of month as start_date, adjust
            # to the next occurrence
            if current_date.day != start_date.day and not use_last_day:
                # Move to the same day of month, or last day of month if needed
                try:
                    current_date = date(current_date.year, current_date.month, start_date.day)
                except ValueError:
                    # Day doesn't exist in this month (e.g., Feb 30), use last day
                    if current_date.month == 12:
                        next_month = date(current_date.year + 1, 1, 1)
                    else:
                        next_month = date(current_date.year, current_date.month + 1, 1)
                    current_date = next_month - timedelta(days=1)
                
                # If we went before range_start, move to next month
                if current_date < range_start:
                    current_date = current_date + relativedelta(months=1)
                    # Adjust day if needed
                    if use_last_day:
                        if current_date.month == 12:
                            next_month = date(current_date.year + 1, 1, 1)
                        else:
                            next_month = date(current_date.year, current_date.month + 1, 1)
                        current_date = next_month - timedelta(days=1)
                    else:
                        try:
                            current_date = date(current_date.year, current_date.month, start_date.day)
                        except ValueError:
                            # Use last day of month
                            if current_date.month == 12:
                                next_month = date(current_date.year + 1, 1, 1)
                            else:
                                next_month = date(current_date.year, current_date.month + 1, 1)
                            current_date = next_month - timedelta(days=1)
            
            # Start from the template's start date if it's later than current_date
            if start_date > current_date:
                current_date = start_date
            
            while current_date <= range_end:
                dates.append(current_date)
                # Move to next month, preserving day of month or using last day
                try:
                    current_date = current_date + relativedelta(months=1)
                    if use_last_day:
                        # Always use last day of month
                        if current_date.month == 12:
                            next_month = date(current_date.year + 1, 1, 1)
                        else:
                            next_month = date(current_date.year, current_date.month + 1, 1)
                        current_date = next_month - timedelta(days=1)
                    else:
                        # Try to set the same day of month
                        try:
                            current_date = date(current_date.year, current_date.month, start_date.day)
                        except ValueError:
                            # Day doesn't exist (e.g., Jan 31 -> Feb), use last day of month
                            if current_date.month == 12:
                                next_month = date(current_date.year + 1, 1, 1)
                            else:
                                next_month = date(current_date.year, current_date.month + 1, 1)
                            current_date = next_month - timedelta(days=1)
                except Exception:
                    break
        
        return dates
    
    def generate_all_instances_up_to(
        self,
        end_date: date,
        regenerate_existing: bool = False
    ) -> List[Transaction]:
        """
        Generate all recurring transaction instances up to a future date.
        
        Args:
            end_date: Generate instances up to this date (inclusive)
            regenerate_existing: If True, regenerate instances that already exist
            
        Returns:
            List of all generated transaction instances
        """
        templates = self.transaction_service.get_template_transactions()
        all_instances = []
        
        for template in templates:
            # Generate from template's date to end_date
            instances = self.generate_instances(
                template,
                template.date,
                end_date,
                regenerate_existing
            )
            
            # Save instances to database
            for instance in instances:
                saved_instance = self.transaction_service.create_transaction(instance)
                all_instances.append(saved_instance)
        
        return all_instances

