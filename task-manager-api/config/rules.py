"""Constantes de domínio usadas por models, services e serializers."""

TASK_STATUS_PENDING = 'pending'
TASK_STATUS_IN_PROGRESS = 'in_progress'
TASK_STATUS_DONE = 'done'
TASK_STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = [TASK_STATUS_PENDING, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE, TASK_STATUS_CANCELLED]
# Tasks nesses estados nunca contam como atrasadas
CLOSED_TASK_STATUSES = (TASK_STATUS_DONE, TASK_STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2   # prioridade <= 2 conta como alta no relatório do usuário
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAGS_SEPARATOR = ','

ROLE_USER = 'user'
VALID_ROLES = [ROLE_USER, 'admin', 'manager']
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_COLOR = '#000000'
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'

RECENT_ACTIVITY_DAYS = 7
FAKE_TOKEN_PREFIX = 'fake-jwt-token-'   # token sem verificação; ver README
