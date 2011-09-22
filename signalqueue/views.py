
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseNotFound
from signalqueue.models import WorkerExceptionLog

@user_passes_test(lambda user: user.is_superuser)
@login_required
def exception_log_entry(request, pk=0):
    try:
        log_entry = WorkerExceptionLog.objects.get(pk=pk)
    except WorkerExceptionLog.DoesNotExist:
        return HttpResponseNotFound()
    else:
        return HttpResponse(log_entry.html)
    

