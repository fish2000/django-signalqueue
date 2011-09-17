import os
import signalqueue
import signalqueue.models
from django.contrib import admin

admin.site.register(signalqueue.models.EnqueuedSignal)
admin.site.index_template = os.path.join(signalqueue.SQ_ROOT, 'templates/admin/index_with_queues.html')
admin.site.app_index_template = os.path.join(signalqueue.SQ_ROOT, 'templates/admin/app_index.html')
