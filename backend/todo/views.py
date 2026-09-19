import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import Task, Category, SubTask
from .forms import TaskForm, CategoryForm, SubTaskForm, RegisterForm, LoginForm


# --- Authentication Views ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('todo:task_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next') or request.POST.get('next')
                return redirect(next_url or 'todo:task_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('todo:task_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            user = User.objects.create_user(username=username, email=email, password=password)

            # Seed default starter categories for new user
            Category.objects.create(user=user, name='Work', color='#3b82f6', icon='briefcase')
            Category.objects.create(user=user, name='Personal', color='#10b981', icon='user')
            Category.objects.create(user=user, name='Study', color='#8b5cf6', icon='book-open')

            # Create welcome task
            welcome_task = Task.objects.create(
                user=user,
                title='Welcome to your TaskFlow workspace!',
                description='Organize your daily tasks, set priorities, and track checklist steps.',
                priority=Task.Priority.HIGH,
                category=Category.objects.filter(user=user, name='Work').first(),
                due_date=timezone.now().date()
            )
            SubTask.objects.create(task=welcome_task, title='Create your first task', is_completed=False)
            SubTask.objects.create(task=welcome_task, title='Explore categories and dark mode', is_completed=False)

            login(request, user)
            messages.success(request, f'Account created successfully! Welcome to TaskFlow, {user.username}.')
            return redirect('todo:task_list')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('todo:login')


# --- Task Statistics & Dashboard ---

def get_task_stats(user):
    today = timezone.now().date()
    aggregates = Task.objects.filter(user=user).aggregate(
        total=Count('id'),
        total_completed=Count('id', filter=Q(completed=True)),
        high_priority=Count('id', filter=Q(completed=False, priority=Task.Priority.HIGH)),
        med_priority=Count('id', filter=Q(completed=False, priority=Task.Priority.MEDIUM)),
        low_priority=Count('id', filter=Q(completed=False, priority=Task.Priority.LOW)),
        overdue=Count('id', filter=Q(completed=False, due_date__lt=today)),
    )
    total = aggregates['total'] or 0
    completed = aggregates['total_completed'] or 0
    pending = total - completed
    high_priority = aggregates['high_priority'] or 0
    med_priority = aggregates['med_priority'] or 0
    low_priority = aggregates['low_priority'] or 0
    overdue = aggregates['overdue'] or 0
    completion_rate = int((completed / total) * 100) if total > 0 else 0

    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'high_priority': high_priority,
        'med_priority': med_priority,
        'low_priority': low_priority,
        'overdue': overdue,
        'completion_rate': completion_rate,
    }


@login_required
def task_list(request):
    user = request.user
    tasks = Task.objects.filter(user=user).select_related('category').prefetch_related('subtasks').all()
    categories = Category.objects.filter(user=user).annotate(
        pending_count=Count('tasks', filter=Q(tasks__completed=False, tasks__user=user)),
        total_count=Count('tasks', filter=Q(tasks__user=user))
    ).all()

    # Filter parameters
    status = request.GET.get('status', 'all')
    category_id = request.GET.get('category', '')
    priority = request.GET.get('priority', '')
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'smart')

    # Apply Status Filter
    if status == 'active':
        tasks = tasks.filter(completed=False)
    elif status == 'completed':
        tasks = tasks.filter(completed=True)

    # Apply Category Filter
    if category_id:
        if category_id == 'none':
            tasks = tasks.filter(category__isnull=True)
        elif category_id.isdigit():
            tasks = tasks.filter(category_id=int(category_id))

    # Apply Priority Filter
    if priority in [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH]:
        tasks = tasks.filter(priority=priority)

    # Apply Search Query
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Apply Sorting
    if sort_by == 'due_date':
        tasks = tasks.order_by('completed', 'due_date', '-priority')
    elif sort_by == 'priority':
        tasks = tasks.order_by('completed', '-priority', 'due_date')
    elif sort_by == 'newest':
        tasks = tasks.order_by('-created_at')
    elif sort_by == 'oldest':
        tasks = tasks.order_by('created_at')
    else:  # Smart default
        tasks = tasks.order_by('completed', '-priority', 'due_date', '-created_at')

    stats = get_task_stats(user)
    form = TaskForm(user=user)
    category_form = CategoryForm()

    context = {
        'tasks': tasks,
        'categories': categories,
        'stats': stats,
        'form': form,
        'category_form': category_form,
        'current_status': status,
        'current_category': category_id,
        'current_priority': priority,
        'current_query': query,
        'current_sort': sort_by,
        'today': timezone.now().date(),
    }
    return render(request, 'todo/index.html', context)


@login_required
@require_POST
def task_create(request):
    user = request.user
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if is_ajax:
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            title = data.get('title', '').strip()
            if not title:
                return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)

            cat_id = data.get('category')
            category = Category.objects.filter(id=cat_id, user=user).first() if cat_id else None

            task = Task.objects.create(
                user=user,
                title=title,
                priority=data.get('priority') or Task.Priority.MEDIUM,
                category=category,
                due_date=data.get('due_date') or None,
                description=data.get('description', ''),
            )
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'completed': task.completed,
                    'priority': task.priority,
                    'priority_display': task.get_priority_display(),
                    'category_id': task.category.id if task.category else None,
                    'category_name': task.category.name if task.category else None,
                    'category_color': task.category.color if task.category else None,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'due_date_formatted': task.due_date.strftime('%b %d') if task.due_date else None,
                    'is_overdue': task.is_overdue,
                    'is_due_today': task.is_due_today,
                },
                'stats': get_task_stats(user),
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    form = TaskForm(request.POST, user=user)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = user
        task.save()
        messages.success(request, f'Task created!')
    return redirect('todo:task_list')


@login_required
@require_http_methods(["GET", "POST"])
def task_update(request, pk):
    user = request.user
    task = get_object_or_404(Task, pk=pk, user=user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if request.method == 'GET':
        if is_ajax:
            return JsonResponse({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'category': task.category_id,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                'completed': task.completed,
            })
        form = TaskForm(instance=task, user=user)
        return render(request, 'todo/task_edit.html', {'form': form, 'task': task})

    # POST update
    if is_ajax:
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            task.title = data.get('title', task.title).strip()
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            cat_id = data.get('category')
            task.category = Category.objects.filter(id=cat_id, user=user).first() if cat_id else None
            task.due_date = data.get('due_date') or None
            task.save()
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'priority': task.priority,
                    'priority_display': task.get_priority_display(),
                    'category_id': task.category.id if task.category else None,
                    'category_name': task.category.name if task.category else None,
                    'category_color': task.category.color if task.category else None,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'due_date_formatted': task.due_date.strftime('%b %d') if task.due_date else None,
                    'is_overdue': task.is_overdue,
                    'is_due_today': task.is_due_today,
                },
                'stats': get_task_stats(user)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    form = TaskForm(request.POST, instance=task, user=user)
    if form.is_valid():
        form.save()
        messages.success(request, f'Task updated!')
    return redirect('todo:task_list')


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save(update_fields=['completed', 'updated_at'])

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'id': task.id,
            'completed': task.completed,
            'stats': get_task_stats(request.user),
        })

    return redirect('todo:task_list')


@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.delete()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'id': pk,
            'stats': get_task_stats(request.user),
        })

    return redirect('todo:task_list')


@login_required
@require_POST
def clear_completed(request):
    deleted_count, _ = Task.objects.filter(user=request.user, completed=True).delete()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'stats': get_task_stats(request.user),
        })

    return redirect('todo:task_list')


# --- Subtasks ---

@login_required
@require_POST
def subtask_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, user=request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

    title = ''
    if is_ajax and request.content_type == 'application/json':
        data = json.loads(request.body)
        title = data.get('title', '').strip()
    else:
        title = request.POST.get('title', '').strip()

    if not title:
        return JsonResponse({'success': False, 'error': 'Title required'}, status=400)

    subtask = SubTask.objects.create(task=task, title=title)

    if is_ajax:
        return JsonResponse({
            'success': True,
            'subtask': {
                'id': subtask.id,
                'title': subtask.title,
                'is_completed': subtask.is_completed,
            },
            'completed_count': task.subtasks_completed_count,
            'total_count': task.subtasks_total_count,
        })

    return redirect('todo:task_list')


@login_required
@require_POST
def subtask_toggle(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk, task__user=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save(update_fields=['is_completed'])
    task = subtask.task

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'id': subtask.id,
            'is_completed': subtask.is_completed,
            'completed_count': task.subtasks_completed_count,
            'total_count': task.subtasks_total_count,
        })

    return redirect('todo:task_list')


@login_required
@require_POST
def subtask_delete(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk, task__user=request.user)
    task = subtask.task
    subtask.delete()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'id': pk,
            'completed_count': task.subtasks_completed_count,
            'total_count': task.subtasks_total_count,
        })

    return redirect('todo:task_list')


# --- Categories ---

@login_required
@require_POST
def category_create(request):
    form = CategoryForm(request.POST)
    if form.is_valid():
        cat = form.save(commit=False)
        cat.user = request.user
        cat.save()
        messages.success(request, f'Category "{cat.name}" created!')
    return redirect('todo:task_list')


@login_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    return redirect('todo:task_list')
