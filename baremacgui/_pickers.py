"""DatePicker and TimePicker on NSDatePicker."""
from __future__ import annotations

import datetime as dt

from ._bridge import AK, FN
from ._controls import Control
from ._events import event


def _to_ns(value):
    return FN().NSDate.dateWithTimeIntervalSince1970_(value.timestamp())


def _from_ns(date):
    return dt.datetime.fromtimestamp(float(date.timeIntervalSince1970()))


class _Picker(Control):
    on_change = event()

    def _setup(self, ns, elements, calendar):
        ak = AK()
        ns.setDatePickerStyle_(
            ak.NSDatePickerStyleClockAndCalendar if calendar else ak.NSDatePickerStyleTextFieldAndStepper
        )
        ns.setDatePickerElements_(elements)
        ns.setDatePickerMode_(ak.NSDatePickerModeSingle)
        ns.setBezeled_(True)
        ns.setDrawsBackground_(True)

    def _finish_setup(self):
        self._bind(self.ns, self.on_change.emit)


class DatePicker(_Picker):
    """A date field with a stepper (calendar=True: a month calendar). value is a datetime.date.

    minimum / maximum limit the choice. Assigning .value never calls on_change; only the user does.
    """

    def __init__(self, value=None, calendar=False, minimum=None, maximum=None, grow=0, **size):
        ak = AK()
        for name, bound in (("minimum", minimum), ("maximum", maximum)):
            if bound is not None and (not isinstance(bound, dt.date) or isinstance(bound, dt.datetime)):
                raise TypeError(f"{name} must be a datetime.date, got {bound!r}")
        ns = ak.NSDatePicker.alloc().init()
        self._setup(ns, ak.NSDatePickerElementFlagYearMonthDay, calendar)
        if minimum is not None:
            ns.setMinDate_(_to_ns(dt.datetime.combine(minimum, dt.time())))
        if maximum is not None:
            ns.setMaxDate_(_to_ns(dt.datetime.combine(maximum, dt.time())))
        super().__init__(ns, grow, **size)
        self._finish_setup()
        self.value = value if value is not None else dt.date.today()

    @property
    def value(self):
        return _from_ns(self.ns.dateValue()).date()

    @value.setter
    def value(self, day):
        if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
            raise TypeError(f"DatePicker value must be a datetime.date, got {day!r}")
        self.ns.setDateValue_(_to_ns(dt.datetime.combine(day, dt.time(12))))  # noon: safe around DST changes


class TimePicker(_Picker):
    """A time field with a stepper (hours and minutes, optionally seconds). value is a datetime.time."""

    def __init__(self, value=None, seconds=False, grow=0, **size):
        ak = AK()
        ns = ak.NSDatePicker.alloc().init()
        elements = ak.NSDatePickerElementFlagHourMinuteSecond if seconds else ak.NSDatePickerElementFlagHourMinute
        self._setup(ns, elements, False)
        super().__init__(ns, grow, **size)
        self._finish_setup()
        self.value = value if value is not None else dt.datetime.now().time().replace(microsecond=0)

    @property
    def value(self):
        return _from_ns(self.ns.dateValue()).time().replace(microsecond=0)

    @value.setter
    def value(self, moment):
        if not isinstance(moment, dt.time):
            raise TypeError(f"TimePicker value must be a datetime.time, got {moment!r}")
        today = dt.date.today()
        self.ns.setDateValue_(_to_ns(dt.datetime.combine(today, moment.replace(microsecond=0))))
