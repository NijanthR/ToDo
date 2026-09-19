// TaskFlow Enterprise High-Performance Client Controller
// Features: 0ms Optimistic UI Updates, Instant In-Memory Filter Navigation, Zero Page Reloads

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initDataAttributes();
  initKeyboardShortcuts();
  initSidebarNavigation();
  initTaskToggles();
  initSubtasks();
  initModals();
  initLiveSearch();
  initQuickAdd();
  initTaskDeletes();
  initClearCompleted();
  initEditForm();
});

/* Helper: Initialize Data Attributes (Color dots & Progress) */
function initDataAttributes() {
  document.querySelectorAll('[data-color]').forEach(el => {
    if (el.dataset.color) el.style.backgroundColor = el.dataset.color;
  });
  const bar = document.getElementById('stat-progress-bar');
  if (bar && bar.dataset.progress !== undefined) {
    bar.style.width = bar.dataset.progress + '%';
  }
}

/* Helper: CSRF */
function getCsrfToken() {
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  if (input) return input.value;
  const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
  return cookieMatch ? cookieMatch[1] : '';
}

/* Toast Notifications */
function showToast(message) {
  let rack = document.getElementById('toast-rack');
  if (!rack) {
    rack = document.createElement('div');
    rack.id = 'toast-rack';
    rack.className = 'toast-rack';
    document.body.appendChild(rack);
  }

  const toast = document.createElement('div');
  toast.className = 'toast-pill';
  toast.innerHTML = `<span>${message}</span>`;
  rack.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 120ms ease, transform 120ms ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(4px)';
    setTimeout(() => toast.remove(), 130);
  }, 2200);
}

/* Theme Management */
function initTheme() {
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const savedTheme = localStorage.getItem('taskflow_theme') || 'dark';

  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('taskflow_theme', next);
      updateThemeIcon(next);
      showToast(`Theme: ${next}`);
    });
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('theme-toggle-icon');
  if (!icon) return;
  if (theme === 'light') {
    icon.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
  } else {
    icon.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
  }
}

/* Keyboard Navigation */
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      if (e.key === 'Escape') {
        document.activeElement.blur();
      }
      return;
    }

    if (e.key === '/' || e.key.toLowerCase() === 'n') {
      e.preventDefault();
      const input = document.getElementById('quick-add-title');
      if (input) input.focus();
    } else if (e.key.toLowerCase() === 's') {
      e.preventDefault();
      const search = document.getElementById('live-search-input');
      if (search) search.focus();
    } else if (e.key.toLowerCase() === 't') {
      e.preventDefault();
      document.getElementById('theme-toggle-btn')?.click();
    } else if (e.key === '?') {
      e.preventDefault();
      openModal('shortcuts-modal');
    }
  });
}

/* UI Statistics Synchronization (Instant Client Calculation & Sync) */
function syncStatsFromDOM() {
  const allRows = document.querySelectorAll('.task-item-row');
  const total = allRows.length;
  let completed = 0;
  let highPriority = 0;
  let medPriority = 0;
  let lowPriority = 0;

  allRows.forEach(row => {
    const isCompleted = row.classList.contains('completed');
    if (isCompleted) {
      completed++;
    } else {
      if (row.classList.contains('priority-HIGH')) highPriority++;
      else if (row.classList.contains('priority-LOW')) lowPriority++;
      else medPriority++;
    }
  });

  const pending = total - completed;
  const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

  updateStatsUI({
    total: total,
    completed: completed,
    pending: pending,
    high_priority: highPriority,
    med_priority: medPriority,
    low_priority: lowPriority,
    completion_rate: rate,
  });
}

function updateStatsUI(stats) {
  if (!stats) return;

  const sideTotal = document.getElementById('side-stat-total');
  const sidePending = document.getElementById('side-stat-pending');
  const sideCompleted = document.getElementById('side-stat-completed');
  const sideHigh = document.getElementById('side-stat-high');
  const sideMed = document.getElementById('side-stat-med');
  const sideLow = document.getElementById('side-stat-low');
  const progressText = document.getElementById('stat-progress-text');
  const progressBar = document.getElementById('stat-progress-bar');
  const viewCount = document.getElementById('view-task-count');

  if (sideTotal) sideTotal.textContent = stats.total ?? '';
  if (sidePending) sidePending.textContent = stats.pending ?? '';
  if (sideCompleted) sideCompleted.textContent = stats.completed ?? '';
  if (sideHigh && stats.high_priority !== undefined) sideHigh.textContent = stats.high_priority;
  if (sideMed && stats.med_priority !== undefined) sideMed.textContent = stats.med_priority;
  if (sideLow && stats.low_priority !== undefined) sideLow.textContent = stats.low_priority;

  if (progressText) progressText.textContent = `${stats.completed}/${stats.total} tasks (${stats.completion_rate}%)`;
  if (progressBar) progressBar.style.width = `${stats.completion_rate}%`;
  if (viewCount) {
    const visibleCount = document.querySelectorAll('.task-item-row:not([style*="display: none"])').length;
    viewCount.textContent = `${visibleCount} tasks`;
  }
}

/* Instant 0ms Sidebar Navigation (Client In-Memory Filtering with History) */
function initSidebarNavigation() {
  document.addEventListener('click', (e) => {
    const navLink = e.target.closest('.sidebar-nav-item');
    if (!navLink || e.metaKey || e.ctrlKey || e.shiftKey) return;

    const href = navLink.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http')) return;

    e.preventDefault();

    // Update active sidebar state
    document.querySelectorAll('.sidebar-nav-item').forEach(el => el.classList.remove('active'));
    navLink.classList.add('active');

    // Parse params
    const url = new URL(href, window.location.origin);
    const status = url.searchParams.get('status') || 'all';
    const category = url.searchParams.get('category') || '';
    const priority = url.searchParams.get('priority') || '';

    // Update Title in top bar
    const titleEl = document.querySelector('.view-title');
    if (titleEl) {
      const labelText = navLink.querySelector('.sidebar-nav-item-left span')?.textContent || 'Tasks';
      titleEl.textContent = labelText;
    }

    // Filter Task Rows Instantly (0ms delay!)
    const rows = document.querySelectorAll('.task-item-row');
    rows.forEach(row => {
      const isCompleted = row.classList.contains('completed');
      const rowPriority = row.classList.contains('priority-HIGH') ? 'HIGH' : (row.classList.contains('priority-LOW') ? 'LOW' : 'MEDIUM');
      const rowCategory = row.dataset.category || '';

      let show = true;
      if (status === 'active' && isCompleted) show = false;
      if (status === 'completed' && !isCompleted) show = false;
      if (category && rowCategory !== category) show = false;
      if (priority && rowPriority !== priority) show = false;

      row.style.display = show ? 'flex' : 'none';
    });

    const viewCount = document.getElementById('view-task-count');
    if (viewCount) {
      const visibleCount = document.querySelectorAll('.task-item-row:not([style*="display: none"])').length;
      viewCount.textContent = `${visibleCount} tasks`;
    }

    // Push URL without reload
    window.history.pushState({}, '', href);
  });
}

/* Instant Optimistic Task Checkbox Toggle (0ms Delay) */
function initTaskToggles() {
  document.addEventListener('change', async (e) => {
    if (!e.target.matches('.task-toggle-checkbox')) return;

    const checkbox = e.target;
    const card = checkbox.closest('.task-item-row');
    const taskId = checkbox.dataset.taskId;
    const isChecked = checkbox.checked;

    // 1. Optimistically update UI instantly (0ms)
    card.classList.toggle('completed', isChecked);
    syncStatsFromDOM();

    // 2. Background sync with backend
    try {
      const response = await fetch(`/tasks/${taskId}/toggle/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        }
      });

      if (!response.ok) throw new Error('Network error');
      const data = await response.json();
      if (data.stats) updateStatsUI(data.stats);
    } catch (err) {
      console.error(err);
      // Revert if error
      card.classList.toggle('completed', !isChecked);
      checkbox.checked = !isChecked;
      syncStatsFromDOM();
      showToast('Error syncing status');
    }
  });
}

/* Subtasks Management */
function initSubtasks() {
  // Toggle subtask optimistically
  document.addEventListener('change', async (e) => {
    if (!e.target.matches('.subtask-toggle-checkbox')) return;

    const checkbox = e.target;
    const subtaskId = checkbox.dataset.subtaskId;
    const item = checkbox.closest('.subtask-single-item');
    const isChecked = checkbox.checked;

    item.classList.toggle('done', isChecked);

    try {
      await fetch(`/subtasks/${subtaskId}/toggle/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
    } catch (err) {
      console.error(err);
      item.classList.toggle('done', !isChecked);
      checkbox.checked = !isChecked;
    }
  });

  // Create subtask
  document.addEventListener('submit', async (e) => {
    if (!e.target.matches('.subtask-add-form')) return;
    e.preventDefault();

    const form = e.target;
    const taskId = form.dataset.taskId;
    const input = form.querySelector('.subtask-input');
    const title = input.value.trim();
    if (!title) return;

    input.value = '';

    try {
      const response = await fetch(`/tasks/${taskId}/subtasks/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ title })
      });

      const data = await response.json();
      if (data.success) {
        const list = form.previousElementSibling;
        const newItem = document.createElement('div');
        newItem.className = 'subtask-single-item';
        newItem.innerHTML = `
          <input type="checkbox" class="task-checkbox subtask-toggle-checkbox" style="width: 15px; height: 15px;" data-subtask-id="${data.subtask.id}">
          <span style="flex: 1;">${escapeHtml(data.subtask.title)}</span>
          <button type="button" class="btn-ui-icon subtask-delete-btn" data-subtask-id="${data.subtask.id}" title="Remove step" style="width: 20px; height: 20px; color: var(--priority-high);">&times;</button>
        `;
        list.appendChild(newItem);
        const card = form.closest('.task-item-row');
        updateCardSubtaskProgress(card, data);
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to add step');
    }
  });

  // Delete subtask optimistically
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.subtask-delete-btn');
    if (!btn) return;

    const subtaskId = btn.dataset.subtaskId;
    const item = btn.closest('.subtask-single-item');
    item.remove();

    try {
      await fetch(`/subtasks/${subtaskId}/delete/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
    } catch (err) {
      console.error(err);
    }
  });
}

function updateCardSubtaskProgress(card, data) {
  if (!card || !data) return;
  const badge = card.querySelector('.subtasks-count-badge');
  if (badge) {
    badge.textContent = `${data.completed_count}/${data.total_count}`;
  }
}

/* Instant 0ms Optimistic Quick Add (No Reload!) */
function initQuickAdd() {
  const form = document.getElementById('quick-add-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const input = document.getElementById('quick-add-title');
    const prioritySelect = document.getElementById('quick-add-priority');
    const categorySelect = document.getElementById('quick-add-category');
    const title = input.value.trim();
    if (!title) return;

    const priority = prioritySelect ? prioritySelect.value : 'MEDIUM';
    const categoryId = categorySelect ? categorySelect.value : '';
    const categoryName = categorySelect && categorySelect.selectedIndex > 0 ? categorySelect.options[categorySelect.selectedIndex].text : '';

    // Clear input immediately
    input.value = '';
    showToast('Task added');

    // 1. Prepend optimistic row in DOM immediately
    const tempId = 'temp-' + Date.now();
    const container = document.getElementById('task-list-container');
    const emptyState = document.querySelector('.empty-placeholder');
    if (emptyState) emptyState.remove();

    const newRow = document.createElement('div');
    newRow.className = `task-item-row priority-${priority}`;
    newRow.id = `task-card-${tempId}`;
    newRow.dataset.category = categoryId;
    newRow.innerHTML = `
      <div class="task-item-header">
        <div class="task-item-left">
          <div class="task-checkbox-wrap">
            <input type="checkbox" class="task-checkbox task-toggle-checkbox" data-task-id="${tempId}">
          </div>
          <div>
            <div class="task-title-text">${escapeHtml(title)}</div>
          </div>
        </div>
        <div class="task-meta-tags">
          <span class="tag-badge tag-priority-${priority}">${priority === 'HIGH' ? 'High' : (priority === 'LOW' ? 'Low' : 'Medium')}</span>
          ${categoryId ? `<span class="tag-badge tag-category"><span>${escapeHtml(categoryName)}</span></span>` : ''}
          <div class="task-actions-wrap">
            <button type="button" class="btn-ui-icon task-edit-btn" data-task-id="${tempId}" title="Edit Task">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
            <button type="button" class="btn-ui-icon task-delete-btn" data-task-id="${tempId}" title="Delete Task" style="color: var(--priority-high);">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
      </div>
    `;

    if (container.firstChild) {
      container.insertBefore(newRow, container.firstChild);
    } else {
      container.appendChild(newRow);
    }

    syncStatsFromDOM();

    // 2. Background server creation
    try {
      const response = await fetch('/tasks/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          title: title,
          priority: priority,
          category: categoryId || null,
        })
      });

      const data = await response.json();
      if (data.success) {
        // Update temporary ID with real database ID
        newRow.id = `task-card-${data.task.id}`;
        newRow.querySelectorAll(`[data-task-id="${tempId}"]`).forEach(el => {
          el.dataset.taskId = data.task.id;
        });
        if (data.stats) updateStatsUI(data.stats);
      }
    } catch (err) {
      console.error(err);
    }
  });
}

/* Modals */
function initModals() {
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-modal-target]');
    if (trigger) {
      const modalId = trigger.dataset.modalTarget;
      openModal(modalId);
    }

    if (e.target.closest('[data-modal-close]') || e.target.classList.contains('modal-overlay')) {
      const modal = e.target.closest('.modal-overlay');
      if (modal) closeModal(modal.id);
    }

    const editBtn = e.target.closest('.task-edit-btn');
    if (editBtn) {
      const taskId = editBtn.dataset.taskId;
      loadTaskIntoEditModal(taskId);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
    }
  });
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('open');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('open');
}

async function loadTaskIntoEditModal(taskId) {
  try {
    const res = await fetch(`/tasks/${taskId}/update/`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();

    const form = document.getElementById('edit-task-form');
    if (!form) return;

    form.dataset.taskId = data.id;
    document.getElementById('edit-task-title').value = data.title;
    document.getElementById('edit-task-desc').value = data.description || '';
    document.getElementById('edit-task-priority').value = data.priority;
    if (document.getElementById('edit-task-category')) {
      document.getElementById('edit-task-category').value = data.category || '';
    }
    if (document.getElementById('edit-task-date')) {
      document.getElementById('edit-task-date').value = data.due_date || '';
    }

    openModal('edit-task-modal');
  } catch (err) {
    console.error(err);
    showToast('Failed to load task');
  }
}

function initEditForm() {
  const form = document.getElementById('edit-task-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const taskId = form.dataset.taskId;
    const title = document.getElementById('edit-task-title').value.trim();
    const description = document.getElementById('edit-task-desc').value.trim();
    const priority = document.getElementById('edit-task-priority').value;
    const category = document.getElementById('edit-task-category')?.value || null;
    const dueDate = document.getElementById('edit-task-date')?.value || null;

    closeModal('edit-task-modal');
    showToast('Task updated');

    // Update DOM instantly
    const card = document.getElementById(`task-card-${taskId}`);
    if (card) {
      const titleEl = card.querySelector('.task-title-text');
      if (titleEl) titleEl.textContent = title;

      card.className = `task-item-row priority-${priority} ${card.classList.contains('completed') ? 'completed' : ''}`;
      const priorityTag = card.querySelector('.tag-priority-HIGH, .tag-priority-MEDIUM, .tag-priority-LOW');
      if (priorityTag) {
        priorityTag.className = `tag-badge tag-priority-${priority}`;
        priorityTag.textContent = priority === 'HIGH' ? 'High' : (priority === 'LOW' ? 'Low' : 'Medium');
      }
    }

    try {
      await fetch(`/tasks/${taskId}/update/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
          title: title,
          description: description,
          priority: priority,
          category: category,
          due_date: dueDate,
        })
      });
    } catch (err) {
      console.error(err);
    }
  });
}

/* Instant 0ms Optimistic Task Deletion (No Reload!) */
function initTaskDeletes() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.task-delete-btn');
    if (!btn) return;

    const taskId = btn.dataset.taskId;
    const card = btn.closest('.task-item-row');

    // 1. Remove DOM element instantly (0ms delay!)
    card.style.transition = 'opacity 80ms ease, transform 80ms ease';
    card.style.opacity = '0';
    card.style.transform = 'scale(0.98)';
    setTimeout(() => {
      card.remove();
      syncStatsFromDOM();
    }, 80);

    showToast('Task deleted');

    // 2. Background deletion
    try {
      const response = await fetch(`/tasks/${taskId}/delete/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
      const data = await response.json();
      if (data.stats) updateStatsUI(data.stats);
    } catch (err) {
      console.error(err);
    }
  });
}

/* Instant Clear Completed Tasks */
function initClearCompleted() {
  const btn = document.getElementById('clear-completed-btn');
  if (!btn) return;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();

    // 1. Remove all completed rows instantly
    const completedRows = document.querySelectorAll('.task-item-row.completed');
    completedRows.forEach(row => row.remove());
    syncStatsFromDOM();
    showToast(`Cleared completed tasks`);

    // 2. Background sync
    try {
      const response = await fetch('/tasks/clear-completed/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
      const data = await response.json();
      if (data.stats) updateStatsUI(data.stats);
    } catch (err) {
      console.error(err);
    }
  });
}

/* Realtime Search (0ms Delay) */
function initLiveSearch() {
  const searchInput = document.getElementById('live-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    const taskRows = document.querySelectorAll('.task-item-row');

    taskRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? 'flex' : 'none';
    });

    const viewCount = document.getElementById('view-task-count');
    if (viewCount) {
      const visibleCount = document.querySelectorAll('.task-item-row:not([style*="display: none"])').length;
      viewCount.textContent = `${visibleCount} tasks`;
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
