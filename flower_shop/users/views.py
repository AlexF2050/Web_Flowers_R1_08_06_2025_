from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('home')  # Перенаправление на главную страницу
        else:
            # Возвращаем форму с ошибками
            return render(request, 'users/register.html', {'form': form})
    else:
        form = RegistrationForm()
        return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')  # Убедитесь, что маршрут 'home' существует
        else:
            return render(request, 'users/login.html', {'error': 'Неверные данные'})
    return render(request, 'users/login.html')

@login_required
def profile(request):
    # Получаем расширенную информацию о пользователе
    user = request.user
    context = {
        'user': user,
        'phone': user.phone if hasattr(user, 'phone') else None  # Если есть поле phone в модели
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✔ Профиль успешно обновлён')
            # Убираем редирект, перезагружаем страницу
            return redirect('users:profile_edit')  # Перенаправляем на ту же страницу

    else:
        form = UserProfileForm(instance=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, "Профиль успешно обновлён")
        return redirect('edit_profile')

    return render(request, 'users/profile_edit.html', {
        'form': form,
        'messages': messages.get_messages(request)  # Явная передача сообщений
    })