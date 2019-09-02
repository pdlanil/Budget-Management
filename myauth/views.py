
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from income.models import Income
from django.contrib.auth.decorators import login_required
from category.models import Category
from .forms import IncomeForm, ExpensesForm
from category.forms import CategoryForm
from django.db.models import Sum
import datetime
from expenses.models import Expenses
import calendar


# Create your views here.
def signup(request):
    if request.method == 'GET':
        context = {
            'form': UserCreationForm()
        }
        return render(request, 'signup.html', context)
    else:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
        return render(request, 'signup.html', {'form': form})


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html')
    else:
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return redirect('signin')


@login_required(login_url='signin')
def dashboard(request):
    expdata = expcategorySum(request.user.id)
    expyearlydata = expcategorySumYearly(request.user.id)
    saving = Saving(request.user.id)
    context = {
        'expdata': expdata,
        'expyeardata':expyearlydata,
        'saving':saving,

    }
    return render(request, 'dashboard.html', context)


def my_logout(request):
    logout(request)
    return redirect('signin')


# INCOME

def income(request):
    if request.method == 'GET':
        context = {
            'form': IncomeForm(),
            'income': Income.objects.filter(user_id=request.user.id, date__month=getCurrentMonth(),
                                            date__year=getCurrentYear()),
            'total': Income.objects.filter(user_id=request.user.id, date__month=getCurrentMonth(),
                                           date__year=getCurrentYear()).aggregate(Sum('rupes')),
            'year': getCurrentYear(),
            'month': getCurrentMonth(),
            'previncome': getPreviousMonthData(request.user.id),
            'prevtotal': getPreviousMonthData(request.user.id).aggregate(Sum('rupes'))

        }
        return render(request, 'income.html', context)
    else:
        form = IncomeForm(request.POST)
        if form.is_valid():
            mydata = form.save(commit=False)
            mydata.user_id = request.user.id
            mydata.save()
            return redirect('income')
        return render(request, 'income.html', {'form': form})


def getPreviousMonthData(id):
    today_month = datetime.date.today().month
    today_year = datetime.date.today().year

    if (today_month != 1):
        previous_month = today_month - 1
        previous_month_year = today_year
    else:
        previous_month = 12
        previous_month_year = today_year - 1

    return Income.objects.filter(user_id=id, date__month=previous_month, date__year=previous_month_year)


def income_edit(request, id):
    data = Income.objects.get(pk=id)
    form = IncomeForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('income')
    context = {
        'form': form
    }
    return render(request, 'income_edit.html', context)


def income_delete(request, id):
    income = Income.objects.get(request.user.id)
    income.delete()
    return redirect('income')


# EXPENSES

@login_required(login_url='signin')
def expenses(request):
    if request.method == 'GET':
        context = {
            'form': ExpensesForm(request.user),
            'monthexpenses': Expenses.objects.filter(user_id=request.user.id, date__month=getCurrentMonth(),
                                                     date__year=getCurrentYear()),
            'monthexpensessum': Expenses.objects.filter(user_id=request.user.id, date__month=getCurrentMonth(),
                                                        date__year=getCurrentYear()).aggregate(Sum('rupes')),
            'year': getCurrentYear(),
            'month': getCurrentMonth(),
            'prevmonthexpenses': getPreviousMonthExpenses(request.user.id),
            'previousmonthexpensestotal': getPreviousMonthExpenses(request.user.id).aggregate(Sum('rupes')),

        }
        return render(request, 'expenses.html', context)
    else:
        form = ExpensesForm(request.user, request.POST, request.FILES)
        context = {}
        if form.is_valid():
            data = form.save(commit=False)
            data.user = request.user
            data.save()
            context.update({'msg': 'successfully added'})
        context.update({'form': form})
        return redirect('expense')


def getPreviousMonthExpenses(id):
    today_month = datetime.date.today().month
    today_year = datetime.date.today().year

    if (today_month != 1):
        previous_month = today_month - 1
        previous_month_year = today_year
    else:
        previous_month = 12
        previous_month_year = today_year - 1

    return Expenses.objects.filter(user_id=id, date__month=previous_month, date__year=previous_month_year)


def expenses_edit(request, id):
    data = Expenses.objects.get(pk=id)
    form = ExpensesForm(request.user, request.POST or None, request.FILES or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('expense')

    context = {
        'form': form
    }
    return render(request, 'expenses_edit.html', context)


def expenses_delete(request, id):
    expense = Expenses.objects.get(pk=id)
    expense.delete()
    return redirect('expense')


def category(request):
    if request.method == 'GET':
        context = {
            'form': CategoryForm(),
            'category': Category.objects.filter(user_id=request.user.id)
        }
        return render(request, 'category.html', context)
    else:
        form = CategoryForm(request.POST)
        if form.is_valid():
            data = form.save(commit=False)
            data.user_id = request.user.id
            data.save()
            return redirect('category')
        return render(request, 'category.html', {'form': form})


def category_edit(request, id):
    data = Category.objects.get(pk=id)
    form = CategoryForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('category')

    context = {
        'form': form
    }
    return render(request, 'category_edit.html', context)


def category_delete(request, id):
    category = Category.objects.get(pk=id)
    category.delete()
    return redirect('category')


def getCurrentMonth():
    return datetime.date.today().month


def getCurrentYear():
    return datetime.date.today().year



#Expense ko lae  monthly(piechart)
def expcategorySum(id):
    all_category = Category.objects.filter(user_id=id)
    category_label = []
    category_sum = []
    for x in all_category:
        exp = Expenses.objects.filter(user_id=id, date__month=getCurrentMonth(), date__year=getCurrentYear(),
                                      category_id=x.id).aggregate(Sum('rupes'))
        if exp['rupes__sum'] is not None:
            total = exp['rupes__sum']
        else:
            total = 0
        category_label.append(x.title)
        category_sum.append(total)
    return list(zip(category_label, category_sum))


#expense ko lae yearly data (piechart)

def expcategorySumYearly(id):
    all_category = Category.objects.filter(user_id=id)
    category_label = []
    category_sum = []
    for x in all_category:
        exp = Expenses.objects.filter(user_id=id, date__year=getCurrentYear(),
                                      category_id=x.id).aggregate(Sum('rupes'))
        if exp['rupes__sum'] is not None:
            total = exp['rupes__sum']
        else:
            total = 0
        category_label.append(x.title)
        category_sum.append(total)
    return list(zip(category_label, category_sum))


def Saving(id):
    all_category = Category.objects.filter()
    category_label = []
    category_sum = []
    for x in all_category:
        exp = Expenses.objects.filter( date__year=getCurrentYear(),
                                      category_id=x.id).aggregate(Sum('rupes'))
        inc = Income.objects.filter(date__year=getCurrentYear()).aggregate(Sum('rupes'))
        if exp['rupes__sum'] and inc['rupes__sum'] is not None:
            total = exp['rupes__sum']+ inc['rupes__sum']
        else:
            total = 0
        category_label.append(x.title)
        category_sum.append(total)
    return list(zip(category_label, category_sum))


