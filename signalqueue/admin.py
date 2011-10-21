import os, socket
from django.contrib import admin
from signalqueue.utils import SQ_ROOT

class WorkerExceptionLogAdmin(admin.ModelAdmin):
    
    class Media:
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js',
        )
    
    save_as = True
    save_on_top = True
    actions_on_top = True
    actions_on_bottom = True
    
    date_hierarchy = 'createdate'
    list_display = ('id', 'with_html')
    list_display_links = ('id',)
    list_per_page = 10
    
    def with_html(self, obj):
        out = u"""
            <div class="exception-html" id="exception-html-%s">
                <h3 class="exception-html">
                    <a href="#">Details for &#8220;%s&#8221;</a>
                </h3>
                <div class="exception-html-details">
                    <iframe name="exception-html-iframe-%s" id="exception-html-iframe-%s"
                        src="%s"
                        width="100%%" height="400" scrolling="auto">
                    </iframe>
                </div>
            </div>
            <script type="text/javascript">
                $(document).ready(function() {
                    $("#exception-html-%s").accordion({
                        active: false,
                        autoHeight: false,
                        animated: true,
                        collapsible: true,
                        changestart: function (e, ui) {
                            $('#exception-html-iframe-%s').attr('src', '%s');
                            window.frames['exception-html-iframe-%s'].location.reload();
                        }
                    });
                });
            </script>
        """ % (
            obj.pk,
            obj.message,
            obj.pk,
            obj.pk,
            #"http://%s%s" % (socket.gethostname().lower(), obj.get_absolute_url()),
            obj.get_absolute_url(),
            obj.pk,
            obj.pk,
            #"http://%s%s" % (socket.gethostname().lower(), obj.get_absolute_url()),
            obj.get_absolute_url(),
            obj.pk,
        )
        
        return out or u'<i style="color: lightgray;">No Info</i>'
    with_html.short_description = "Exception Traceback"
    with_html.allow_tags = True


admin.site.index_template = os.path.join(SQ_ROOT, 'templates/admin/index_with_queues.html')
admin.site.app_index_template = os.path.join(SQ_ROOT, 'templates/admin/app_index.html')

import signalqueue.models
admin.site.register(signalqueue.models.EnqueuedSignal)
admin.site.register(signalqueue.models.WorkerExceptionLog, WorkerExceptionLogAdmin)
