from crispy_forms.helper import FormHelper
from django import forms
from SyncVideo.rooms.models import Room, Video, ChatMessage, Category


class VideoForm(forms.ModelForm):
    video_id = forms.CharField(
                        label='',
                        required=False,
                        widget=forms.TextInput(attrs={
                           'placeholder':'Enter video URL',
                           'required': 'True'
                        }))

    class Meta:
        model = Video
        fields = ["video_id"]


class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('url', 'visibility')
        labels = {
            'url': 'Enter a shorthand name for your room:',
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ('message',)
        widgets = {
            'message': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Type your message here...'}),
        }


class EditRoomForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Room
        fields = ['url', 'description', 'categories', 'visibility']


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EditRoomForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.creator != self.user:
            raise forms.ValidationError("You are not authorized to edit this room.")
        return cleaned_data


class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'file', ]

    def __init__(self, *args, **kwargs):
        super(VideoUploadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = 'display_none'