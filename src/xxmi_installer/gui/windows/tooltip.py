from tktooltip import ToolTip


def CTkToolTip(target, message, **kwargs):
    default = {'delay': 0.5, 'follow': True, 'padx': 7, 'pady': 7, 'fg': "black", 'bg': "white", 'parent_kwargs': {"bg": "black", "padx": 1, "pady": 1}}
    default.update(kwargs)
    return ToolTip(target, msg=message, **default)
