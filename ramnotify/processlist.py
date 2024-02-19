import multiprocessing
import subprocess
import threading
import time
import traceback
from collections import deque, namedtuple
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import psutil
import wx
import wx.lib.agw.ultimatelistctrl as ulc

from layout import ProcessListPanel
from util import freezing
from widget import PlotLine, PyGauge

if TYPE_CHECKING:
    from .ramnotify import RamNotify

DummyFormatter = namedtuple("DummyFormatter", ["format"])
DEFAULT_SORT_TYPE_DIRECTION = (False, False, True, True)


class SortType(Enum):
    PID_ASC = 0, False
    PID_DESC = 0, True
    NAME_ASC = 1, False
    NAME_DESC = 1, True
    P_USED_ASC = 2, False
    P_USED_DESC = 2, True
    V_USED_ASC = 3, False
    V_USED_DESC = 3, True

    def value_by(self, info: dict):
        e_type, _ = self.value
        if e_type == 0:
            return info["pid"]
        elif e_type == 1:
            return info["name"]
        elif e_type == 2:
            return info["memory_info"].rss
        elif e_type == 3:
            return info["memory_info"].vms
        raise ValueError(f"invalid type index: {e_type}")


class MemoryInfo:
    def __init__(self, total: int, used: int, available: int):
        self.total = total
        self.used = used
        self.available = available

    @property
    def percent(self):
        return self.used / self.total


def _dump_process(pid: int):
    return psutil.Process(pid).as_dict(["pid", "name", "memory_info", "cmdline"])


def _dump_processes(ret_info: dict, wait: multiprocessing.Event):
    try:
        for proc in psutil.process_iter(["pid", "name", "memory_info", "cmdline"]):
            ret_info[proc.pid] = proc.info
    finally:
        wait.set()


def _format_gauge_label(label: str):
    return DummyFormatter(lambda *_: label)


class ProcessListApp(ProcessListPanel):
    def __init__(self, parent: "Optional[RamNotify]", config: "RamNotifyConfig"):
        style = wx.CAPTION | wx.SYSTEM_MENU | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR
        if parent is None:
            style |= wx.MINIMIZE_BOX
            style ^= wx.FRAME_NO_TASKBAR
        self.frame = frame = wx.Frame(parent, size=(450, 500), style=style, title="プロセス一覧")
        if parent:
            frame.SetIcon(parent.frame.GetIcon())
        ProcessListPanel.__init__(self, frame)
        self.app = parent
        self.config = config
        self.sort_type = SortType.P_USED_DESC
        #
        self.refresh_rate = 1  # 0.5
        self.plot_count = 0
        self.p_mem_line_points = deque([-1] * 60, maxlen=60)
        self.v_mem_line_points = deque([-1] * 60, maxlen=60)
        self.p_mem = MemoryInfo(0, 0, 0)
        self.v_mem = MemoryInfo(0, 0, 0)
        #
        self._thread_interrupt = threading.Event()
        self._thread = None  # type: threading.Thread | None
        self._multiprocessing_manager = manager = multiprocessing.Manager()
        self._multiprocessing_dict = manager.dict()
        self._multiprocessing_wait = manager.Event()
        self._reading = False
        self._deselect_flag = False
        #
        self._init()

    def _init(self):
        self.lab_select_process.SetLabel("")
        self.lab_physical_percent.SetLabel("")
        self.lab_physical_size.SetLabel("")
        self.lab_virtual_percent.SetLabel("")
        self.lab_virtual_size.SetLabel("")

        self.list.ClearAll()
        header = (
            ("PID", 50, ulc.ULC_FORMAT_LEFT),
            ("プロセス", 164, ulc.ULC_FORMAT_LEFT),
            ("物理", 83, ulc.ULC_FORMAT_RIGHT),
            ("仮想", 83, ulc.ULC_FORMAT_RIGHT),
        )
        for idx, (label, width, fmt) in enumerate(header):
            item = ulc.UltimateListItem()
            item.SetText(label)
            item.SetAlign(fmt)
            self.list.InsertColumnInfo(idx, item)
            self.list.SetColumnWidth(idx, width)

        self.update_select_process(None)
        self.update_list_layout(True)

        self.list.Bind(ulc.EVT_LIST_ITEM_SELECTED, self.on_list_select)
        self.list.Bind(ulc.EVT_LIST_ITEM_DESELECTED, self.on_list_deselect)
        self.list.Bind(ulc.EVT_LIST_COL_CLICK, self.on_list_col_click)
        self.list._mainWin.Bind(wx.EVT_SCROLLWIN, self.on_list_scroll)
        self.list.Bind(wx.EVT_KEY_DOWN, self.on_list_char)

        self.frame.Bind(wx.EVT_SHOW, self.on_frame_show)
        self.frame.Bind(wx.EVT_CLOSE, self.on_frame_close)

        if self.frame.IsShown():
            wx.CallAfter(self.read_processes)
            self.start()
        else:
            def _show(e):
                e.Skip()
                self.frame.Unbind(wx.EVT_SHOW, handler=_show)
                wx.CallAfter(self.read_processes)
            self.frame.Bind(wx.EVT_SHOW, _show)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread_interrupt.clear()
        self._thread = th = threading.Thread(target=self._run_loop, daemon=True)
        th.start()

    def stop(self):
        self._thread_interrupt.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def _run_loop(self):
        while not self._thread_interrupt.is_set():
            _last = time.time()
            self._run()

            next_delay = self.refresh_rate - (time.time() - _last)
            if next_delay <= 0:
                print(f"WARN: process loop too long: {round(next_delay * -1000)}ms")
                next_delay = self.refresh_rate

            time.sleep(next_delay)

    def _run(self):
        try:
            wx.CallAfter(self.put_memory_usage)

        except (Exception,):
            traceback.print_exc()

    def put_memory_usage(self):
        p_mem = psutil.virtual_memory()
        v_mem = psutil.swap_memory()

        total = p_mem.total
        used = total - p_mem.available
        percent = used / total * 100
        self.p_mem.total = total
        self.p_mem.used = used
        self.p_mem.available = p_mem.available
        self.lab_physical_percent.SetLabel(f"{round(percent, 1)} %")
        total /= 1024 ** 2
        used /= 1024 ** 2
        self.lab_physical_size.SetLabel(f"{round(used):,} MB / {round(total):,} MB")
        self.p_mem_line_points.append(used)
        p_line = PlotLine(
            min_value=0,
            max_value=total,
            values=self.p_mem_line_points,
            color=wx.Colour(170, 80, 180),
            fill_color=wx.Colour(170, 80, 180, 70),
        )

        total = v_mem.total
        used = v_mem.used
        percent = used / total * 100
        self.v_mem.total = total
        self.v_mem.used = used
        self.v_mem.available = total - used
        self.lab_virtual_percent.SetLabel(f"{round(percent, 1)} %")
        total /= 1024 ** 2
        used /= 1024 ** 2
        self.lab_virtual_size.SetLabel(f"{round(used):,} MB / {round(total):,} MB")
        self.v_mem_line_points.append(used)
        v_line = PlotLine(
            min_value=0,
            max_value=total,
            values=self.v_mem_line_points,
            color=wx.Colour(210, 162, 39),
            fill_color=wx.Colour(210, 162, 39, 40),
        )

        self.sizer_mem_info.Layout()
        self.plot_count += 1
        self.canvas.draw([v_line, p_line])

    def on_frame_show(self, event):
        event.Skip()
        wx.CallAfter(self.start)

    def on_frame_close(self, event):
        event.Skip()
        self.stop()

    def on_button(self, event: wx.CommandEvent):
        try:
            if event.GetEventObject() is self.btn_read:
                self.read_processes()

            elif event.GetEventObject() is self.btn_restart:
                self._restart_select()

            elif event.GetEventObject() is self.btn_terminate:
                self._terminate_select()

        finally:
            event.Skip()

    def on_list_select(self, event: ulc.UltimateListEvent):
        self._deselect_flag = False
        info = self.list.GetItemPyData(event.GetIndex())
        self.update_select_process(info)
        event.Skip()

    def on_list_deselect(self, event: ulc.UltimateListEvent):
        self._deselect_flag = True
        event.Skip()

        def _deselect():
            if self._deselect_flag:
                self.update_select_process(None)

        wx.CallAfter(_deselect)

    def on_list_col_click(self, event: ulc.UltimateListEvent):
        event.Skip()
        column = event.GetColumn()

        e_type, desc = self.sort_type.value
        if e_type == column:
            self.sort_type = SortType((e_type, not desc))
        else:
            self.sort_type = SortType((column, DEFAULT_SORT_TYPE_DIRECTION[column]))
        self.sort_lists()

    def on_list_scroll(self, event: wx.ScrollWinEvent):
        event.Skip()
        wx.CallAfter(self.list.Refresh)  # fix item visibility

    def on_list_char(self, event: wx.KeyEvent):
        first_char = chr(event.GetUnicodeKey()).lower()

        lists = self.list
        count = lists.GetItemCount()
        offset = lists.GetFirstSelected() + 1
        for n in range(count):
            index = (offset + n) % count
            info = lists.GetItemPyData(index)
            if info["name"].lower().startswith(first_char):
                lists.Select(index)
                lists.Focus(index)
                wx.CallAfter(lists.Update)
                break
        event.Skip()

    def _append_process_item_to_list(self, proc_info):
        lists = self.list
        index = lists.GetItemCount()
        mem_info = proc_info["memory_info"]
        p_used = mem_info.rss
        p_used_str = f"{round(p_used / 1024 / 1024, 1):,} MB"
        v_used = mem_info.vms
        v_used_str = f"{round(v_used / 1024 / 1024, 1):,} MB"

        lists.Append((str(proc_info["pid"]), proc_info["name"], "", ""))

        p_gauge = PyGauge(lists, style=wx.GA_HORIZONTAL)
        p_gauge._barColour = [wx.Colour(222, 147, 230)]
        p_gauge.SetDrawValue(drawPercent=True, formatString=_format_gauge_label(p_used_str))
        p_gauge.SetValue(round(p_used / self.p_mem.used * 100))
        p_gauge_item = lists.GetItem(index, 2)  # type: ulc.UltimateListItem
        p_gauge_item.SetWindow(p_gauge, expand=True)
        lists.SetItem(p_gauge_item)

        v_gauge = PyGauge(lists, style=wx.GA_HORIZONTAL)
        v_gauge._barColour = [wx.Colour(227, 202, 136)]
        v_gauge.SetDrawValue(drawPercent=True, formatString=_format_gauge_label(v_used_str))
        v_gauge.SetValue(round(v_used / self.v_mem.used * 100))
        v_gauge_item = lists.GetItem(index, 3)  # type: ulc.UltimateListItem
        v_gauge_item.SetWindow(v_gauge, expand=True)
        lists.SetItem(v_gauge_item)
        lists.SetItemPyData(index, proc_info)

    def update_select_process(self, proc_info: Optional[dict]):
        if proc_info is None:
            self.txt_commandline.ChangeValue("")
            self.lab_select_process.SetLabel("")
            self.btn_restart.Disable()
            self.btn_terminate.Disable()
        else:
            with freezing(self):
                self.btn_restart.Enable()
                self.btn_terminate.Enable()
                cmdline = proc_info["cmdline"] or []
                self.txt_commandline.ChangeValue(" ".join(cmdline))
                self.txt_commandline.SetInsertionPointEnd()
                self.lab_select_process.SetLabel(proc_info["name"])

    def update_list_layout(self, reading: bool):
        with freezing(self):
            self.list.Show(not reading)
            self.lab_reading.Show(reading)
            self.lab_reading.SetLabel("リストを更新してください")
            self.sizer_list.Layout()

    def read_processes(self):
        if self._reading:
            return

        self.btn_read.Disable()
        self.update_select_process(None)
        self.update_list_layout(True)

        self._reading = True
        wait = self._multiprocessing_wait
        wait.clear()
        ret_info = self._multiprocessing_dict
        ret_info.clear()
        p = multiprocessing.Process(target=_dump_processes, args=(ret_info, wait), daemon=True)
        p.start()

        def _waiter():
            try:
                while not wait.is_set():
                    wx.CallAfter(_progress)
                    time.sleep(.05)

                self.lab_reading.SetLabel("リストを作成中...")
                self.sizer_list.Layout()
            finally:
                wx.CallAfter(_done)

        def _progress():
            process_count = len(ret_info)
            self.lab_reading.SetLabel(f"プロセスを読み込み中 ({process_count})")
            self.sizer_list.Layout()

        def _done():
            try:
                with freezing(self.list):
                    for index in range(self.list.GetItemCount()):
                        win = self.list.GetItemWindow(index, col=2)  # type: wx.Window
                        if win:
                            win.Destroy()
                            self.list.DeleteItemWindow(index, col=2)
                        win = self.list.GetItemWindow(index, col=3)
                        if win:
                            win.Destroy()
                            self.list.DeleteItemWindow(index, col=3)

                    self.list.DeleteAllItems()

                    for info in ret_info.values():
                        self._append_process_item_to_list(info)

            finally:
                try:
                    p.terminate()
                except (Exception,):
                    traceback.print_exc()

                self._reading = False
                self.btn_read.Enable()
                self.update_list_layout(False)
                self.sort_lists()
                self.list.SetFocus()

        threading.Thread(target=_waiter, daemon=True).start()

    def sort_lists(self, *, select_pid: int = None):
        e_type, desc = self.sort_type.value

        lists = self.list
        lines = lists._mainWin._lines  # type: list[ulc.UltimateListLineData]

        def _key(e: ulc.UltimateListLineData):
            info = e._items[0]._pyData
            value = self.sort_type.value_by(info)
            return value.lower() if isinstance(value, str) else value

        lines.sort(key=_key, reverse=desc)

        with freezing(lists):
            lists.SortItems(func=lambda *_: 0)
            # lists.Select()

            if select_pid is not None:
                for idx, line in enumerate(lines):
                    info = line._items[0]._pyData
                    if info["pid"] == select_pid:
                        lists.Select(idx)
                        wx.CallAfter(lists.Update)
                        break

    def _kill_select(self):
        selected = self.list.GetFirstSelected()
        if selected != -1:
            info = self.list.GetItemPyData(selected)
            pid = info["pid"]
            name = info["name"]
            result = removed = False
            process = None
            try:
                process = psutil.Process(pid)
                if wx.ID_YES != wx.MessageDialog(
                        self,
                        f"プロセス {name} (PID: {pid}) を強制終了しますか？\n\n"
                        f"強制終了するとエラーが発生したり、データが破損する可能性があります。\n"
                        f"可能な限り、アプリで終了操作を行ってください。\n"
                        f"\n"
                        f"続行しますか？",
                        "強制終了",
                        style=wx.YES_NO | wx.CENTRE,
                ).ShowModal():
                    return

                process.kill()
                result = True

            except psutil.NoSuchProcess:
                removed = True

            except psutil.AccessDenied as e:
                wx.MessageDialog(
                    self,
                    f"アクセスが拒否されました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            except Exception as e:
                traceback.print_exc()
                wx.MessageDialog(
                    self,
                    f"処理に失敗しました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            if removed:
                wx.MessageDialog(
                    self,
                    f"プロセスが見つかりませんでした",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_WARNING,
                ).ShowModal()

            if result or removed:
                if process and process.is_running():
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        return
                self.list.DeleteItem(selected)
                self.update_select_process(None)

    def _terminate_select(self):
        selected = self.list.GetFirstSelected()
        if selected != -1:
            info = self.list.GetItemPyData(selected)
            pid = info["pid"]
            name = info["name"]
            result = removed = False
            process = None
            try:
                process = psutil.Process(pid)
                if wx.ID_YES != wx.MessageDialog(
                        self,
                        f"プロセス {name} (PID: {pid}) を終了しますか？\n\n"
                        f"可能な限り、アプリで終了操作を行ってください。\n"
                        f"続行しますか？",
                        "終了",
                        style=wx.YES_NO | wx.CENTRE,
                ).ShowModal():
                    return

                process.terminate()
                result = True

            except psutil.NoSuchProcess:
                removed = True

            except psutil.AccessDenied as e:
                wx.MessageDialog(
                    self,
                    f"アクセスが拒否されました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            except Exception as e:
                traceback.print_exc()
                wx.MessageDialog(
                    self,
                    f"処理に失敗しました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            if removed:
                wx.MessageDialog(
                    self,
                    f"プロセスが見つかりませんでした",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_WARNING,
                ).ShowModal()

            if result or removed:
                if process and process.is_running():
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        return
                self.list.DeleteItem(selected)
                self.update_select_process(None)

    def _restart_select(self):
        selected = self.list.GetFirstSelected()
        if selected != -1:
            info = self.list.GetItemPyData(selected)
            pid = info["pid"]
            name = info["name"]
            cmdline = info["cmdline"] or None
            result = removed = False
            new_process = process = None
            try:
                process = psutil.Process(pid)

                if not cmdline:
                    wx.MessageDialog(
                        self,
                        "プロセスのコマンドラインを取得できませんでした",
                        "再起動",
                        style=wx.OK | wx.CENTRE,
                    ).ShowModal()
                    return

                if wx.ID_YES != wx.MessageDialog(
                        self,
                        f"プロセス {name} (PID: {pid}) を再起動しますか？\n\n"
                        f"可能な限り、アプリで再起動操作を行ってください。\n"
                        f"\n"
                        f"続行しますか？",
                        "再起動",
                        style=wx.YES_NO | wx.CENTRE,
                ).ShowModal():
                    return

                cwd = process.cwd()
                environ = process.environ()
                process.kill()
                new_process = subprocess.Popen(cmdline, cwd=cwd, env=environ)

                result = True

            except psutil.NoSuchProcess:
                removed = True

            except psutil.AccessDenied as e:
                wx.MessageDialog(
                    self,
                    f"アクセスが拒否されました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            except Exception as e:
                traceback.print_exc()
                wx.MessageDialog(
                    self,
                    f"処理に失敗しました\n\n{type(e).__name__}: {e}",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR,
                ).ShowModal()
                return

            if removed:
                wx.MessageDialog(
                    self,
                    f"プロセスが見つかりませんでした",
                    "エラー",
                    style=wx.OK | wx.CENTRE | wx.ICON_WARNING,
                ).ShowModal()

            if result or removed:
                if process and process.is_running():
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        return
                self.list.DeleteItem(selected)
                self.update_select_process(None)

            if new_process:
                try:
                    new_process_info = _dump_process(new_process.pid)
                except psutil.Error as e:
                    print(f"WARN: Failed to get info: {e}")
                else:
                    self._append_process_item_to_list(new_process_info)
                    self.sort_lists(select_pid=new_process.pid)


if __name__ == '__main__':
    _app = wx.App()
    from ramnotify import RamNotifyConfig
    config = RamNotifyConfig(Path("../settings.json"))
    config.load()
    app = ProcessListApp(None, config)
    app.frame.SetPosition((50, -(50 + app.frame.GetSize()[1])))
    app.frame.Show()
    _app.MainLoop()
