from django import forms
from models import Profile
from django.contrib.auth.models import User


class PostForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea)



class ProfileEditForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField(label="jabber jid", required=False)
    class Meta:
        model = Profile
        fields = ('name', 'url', 'comment', 'avatar', 'is_off', 'email')

    def __init__(self, *args, **kwargs):
        ins = kwargs['instance']
        kwargs['initial'] = {'username':ins.user.username,'email': ins.user.email}
        super(ProfileEditForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        user = self.instance.user
        instance = super(ProfileEditForm, self).save(*args, **kwargs)
        user_save = False
        data = self.cleaned_data
        new_username = data['username']
        if user.username != new_username:
            user.username = new_username
            user_save = True
        new_email = data['email']
        if new_email and user.email != new_email:
            user.email = new_email
            user_save = True

        if user_save:
            user.save()

        return instance

    def clean_email(self):
        data = self.cleaned_data
        email = data.get('email')
        if email and User.objects.filter(email=email
                ).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError("New jid exists!")
        return email

    def clean_username(self):
        data = self.cleaned_data
        username = data.get('username')
        if User.objects.filter(username=username
                ).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError("New username exists!")

        return username


