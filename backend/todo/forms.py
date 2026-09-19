from django import forms
from django.contrib.auth.models import User
from .models import Task, Category, SubTask


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'field-input',
            'placeholder': 'Enter your username',
            'required': True,
            'autocomplete': 'off',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
            'onpointerdown': "this.removeAttribute('readonly');",
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'field-input',
            'placeholder': 'email@example.com (optional)',
            'autocomplete': 'off',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'field-input',
            'placeholder': 'Create a password (min 6 characters)',
            'required': True,
            'autocomplete': 'new-password',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
            'onpointerdown': "this.removeAttribute('readonly');",
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'field-input',
            'placeholder': 'Confirm your password',
            'required': True,
            'autocomplete': 'new-password',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
            'onpointerdown': "this.removeAttribute('readonly');",
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        if password and len(password) < 6:
            self.add_error('password', 'Password must be at least 6 characters long.')
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'field-input',
            'placeholder': 'Enter your username',
            'required': True,
            'autocomplete': 'off',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
            'onpointerdown': "this.removeAttribute('readonly');",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'field-input',
            'placeholder': 'Enter your password',
            'required': True,
            'autocomplete': 'new-password',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
            'onpointerdown': "this.removeAttribute('readonly');",
        })
    )


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'field-input',
                'placeholder': 'What needs to be done?',
                'required': True,
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'field-textarea',
                'placeholder': 'Add details, notes, or links (optional)...',
                'rows': 3,
            }),
            'category': forms.Select(attrs={
                'class': 'field-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'field-select',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'field-input',
                'type': 'date',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "No Category"
        self.fields['category'].required = False
        self.fields['due_date'].required = False
        if user and user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(user=user)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'field-input',
                'placeholder': 'Category name...',
                'required': True,
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-color-picker',
                'type': 'color',
                'value': '#6366f1',
            }),
        }


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'subtask-inline-input',
                'placeholder': 'Add step...',
                'required': True,
                'autocomplete': 'off',
            }),
        }
