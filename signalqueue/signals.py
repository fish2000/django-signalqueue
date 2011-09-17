
from signalqueue import mappings
from signalqueue.dispatcher import AsyncSignal

test_signal = AsyncSignal(providing_args={

    'instance':             mappings.ModelInstanceMap,
    'signal_label':         mappings.IDMap,

})