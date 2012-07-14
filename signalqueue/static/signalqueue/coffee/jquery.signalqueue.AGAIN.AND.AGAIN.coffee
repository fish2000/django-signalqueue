
$ = jQuery
ß = io.connect('http://queueserver.asio-otus.local/')

class @SQStatus

    defaults =
        interval: 500
        queuename: 'default'

    constructor: (element, options) ->
        @elem = $(element)
        @options = $.extend {}, defaults, options
        @recently = [0,0,0,0,0,0,0,0,0]
        @interval_id = null

    start: () ->
        if not @interval_id
            @interval_id = window.setInterval =>
                ß.emit 'status', @options['queuename'], (data) =>
                    qlen = data.queue_length
                    lastvalues = @recently[..]
                    lastvalues.shift()
                    lastvalues.push qlen
                    if (lastvalues.every (itm) -> (itm == 0))
                        @elem.html("<b>Currently Idle</b>")
                    else
                        @elem.html("<b>#{ qlen }</b> Queued Signals")
            , @options.interval

    stop: () ->
        if @interval_id
            window.clearInterval @interval_id

#$.fn.extend

    sqstatus: (cmd, args...) ->
        command = "#{ cmd }".toLowerCase()
        return @each () ->
            instance = $.data this, 'sqstatus'
            if not instance
                $.data this, 'sqstatus', new SQStatus this, args
            else if typeof options is "string"
                instance[command] args...
