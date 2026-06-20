"""간단한 계산기 (toolchain 검증용)
Tkinter + PyInstaller 로 .exe 가 제대로 만들어지는지 확인하기 위한 샘플.
"""
import tkinter as tk


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("계산기 테스트")
        self.resizable(False, False)

        self.expr = ""
        self.display = tk.Entry(
            self, font=("Segoe UI", 20), justify="right", bd=8, relief="flat"
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)

        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
            ("C", 5, 0),
        ]
        for (text, r, c) in buttons:
            span = 4 if text == "C" else 1
            tk.Button(
                self, text=text, font=("Segoe UI", 16), width=4, height=2,
                command=lambda t=text: self.on_click(t),
            ).grid(row=r, column=c, columnspan=span, sticky="nsew", padx=2, pady=2)

    def on_click(self, char):
        if char == "C":
            self.expr = ""
        elif char == "=":
            try:
                self.expr = str(eval(self.expr))
            except Exception:
                self.expr = "오류"
        else:
            if self.expr == "오류":
                self.expr = ""
            self.expr += char
        self.display.delete(0, tk.END)
        self.display.insert(0, self.expr)


if __name__ == "__main__":
    Calculator().mainloop()
