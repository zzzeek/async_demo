import sys
import io
import re
import os
import collections
import time
import curses
import curses.textpad


class sensical_frame:
    __slots__ = ("frame",)

    def __init__(self, frame):
        self.frame = frame

    def get_segment(self, start, end):
        if "<" in self.filename:
            return

        with open(self.filename, "r") as file_:
            for lineno, line in enumerate(file_):
                if lineno >= end:
                    break
                elif lineno >= start:
                    yield line.rstrip()

    def is_part_of(self, fn_name):
        ff = self.frame

        while ff is not None:
            if ff.f_code.co_name == fn_name:
                return True
            elif (
                ff.f_code.co_name == "greenlet_spawn"
                and ff.f_locals["fn"].__code__.co_name == fn_name
            ):
                return True

            ff = ff.f_back

        return False

    @property
    def is_stdlib(self):
        return self.filename.startswith(
            sys.base_prefix
        ) or self.filename.startswith("<frozen")

    @property
    def filename(self):
        return self.frame.f_code.co_filename

    @property
    def function_name(self):
        return self.frame.f_code.co_name

    @property
    def line_number(self):
        return self.frame.f_lineno

    def __str__(self):
        return f"{self.filename} {self.function_name} {self.line_number}"


COLOR_MAP = {
    "K": curses.COLOR_BLACK,
    "B": curses.COLOR_BLUE,
    "C": curses.COLOR_CYAN,
    "G": curses.COLOR_GREEN,
    "M": curses.COLOR_MAGENTA,
    "R": curses.COLOR_RED,
    "W": curses.COLOR_WHITE,
    "Y": curses.COLOR_YELLOW,
}


class widget:

    def resize(self, window, top, left, char_height, char_width):
        self.window = window
        self.top = top
        self.left = left
        self.char_height = char_height
        self.char_width = char_width

    def _rectangle(self, win, uly, ulx, lry, lrx, attr=0):
        """Draw a rectangle with corners at the provided upper-left
        and lower-right coordinates.
        """
        win.vline(uly + 1, ulx, curses.ACS_VLINE, lry - uly - 1, attr)
        win.hline(uly, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1, attr)
        win.hline(lry, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1, attr)
        win.vline(uly + 1, lrx, curses.ACS_VLINE, lry - uly - 1, attr)
        win.addch(uly, ulx, curses.ACS_ULCORNER, attr)
        win.addch(uly, lrx, curses.ACS_URCORNER, attr)
        win.addch(lry, lrx, curses.ACS_LRCORNER, attr)
        win.addch(lry, ulx, curses.ACS_LLCORNER, attr)

    def _draw_border(self, attr=0):

        bottom = min(self.top + self.char_height, curses.LINES - 1)
        right = min(self.left + self.char_width, curses.COLS - 2)

        self._rectangle(
            self.window, self.top - 1, self.left - 1, bottom, right, attr=attr
        )

    def _blank(self):
        for vert in range(self.char_height):
            self.window.addstr(
                self.top + vert, self.left, " " * (self.char_width - 1)
            )

    def write_header(self, text, attr=0):
        self.window.addstr(self.top - 1, self.left + 5, f" {text} ", attr)

    def write_text(self, relative_vert_pos, text, color=None):
        top = self.top + relative_vert_pos + 1
        bottom = curses.LINES - 2
        if top > bottom:
            raise Exception(f"vert pos too great: {top}")

        text = text[0 : self.char_width - 2]

        if color:
            self.window.addstr(
                self.top + relative_vert_pos,
                self.left + 1,
                text,
                _COLOR_PAIRS[color],
            )
        else:
            self.window.addstr(
                self.top + relative_vert_pos, self.left + 1, text
            )


class screen(widget):
    started = False
    running = False

    def __init__(self):
        self.window = curses.initscr()

        curses.noecho()
        curses.start_color()

        self.window.nodelay(True)

        global _COLOR_PAIRS
        _COLOR_PAIRS = {}
        for i, (k, v) in enumerate(COLOR_MAP.items(), 1):
            curses.init_pair(i, v, curses.COLOR_BLACK)
            _COLOR_PAIRS[k] = curses.color_pair(i)

        self.console = console()
        self.column_one = draw_column()
        self.column_two = draw_column()
        self._redraw()
        self.started = True

    def _update_header(self):
        if not self.running:
            self.console.write_header(
                "stopped: press space to resume, or S to step",
                _COLOR_PAIRS["R"],
            )
        else:
            self.console.write_header(
                "running...press space to pause", _COLOR_PAIRS["G"]
            )

    def _redraw(self):
        self.char_height = curses.LINES - 1
        self.char_width = curses.COLS - 1

        self.window.clear()

        thirds = self.char_height // 3
        quarters = self.char_height // 4

        code_col_height = 3 * quarters - 4
        code_col_width = curses.COLS // 2 - 3

        self.console.resize(
            self.window,
            self.char_height - quarters,
            2,
            quarters - 1,
            self.char_width - 4,
        )

        self.column_one.resize(self.window, 2, 2, code_col_height, code_col_width)
        self.column_two.resize(
            self.window,
            2,
            curses.COLS // 2 + 1,
            code_col_height,
            code_col_width,
        )
        self._update_header()
        self.window.refresh()

    def process_input(self):
        time.sleep(0.2)
        while True:
            ch = self.window.getch()
            if ch == curses.KEY_RESIZE:
                y, x = self.window.getmaxyx()
                if y != curses.LINES or x != curses.COLS:
                    curses.resizeterm(y, x)
                    self._redraw()
            elif ch == ord(" "):
                self.running = not self.running
                self._update_header()
            elif ch == ord("s"):
                if self.running:
                    self.running = False
                    self._update_header()
                break

            if not self.running:
                time.sleep(0.1)
            else:
                break


class console(widget):
    class stream(io.TextIOBase):
        def __init__(self, console):
            self.console = console

        def write(self, text):
            self.console.write(text)

    def __init__(self):
        self.buf = collections.deque(maxlen=200)
        self.out = console.stream(self)

    def resize(self, window, top, left, char_height, char_width):
        super().resize(window, top, left, char_height, char_width)
        self._draw_border()

    def _append_viewport(self, text):
        text = text.rstrip()
        self.buf.append(text.rstrip())

    def _get_viewport(self):
        return list(self.buf)[-self.char_height :]

    def write(self, text):
        self._append_viewport(text)

        for vert, line in enumerate(self._get_viewport()):
            line = line[0 : self.char_width] + (
                " " * (self.char_width - len(line))
            )
            self.write_text(vert, f"{line[0:self.char_width]}")


class draw_column(widget):

    _current_frame: sensical_frame | None

    def __init__(self):
        self._current_frame = None
        self._primary_color = "W"

    def unset(self):
        if self._primary_color != "W":
            self._primary_color = "W"
            self._redraw()

    def write_code(self, sf: sensical_frame):
        self._current_frame = sf
        self._primary_color = "C"
        self._redraw()

    def resize(self, window, top, left, char_height, char_width):
        super().resize(window, top, left, char_height, char_width)
        self._redraw()

    def _redraw(self):
        self._draw_border(attr=_COLOR_PAIRS[self._primary_color])

        self._blank()

        sf = self._current_frame
        if sf is None:
            return

        fn_parts = sf.filename.split(os.sep)
        self.write_header(os.sep.join(fn_parts[-4:]), attr=_COLOR_PAIRS["M"])

        code_height = self.char_height - 3

        zb_lineno = sf.line_number - 1

        start = max(0, zb_lineno - code_height // 2)
        end = zb_lineno + code_height // 2

        codelines = list(sf.get_segment(start, end))

        for vert, line in enumerate(codelines):
            self.write_text(
                vert + 1,
                f"{start + vert + 1:5d}  {line}",
                "G" if vert + start == zb_lineno else None,
            )


class Demo:
    def __init__(self, col1, col2):
        self.col1 = col1
        self.col2 = col2

    def show_methods(self, *meths):

        allnames = set()
        self.per_meth = {}
        for filespec, fnnames in meths:
            allnames.add(filespec)
            if fnnames:
                self.per_meth[rf".*(?:{filespec})"] = fnnames
        self.catch_names = re.compile(rf".*(?:{'|'.join(allnames)})")
        return self

    def start(self):
        self.scr = scr = screen()

        window = scr.window
        window.refresh()

        import sys

        sys.settrace(self._set_trace())
        sys.stdout = scr.console.out

    def _set_trace(self):

        current_fn = None

        scr = self.scr

        def myfunc(frame, event, arg):
            sf = sensical_frame(frame)

            if sf.is_stdlib or not self.catch_names.match(
                sf.filename,
            ):
                return myfunc

            for per_name, meths in self.per_meth.items():
                if re.match(per_name, sf.filename):
                    if sf.function_name not in meths:
                        # scr.console.write(
                        # f"Skipping {sf.filename} -> {sf.function_name}")
                        return myfunc

            nonlocal current_fn
            if sf.is_part_of(self.col1):
                current_fn = self.col1
            elif sf.is_part_of(self.col2):
                current_fn = self.col2

            if current_fn == self.col1:
                scr.column_two.unset()
                scr.column_one.write_code(sf)
                scr.process_input()

            elif current_fn == self.col2:
                scr.column_one.unset()
                scr.column_two.write_code(sf)
                scr.process_input()

            return myfunc

        return myfunc
