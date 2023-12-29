from django import forms
from .models import Transaction
from django.core.exceptions import ValidationError

class TransactionForm(forms.ModelForm):
      class Meta:
            model = Transaction
            fields = ['amount', 'transaction_type']
            
            
      def __init__(self, *args, **kwargs):
            self.account = kwargs.pop('account') # Take account
            super().__init__(*args, **kwargs)
            self.fields['transaction_type'].disabled = True # Disable the field
            self.fields['transaction_type'].widget = forms.HiddenInput() #Hide from user
            
      def save(self, commit = True):
            # instance will call the model and find the object
            self.instance.account = self.account
            self.instance.balance_after_transaction = self.account.balance
            return super().save()
      

class DepositForm(TransactionForm):
      # For filtering amount. clean_fieldName to do validation on that field.
      def clean_amount(self):
            min_deposit_amount = 500
            amount = self.cleaned_data.get('amount') # Take amount field value
            if amount < min_deposit_amount:
                  raise forms.ValidationError(
                        f'You need to deposit at least {min_deposit_amount}'
                  )
            return amount


class WithdrawFrom(TransactionForm):
      def clean_amount(self):
            account = self.account
            min_withdraw_amount = 500
            max_withdraw_amount = 20000
            balance = account.balance
            amount = self.cleaned_data.get('amount')
            if amount < min_withdraw_amount:
                  raise forms.ValidationError(
                        f'You can withdraw at least {min_withdraw_amount}'
                  )
                  
            if amount > max_withdraw_amount:
                  raise forms.ValidationError(
                        f'You can withdraw at most {max_withdraw_amount}'
                  )
            
            if amount > balance:
                  raise forms.ValidationError(
                        f'You have {balance} in your account. '
                        'You can not withdraw more than your account balance.'
                  )
            
            return amount
      

class LoanRequestForm(TransactionForm):
      def clean_amount(self):
            amount = self.cleaned_data.get('amount')
            
            return amount