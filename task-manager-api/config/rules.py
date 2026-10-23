"""Regras de domínio nomeadas (antes espalhadas como literais nas rotas)."""

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2          # prioridade <= 2 conta como "alta" no relatório
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_COLOR = '#000000'
COLOR_PATTERN = r'^#[0-9A-Fa-f]{6}$'

DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7
FAKE_TOKEN_PREFIX = 'fake-jwt-token-'
