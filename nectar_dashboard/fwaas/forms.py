from django import forms


class LaunchForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField()

    def clean(self):
        cleaned_data = super(LaunchForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

class BackupForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())

class RecoverForm(forms.Form):
    deact_key = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    backup_id = forms.CharField()

class UpgradeForm(forms.Form):
    deact_key = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
