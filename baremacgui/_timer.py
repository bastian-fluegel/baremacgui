"""Timer: call handlers on the UI thread at an interval."""
from __future__ import annotations

from ._bridge import FN, make_target
from ._events import connect_options, event, split_options
from ._options import check_interval


class Timer:
    """Calls on_tick on the UI thread every `interval` seconds.

        clock = Timer(1.0, update_clock)            # starts at once
        once = Timer(3, hide_hint, repeat=False)
        clock.stop(); clock.start()

    start=False creates it stopped. The timer keeps running while a menu is open
    or a window is resized (it runs in the common run-loop modes).
    """

    on_tick = event()

    def __init__(self, interval, handler=None, repeat=True, start=True, **options):
        handlers = split_options(options)
        if options:
            raise TypeError(f"Timer got unexpected options: {sorted(options)}")
        self._interval = check_interval(interval)
        self.repeat = bool(repeat)
        self._timer = None
        self._target = make_target(self._fire)
        connect_options(self, handlers)
        if handler is not None:
            self.on_tick(handler)
        if start:
            self.start()

    def _fire(self):
        if not self.repeat:
            self._timer = None
        self.on_tick.emit()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = check_interval(seconds)
        if self.running:
            self.start()  # restart with the new interval

    @property
    def running(self):
        return self._timer is not None and bool(self._timer.isValid())

    def start(self):
        """(Re)start the timer; the first tick comes after one interval."""
        self.stop()
        foundation = FN()
        timer = foundation.NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            self._interval, self._target, b"fire:", None, self.repeat
        )
        foundation.NSRunLoop.mainRunLoop().addTimer_forMode_(timer, foundation.NSRunLoopCommonModes)
        self._timer = timer

    def stop(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
