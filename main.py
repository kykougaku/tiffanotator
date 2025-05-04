import re
import tkinter as tk
from tkinter import ttk
import os
import cv2
import pandas as pd
import numpy as np
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable

font_lg = ('Arial', 24)
font_md = ('Arial', 16)
font_sm = ('Arial', 12)

plt.rcParams['font.family'] = 'Arial'

plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.major.width'] = 1.0
plt.rcParams['ytick.major.width'] = 1.0
plt.rcParams['xtick.labelsize'] = 25
plt.rcParams['ytick.labelsize'] = 25

plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['axes.labelsize'] = 35         # 軸ラベルのフォントサイズ
plt.rcParams['axes.linewidth'] = 1.0        # グラフ囲う線の太さ

plt.rcParams['legend.loc'] = 'best'        # 凡例の位置、"best"でいい感じのところ
plt.rcParams['legend.frameon'] = True       # 凡例を囲うかどうか、Trueで囲う、Falseで囲わない
plt.rcParams['legend.framealpha'] = 1.0     # 透過度、0.0から1.0の値を入れる
plt.rcParams['legend.facecolor'] = 'white'  # 背景色
plt.rcParams['legend.edgecolor'] = 'black'  # 囲いの色
plt.rcParams['legend.fancybox'] = False     # Trueにすると囲いの四隅が丸くなる

plt.rcParams['lines.linewidth'] = 1.0
plt.rcParams['image.cmap'] = 'jet'
plt.rcParams['figure.subplot.top'] = 0.95
plt.rcParams['figure.subplot.bottom'] = 0.15
plt.rcParams['figure.subplot.left'] = 0.1
plt.rcParams['figure.subplot.right'] = 0.95

class EditableTable(ttk.Treeview):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._init_bindings()

    def _init_bindings(self):
        self.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region == "cell":
            column = self.identify_column(event.x)
            row = self.identify_row(event.y)
            self._edit_cell(row, column)

    def _edit_cell(self, row, column):
        x, y, width, height = self.bbox(row, column)
        value = self.item(row, "values")[int(column[1:]) - 1]

        self.entry = tk.Entry(self)
        self.entry.place(x=x, y=y, width=width, height=height)
        self.entry.insert(0, value)
        self.entry.focus()
        self.entry.bind("<Return>", lambda event: self._save_edit(row, column))

    def _save_edit(self, row, column):
        new_value = self.entry.get()
        values = list(self.item(row, "values"))
        values[int(column[1:]) - 1] = new_value
        self.item(row, values=values)
        self.entry.destroy()


def is_num(s):
    try:
        float(s)
    except ValueError:
        if s == "-":
            return True
        return False
    else:
        return True

def update_spec_plot(func):
    def wrapper(*args, **kwargs):
        args[0].ax.clear()
        ret = func(*args, **kwargs)
        args[0].canvas.draw()
        return ret
    return wrapper

def check_map_loaded(func):
    # マッピングデータが読み込まれているか確認するデコレータ
    # 読み込まれていない場合，エラーメッセージを表示する
    def wrapper(*args, **kwargs):
        if len(args[0].dl_raw.spec_dict) == 0:
            messagebox.showerror('Error', 'Choose map data.')
            return
        return func(*args, **kwargs)

    return wrapper

class SpeDataLoader_wrpper:
    def __init__(self):
        self.spec_dict = {}

    def load_files(self, filenames:list) -> None:
        filenames = sorted(filenames, key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()))
        for filename in filenames:
            if filename in self.spec_dict:
                continue

            if filename.endswith('.tif') or filename.endswith('.tiff'):
                image_data= cv2.imread(filename, cv2.IMREAD_UNCHANGED)
                self.spec_dict[filename] = image_data.astype(np.float32)

    def delete_file(self, filename):
        if filename in self.spec_dict:
            del self.spec_dict[filename]


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master = master

        self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0
        self.rectangles = []
        self.texts = []
        self.ranges = []
        self.drawing = False
        self.rect_drawing = None
        self.dl_raw = SpeDataLoader_wrpper()

        self.new_window = None
        self.widgets_assign = {}

        self.create_widgets()

    def create_widgets(self) -> None:
        # スタイル設定
        style = ttk.Style()
        style.theme_use('winnative')
        style.configure('TButton', font=font_md, width=14, padding=[0, 4, 0, 4], foreground='black')
        style.configure('R.TButton', font=font_md, width=14, padding=[0, 4, 0, 4], foreground='red')
        style.configure('TLabel', font=font_sm, padding=[0, 4, 0, 4], foreground='black')
        style.configure('Color.TLabel', font=font_lg, padding=[0, 0, 0, 0], width=4, background='black')
        style.configure('TEntry', font=font_md, width=14, padding=[0, 4, 0, 4], foreground='black')
        style.configure('TCheckbutton', font=font_md, padding=[0, 4, 0, 4], foreground='black')
        style.configure('TMenubutton', font=font_md, padding=[20, 4, 0, 4], foreground='black')
        style.configure('TCombobox', font=font_md, padding=[20, 4, 0, 4], foreground='black')
        style.configure('TTreeview', font=font_md, foreground='black')

        self.width_canvas = 900
        self.height_canvas = 600
        dpi = 50
        if os.name == 'posix':
            fig = plt.figure(figsize=(self.width_canvas / 2 / dpi, self.height_canvas / 2 / dpi), dpi=dpi)
        else:
            fig = plt.figure(figsize=(self.width_canvas / dpi, self.height_canvas / dpi), dpi=dpi)

        self.ax = fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(fig, self.master)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=3)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=3, column=0)

        frame_download = ttk.LabelFrame(self.master, text='download')
        frame_map = ttk.LabelFrame(self.master, text='settings')
        frame_download.grid(row=0, column=1)
        frame_map.grid(row=1, column=1)

        # frame_listbox
        self.treeview = EditableTable(frame_download, height=20, selectmode=tk.EXTENDED)
        self.treeview_scrollbar = ttk.Scrollbar(frame_download, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview['yscrollcommand'] = self.treeview_scrollbar.set
        self.treeview['columns'] = ['filename', "Si", "SWCNT"]
        self.treeview.column('#0', width=100, stretch=tk.NO)
        self.treeview.column('filename', width=100, anchor=tk.CENTER)
        self.treeview.column('Si', width=100, anchor=tk.CENTER)
        self.treeview.column('SWCNT', width=100, anchor=tk.CENTER)
        self.treeview.heading('#0', text='#')
        self.treeview.heading('filename', text='filename')
        self.treeview.heading('Si', text='Si')
        self.treeview.heading('SWCNT', text='SWCNT')
        self.treeview.bind('<<TreeviewSelect>>', self.select_data)
        self.treeview.bind('<Button-2>', self.delete_data)
        self.treeview.bind('<Button-3>', self.delete_data)

        self.button_download = ttk.Button(frame_download, text='DOWNLOAD', command=self.download, state=tk.DISABLED)

        self.treeview.grid(row=0, column=0, sticky=tk.NSEW)
        self.treeview_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.button_download.grid(row=1, column=0, columnspan=2, sticky=tk.EW)

        # frame_map

        vcmr1 = (self.register(self.validate_cmap_range_1), '%P')
        vcmr2 = (self.register(self.validate_cmap_range_2), '%P')
        vwr1 = (self.register(self.validate_width_range_1), '%P')
        vwr2 = (self.register(self.validate_width_range_2), '%P')
        vhr1 = (self.register(self.validate_height_range_1), '%P')
        vhr2 = (self.register(self.validate_height_range_2), '%P')
        label_cmap_range = ttk.Label(frame_map, text='Color Range')
        label_width_range = ttk.Label(frame_map, text='Width Range')
        label_height_range = ttk.Label(frame_map, text='Height Range')
        self.cmap_range_1 = tk.DoubleVar(value=0)
        self.cmap_range_2 = tk.DoubleVar(value=100)
        self.width_range_1 = tk.DoubleVar(value=0)
        self.width_range_2 = tk.DoubleVar(value=640)
        self.height_range_1 = tk.DoubleVar(value=0)
        self.height_range_2 = tk.DoubleVar(value=512)
        self.entry_cmap_range_1 = ttk.Entry(frame_map, textvariable=self.cmap_range_1, validate="key", validatecommand=vcmr1, justify=tk.CENTER, font=font_md, width=6)
        self.entry_cmap_range_2 = ttk.Entry(frame_map, textvariable=self.cmap_range_2, validate="key", validatecommand=vcmr2, justify=tk.CENTER, font=font_md, width=6)
        self.entry_width_range_1 = ttk.Entry(frame_map, textvariable=self.width_range_1, validate="key", validatecommand=vwr1, justify=tk.CENTER, font=font_md, width=6)
        self.entry_width_range_2 = ttk.Entry(frame_map, textvariable=self.width_range_2, validate="key", validatecommand=vwr2, justify=tk.CENTER, font=font_md, width=6)
        self.entry_height_range_1 = ttk.Entry(frame_map, textvariable=self.height_range_1, validate="key", validatecommand=vhr1, justify=tk.CENTER, font=font_md, width=6)
        self.entry_height_range_2 = ttk.Entry(frame_map, textvariable=self.height_range_2, validate="key", validatecommand=vhr2, justify=tk.CENTER, font=font_md, width=6)
        self.entry_cmap_range_1.config(state=tk.DISABLED)
        self.entry_cmap_range_2.config(state=tk.DISABLED)
        self.map_color = tk.StringVar(value='gray')
        label_map_color = ttk.Label(frame_map, text='Color Map')
        self.optionmenu_map_color = ttk.OptionMenu(frame_map, self.map_color, self.map_color.get(),
                                           *sorted(['viridis', 'plasma', 'inferno', 'magma', 'cividis',
                                                    'Wistia', 'hot', 'binary', 'bone', 'cool', 'copper',
                                                    'gray', 'pink', 'spring', 'summer', 'autumn', 'winter',
                                                    'RdBu', 'Spectral', 'bwr', 'coolwarm', 'hsv', 'twilight',
                                                    'CMRmap', 'cubehelix', 'brg', 'gist_rainbow', 'rainbow',
                                                    'jet', 'nipy_spectral', 'gist_ncar']),
                                                   command=self.on_change_cmap_settings)
        self.optionmenu_map_color['menu'].config(font=font_md)
        self.map_autoscale = tk.BooleanVar(value=True)
        checkbox_map_autoscale = ttk.Checkbutton(frame_map, text='Color Map Auto Scale', command=self.on_change_cmap_settings, variable=self.map_autoscale, takefocus=False)
        self.median_filter = tk.BooleanVar(value=False)
        checkbox_median_filter = ttk.Checkbutton(frame_map, text='Median Filter', variable=self.median_filter, takefocus=False)

        checkbox_map_autoscale.grid(row=1, column=0, columnspan=4)
        label_cmap_range.grid(row=2, column=0)
        self.entry_cmap_range_1.grid(row=2, column=1)
        self.entry_cmap_range_2.grid(row=2, column=2)
        label_map_color.grid(row=3, column=0)
        self.optionmenu_map_color.grid(row=3, column=1, columnspan=2, sticky=tk.EW)
        label_width_range.grid(row=4, column=0)
        self.entry_width_range_1.grid(row=4, column=1)
        self.entry_width_range_2.grid(row=4, column=2)
        label_height_range.grid(row=5, column=0)
        self.entry_height_range_1.grid(row=5, column=1)
        self.entry_height_range_2.grid(row=5, column=2)
        # canvas_drop
        checkbox_median_filter.grid(row=6, column=0)
        self.canvas_drop = tk.Canvas(self.master, width=self.width_canvas, height=self.height_canvas)
        self.canvas_drop.create_rectangle(0, 0, self.width_canvas, self.height_canvas, fill='lightgray')
        self.canvas_drop.create_text(self.width_canvas / 2, self.height_canvas * 1 / 2, text='Data Drop Here',
                                     font=('Arial', 30))

    @check_map_loaded
    def validate_cmap_range_1(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if after == '-':
                after = 0
            if float(after) < self.cmap_range_2.get():
                pass #Todo: width_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def validate_cmap_range_2(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if after == '-':
                after = 0
            if self.cmap_range_1.get() < float(after):
                pass #Todo: cmap_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def validate_width_range_1(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if float(after) < self.width_range_2.get():
                pass #Todo: width_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def validate_width_range_2(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if self.width_range_1.get() < float(after):
                pass #Todo: width_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def validate_height_range_1(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if float(after) < self.height_range_2.get():
                pass #Todo: width_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def validate_height_range_2(self, after):
        if self.dl_raw.spec_dict is None:
            return False
        if is_num(after):
            if self.height_range_1.get() < float(after):
                pass #Todo: width_rangeの更新
            return True
        elif after == '':
            return True
        else:
            return False

    @check_map_loaded
    def on_change_cmap_settings(self, *args) -> None:
        if self.map_autoscale.get():
            self.entry_cmap_range_1.config(state=tk.DISABLED)
            self.entry_cmap_range_2.config(state=tk.DISABLED)
        else:
            self.entry_cmap_range_1.config(state=tk.NORMAL)
            self.entry_cmap_range_2.config(state=tk.NORMAL)

    @check_map_loaded
    def download(self) -> None:
        data = []
        save_path = os.path.dirname(self.treeview.item(0)['values'][0])
        for i in self.treeview.get_children():
            row_data = self.treeview.item(i)['values']
            row_data[0] = os.path.basename(row_data[0])
            row_data[1] = float(row_data[1])
            row_data[2] = float(row_data[2])
            data.append(row_data)
        df = pd.DataFrame(data, columns=['filename', 'Si', 'SWCNT'])
        df.to_csv(os.path.join(save_path, 'data.csv'), index=False, header=True)

    @update_spec_plot
    def select_data(self, event) -> None:
        if self.treeview.focus() == '':
            return
        key = self.treeview.item(self.treeview.focus())['values'][0]
        self.show_spectrum(self.dl_raw.spec_dict[key])

    @update_spec_plot
    def delete_data(self, event) -> None:
        if self.treeview.focus() == '':
            return
        key = self.treeview.item(self.treeview.focus())['values'][0]
        ok = messagebox.askyesno('確認', f'Delete {key}?')
        if not ok:
            return
        self.dl_raw.delete_file(key)

        self.update_treeview()
        self.msg.set(f'Deleted {key}.')

    @update_spec_plot
    def drop(self, event=None) -> None:
        self.canvas_drop.place_forget()
        if event.data[0] == '{':
            filenames = list(map(lambda x: x.strip('{').strip('}'), event.data.split('} {')))
        else:
            filenames = event.data.split()
        self.dl_raw.load_files(filenames)
        self.show_spectrum(self.dl_raw.spec_dict[filenames[0]])
        self.update_treeview()

    def drop_enter(self, event: TkinterDnD.DnDEvent) -> None:
        self.canvas_drop.place(anchor='nw', x=0, y=0)

    def drop_leave(self, event: TkinterDnD.DnDEvent) -> None:
        self.canvas_drop.place_forget()

    def show_spectrum(self, imagedata:np.ndarray) -> None:
        if self.median_filter.get():
            imagedata = cv2.medianBlur(imagedata, 3)

        imagedata = imagedata[int(self.height_range_1.get()):int(self.height_range_2.get()),
                                int(self.width_range_1.get()):int(self.width_range_2.get())]

        if self.map_autoscale.get():
            self.ax.imshow(imagedata, cmap=self.map_color.get(), aspect='equal')
            self.cmap_range_1.set(np.min(imagedata))
            self.cmap_range_2.set(np.max(imagedata))
        else:
            self.ax.imshow(imagedata, cmap=self.map_color.get(), aspect='equal',
                           vmin=self.cmap_range_1.get(), vmax=self.cmap_range_2.get())



    def update_treeview(self) -> None:
        self.treeview.delete(*self.treeview.get_children())
        for i, filename in enumerate(self.dl_raw.spec_dict.keys()):
            self.treeview.insert(
                '',
                tk.END,
                iid=str(i),
                text=str(os.path.basename(filename).split(".")[0]),
                values=[filename, 0, 0],
                open=True,
                )
            self.button_download.config(state=tk.NORMAL)


def main():
    root = TkinterDnD.Tk()
    app = MainWindow(master=root)
    root.protocol('WM_DELETE_WINDOW', app.quit)
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<DropEnter>>', app.drop_enter)
    root.dnd_bind('<<DropLeave>>', app.drop_leave)
    root.dnd_bind('<<Drop>>', app.drop)
    app.mainloop()


if __name__ == '__main__':
    main()