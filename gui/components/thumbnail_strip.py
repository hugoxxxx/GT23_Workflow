# gui/components/thumbnail_strip.py
"""
EN: XHS-style horizontal thumbnail strip for image selection
CN: 小红书风格的水平样片导航条，用于图片选择
"""

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageDraw
from concurrent.futures import ThreadPoolExecutor

class ThumbnailStrip(ttk.Frame):
    """
    EN: XHS-style horizontal thumbnail strip for image selection
    CN: 小红书风格的水平样片导航条，用于图片选择
    """
    def __init__(self, parent, lang="en", on_select=None, on_delete=None, on_add=None, on_order_changed=None):
        super().__init__(parent)
        self.lang = lang
        self.on_select = on_select
        self.on_delete = on_delete
        self.on_add = on_add
        self.on_order_changed = on_order_changed
        self.thumbs = {} # path -> photoimage
        self.active_path = None
        self.drag_widget = None # EN: Currently dragging widget / CN: 当前正在拖拽的组件
        self._drag_data = {"x": 0, "y": 0}
        
        # UI Components
        self.canvas = tk.Canvas(self, height=185, bg=ttk.Style().colors.bg, highlightthickness=0)
        self.canvas.pack(side=TOP, fill=X, expand=YES)
        
        self.scrollbar = ttk.Scrollbar(self, orient=HORIZONTAL, command=self.canvas.xview, bootstyle="round")
        self.scrollbar.pack(side=BOTTOM, fill=X)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=NW)
        
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.executor = ThreadPoolExecutor(max_workers=4)

    def update_language(self, lang):
        """EN: Update UI language / CN: 更新界面语言"""
        self.lang = lang
        # EN: Update the "+" button label if it exists / CN: 更新“+”按钮标签（如果存在）
        siblings = self.inner_frame.pack_slaves()
        if siblings:
            add_frame = siblings[-1]
            # EN: The "Add" button frame has two labels: "+" and "Add/添加"
            # CN: “添加”按钮框架有两个标签：“+”和“Add/添加”
            widgets = add_frame.winfo_children()
            if len(widgets) >= 2:
                # The second widget is the text label
                widgets[1].config(text="Add" if lang == "en" else "添加")

    def _on_mousewheel(self, event):
        # EN: Support horizontal scrolling with mouse wheel / CN: 支持滚轮水平滑动
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def update_images(self, paths):
        """EN: Load and render thumbnails from list of paths / CN: 从路径列表加载并渲染缩略图"""
        # Clear old
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        if not paths:
            return
            
        for idx, path in enumerate(paths):
            self._create_thumb_widget(path, idx)
            
        # EN: Add "+" button at the end / CN: 在末尾添加“+”按钮
        self._create_add_button()

    def _create_add_button(self):
        frame = ttk.Frame(self.inner_frame, padding=5)
        frame.pack(side=LEFT)
        
        # EN: Square placeholder for + / CN: 用于 + 的方型占位符
        btn = ttk.Label(frame, text="+", font=("Segoe UI", 28, "bold"), 
                       width=5, anchor=CENTER, cursor="hand2", 
                       bootstyle="secondary", padding=40)
        btn.pack()
        btn.bind("<Button-1>", lambda e: self.on_add() if self.on_add else None)
        
        ttk.Label(frame, text="Add" if self.lang == "en" else "添加", 
                 font=("Segoe UI", 8), foreground="gray").pack()

    def _create_thumb_widget(self, path, index):
        from PIL import ImageOps, ImageDraw
        
        container = ttk.Frame(self.inner_frame, padding=2)
        container.pack(side=LEFT)
        
        # EN: Actual frame for the thumbnail with 3px border space / CN: 带有 3px 描边空间的样片容器
        frame = ttk.Frame(container, padding=3, bootstyle="default")
        frame.pack()
        
        lbl = ttk.Label(frame, text="...", cursor="hand2")
        lbl.pack()
        
        # EN: Small Delete button at top-right (Hidden by default, hover to show)
        # CN: 右上角的小删除按钮 (默认隐藏，悬停显示)
        del_btn = ttk.Label(frame, text="×", cursor="hand2", font=("Segoe UI", 12), foreground="gray")
        # del_btn.place() is called in hover events
        del_btn.bind("<Button-1>", lambda e: self.on_delete(path) if self.on_delete else None)

        # EN: Async thumbnail generation / CN: 异步生成缩略图
        def generate():
            try:
                from PIL import ImageTk
                with Image.open(path) as img:
                    # EN: Force 1:1 Square Crop (Increased size) / CN: 强制 1:1 方型裁切 (增加尺寸)
                    img = ImageOps.fit(img, (120, 120), Image.Resampling.LANCZOS)
                    
                    # EN: Create rounded corners with PIL / CN: 使用 PIL 制作 8px 圆角
                    mask = Image.new('L', img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle((0, 0) + img.size, radius=8, fill=255)
                    img.putalpha(mask)
                    
                    # EN: IMPORTANT - Do NOT create PhotoImage in sub-thread
                    # CN: 重要 - 不要在子线程中创建 PhotoImage，否则会导致 Tcl/Tk 内部报错 (AttributeError)
                    processed_img = img.copy()
                    
                    # EN: Safely update UI using the parent frame's after()
                    # CN: 使用父框架's after() 安全更新 UI
                    def safe_update(pil_img=processed_img, target_lbl=lbl):
                        try:
                            if target_lbl.winfo_exists():
                                # EN: Create PhotoImage in MAIN thread
                                # CN: 在主线程中创建 PhotoImage
                                photo = ImageTk.PhotoImage(pil_img)
                                self.thumbs[path] = photo # EN: Persist reference / CN: 保持引用防止 GC
                                target_lbl.configure(image=photo, text="")
                        except Exception:
                            pass
                    self.after(0, safe_update)
            except Exception:
                pass
                
        self.executor.submit(generate)
        
        # EN: Interaction Events / CN: 交互事件
        def on_enter(e):
            del_btn.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-5, y=5)
            
        def on_leave(e):
            del_btn.place_forget()

        # EN: Drag and Drop Handlers / CN: 拖拽排序逻辑
        def on_drag_start(event):
            self.drag_widget = container
            self._drag_data["x"] = event.x
            self.drag_widget.configure(cursor="fleur")
            # EN: Visually highlight the one being moved / CN: 视觉高亮正在移动的对象
            frame.configure(bootstyle="info")

        def on_drag_motion(event):
            if not self.drag_widget: return
            
            # EN: Calculate global X of parent container / CN: 计算父容器的全局 X 坐标
            current_x = self.drag_widget.winfo_x() + (event.x - self._drag_data["x"])
            
            # EN: Find new insertion point among siblings / CN: 在兄弟组件中寻找新的插入点
            siblings = self.inner_frame.pack_slaves()
            # EN: Exclude ourselves and the "+" button (last child) / CN: 排除自身和末尾的 "+" 按钮
            for other in siblings[:-1]:
                if other == self.drag_widget: continue
                
                other_x = other.winfo_x()
                other_w = other.winfo_width()
                
                # EN: If center point passed, swap order / CN: 如果超过中心点，则交换位置
                if current_x < (other_x + other_w // 2) and self.drag_widget.winfo_x() > other_x:
                    self.drag_widget.pack_forget()
                    self.drag_widget.pack(side=LEFT, before=other)
                    break
                elif current_x > (other_x + other_w // 2) and self.drag_widget.winfo_x() < other_x:
                    self.drag_widget.pack_forget()
                    # EN: To pack AFTER 'other', we need to find the one after 'other'
                    idx = siblings.index(other)
                    if idx + 1 < len(siblings):
                        self.drag_widget.pack(side=LEFT, before=siblings[idx+1])
                    else:
                        # EN: Should not happen because of "+" button, but safe fallback
                        self.drag_widget.pack(side=LEFT)
                    break

        def on_drag_stop(event):
            if not self.drag_widget: return
            self.drag_widget.configure(cursor="hand2")
            # EN: Restore original highlight if it was active / CN: 如果之前是激活态，恢复高亮
            if getattr(lbl, '_img_path', None) == self.active_path:
                frame.configure(bootstyle="primary")
            else:
                frame.configure(bootstyle="default")
            
            self.drag_widget = None
            # EN: Inform order change / CN: 通知顺序已改变
            self._notify_order_changed()

        # EN: Re-bind selection vs drag logic / CN: 重新绑定选择与拖拽逻辑
        # Use B1-Motion for drag start to avoid conflict with Click
        lbl.bind("<Button-1>", on_drag_start, add="+")
        lbl.bind("<B1-Motion>", on_drag_motion)
        lbl.bind("<ButtonRelease-1>", on_drag_stop)
        
        container.bind("<Enter>", on_enter)
        container.bind("<Leave>", on_leave)
        lbl.bind("<Enter>", on_enter) # Ensure child labels also trigger
        # Note: del_btn itself needs to keep showing on enter
        del_btn.bind("<Enter>", lambda e: del_btn.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-5, y=5))
        
        lbl._img_path = path 
        lbl._original_on_click = lambda e: self.on_select(path)
        # Bind original click AFTER drag handlers to see if we moved
        lbl.bind("<Button-1>", lambda e: self.on_select(path), add="+")
        
        # Filename label (shortened)
        fname = os.path.basename(path)
        if len(fname) > 12: fname = fname[:10] + ".."
        ttk.Label(container, text=fname, font=("Segoe UI", 8), foreground="gray").pack()

    def set_active(self, path):
        self.active_path = path
        # EN: Update highlight border / CN: 更新高亮边框 (主色调蓝色 3px 描边)
        for container in self.inner_frame.pack_slaves():
            # The frame is inside the container
            widgets = container.winfo_children()
            if not widgets: continue
            frame = widgets[0]
            lbl_widgets = frame.winfo_children()
            if lbl_widgets:
                lbl = lbl_widgets[0]
                if getattr(lbl, '_img_path', None) == path:
                    frame.configure(bootstyle="primary") # Indicates 3px border in some themes
                else:
                    frame.configure(bootstyle="default")

    def get_all_images(self):
        """EN: Return current image paths in UI order / CN: 按 UI 顺序返回当前所有图片路径"""
        paths = []
        for container in self.inner_frame.pack_slaves():
            widgets = container.winfo_children()
            if widgets and len(widgets) > 0:
                frame = widgets[0]
                lbl_widgets = frame.winfo_children()
                if lbl_widgets and hasattr(lbl_widgets[0], '_img_path'):
                    paths.append(lbl_widgets[0]._img_path)
        return paths

    def _notify_order_changed(self):
        """EN: Extract current paths from UI order and notify / CN: 从 UI 顺序提取路径并通知"""
        new_paths = []
        for container in self.inner_frame.pack_slaves():
            # Skip the "+" button frame (it doesn't have an _img_path label at idx 0 index 0)
            widgets = container.winfo_children()
            if widgets:
                frame = widgets[0]
                lbl_widgets = frame.winfo_children()
                if lbl_widgets:
                    lbl = lbl_widgets[0]
                    if hasattr(lbl, '_img_path'):
                        new_paths.append(lbl._img_path)
        
        if self.on_order_changed:
            self.on_order_changed(new_paths)
