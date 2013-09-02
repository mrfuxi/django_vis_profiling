from django import forms


class ProfileFileForm(forms.Form):
    prof_file = forms.FileField(
        label='Select a profile file',
    )
