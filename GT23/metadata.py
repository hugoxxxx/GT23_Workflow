import exifread
from fractions import Fraction

class MetadataHandler:
    """
    EN: High-robustness metadata extractor using ExifRead.
    CN: 中英双语：使用 ExifRead 实现的高鲁棒性元数据提取器。
    """
    def get_data(self, img_path):
        with open(img_path, 'rb') as f:
            # EN: Process file without loading large binary thumbnails
            # CN: 处理文件，且不加载体积巨大的缩略图数据以提高速度
            tags = exifread.process_file(f, details=False)

        # EN: Extract Make & Model / CN: 提取品牌与型号
        make = str(tags.get('Image Make', 'Unknown')).strip()
        model = str(tags.get('Image Model', 'Unknown')).strip()

        # EN: Smart Lens Lookup / CN: 智能镜头查询
        lens = str(tags.get('EXIF LensModel', 
                   tags.get('MakerNote LensModel', 
                   tags.get('EXIF LensSpecification', '')))).strip()

        # EN: Shutter Speed Formatting / CN: 快门速度规范化
        exposure_time = tags.get('EXIF ExposureTime')
        shutter_str = ""
        if exposure_time:
            val = exposure_time.values[0]
            # EN: Ensure no division by zero / CN: 确保分母不为零
            if val != 0:
                shutter_str = str(Fraction(val).limit_denominator()) if val < 1 else str(val)

        # EN: Aperture Formatting / CN: 光圈值规范化
        f_number = tags.get('EXIF FNumber')
        aperture_str = ""
        if f_number:
            v = f_number.values[0]
            aperture_str = str(round(float(v.numerator) / float(v.denominator), 1))

        # --- EN: MULTI-TAG FILM DETECTION (CRUCIAL FIX) ---
        # --- CN: 多标签胶片识别逻辑 (核心修复) ---
        # EN: We look for 'Description' first as you requested, across all likely tag locations.
        # CN: 按照你说的，优先从 Description 相关的标签里找。
        film_raw = (tags.get('Image ImageDescription') or   # EN: Standard IFD0 Description / CN: 标准描述标签
                    tags.get('EXIF ImageDescription') or    # EN: Secondary EXIF Description / CN: 次要描述标签
                    tags.get('EXIF UserComment') or         # EN: User Comment / CN: 用户注释
                    tags.get('Image Software', ''))         # EN: Software name / CN: 软件名称作为最后兜底
        
        film_str = str(film_raw).strip()

        return {
            'Make': make,
            'Model': model,
            'ExposureTimeStr': shutter_str,
            'FNumber': aperture_str,
            'Film': film_str if 0 < len(film_str) < 80 else "", # EN: Filter out noise / CN: 过滤掉过长的无效字符
            'LensModel': lens
        }