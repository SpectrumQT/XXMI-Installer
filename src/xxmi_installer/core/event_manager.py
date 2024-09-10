import logging

import app
import core.update_manager as update_manager
from core.asset_managers import launcher_manager as launcher_manager

log = logging.getLogger(__name__)


Application = app.ApplicationEvents
LauncherManager = launcher_manager.LauncherManagerEvents
UpdateManager = update_manager.UpdateManagerEvents

events = {}


def Fire(event, **kw):
    # self.event_generate(f'<<{str(event)}>>', **kw)
    log.debug(f'FIRED: {str(event)}')
    callbacks = events.get(event.__class__.__qualname__, None)
    if callbacks is not None:
        for callback in callbacks:
            callback(event, **kw)


def Subscribe(event, callback):
    event = event.__qualname__
    if event not in events:
        events[event] = [callback]
    else:
        events[event].append(callback)