"""A long task in a worker thread: progress bar, cancel, elapsed time, results handed back with invoke."""
import threading
import time

from baremacgui import App, Button, HBox, Label, ProgressBar, Spacer, Timer, VBox, Window


def format_elapsed(seconds):
    """65.4 -> '1:05'."""
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"


STEPS = 40

app = App("Progress")
job = {"cancel": threading.Event(), "started": 0.0}

with Window("Progress", size=(420, 200)) as win:
    with VBox(padding=20, gap=12):
        status = Label("Ready")
        bar = ProgressBar(0, 0, STEPS)
        elapsed = Label("0:00")
        Spacer()
        with HBox(gap=8):
            Spacer()
            cancel = Button("Cancel")
            start = Button("Start", default=True)

cancel.enabled = False
clock = Timer(0.5, lambda: setattr(elapsed, "text", format_elapsed(time.monotonic() - job["started"])), start=False)


def finish(text):
    clock.stop()
    status.text = text
    start.enabled = True
    cancel.enabled = False


def work():  # worker thread: only app.invoke touches the window
    for step in range(1, STEPS + 1):
        if job["cancel"].is_set():
            app.invoke(finish, f"Cancelled after {step - 1} of {STEPS} steps")
            return
        time.sleep(0.1)
        app.invoke(lambda value=step: (setattr(bar, "value", value), setattr(status, "text", f"Step {value} of {STEPS}")))
    app.invoke(finish, "Done")


def begin():
    job["cancel"].clear()
    job["started"] = time.monotonic()
    bar.value = 0
    start.enabled = False
    cancel.enabled = True
    clock.start()
    threading.Thread(target=work, daemon=True).start()


start.on_click(begin)
cancel.on_click(job["cancel"].set)

if __name__ == "__main__":
    app.run()
