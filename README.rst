
===============
django-delegate
===============

With django-delegate, you get AUTOMATICALLY CHAINABLE MANAGER/QUERYSET DELEGATE METHODS.

Normally, by defining manager methods, Django lets you do this:

::

    >>> SomeModel.objects.custom_query()

... but it WON'T let you do this:

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

