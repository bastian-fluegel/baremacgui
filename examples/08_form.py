"""A registration form with live validation, a date picker and a switchable button."""
import datetime as dt
import re

from baremacgui import (
    App, Button, CheckBox, DatePicker, DropDown, HBox, Label, Spacer, TextBox, VBox, Window, show_info,
)


def validate(name, email, password, accepted, birthday=None, today=None):
    """Return the first problem as text, or None when the form is fine."""
    today = today or dt.date.today()
    if not name.strip():
        return "Please enter your name."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        return "That does not look like an e-mail address."
    if len(password) < 8:
        return "The password needs at least 8 characters."
    if birthday is not None and birthday > today:
        return "The birthday lies in the future."
    if not accepted:
        return "Please accept the terms."
    return None


app = App("Register")

with Window("Register", size=(440, 360)) as win:
    with VBox(padding=20, gap=10):
        name = TextBox(placeholder="Full name")
        email = TextBox(placeholder="E-mail")
        password = TextBox(placeholder="Password (8+ characters)", password=True)
        with HBox(gap=8):
            Label("Birthday")
            birthday = DatePicker(dt.date(2000, 1, 1))
            Spacer()
            plan = DropDown(["Free", "Pro", "Team"])
        terms = CheckBox("I accept the terms")
        problem = Label("")
        Spacer()
        with HBox():
            Spacer()
            submit = Button("Create account", default=True)


def current_problem():
    return validate(name.text, email.text, password.text, terms.checked, birthday.value)


def refresh():
    text = current_problem()
    problem.text = text or ""
    submit.enabled = text is None


def create():
    show_info(f"Welcome, {name.text.strip()}! Plan: {plan.text}.", "Account created", parent=win)


for field in (name, email, password):
    field.on_change(refresh)
terms.on_change(refresh)
birthday.on_change(refresh)
submit.on_click(create)
win.default_button = submit
refresh()

if __name__ == "__main__":
    app.run()
