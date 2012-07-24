
from signalqueue import mappings
from signalqueue.dispatcher import AsyncSignal

test_signal = AsyncSignal(providing_args={

    'instance':             mappings.ModelInstanceMapper,
    'signal_label':         mappings.LiteralValueMapper,

})