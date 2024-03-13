from django.contrib import messages
from django.contrib.auth import views as auth_views, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, LogoutView
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.urls import reverse_lazy
from django.views import generic as generic_views

from SyncVideo.rooms.models import Room
from SyncVideo.user_auth.forms import ProfileCreateForm, UserUpdateForm, DeleteProfileForm


class UserRegisterView(generic_views.CreateView):
    form_class = ProfileCreateForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        result = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Account created successfully!')
        return result


class UserLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('index')

    def get_success_url(self):
        if self.success_url:
            return self.success_url
        return super().get_success_url()


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('index')


@login_required
def details_profile(request):
    user = request.user
    rooms = Room.objects.filter(creator=user)
    context = {'user': user, 'rooms': rooms}
    return render(request, 'accounts/details_profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f"{field}: {error}")

    return render(request, 'accounts/edit_profile.html', {'form': form})



@login_required
def delete_profile(request):
    if request.method == 'POST':
        form = DeleteProfileForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Account deleted successfully.')
            return redirect('index')
    else:
        form = DeleteProfileForm(request.user)

    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f"{field}: {error}")

    return render(request, 'accounts/delete_profile.html', {'form': form})


class UserChangePasswordView(PasswordChangeView):
    template_name = 'accounts/password.html'
    success_url = reverse_lazy('/')

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        res = super().form_valid(form)
        messages.success(self.request, 'Password changed successfully.')
        return res