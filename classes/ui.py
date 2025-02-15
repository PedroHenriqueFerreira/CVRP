from tkinter import Tk, Canvas

class UI:
    def __init__(self):
        self.root = Tk()
        self.canvas = Canvas(self.root, width=800, height=600)
        self.canvas.pack()
        
        x = 400
        y = 300
        
        self.canvas.create_oval(x, y, x+10, y+10, fill='black')
        
        self.root.mainloop()
        
UI()