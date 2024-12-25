from eventmanager import Evt
from .fpvscores import FPVScores
from .fpvs_export import FPVSExport


def initialize(rhapi):
    fpvscores = FPVScores(rhapi)
    fpvs_export = FPVSExport(rhapi)

    rhapi.events.on(Evt.STARTUP, fpvscores.init_plugin)

    rhapi.events.on(Evt.CLASS_ADD, fpvscores.class_listener,  priority = 20)
    rhapi.events.on(Evt.CLASS_ALTER, fpvscores.class_listener,  priority = 50)
    rhapi.events.on(Evt.CLASS_DELETE, fpvscores.class_delete)

    rhapi.events.on(Evt.HEAT_GENERATE, fpvscores.heat_listener, priority = 99)
    rhapi.events.on(Evt.HEAT_ALTER, fpvscores.heat_listener)
    rhapi.events.on(Evt.HEAT_DELETE, fpvscores.heat_delete)

    rhapi.events.on(Evt.PILOT_ADD, fpvscores.pilot_listener, priority = 99)
    rhapi.events.on(Evt.PILOT_ALTER, fpvscores.pilot_listener)
    #rhapi.events.on(Evt.PILOT_DELETE, fpvscores.pilot_listener)

    rhapi.events.on(Evt.LAPS_SAVE, fpvscores.results_listener)
    rhapi.events.on(Evt.LAPS_RESAVE, fpvscores.results_listener)

    rhapi.events.on(Evt.DATA_EXPORT_INITIALIZE, fpvs_export.register_handlers)