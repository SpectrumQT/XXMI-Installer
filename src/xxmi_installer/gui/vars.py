
import customtkinter

import core.event_manager as Events


gui_vars = {}


def new(frame, setting_container, setting_name):
    setting_value = getattr(setting_container, setting_name)
    if isinstance(setting_value, bool):
        var = customtkinter.BooleanVar(master=frame, value=setting_value)
    elif isinstance(setting_value, str):
        var = customtkinter.StringVar(master=frame, value=setting_value)
    elif isinstance(setting_value, int):
        var = customtkinter.IntVar(master=frame, value=setting_value)
    elif isinstance(setting_value, float):
        var = customtkinter.DoubleVar(master=frame, value=setting_value)
    else:
        raise ValueError(f'Unsupported settings var type {type(setting_value)}!')
    gui_vars[setting_name] = (var, setting_container)
    return gui_vars[setting_name][0]


def save():
    for setting_name, (var, setting_container) in gui_vars.items():
        old_value = getattr(setting_container, setting_name)
        new_value = var.get()
        setattr(setting_container, setting_name, new_value)
        if new_value != old_value:
            Events.Fire(Events.Application.SettingsUpdate(
                name=setting_name,
                value=new_value,
            ))


def announce():
    for setting_name, (var, setting_container) in gui_vars.items():
        old_value = getattr(setting_container, setting_name)
        Events.Fire(Events.Application.SettingsUpdate(
            name=setting_name,
            value=old_value,
        ))