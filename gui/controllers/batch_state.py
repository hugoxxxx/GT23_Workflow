# gui/controllers/batch_state.py
"""
EN: Thread-safe state management for image batches
CN: 图片批次的线程安全状态管理中心
"""
import threading
import os

class BatchState:
    """
    EN: Encapsulates all batch-related data with built-in thread safety.
    CN: 封装所有批次相关数据，并内置线程安全机制。
    """
    def __init__(self):
        # --- Data Holders / 数据持有 ---
        self._image_configs = {}     # path -> params
        self._batch_width_cache = {} # normalized_path -> aspect_ratio
        self._current_paths = []     # List of absolute normalized paths
        
        # --- Concurrency Control (#3, #4, #5) / 并发控制 ---
        self._lock = threading.Lock()
        self._image_semaphore = threading.Semaphore(2) # EN: Limit concurrent PIL opens (#5) / CN: 限制 PIL 并发打开数
        self._preview_job_id = 0     # EN: Atomic job tracking (#4) / CN: 原子化任务追踪
        
    # --- Thread-Safe Accessors for Paths / 路径安全访问器 ---
    
    def set_paths(self, paths):
        with self._lock:
            self._current_paths = [os.path.normcase(os.path.normpath(p)) for p in paths]
            
    def get_paths(self):
        with self._lock:
            return list(self._current_paths)
            
    def add_path(self, path):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            if p_norm not in self._current_paths:
                self._current_paths.append(p_norm)
                
    def remove_path(self, path):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            if p_norm in self._current_paths:
                self._current_paths.remove(p_norm)
            if p_norm in self._image_configs:
                del self._image_configs[p_norm]
            # EN: We don't necessarily clear width cache here to avoid re-scanning if re-added
            
    # --- Image Config Management / 配置管理 ---
    
    def set_config(self, path, params):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            if params is None:
                if p_norm in self._image_configs:
                    del self._image_configs[p_norm]
            else:
                self._image_configs[p_norm] = params
                
    def get_config(self, path):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            return self._image_configs.get(p_norm)
            
    def get_all_configs(self):
        with self._lock:
            return dict(self._image_configs) # EN: Return a copy / CN: 返回副本防止外部修改
            
    # --- Width Cache Management (#3) / 宽度缓存管理 ---
    
    def update_width(self, path, ratio):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            self._batch_width_cache[p_norm] = ratio
            
    def get_width(self, path):
        p_norm = os.path.normcase(os.path.normpath(path))
        with self._lock:
            return self._batch_width_cache.get(p_norm)
            
    def get_full_width_cache(self):
        with self._lock:
            return dict(self._batch_width_cache)
            
    # --- Preview Job Tracking (#4) / 预览任务追踪 ---
    
    def get_next_job_id(self):
        with self._lock:
            self._preview_job_id += 1
            return self._preview_job_id
            
    def sync_job_id(self, job_id):
        with self._lock:
            if job_id > self._preview_job_id:
                self._preview_job_id = job_id

    def is_job_current(self, job_id):
        with self._lock:
            return job_id == self._preview_job_id

    # --- PIL Semaphore Utility (#5) / PIL 信号量工具 ---
    
    @property
    def image_limit(self):
        """EN: Access to the semaphore for 'with state.image_limit:' usage"""
        return self._image_semaphore
