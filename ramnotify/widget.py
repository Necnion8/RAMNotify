import copy
from typing import Optional, List, Sequence

import wx
import wx.lib.agw.pygauge

__all__ = [
    "PlotLine",
    "PlotCanvas",
    "PyGauge",
]


class PlotLine(object):
    def __init__(self,
                 min_value: float, max_value: float,
                 values: Sequence[float], color: wx.Colour, fill_color: wx.Colour = None):
        self.min_value = min_value
        self.max_value = max_value
        self.values = values
        self.color = color
        self.fill_color = fill_color


class PlotCanvas(wx.Panel):
    _buffer: wx.Bitmap

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name="plotCanvas"):
        wx.Panel.__init__(self, parent, id, pos, size, style, name)

        sizer = wx.FlexGridSizer(2, 2, 0, 0)
        self.canvas = wx.Window(self, -1)

        sizer.Add(self.canvas, 1, wx.EXPAND)

        self.SetSizer(sizer)
        sizer.AddGrowableRow(0, 1)
        sizer.AddGrowableCol(0, 1)
        self.Fit()

        self.border = (1, 1)

        self.SetBackgroundColour(wx.BLACK)

        self._last_draw = None
        self._count = 0
        self.divider = 5

        self.OnSize(None)
        self.canvas.Bind(wx.EVT_PAINT, self.OnPaint)
        self.canvas.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, _: wx.PaintEvent):
        wx.BufferedPaintDC(self.canvas, self._buffer)
        pass

    def OnSize(self, _: Optional[wx.SizeEvent]):
        size = self.canvas.GetClientSize()
        size.width = max(1, size.width)
        size.height = max(1, size.height)

        self._buffer = wx.Bitmap(size.width, size.height)

        if self._last_draw is None:
            self.clear()
        else:
            self.draw(self._last_draw)

    def draw(self, lines: List[PlotLine]):
        dc = wx.BufferedDC(wx.ClientDC(self.canvas), self._buffer)
        dc = wx.GCDC(dc)
        bbr = wx.Brush(self.GetBackgroundColour(), wx.BRUSHSTYLE_SOLID)
        dc.SetBackground(bbr)
        dc.SetBackgroundMode(wx.SOLID)
        dc.Clear()

        self._draw_background_line(dc)

        for line in lines:
            self._draw_line(dc, line)

        self._count += 1
        pass

    def _draw_line(self, dc: wx.DC, line: PlotLine):
        width, height = dc.GetSize()
        min_v, max_v = line.min_value, line.max_value

        val_width = width / (len(line.values) - 1)
        vh = vw = None
        for idx, val in enumerate(line.values):
            val = max(min_v, min(val, max_v))
            val_height = (val - min_v) / (max_v - min_v) * height

            if vh is not None and vw is not None:
                if line.fill_color is not None:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, 0)))
                    dc.SetBrush(wx.Brush(line.fill_color))
                    dc.DrawPolygon(
                        (
                            (vw, height - vh),
                            (vw + val_width, height - val_height),
                            (vw + val_width, height),
                            (vw, height),
                        ),
                    )

                dc.SetPen(wx.Pen(line.color, width=2))
                dc.DrawLine(vw, height - vh, vw + val_width, height - val_height)

            vh = val_height
            vw = 0 if vw is None else vw + val_width

    def _draw_background_line(self, dc: wx.DC):
        width, height = dc.GetSize()
        dc.SetPen(wx.Pen(wx.Colour(60, 60, 60), width=1))
        h = round(height / 10)
        for n in range(10):
            y = h * n
            dc.DrawLine(0, y, width, y)

        w = round(width / 12)
        for n in range(12):
            x = w * n + (5 - self._count % 5) * round(width / 59)
            dc.DrawLine(x, 0, x, height)

    def clear(self):
        dc = wx.BufferedDC(wx.ClientDC(self.canvas), self._buffer)
        bbr = wx.Brush(self.GetBackgroundColour(), wx.SOLID)
        dc.SetBackground(bbr)
        dc.SetBackgroundMode(wx.SOLID)
        dc.Clear()
        dc.SetTextForeground(self.GetForegroundColour())
        dc.SetTextBackground(self.GetBackgroundColour())
        self._last_draw = None


class PyGauge(wx.lib.agw.pygauge.PyGauge):
    def OnPaint(self, event):
        """
        Handles the ``wx.EVT_PAINT`` event for :class:`PyGauge`.

        :param `event`: a :class:`PaintEvent` event to be processed.
        """

        dc = wx.BufferedPaintDC(self)
        rect = self.GetClientRect()

        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        colour = self.GetBackgroundColour()
        dc.SetBrush(wx.Brush(colour))
        dc.SetPen(wx.Pen(colour))
        dc.DrawRectangle(rect)

        if self._border_colour:
            dc.SetPen(wx.Pen(self.GetBorderColour()))
            dc.DrawRectangle(rect)
            pad = 1 + self.GetBorderPadding()
            rect.Deflate(pad,pad)

        if self.GetBarGradient():
            for i, gradient in enumerate(self._barGradientSorted):
                c1,c2 = gradient
                w = rect.width * (float(self._valueSorted[i]) / self._range)
                r = copy.copy(rect)
                r.width = w
                dc.GradientFillLinear(r, c1, c2, wx.EAST)
        else:
            for i, colour in enumerate(self._barColourSorted):
                dc.SetBrush(wx.Brush(colour))
                dc.SetPen(wx.Pen(colour))
                w = rect.width * (float(self._valueSorted[i]) / self._range)
                r = copy.copy(rect)
                r.width = w
                dc.DrawRectangle(r)

        if self._drawIndicatorText:
            dc.SetFont(self._drawIndicatorText_font)
            dc.SetTextForeground(self._drawIndicatorText_colour)
            drawValue = self._valueSorted[i]

            if self._drawIndicatorText_drawPercent:
                drawValue = (float(self._valueSorted[i]) * 100) / self._range

            drawString = self._drawIndicatorText_formatString.format(drawValue)
            rect = self.GetClientRect()
            (textWidth, textHeight, descent, extraLeading) = dc.GetFullTextExtent(drawString)
            textYPos = (rect.height-textHeight)/2

            if textHeight > rect.height:
                textYPos = 0-descent+extraLeading

            # textXPos = (rect.width-textWidth) / 2
            textXPos = (rect.width - textWidth)

            if textWidth>rect.width:
                textXPos = 0

            dc.DrawText(drawString, textXPos, textYPos)
