
==================
django-signalqueue
==================

After a certain amount of time anyone concerning themselves with the Django framework is going
to ask the question:

What is up with signals???
==========================

Soon after that, the person asking this question will sit back in their chair and say, "Ahaaaa...
Hmmmm yes I see. They aren't asynchronous, or multithreaded, or symmetric; nor are they concurrent or reentrant or
simultaneous in any fashion. Huh."

Now look, I love signals -- I point this out because coming to terms with the fact that signals are basically 
a completely synchronous centralized-callback registry type of thing, the implementation of which will look 
spiffy right off while slowly confounding you throughout the marginally longer term, resisting the ex-post-facto
testing approach that you adopted when you finally sorted out what django signals were actually doing -- what all
the enigmatic hoohah with, like, stuff all like the Heisenbergian-y weakref-based connections, arg options like
"dispatch_uid" which (if you go and look) have implementations that are some kind of Einstein/Macgyver hybrid,
bending python's uglier and harsher edges into a probalistic weapon of NP-hardness... yes, like that, clearly, OR... or
actually when you sit down and give it the benefit of the doubt, the signals code is basically an unclear mess. 


Look, Stuff in there doesn't work like it says it does. Many of the flaws were right there, if you read the source... 
I did not need to write enormous test suites, or wade through terabytes of log data, or any of that shit. Look at this bit --

::

    def send_robust(self, sender, **named):
        """
        Send signal from sender to all connected receivers catching errors.

        Arguments:
        
            sender
                The sender of the signal. Can be any python object (normally one
                registered with a connect if you actually want something to
                occur).

            named
                Named arguments which will be passed to receivers. *These
                arguments must be a subset of the argument names defined in
                providing_args.*

        Return a list of tuple pairs [(receiver, response), ... ]. May raise
        DispatcherKeyError.

        If any receiver raises an error (specifically any subclass of
        Exception), the error instance is returned as the result for that
        receiver.
        """
        responses = []
        if not self.receivers:
            return responses

        # Call each receiver with whatever arguments it can accept.
        # Return a list of tuple pairs [(receiver, response), ... ].
        for receiver in self._live_receivers(_make_id(sender)):
            try:
                response = receiver(signal=self, sender=sender, **named)
            except Exception, err:
                responses.append((receiver, err))
            else:
                responses.append((receiver, response))
        return responses

-- which this couldn't stand the scrutiny of a casual code-review, like say e.g. this implementation of `Signal.send()` from `django.dispatch.dispatcher`:

Emphasis is mine -- this isn't some nightly tarball or third-order github fork, this is from the certified Release Quality
Django 1.3 stuff. It's pretty hillarious when you finally read through it all -- you may not find this one method as funny as I do,
just because there is ABSOLUTELY NOTHING to back up the claim about the `providing_args` subset requirement for `**kwargs` (or `**named`;
so which ok, you'd expect the signals author to be a beautiful and unique snoflake who is way to special for )


::

    >>> SomeModel.objects.custom_query().another_custom_query()

... unless you duplicate your methods and define a redundant queryset subclass... UNTIL NOW. 

With DelegateManager and @delegate, you can write maintainable custom-query logic
with free chaining. instead of defining manager methods, you define queryset methods,
decorate those you'd like to delegate, and a two-line DelegateManager subclass
specifying the queryset. ET VIOLA. Like so:

::

    class CustomQuerySet(models.query.QuerySet):
    
        @delegate
        def qs_method(self, some_value):
            return self.filter(some_param__icontains=some_value)
    
        def dont_delegate_me(self):
            return self.filter(some_other_param="something else")
    
    class CustomManager(DelegateManager):
        __queryset__ = CustomQuerySet
    
    class SomeModel(models.Model):
        objects = CustomManager()
    
    
    # will work:
    SomeModel.objects.qs_method('yo dogg')
    # will also work:
    SomeModel.objects.qs_method('yo dogg').qs_method('i heard you like queryset method delegation')

To delegate all of the methods in a QuerySet automatically, you can create a subclass
of DelegateQuerySet. These two QuerySet subclasses work identically:

::

    class ManualDelegator(models.query.QuerySet):
        @delegate
        def qs_method(self):
            # ...
    
    class AutomaticDelegator(DelegateQuerySet):
        def qs_method(self):
            # ...


You can also apply the @delegate decorator directly to a class -- this permits you to
delegate all the methods in a class without disrupting its inheritance chain. This example
works identically to the previous two:

::

    @delegate
    class CustomQuerySet(models.query.QuerySet):
    
        def qs_method(self, some_value):
            return self.filter(some_param__icontains=some_value)

