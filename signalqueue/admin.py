import os
from django.contrib import admin
from signalqueue.utils import SQ_ROOT

admin.site.index_template = os.path.join(SQ_ROOT, 'templates/admin/index_with_queues.html')
admin.site.app_index_template = os.path.join(SQ_ROOT, 'templates/admin/app_index.html')

import signalqueue.models
admin.site.register(signalqueue.models.EnqueuedSignal)
