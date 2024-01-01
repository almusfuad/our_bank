from django.views.generic import CreateView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction
from accounts.models import UserBankAccount
from .forms import DepositForm, WithdrawFrom, LoanRequestForm, TransferAmountForm
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID, TRANSFER_AMOUNT
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string



def send_transactions_email(user, amount, subject, template):
      # Sending auto mail to user
      message = render_to_string(template, {
                  'user': user,
                  'amount': amount,
      })
      send_email = EmailMultiAlternatives(subject, '', to = [user.email])
      send_email.attach_alternative(message, "text/html")
      send_email.send()
      # sending email finish      


# A single transaction views for make deposit, withdraw and loan
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
      template_name = 'transactions/transaction_form.html'
      model = Transaction
      title = ''
      success_url = reverse_lazy('transaction_report')
      
      
      
      def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            kwargs.update({
                  'account': self.request.user.account
            })
            return kwargs
      
      def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update({
                  'title': self.title,
            })
            return context
      

class DepositMoneyView(TransactionCreateMixin):
      form_class = DepositForm
      title = 'Deposit'
      
      
      def get_initial(self):
            initial = {'transaction_type': DEPOSIT}
            return initial
      
      def form_valid(self, form):
            amount = form.cleaned_data.get('amount')
            account = self.request.user.account
            account.balance += amount          # Add new balance to old balance
            account.save(
                  update_fields = ['balance']
            )
            messages.success(self.request, f'Amount {amount} was deposited to your account successfully.')
            
            # Sending auto mail to user
            send_transactions_email(self.request.user, amount, 'Deposit Balance', 'transactions/deposit_email.html')
      
            
            return super().form_valid(form)           # It inherit the class and make override
      
    
class WithdrawMoneyView(TransactionCreateMixin):
      form_class = WithdrawFrom
      title = 'Withdraw Money'
      
      
      def get_initial(self):
            initial = {'transaction_type': WITHDRAWAL}
            return initial
      
      def form_valid(self, form):
            amount = form.cleaned_data.get('amount')
            account = self.request.user.account
            
            try: 
                  # attempting to withdraw money
                  account.balance -= amount          # Subtract request balance to old balance
                  account.save(
                        update_fields = ['balance']
                  )
                  messages.success(self.request, f'Amount {amount} was withdrawal from your account successfully.')
                  
                  send_transactions_email(self.request.user, amount, 'Withdrawal Balance', 'transactions/withdrawal_email.html')
            
                  return super().form_valid(form)           # It inherit the class and make override
            except Exception:
                  messages.error(self.request, f'The bank is bankrupt.')
                  return self.form_invalid(form)
      
     
class LoanRequestView(TransactionCreateMixin):
      form_class = LoanRequestForm
      title = 'Request For Loan'
      
      
      def get_initial(self):
            initial = {'transaction_type': LOAN}
            return initial
      
      def form_valid(self, form):
            amount = form.cleaned_data.get('amount')
            current_loan_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = 3, loan_approve = True).count()         # Get the transactions history and filter the result with transaction_type(LOAN) and loan approve is true
            
            if current_loan_count >= 3:
                  return HttpResponse('You have crossed your limits.')
            messages.success(self.request, f'Loan request for {amount} has sent successfully.')
            
            send_transactions_email(self.request.user, amount, 'Loan Request Message', 'transactions/loan_email.html')
            
            return super().form_valid(form)           # It inherit the class and make override
      
      
class TransactionReportView(LoginRequiredMixin, ListView):
      template_name = 'transactions/transaction_report.html'
      model = Transaction
      balance = 0
      title = 'Transaction Report'
      context_object_name = 'report_list'
      
      def get_queryset(self):
            # queryset 1 = if user does not make any filter then show all the result
            queryset = super().get_queryset().filter(
                  account = self.request.user.account
            )
            
            start_date_str = self.request.GET.get('start_date')
            end_date_str = self.request.GET.get('end_date')
            
            
            if start_date_str and end_date_str:
                  start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()        # Make the string date to datetime
                  end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                  
                  # queryset 2 = After filtering with start_date and end_date. __date__gte && __date__lte to filter by date
                  queryset = queryset.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date)      # gte = greater than equal, lte = less than equal
                  
                  self.balance = Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aggregate(Sum('amount'))['amount__sum']
            else:
                  # self.balance = self.request.user.account.balance
                  self.balance = queryset.aggregate(Sum('amount'))['amount__sum']
                  
            return queryset.distinct()
      
      
      def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update({
                  'account': self.request.user.account,
                  'total_amount': self.balance,
            })
            return context


class PayLoanView(LoginRequiredMixin, View):
      def get(self, request, loan_id):
            loan = get_object_or_404(Transaction, id = loan_id)
            
            if loan.loan_approve: 
                  # Update user account balance
                  user_account = loan.account
                  if loan.amount < user_account.balance:
                        user_account.balance -= loan.amount
                        loan.balance_after_transaction = user_account.balance
                        user_account.save()
                        # update loan sheet
                        loan.transaction_type = LOAN_PAID
                        loan.save()
                        return redirect('loan_list')
                  else:
                        messages.error(self.request, f'Loan amount is greater than available balance.')
            return redirect('loan_list')
                  
               
class LoanListView(LoginRequiredMixin, ListView):
      model = Transaction
      template_name = 'transactions/loan_request.html'
      context_object_name = 'loans'
      
      def get_queryset(self):
            user_account = self.request.user.account
            queryset = Transaction.objects.filter(account = user_account, transaction_type = LOAN)
            return queryset
      
      
class TransferMoneyView(TransactionCreateMixin):
      form_class = TransferAmountForm
      title = 'Transfer Amount'
      
      def get_initial(self):
            initial = {'transaction_type': TRANSFER_AMOUNT}
            return initial
      
      def form_valid(self, form):
            amount = form.cleaned_data.get('amount')
            sender_account = self.request.user.account
            recipient_account_number = form.cleaned_data.get('recipient_account_number')
            recipient_account = UserBankAccount.objects.get(account_no = recipient_account_number)
            
            # Update balance for both accounts
            sender_account.balance -= amount
            recipient_account.balance += amount
                  
            sender_account.save(
                  update_fields = ['balance']
            )
            messages.success(self.request, f'Transfer amount BDT{amount} to acc_no:{recipient_account} successfully.')
            
            recipient_account.save()
            
            # send email to the sender
            sender = self.request.user
            send_transactions_email(sender, amount, 'Send Money', 'transactions/send_money_email.html')
            
            # send email to the recipient
            receiver = recipient_account.user
            send_transactions_email(receiver, amount, 'Receive Money', 'transactions/receive_money_email.html')
            
            return super().form_valid(form)
                  