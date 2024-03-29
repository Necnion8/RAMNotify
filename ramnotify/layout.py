#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.9.4 on Mon Feb 19 16:23:08 2024
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
import wx.lib.agw.ultimatelistctrl as ulc
from widget import PlotCanvas
# end wxGlade


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.SYSTEM_MENU
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = RamNotifyPanel(self, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("frame")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_14 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_14.Add(self.panel, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_14)
        sizer_14.Fit(self)
        self.Layout()
        self.Centre()
        # end wxGlade

# end of class MyFrame

class RamNotifyPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: RamNotifyPanel.__init__
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.gauge_used_virtual = wx.Gauge(self, wx.ID_ANY, 100)
        self.text_used_virtual = wx.TextCtrl(self, wx.ID_ANY, "?%", style=wx.TE_READONLY)
        self.slider_limit_virtual = wx.Slider(self, wx.ID_ANY, 1, 1, 100)
        self.spin_limit_virtual = wx.SpinCtrl(self, wx.ID_ANY, "1", min=1, max=100)
        self.check_virtual_notify = wx.CheckBox(self, wx.ID_ANY, u"通知する")
        self.check_virtual_command = wx.CheckBox(self, wx.ID_ANY, u"コマンドを実行する")
        self.text_virtual_command = wx.TextCtrl(self, wx.ID_ANY, "")
        self.btn_call_virtual_command = wx.Button(self, wx.ID_ANY, u"実行")
        self.label_virtual_command_repeat = wx.StaticText(self, wx.ID_ANY, "")
        self.spin_virtual_command_repeat = wx.SpinCtrl(self, wx.ID_ANY, "0", min=0, max=99999999)
        self.gauge_used_swap = wx.Gauge(self, wx.ID_ANY, 100)
        self.text_used_swap = wx.TextCtrl(self, wx.ID_ANY, "?%", style=wx.TE_READONLY)
        self.slider_limit_swap = wx.Slider(self, wx.ID_ANY, 1, 1, 100)
        self.spin_limit_swap = wx.SpinCtrl(self, wx.ID_ANY, "1", min=1, max=100)
        self.check_swap_custom_size = wx.CheckBox(self, wx.ID_ANY, u"最大値を指定 (単位: GB)")
        self.spin_swap_custom_max = wx.SpinCtrl(self, wx.ID_ANY, "", min=1, max=1024)
        self.check_swap_notify = wx.CheckBox(self, wx.ID_ANY, u"通知する")
        self.check_swap_command = wx.CheckBox(self, wx.ID_ANY, u"コマンドを実行する")
        self.text_swap_command = wx.TextCtrl(self, wx.ID_ANY, "")
        self.btn_call_swap_command = wx.Button(self, wx.ID_ANY, u"実行")
        self.label_swap_command_repeat = wx.StaticText(self, wx.ID_ANY, "")
        self.spin_swap_command_repeat = wx.SpinCtrl(self, wx.ID_ANY, "0", min=0, max=99999999)
        self.choice_refresh_rate = wx.Choice(self, wx.ID_ANY, choices=[u"0.5秒", u"1秒", u"2秒", u"5秒", u"10秒", u"30秒", u"1分", u"5分"])
        self.choice_notify_cool = wx.Choice(self, wx.ID_ANY, choices=[u"1分", u"5分", u"10分", u"15分", u"30分", u"1時間", u"2時間", u"4時間", u"6時間"])
        self.choice_task_bar_icon = wx.Choice(self, wx.ID_ANY, choices=[u"シンプル", u"物理メモリの使用率", u"論理メモリの使用率"])
        self.button_quit = wx.Button(self, wx.ID_ANY, u"終了")
        self.button_github = wx.BitmapButton(self, wx.ID_ANY, wx.NullBitmap)
        self.check_processlist = wx.CheckBox(self, wx.ID_ANY, u"プロセス一覧")
        self.button_close = wx.Button(self, wx.ID_ANY, u"適用＆閉じる")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_SLIDER, self.on_change_value, self.slider_limit_virtual)
        self.Bind(wx.EVT_TEXT, self.on_change_value, self.spin_limit_virtual)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_virtual_notify)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_virtual_command)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.btn_call_virtual_command)
        self.Bind(wx.EVT_TEXT, self.on_change_value, self.spin_virtual_command_repeat)
        self.Bind(wx.EVT_SLIDER, self.on_change_value, self.slider_limit_swap)
        self.Bind(wx.EVT_TEXT, self.on_change_value, self.spin_limit_swap)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_swap_custom_size)
        self.Bind(wx.EVT_TEXT, self.on_change_value, self.spin_swap_custom_max)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_swap_notify)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_swap_command)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.btn_call_swap_command)
        self.Bind(wx.EVT_TEXT, self.on_change_value, self.spin_swap_command_repeat)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.button_quit)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.button_github)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_processlist)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.button_close)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: RamNotifyPanel.__set_properties
        self.gauge_used_virtual.SetToolTip(u"現在の使用率")
        self.text_used_virtual.SetMinSize((50, -1))
        self.text_used_virtual.SetToolTip(u"現在の使用率\n")
        self.spin_limit_virtual.SetMinSize((50, -1))
        self.btn_call_virtual_command.SetMinSize((50, 24))
        self.spin_virtual_command_repeat.SetMinSize((50, -1))
        self.gauge_used_swap.SetToolTip(u"現在の使用率\n")
        self.text_used_swap.SetMinSize((50, -1))
        self.text_used_swap.SetToolTip(u"現在の使用率\n")
        self.spin_limit_swap.SetMinSize((50, -1))
        self.btn_call_swap_command.SetMinSize((50, 24))
        self.spin_swap_command_repeat.SetMinSize((50, -1))
        self.choice_refresh_rate.SetMinSize((65, -1))
        self.choice_refresh_rate.SetSelection(0)
        self.choice_notify_cool.SetMinSize((65, -1))
        self.choice_notify_cool.SetSelection(0)
        self.choice_task_bar_icon.SetSelection(0)
        self.button_quit.SetMinSize((-1, 23))
        self.button_github.SetMinSize((23, 23))
        self.button_github.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.button_close.SetMinSize((-1, 23))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: RamNotifyPanel.__do_layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_footer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_content = wx.BoxSizer(wx.VERTICAL)
        sizer_task_bar_icon = wx.BoxSizer(wx.HORIZONTAL)
        sizer_notify_cool = wx.BoxSizer(wx.HORIZONTAL)
        sizer_refresh_rate = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_swap = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"論理メモリの使用率が {percent}% を上回ったら･･･"), wx.VERTICAL)
        sizer_swap_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_swap_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_swap_custom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_swap_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_swap_1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_virtual = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"物理メモリの使用率が {percent}% を上回ったら･･･"), wx.VERTICAL)
        sizer_virtual_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_virtual_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_virtual_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_virtual_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((0, 0), 0, wx.TOP, 12)
        sizer_virtual_1.Add(self.gauge_used_virtual, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
        sizer_virtual_1.Add(self.text_used_virtual, 0, 0, 0)
        self.sizer_virtual.Add(sizer_virtual_1, 1, wx.EXPAND, 0)
        sizer_virtual_2.Add(self.slider_limit_virtual, 1, 0, 0)
        sizer_virtual_2.Add(self.spin_limit_virtual, 0, wx.ALIGN_BOTTOM, 0)
        self.sizer_virtual.Add(sizer_virtual_2, 0, wx.EXPAND, 0)
        static_line_2 = wx.StaticLine(self, wx.ID_ANY)
        self.sizer_virtual.Add(static_line_2, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 8)
        self.sizer_virtual.Add(self.check_virtual_notify, 0, wx.BOTTOM, 8)
        sizer_virtual_3.Add(self.check_virtual_command, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 4)
        sizer_virtual_3.Add((0, 0), 1, 0, 0)
        sizer_virtual_3.Add(self.text_virtual_command, 7, 0, 0)
        sizer_virtual_3.Add(self.btn_call_virtual_command, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer_virtual.Add(sizer_virtual_3, 0, wx.EXPAND, 0)
        sizer_virtual_4.Add(self.label_virtual_command_repeat, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_virtual_4.Add(self.spin_virtual_command_repeat, 0, 0, 0)
        self.sizer_virtual.Add(sizer_virtual_4, 1, wx.EXPAND, 0)
        sizer_content.Add(self.sizer_virtual, 0, wx.BOTTOM | wx.EXPAND, 8)
        sizer_content.Add((0, 8), 0, 0, 0)
        sizer_swap_1.Add(self.gauge_used_swap, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
        sizer_swap_1.Add(self.text_used_swap, 0, 0, 0)
        self.sizer_swap.Add(sizer_swap_1, 1, wx.EXPAND, 0)
        sizer_swap_2.Add(self.slider_limit_swap, 1, 0, 0)
        sizer_swap_2.Add(self.spin_limit_swap, 0, wx.ALIGN_BOTTOM, 0)
        self.sizer_swap.Add(sizer_swap_2, 0, wx.BOTTOM | wx.EXPAND, 4)
        sizer_swap_custom.Add(self.check_swap_custom_size, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 4)
        sizer_swap_custom.Add((0, 0), 1, 0, 0)
        sizer_swap_custom.Add(self.spin_swap_custom_max, 0, wx.ALIGN_BOTTOM, 0)
        self.sizer_swap.Add(sizer_swap_custom, 0, wx.EXPAND, 0)
        static_line_3 = wx.StaticLine(self, wx.ID_ANY)
        self.sizer_swap.Add(static_line_3, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 8)
        self.sizer_swap.Add(self.check_swap_notify, 0, wx.BOTTOM, 8)
        sizer_swap_3.Add(self.check_swap_command, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 4)
        sizer_swap_3.Add((0, 0), 1, 0, 0)
        sizer_swap_3.Add(self.text_swap_command, 7, 0, 0)
        sizer_swap_3.Add(self.btn_call_swap_command, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer_swap.Add(sizer_swap_3, 0, wx.EXPAND, 0)
        sizer_swap_4.Add(self.label_swap_command_repeat, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_swap_4.Add(self.spin_swap_command_repeat, 0, 0, 0)
        self.sizer_swap.Add(sizer_swap_4, 1, wx.EXPAND, 0)
        sizer_content.Add(self.sizer_swap, 0, wx.EXPAND, 0)
        label_2 = wx.StaticText(self, wx.ID_ANY, u"監視頻度")
        sizer_refresh_rate.Add(label_2, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        sizer_refresh_rate.Add(self.choice_refresh_rate, 0, 0, 0)
        sizer_content.Add(sizer_refresh_rate, 0, wx.EXPAND | wx.TOP, 16)
        label_3 = wx.StaticText(self, wx.ID_ANY, u"通知頻度")
        sizer_notify_cool.Add(label_3, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        sizer_notify_cool.Add(self.choice_notify_cool, 0, 0, 0)
        sizer_content.Add(sizer_notify_cool, 0, wx.EXPAND | wx.TOP, 6)
        label_1 = wx.StaticText(self, wx.ID_ANY, u"タスクバー アイコン")
        sizer_task_bar_icon.Add(label_1, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        sizer_task_bar_icon.Add(self.choice_task_bar_icon, 0, 0, 0)
        sizer_content.Add(sizer_task_bar_icon, 0, wx.EXPAND | wx.TOP, 6)
        sizer.Add(sizer_content, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        static_line_1 = wx.StaticLine(self, wx.ID_ANY)
        sizer.Add(static_line_1, 0, wx.EXPAND | wx.TOP, 12)
        sizer_footer.Add(self.button_quit, 0, 0, 0)
        sizer_footer.Add(self.button_github, 0, wx.LEFT, 4)
        sizer_footer.Add((0, 0), 1, 0, 0)
        sizer_footer.Add(self.check_processlist, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        sizer_footer.Add(self.button_close, 0, 0, 0)
        sizer.Add(sizer_footer, 0, wx.ALL | wx.EXPAND, 12)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        # end wxGlade

    def on_change_value(self, event):  # wxGlade: RamNotifyPanel.<event_handler>
        print("Event handler 'on_change_value' not implemented!")
        event.Skip()

    def on_check(self, event):  # wxGlade: RamNotifyPanel.<event_handler>
        print("Event handler 'on_check' not implemented!")
        event.Skip()

    def on_button(self, event):  # wxGlade: RamNotifyPanel.<event_handler>
        print("Event handler 'on_button' not implemented!")
        event.Skip()

# end of class RamNotifyPanel

class ProcessListPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ProcessListPanel.__init__
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.canvas = PlotCanvas(self, wx.ID_ANY)
        self.lab_physical_percent = wx.StaticText(self, wx.ID_ANY, "12.3%")
        self.lab_physical_size = wx.StaticText(self, wx.ID_ANY, "12,345 MB / 12,345 MB", style=wx.ALIGN_RIGHT)
        self.lab_virtual_percent = wx.StaticText(self, wx.ID_ANY, "12.3%")
        self.lab_virtual_size = wx.StaticText(self, wx.ID_ANY, "12,345 MB / 12,345 MB", style=wx.ALIGN_RIGHT)
        self.list = ulc.UltimateListCtrl(self, wx.ID_ANY, agwStyle=(ulc.ULC_HRULES | ulc.ULC_REPORT | ulc.ULC_SINGLE_SEL | ulc.ULC_BORDER_SELECT))
        self.lab_reading = wx.StaticText(self, wx.ID_ANY, "", style=wx.ALIGN_CENTER)
        self.txt_commandline = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.btn_read = wx.Button(self, wx.ID_ANY, u"リスト更新")
        self.lab_select_process = wx.StaticText(self, wx.ID_ANY, "label_5", style=wx.ST_NO_AUTORESIZE)
        self.btn_restart = wx.Button(self, wx.ID_ANY, u"再起動")
        self.btn_terminate = wx.Button(self, wx.ID_ANY, u"終了")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_button, self.btn_read)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.btn_restart)
        self.Bind(wx.EVT_BUTTON, self.on_button, self.btn_terminate)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ProcessListPanel.__set_properties
        self.lab_physical_size.SetMinSize((150, -1))
        self.lab_virtual_size.SetMinSize((150, -1))
        self.btn_read.SetMinSize((-1, 23))
        self.btn_restart.SetMinSize((-1, 23))
        self.btn_terminate.SetMinSize((-1, 23))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ProcessListPanel.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_footer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_list = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_mem_info = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.canvas, 1, wx.EXPAND, 0)
        label_7 = wx.StaticText(self, wx.ID_ANY, u"●")
        label_7.SetForegroundColour(wx.Colour(170, 80, 180))
        sizer_5.Add(label_7, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        label_5 = wx.StaticText(self, wx.ID_ANY, u"物理メモリ:")
        sizer_5.Add(label_5, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.lab_physical_percent, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer_mem_info.Add(sizer_5, 0, wx.EXPAND, 0)
        self.sizer_mem_info.Add(self.lab_physical_size, 0, 0, 0)
        static_line_4 = wx.StaticLine(self, wx.ID_ANY)
        self.sizer_mem_info.Add(static_line_4, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 4)
        label_8 = wx.StaticText(self, wx.ID_ANY, u"●")
        label_8.SetForegroundColour(wx.Colour(210, 162, 39))
        sizer_6.Add(label_8, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        label_6 = wx.StaticText(self, wx.ID_ANY, u"仮想メモリ:")
        sizer_6.Add(label_6, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.lab_virtual_percent, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer_mem_info.Add(sizer_6, 0, wx.EXPAND, 0)
        self.sizer_mem_info.Add(self.lab_virtual_size, 0, 0, 0)
        sizer_3.Add(self.sizer_mem_info, 0, wx.EXPAND | wx.LEFT, 12)
        sizer_1.Add(sizer_3, 2, wx.ALL | wx.EXPAND, 12)
        static_line_2 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_2, 0, wx.EXPAND, 0)
        self.sizer_list.Add(self.list, 1, wx.EXPAND, 0)
        self.sizer_list.Add(self.lab_reading, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add(self.sizer_list, 5, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)
        sizer_1.Add(self.txt_commandline, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        static_line_1 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_1, 0, wx.EXPAND | wx.TOP, 12)
        sizer_footer.Add(self.btn_read, 0, wx.RIGHT, 8)
        label_4 = wx.StaticText(self, wx.ID_ANY, u"選択:")
        sizer_footer.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        sizer_footer.Add(self.lab_select_process, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        sizer_footer.Add(self.btn_restart, 0, 0, 0)
        sizer_footer.Add(self.btn_terminate, 0, wx.LEFT, 8)
        sizer_1.Add(sizer_footer, 0, wx.ALL | wx.EXPAND, 12)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def on_button(self, event):  # wxGlade: ProcessListPanel.<event_handler>
        print("Event handler 'on_button' not implemented!")
        event.Skip()

# end of class ProcessListPanel

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    RAMNotify = MyApp(0)
    RAMNotify.MainLoop()
