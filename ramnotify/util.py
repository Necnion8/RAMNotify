import wx

__all__ = [
    "freezing",
]


class _Freezing(object):
    def __init__(self, *window: wx.Window):
        self.windows = window
        self._frozen = None

    def __enter__(self):
        self._frozen = [win.IsFrozen() for win in self.windows]
        for idx, win in enumerate(self.windows):
            if not self._frozen[idx]:
                win.Freeze()
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        for idx, win in enumerate(self.windows):
            if not self._frozen[idx]:
                win.Thaw()
        return


def freezing(*window: wx.Window):
    return _Freezing(*window)
