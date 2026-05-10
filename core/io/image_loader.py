import time
import os
import sys
from PIL import Image, ImageOps

class ImageLoader:
    """
    EN: Responsible for image loading, rotation handling, and smart resizing.
    CN: 负责图片加载、旋转处理及智能缩放逻辑。
    """
    
    @staticmethod
    def load_and_preprocess(img_path, target_long_edge=4500, manual_rotation=0):
        """
        EN: Loads an image, applies EXIF orientation and manual rotation, then resizes.
        CN: 加载图片，处理 EXIF 翻转、手动旋转并进行智能缩放。
        """
        timings = {}
        t_start = time.perf_counter()
        
        # 1. EN: Load Image / CN: 加载图片
        img = Image.open(img_path)
        
        # 2. EN: Use draft mode for fast preview loading (JPEG only)
        # CN: 针对预览（小尺寸）开启 JPEG draft 模式以加速加载
        if target_long_edge <= 1200 and getattr(img, 'format', '') == 'JPEG':
            # EN: Target approx 2x preview size for draft to keep some head room
            # CN: 为 draft 设置约 2 倍预览尺寸的目标，保留一定的采样余量
            img.draft(img.mode, (target_long_edge * 2, target_long_edge * 2))
        
        # 3. EN: Handle EXIF orientation / CN: 自动处理 EXIF 旋转信息
        img = ImageOps.exif_transpose(img)
        
        # 4. EN: Apply manual rotation (0, 90, 180, 270) / CN: 应用手动旋转
        if manual_rotation != 0:
            # EN: Negative sign for counter-clockwise consistency with GUI
            # CN: 使用负值以匹配 GUI 的逆时针旋转逻辑
            img = img.rotate(-manual_rotation, expand=True)
            
        # 5. EN: Standardize to RGB / CN: 统一转为 RGB 模式（丢弃 Alpha 或索引色）
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        timings['load_rotate'] = time.perf_counter() - t_start
        
        # 6. EN: Smart Resize / CN: 智能缩放
        t_resize_start = time.perf_counter()
        img = ImageLoader.smart_resize(img, target_long_edge)
        timings['resize'] = time.perf_counter() - t_resize_start
        
        return img, timings

    @staticmethod
    def smart_resize(img, target):
        """
        EN: Resizes image based on target long edge with quality-aware algorithms.
        CN: 根据目标长边选择缩放算法（预览用 BILINEAR，正式用 LANCZOS）。
        """
        w, h = img.size
        if max(w, h) == target:
            return img
            
        scale = target / max(w, h)
        
        # EN: Use BILINEAR for fast preview, LANCZOS for high-quality production
        # CN: 预览使用 BILINEAR 加速，正式输出使用 LANCZOS 保证质量
        algo = Image.Resampling.BILINEAR if target <= 1200 else Image.Resampling.LANCZOS
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        return img.resize((new_w, new_h), algo)
    @staticmethod
    def get_metadata(img_path):
        """
        EN: Extracts basic camera metadata from image EXIF.
        CN: 从图片 EXIF 中提取基础相机元数据（品牌、型号、曝光参数等）。
        """
        data = {}
        try:
            with Image.open(img_path) as img:
                exif = img.getexif()
                if not exif:
                    return data
                
                # EN: Mapping standard EXIF tags / CN: 映射标准 EXIF 标签
                # 271: Make, 272: Model
                data['Make'] = exif.get(271, "")
                data['Model'] = exif.get(272, "")
                
                # EN: Advanced Exif IFD / CN: 进阶 Exif 信息
                exif_ifd = exif.get_ifd(0x8769)
                if exif_ifd:
                    # 33434: ExposureTime, 33437: FNumber, 34855: ISOSpeedRatings, 42036: LensModel
                    data['ISO'] = str(exif_ifd.get(34855, ""))
                    data['FNumber'] = str(exif_ifd.get(33437, ""))
                    data['LensModel'] = exif_ifd.get(42036, "")
                    
                    # EN: Exposure Time Fraction / CN: 快门时间分数处理
                    shutter = exif_ifd.get(33434)
                    if shutter:
                        if shutter < 1:
                            data['ExposureTimeStr'] = f"1/{int(1/shutter)}"
                        else:
                            data['ExposureTimeStr'] = str(shutter)
        except Exception as e:
            print(f"CN: [!] 自动提取 EXIF 失败: {e}")
            
        return data
