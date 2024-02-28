import json
import multiprocessing
import signal
import subprocess
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from typing import List, Callable, Optional, TYPE_CHECKING

import psutil
import wx
import wx.adv

import embedded_image
from layout import RamNotifyPanel

if TYPE_CHECKING:
    from processlist import ProcessListApp

__author__ = "Necnion8"
__version__ = "1.1.0"
# v1.0.0 2020.05.27 Release
# v1.1.0      06.12 論理メモリの最大値を指定できるオプションを追加
#                   開かれてるウインドウの裏に設定画面が開かれる不具合修正


GITHUB_URL = "https://github.com/Necnion8/RAMNotify"
REFRESH_RATE_VALS = [
    500,
    1000,
    1000 * 2,
    1000 * 5,
    1000 * 10,
    1000 * 30,
    1000 * 60,
    1000 * 60 * 5,
]
NOTIFY_COOLS_VALS = [
    1000 * 60,
    1000 * 60 * 5,
    1000 * 60 * 10,
    1000 * 60 * 15,
    1000 * 60 * 30,
    1000 * 60 * 60,
    1000 * 60 * 60 * 2,
    1000 * 60 * 60 * 4,
    1000 * 60 * 60 * 6,
]


def find_near_vals(value: int, values: List[int]):
    near_value = min(values, key=lambda v: abs(v - value))
    return near_value, values.index(near_value)


class CoolTime(object):
    def __init__(self, cool_seconds: int):
        self.cool = cool_seconds
        self.last_check = 0

    @property
    def is_cool(self):
        return time.time() - self.last_check > self.cool

    def set(self):
        self.last_check = time.time()


class Timer(object):
    def __init__(self, id_: str, on_timer, seconds: int = None):
        self.id = id_
        self.on_timer = on_timer  # type: Callable[[Timer], None]
        self.delay = seconds or 60
        self._timer: Optional[wx.CallLater] = None

    def __repr__(self):
        return f"<{type(self).__name__} id={self.id!r} isRunning={self.is_running!r}>"

    def change_delay(self, seconds: int):
        self.delay = seconds

    def stop(self, *, restart=False):
        if self._timer:
            self._timer.Stop()
            self._timer = None
            if not restart:
                print(f"Stop timer: {self!r}")
            return True

    def start(self):
        if self.stop(restart=True):
            print(f"Restart timer: {self!r}")
        else:
            print(f"Start timer: {self!r}")
        self._timer = wx.CallLater(self.delay * 1000, self._on_time)

    def _on_time(self):
        self.on_timer(self)

    @property
    def is_running(self):
        return self._timer.IsRunning() if self._timer else False


class EmbeddedImage:
    APP_ICON: wx.Icon
    GAUGES: List[wx.Icon]

    @classmethod
    def init(cls):
        cls.APP_ICON = embedded_image.mem_x512.GetIcon()
        cls.GAUGES = [
            embedded_image.gauge0.GetIcon(),
            embedded_image.gauge1.GetIcon(),
            embedded_image.gauge2.GetIcon(),
            embedded_image.gauge3.GetIcon(),
            embedded_image.gauge4.GetIcon(),
            embedded_image.gauge5.GetIcon(),
            embedded_image.gauge6.GetIcon(),
            embedded_image.gauge7.GetIcon(),
            embedded_image.gauge8.GetIcon(),
            embedded_image.gauge9.GetIcon(),
            embedded_image.gauge10.GetIcon(),
        ]


class RamNotifyConfig(object):
    def __init__(self, filename: Path):
        self.config = filename
        self.virtual_percent = 90
        self.swap_percent = 90
        self.virtual_notify = False
        self.virtual_command_call = False
        self.virtual_command = ""
        self.virtual_command_call_repeat = 0
        self.swap_notify = False
        self.swap_command_call = False
        self.swap_command = ""
        self.swap_command_call_repeat = 0
        self.swap_custom_size = False
        self.swap_custom_size_max = 1
        self.refresh_rate_ms = 5000
        self.notify_cool_ms = 1000 * 60 * 30
        self.task_bar_icon = 0
        self.enable_processlist_app = False
        # shadow
        self.virtual_command_call_delay = 10
        self.swap_command_call_delay = 10

        #
        self.first_load = False

    def load(self):
        if not self.config.is_file():
            self.save()
            self.first_load = True
        else:
            self.first_load = False

        with self.config.open("r", encoding="utf-8") as file:
            try:
                config: dict = json.load(file) or {}
            except json.JSONDecodeError:
                traceback.print_exc()
                config = {}

        try:
            _virtual = config.get("virtual") or {}
            self.virtual_percent = int(_virtual.get("percentage") or 90)
            self.virtual_notify = bool(_virtual.get("notify"))
            self.virtual_command_call = bool(_virtual.get("call_command"))
            self.virtual_command = str(_virtual.get("command") or "")
            self.virtual_command_call_delay = int(_virtual.get("command_call_delay") or 10)
            self.virtual_command_call_repeat = int(_virtual.get("command_call_repeat") or 0)

            _swap = config.get("swap") or {}
            self.swap_percent = int(_swap.get("percentage") or 90)
            self.swap_notify = bool(_swap.get("notify"))
            self.swap_command_call = bool(_swap.get("call_command"))
            self.swap_command = str(_swap.get("command") or "")
            self.swap_command_call_delay = int(_swap.get("command_call_delay") or 10)
            self.swap_command_call_repeat = int(_swap.get("command_call_repeat") or 0)
            self.swap_custom_size = bool(_swap.get("custom_size"))
            self.swap_custom_size_max = int(_swap.get("custom_size_max") or 1)

            self.notify_cool_ms = int(config.get("notify_cool_ms") or 1000 * 60 * 30)
            self.task_bar_icon = int(config.get("task_bar_icon") or 0)
            self.enable_processlist_app = bool(config.get("enable_processlist_app"))

            refresh_rate_ms = 5000
            if "refresh_rate_ms" in config:
                refresh_rate_ms = int(config["refresh_rate_ms"])
            elif "refresh_rate" in config:  # old ver
                presets = [
                    500,
                    1000,
                    1000 * 5,
                    1000 * 10,
                    1000 * 30,
                    1000 * 60,
                    1000 * 60 * 5,
                ]
                try:
                    refresh_rate_ms = presets[max(0, min(int(config["refresh_rate"]), len(presets) - 1))]
                except (KeyError, ValueError):
                    pass
            self.refresh_rate_ms = refresh_rate_ms

        except (TypeError, ValueError):
            traceback.print_exc()

    def save(self):
        config = dict(
            version=1,
            virtual=dict(
                percentage=self.virtual_percent,
                notify=self.virtual_notify,
                call_command=self.virtual_command_call,
                command=self.virtual_command,
                command_call_delay=self.virtual_command_call_delay,
                command_call_repeat=self.virtual_command_call_repeat,
            ),
            swap=dict(
                percentage=self.swap_percent,
                notify=self.swap_notify,
                call_command=self.swap_command_call,
                command=self.swap_command,
                command_call_delay=self.swap_command_call_delay,
                command_call_repeat=self.swap_command_call_repeat,
                custom_size=self.swap_custom_size,
                custom_size_max=self.swap_custom_size_max,
            ),
            task_bar_icon=self.task_bar_icon,
            refresh_rate_ms=self.refresh_rate_ms,
            notify_cool_ms=self.notify_cool_ms,
            enable_processlist_app=self.enable_processlist_app,
        )
        with self.config.open("w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False)


class RamNotify(RamNotifyPanel):
    def __init__(self, frame: wx.Frame, *args, **kwargs):
        RamNotifyPanel.__init__(self, *args, **kwargs)
        self.frame = frame
        self.config = RamNotifyConfig(Path("../settings.json"))
        self.load_all()
        self.task_bar = MyTaskBar("RAM-Notify", self)
        self.timer = wx.Timer(self)  # refresh timer
        self.processlist_app = None  # type: ProcessListApp | None
        # last-cache
        self.last_virtual_over = False
        self.last_swap_over = False
        # timer
        self.cool_notify = CoolTime(int(self.config.notify_cool_ms / 1000))
        self.cool_virtual_command = CoolTime(self.config.virtual_command_call_delay)
        self.cool_swap_command = CoolTime(self.config.swap_command_call_delay)
        self.wait_virtual_command_wait = False
        self.wait_swap_command_wait = False
        self.timer_virtual_command = Timer("VCmdTimer", self.on_timer_virtual_command)
        self.timer_swap_command = Timer("SCmdTimer", self.on_timer_swap_command)
        # load
        self.register_signals()
        self.frame.Bind(wx.EVT_CLOSE, lambda e: self.hide_frame(save=False))
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.task_bar.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_icon_click)
        self.on_timer()
        self.button_github.SetBitmap(embedded_image.github_icon.GetBitmap())
        self.button_github.SetToolTip(GITHUB_URL)

        if self.config.enable_processlist_app:
            self.init_processlist()
            self._init_processlist_moves()

        if self.config.first_load:
            self.frame.Centre()
            self.show_frame()

    def app_exit(self):
        self.task_bar.Destroy()
        wx.Exit()

    def register_signals(self):
        signal.signal(signal.SIGINT, lambda *_: self.app_exit())
        signal.signal(signal.SIGTERM, lambda *_: self.app_exit())

    def on_check(self, event):
        if event.GetEventObject() is self.check_virtual_command:
            self.set_active_virtual_command(self.check_virtual_command.GetValue())

        elif event.GetEventObject() is self.check_swap_command:
            self.set_active_swap_command(self.check_swap_command.GetValue())

        elif event.GetEventObject() is self.check_swap_custom_size:
            self.set_swap_custom(active=self.check_swap_custom_size.GetValue())

        elif event.GetEventObject() is self.check_processlist:
            if self.check_processlist.GetValue():
                self.show_processlist()
            else:
                self.hide_processlist()

        event.Skip()

    def on_change_value(self, event):
        if event.GetEventObject() is self.slider_limit_virtual:
            self.set_virtual_limit(self.slider_limit_virtual.GetValue())

        elif event.GetEventObject() is self.slider_limit_swap:
            self.set_swap_limit(self.slider_limit_swap.GetValue())

        elif event.GetEventObject() is self.spin_limit_virtual:
            self.set_virtual_limit(self.spin_limit_virtual.GetValue())

        elif event.GetEventObject() is self.spin_limit_swap:
            self.set_swap_limit(self.spin_limit_swap.GetValue())

        elif event.GetEventObject() is self.spin_virtual_command_repeat:
            self.set_virtual_command_repeat(self.spin_virtual_command_repeat.GetValue())

        elif event.GetEventObject() is self.spin_swap_command_repeat:
            self.set_swap_command_repeat(self.spin_swap_command_repeat.GetValue())

        elif event.GetEventObject() is self.spin_swap_custom_max:
            self.set_swap_custom(max_size=self.spin_swap_custom_max.GetValue())

        event.Skip()

    def on_button(self, event):
        if event.GetEventObject() is self.button_quit:
            self.save_all()
            self.app_exit()

        elif event.GetEventObject() is self.button_close:
            self.hide_frame()
            self.on_timer()

        elif event.GetEventObject() is self.btn_call_virtual_command:
            self.call_command_virtual(self.text_virtual_command.GetValue())

        elif event.GetEventObject() is self.btn_call_swap_command:
            self.call_command_swap(self.text_swap_command.GetValue())

        elif event.GetEventObject() is self.button_github:
            webbrowser.open(GITHUB_URL)

        event.Skip()

    def on_timer(self, _=None, *, force_update=False):
        self.timer.Start(self.config.refresh_rate_ms, oneShot=wx.TIMER_ONE_SHOT)

        frame = getattr(wx.GetApp(), "frame", None)
        is_shown = frame.IsShown() if frame else False

        virtual = psutil.virtual_memory().percent
        if is_shown and self.check_swap_custom_size.GetValue():
            swap = self.get_swap_percent(self.spin_swap_custom_max.GetValue())
        else:
            swap = self.get_swap_percent()

        icon_mode = self.config.task_bar_icon
        if icon_mode == 1:
            icon = EmbeddedImage.GAUGES[round(virtual / 10)]
        elif icon_mode == 2:
            icon = EmbeddedImage.GAUGES[round(swap / 10)]
        else:
            icon = EmbeddedImage.GAUGES[0]
        self.task_bar.change_icon(icon)

        if force_update or is_shown:
            self.gauge_used_virtual.SetValue(int(virtual))
            self.text_used_virtual.ChangeValue(f"{virtual}%")
            self.gauge_used_swap.SetValue(int(swap))
            self.text_used_swap.ChangeValue(f"{swap}%")

        # notify / run-command
        swap = self.get_swap_percent()  # load from config value
        notify_send = False

        if virtual >= self.config.virtual_percent:
            if self.config.virtual_notify and self.cool_notify.is_cool:
                self.cool_notify.set()
                self.task_bar.ShowBalloon("メモリ通知", f"物理メモリ 使用率が{int(virtual)}%です！")
                notify_send = True

            if self.last_virtual_over:
                if self.config.virtual_command_call and self.cool_virtual_command.is_cool:
                    self.cool_virtual_command.set()
                    self.call_command_virtual()

        self.last_virtual_over = virtual >= self.config.virtual_percent
        if self.last_virtual_over:
            if not self.timer_virtual_command.is_running and self.is_enable_virtual_timer:
                self.timer_virtual_command.start()
        else:
            self.timer_virtual_command.stop()

        if swap >= self.config.swap_percent:
            if self.config.swap_notify and self.cool_notify.is_cool and not notify_send:
                self.cool_notify.set()
                self.task_bar.ShowBalloon("メモリ通知", f"論理メモリ 使用率が{int(virtual)}%です！")

            if self.last_swap_over:
                if self.config.swap_command_call and self.cool_swap_command.is_cool:
                    self.cool_swap_command.set()
                    self.call_command_swap()

        self.last_swap_over = swap >= self.config.swap_percent
        if self.last_swap_over:
            if not self.timer_swap_command.is_running and self.is_enable_swap_timer:
                self.timer_swap_command.start()
        else:
            self.timer_swap_command.stop()

    # noinspection PyMethodMayBeStatic
    def on_icon_click(self, _):
        self.show_frame()

    def on_timer_virtual_command(self, timer: Timer):
        timer.start()
        self.call_command_virtual()

    def on_timer_swap_command(self, timer: Timer):
        timer.start()
        self.call_command_swap()

    # control

    def hide_frame(self, save=True):
        self.frame.Hide()
        try:
            if self.processlist_app:
                self.hide_processlist()
        finally:
            if save:
                self.save_all()
            else:
                self.load_all()  # reset

    def show_frame(self):
        _shown = self.frame.IsShown()
        self.frame.Show()
        self.frame.SetFocus()
        self.on_timer(force_update=True)

        if not _shown and self.processlist_app and self.check_processlist.GetValue():
            self.show_processlist()

    def set_virtual_limit(self, percent: int):
        self.sizer_virtual.GetStaticBox().SetLabel(f"物理メモリの使用率が {percent}% を上回ったら･･･")
        self.slider_limit_virtual.SetValue(percent)
        self.spin_limit_virtual.SetValue(percent)

    def set_swap_limit(self, percent: int):
        self.sizer_swap.GetStaticBox().SetLabel(f"論理メモリの使用率が {percent}% を上回ったら･･･")
        self.slider_limit_swap.SetValue(percent)
        self.spin_limit_swap.SetValue(percent)

    def set_active_virtual_command(self, enabled: bool):
        self.check_virtual_command.SetValue(enabled)
        self.text_virtual_command.Enable(enabled)
        self.label_virtual_command_repeat.Enable(enabled)
        self.spin_virtual_command_repeat.Enable(enabled)

    def set_active_swap_command(self, enabled: bool):
        self.check_swap_command.SetValue(enabled)
        self.text_swap_command.Enable(enabled)
        self.label_swap_command_repeat.Enable(enabled)
        self.spin_swap_command_repeat.Enable(enabled)

    def set_virtual_command_repeat(self, minutes: int):
        self.spin_virtual_command_repeat.SetValue(minutes)
        self.label_virtual_command_repeat.SetLabel(
            f"指定より超えていたら、{minutes}分毎に実行します。(単位: 分)"
            if minutes > 0 else
            "指定より超えた時に一度だけ実行します。(単位: 分)"
        )

    def set_swap_command_repeat(self, minutes: int):
        self.spin_swap_command_repeat.SetValue(minutes)
        self.label_swap_command_repeat.SetLabel(
            f"指定より超えていたら、{minutes}分毎に実行します。(単位: 分)"
            if minutes > 0 else
            "指定より超えた時に一度だけ実行します。(単位: 分)"
        )

    def set_swap_custom(self, active: bool = None, max_size: int = None):
        if active is not None:
            self.check_swap_custom_size.SetValue(active)
            self.spin_swap_custom_max.Enable(bool(active))
        if max_size is not None:
            self.spin_swap_custom_max.SetValue(max_size)

    # noinspection PyMethodMayBeStatic
    def call_command(self, command: str, *, on_done: Callable[[Optional[int]], None] = None):
        print(f"call-command: {command!r}")

        def call():
            code = None
            try:
                process = subprocess.Popen(command, shell=True, start_new_session=True)
                process.wait()
                code = process.returncode
            finally:
                def finish():
                    print("call-command complete:", code)
                    if on_done:
                        on_done(code)
                wx.CallAfter(finish)

        th = threading.Thread(target=call, daemon=True)
        th.start()

    def call_command_virtual(self, command: str = None):
        if self.wait_virtual_command_wait:
            return

        def done_action(_):
            self.btn_call_virtual_command.Enable(True)
            self.wait_virtual_command_wait = False

        if command is None:
            command = self.config.virtual_command

        if command:
            self.wait_virtual_command_wait = True
            self.btn_call_virtual_command.Enable(False)
            self.call_command(command, on_done=done_action)

    def call_command_swap(self, command: str = None):
        if self.wait_swap_command_wait:
            return

        def done_action(_):
            self.btn_call_swap_command.Enable(True)
            self.wait_swap_command_wait = False

        if command is None:
            command = self.config.swap_command

        if command:
            self.wait_swap_command_wait = True
            self.btn_call_swap_command.Enable(False)
            self.call_command(command, on_done=done_action)

    # config

    def get_swap_percent(self, max_size: int = None):
        if self.config.swap_custom_size or max_size:
            max_ = max_size if max_size else self.config.swap_custom_size_max

            total = max_ * (1024 ** 3)
            swap = psutil.swap_memory()
            percent = round(max(min(swap.used / total * 100, 100), 0), 1)

        else:
            percent = psutil.swap_memory().percent

        return percent

    @property
    def is_enable_virtual_timer(self):
        return bool(self.config.virtual_command_call and self.config.virtual_command_call_repeat)

    @property
    def is_enable_swap_timer(self):
        return bool(self.config.swap_command_call and self.config.swap_command_call_repeat)

    @property
    def is_over_virtual_limit(self):
        return psutil.virtual_memory().percent >= self.config.virtual_percent

    @property
    def is_over_swap_limit(self):
        return psutil.swap_memory().percent >= self.config.swap_percent

    def load_all(self):
        self.config.load()
        self.set_virtual_limit(self.config.virtual_percent)
        self.set_swap_limit(self.config.swap_percent)

        self.check_virtual_notify.SetValue(self.config.virtual_notify)
        self.set_active_virtual_command(self.config.virtual_command_call)
        self.text_virtual_command.ChangeValue(self.config.virtual_command)
        self.set_virtual_command_repeat(self.config.virtual_command_call_repeat)

        self.check_swap_notify.SetValue(self.config.swap_notify)
        self.set_active_swap_command(self.config.swap_command_call)
        self.text_swap_command.ChangeValue(self.config.swap_command)
        self.set_swap_command_repeat(self.config.swap_command_call_repeat)

        self.set_swap_custom(
            self.config.swap_custom_size,
            self.config.swap_custom_size_max
        )

        value = min(max(self.config.task_bar_icon, 0), len(self.choice_task_bar_icon.GetItems())-1)
        self.choice_task_bar_icon.Select(value)
        self.choice_refresh_rate.Select(find_near_vals(self.config.refresh_rate_ms, REFRESH_RATE_VALS)[1])
        self.choice_notify_cool.Select(find_near_vals(self.config.notify_cool_ms, NOTIFY_COOLS_VALS)[1])
        self.check_processlist.SetValue(self.config.enable_processlist_app)

    def save_all(self):
        self.config.virtual_percent = self.slider_limit_virtual.GetValue()
        self.config.virtual_notify = self.check_virtual_notify.GetValue()
        self.config.virtual_command_call = self.check_virtual_command.GetValue()
        self.config.virtual_command = self.text_virtual_command.GetValue()
        self.config.virtual_command_call_repeat = self.spin_virtual_command_repeat.GetValue()
        self.config.swap_percent = self.slider_limit_swap.GetValue()
        self.config.swap_notify = self.check_swap_notify.GetValue()
        self.config.swap_command_call = self.check_swap_command.GetValue()
        self.config.swap_command = self.text_swap_command.GetValue()
        self.config.swap_command_call_repeat = self.spin_swap_command_repeat.GetValue()
        self.config.swap_custom_size = self.check_swap_custom_size.GetValue()
        self.config.swap_custom_size_max = self.spin_swap_custom_max.GetValue()
        self.config.task_bar_icon = self.choice_task_bar_icon.GetSelection()
        self.config.refresh_rate_ms = REFRESH_RATE_VALS[self.choice_refresh_rate.GetSelection()]
        self.config.notify_cool_ms = NOTIFY_COOLS_VALS[self.choice_notify_cool.GetSelection()]
        self.config.enable_processlist_app = self.check_processlist.GetValue()

        self.timer_virtual_command.stop()
        if self.is_enable_virtual_timer:
            self.timer_virtual_command.change_delay(self.config.virtual_command_call_repeat * 60)

            if self.is_over_virtual_limit:
                self.timer_virtual_command.start()

        self.timer_swap_command.stop()
        if self.is_enable_swap_timer:
            self.timer_swap_command.start()

            if self.is_over_swap_limit:
                self.timer_swap_command.change_delay(self.config.swap_command_call_repeat * 60)

        self.cool_notify.cool = int(self.config.notify_cool_ms / 1000)

        self.config.save()

    # process list app

    def init_processlist(self):
        style = wx.CAPTION | wx.SYSTEM_MENU | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR
        frame = wx.Frame(None, size=(450, 500), style=style, title="プロセス一覧")
        frame.SetIcon(EmbeddedImage.APP_ICON)

        try:
            from processlist import ProcessListApp
            app = ProcessListApp(frame, self.config)

        except (Exception,):
            traceback.print_exc()
            frame.Destroy()
            self.check_processlist.SetValue(False)
            return False

        else:
            self.processlist_app = app
            return True

    def _init_processlist_moves(self):
        _flag = [False]

        def _close(_):
            self.check_processlist.SetValue(False)
            self.hide_processlist()

        def _move(_):
            if _flag[0]:  # ignore
                return

            _flag[0] = True
            self.move_processlist()
            _flag[0] = False

        def _move_self(_):
            if _flag[0]:  # ignore
                return

            _flag[0] = True
            self.move_processlist(from_child=True)
            _flag[0] = False

        def _focus_self(_):
            self.frame.SetFocus()
            self.processlist_app.SetFocus()

        def _focus(_):
            self.processlist_app.SetFocus()
            self.frame.SetFocus()

        self.processlist_app.frame.Bind(wx.EVT_CLOSE, _close)
        self.processlist_app.frame.Bind(wx.EVT_MOVE, _move_self)
        self.processlist_app.frame.Bind(wx.EVT_ACTIVATE, _focus_self)
        self.frame.Bind(wx.EVT_MOVE, _move)
        self.frame.Bind(wx.EVT_ACTIVATE, _focus)

    def show_processlist(self):
        _init = False
        if self.processlist_app is None:
            if self.init_processlist():
                _init = True

        self.move_processlist(resize=True)
        self.processlist_app.frame.Show()
        self.processlist_app.start()
        wx.CallAfter(self.processlist_app.read_processes)

        if _init:
            self._init_processlist_moves()

    def hide_processlist(self):
        if self.processlist_app is None:
            return

        self.processlist_app.stop()
        self.processlist_app.frame.Hide()

    def move_processlist(self, from_child=False, resize=False):
        if self.processlist_app is None:
            return

        p_frame = self.frame
        c_frame = self.processlist_app.frame
        if from_child:
            p_frame, c_frame = c_frame, p_frame

        w, h = p_frame.GetSize()
        x, y = p_frame.GetPosition()

        if from_child:
            w, _ = c_frame.GetSize()
            x -= w + 2
        else:
            x += w + 2

        w, _ = c_frame.GetSize()

        if resize:
            c_frame.SetSize((w, h))
        c_frame.SetPosition((x, y))


class MyTaskBar(wx.adv.TaskBarIcon):
    def __init__(self, app_name: str, parent: RamNotify):
        wx.adv.TaskBarIcon.__init__(self)
        self.app_name = app_name
        self.parent = parent
        self.last_title = ""
        self.last_icon = EmbeddedImage.GAUGES[0]
        self.change_icon(init=True)

    def change_icon(self, icon: wx.Icon = None, title: str = None, *, init=False):
        title = title or self.last_title
        icon = icon or self.last_icon

        if init or (self.last_title != title or self.last_icon != icon):
            _title = f"{self.app_name} - {title}" if title else self.app_name
            self.SetIcon(icon, _title)

        self.last_title = title
        self.last_icon = icon

    def CreatePopupMenu(self):
        menu = wx.Menu()

        def create_label(l: str):
            i = wx.MenuItem(None, -1, l)
            i.Enable(False)
            return i

        def byte_to_label(s: int):
            if s < 1024:
                return str(s) + " bytes"
            elif s < 1024 ** 2:
                return str(round(s / 1024.0, 1)) + " KB"
            elif s < 1024 ** 3:
                return str(round(s / (1024.0 ** 2), 1)) + " MB"
            elif s < 1024 ** 4:
                return str(round(s / (1024.0 ** 3), 1)) + " GB"
            else:  # elif s < 1024 ** 5:
                return str(round(s / (1024.0 ** 4), 1)) + " TB"

        gauge = 20

        virtual = psutil.virtual_memory()
        menu.Append(create_label(f"物理メモリ - {virtual.percent}%    ({byte_to_label(virtual.available)} 利用可能)"))
        bar1 = int((virtual.percent/100) * gauge)
        bar2 = gauge - bar1
        progress = f"[{bar1*'⬛'}{bar2*'⬜'}]"
        menu.Append(create_label(progress))

        swap = psutil.swap_memory()
        swap_percent = self.parent.get_swap_percent()
        menu.Append(create_label(f"論理メモリ - {swap_percent}%    ({byte_to_label(swap.free)} 利用可能)"))
        bar1 = int((swap_percent/100) * gauge)
        bar2 = gauge - bar1
        progress = f"[{bar1*'⬛'}{bar2*'⬜'}]"
        menu.Append(create_label(progress))

        menu.AppendSeparator()
        btn_call_virtual_command = menu.Append(wx.MenuItem(None, -1, "コマンド実行 (物理メモリ)"))
        btn_call_swap_command = menu.Append(wx.MenuItem(None, -1, "コマンド実行 (論理メモリ)"))
        btn_settings = menu.Append(wx.MenuItem(None, -1, "設定を開く"))
        menu.AppendSeparator()
        btn_exit = menu.Append(wx.MenuItem(None, -1, "終了"))

        if not self.parent.config.virtual_command:
            btn_call_virtual_command.Enable(False)
        if not self.parent.config.swap_command:
            btn_call_swap_command.Enable(False)

        menu.Bind(wx.EVT_MENU, self.on_menu_virtual_call_command, btn_call_virtual_command)
        menu.Bind(wx.EVT_MENU, self.on_menu_swap_call_command, btn_call_swap_command)
        menu.Bind(wx.EVT_MENU, self.on_menu_settings, btn_settings)
        menu.Bind(wx.EVT_MENU, self.on_menu_exit, btn_exit)
        return menu

    def on_menu_virtual_call_command(self, event):
        self.parent.call_command_virtual()
        event.Skip()

    def on_menu_swap_call_command(self, event):
        self.parent.call_command_swap()
        event.Skip()

    def on_menu_settings(self, event):
        self.parent.show_frame()
        event.Skip()

    def on_menu_exit(self, _):
        self.Destroy()
        wx.Exit()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.SYSTEM_MENU
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((400, 600))
        self.SetIcon(EmbeddedImage.APP_ICON)
        self.panel = RamNotify(self, self, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle(f"RAM-Notify v{__version__}/{__date__}")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_14 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_14.Add(self.panel, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_14)
        self.Layout()
        self.Fit()


class MyApp(wx.App):
    frame: MyFrame

    def OnInit(self):
        import os
        import sys
        os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
        EmbeddedImage.init()
        self.frame = MyFrame(None, wx.ID_ANY)
        self.SetTopWindow(self.frame)
        self.frame.Centre()
        return True


if __name__ == "__main__":
    multiprocessing.freeze_support()
    RAMNotify = MyApp(0)
    RAMNotify.MainLoop()
