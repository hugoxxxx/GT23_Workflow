import os
from fractions import Fraction
from PIL import Image
try:
    import piexif
except ImportError:
    piexif = None

class ExifEditor:
    """
    EN: Responsible for metadata extraction, modification and EXIF write-back.
    CN: 负责元数据提取、修改与 EXIF 回写逻辑。
    """
    
    @staticmethod
    def build_exif_bytes(original_path, data):
        """
        EN: Extract original EXIF and patch it with manual UI overrides.
        CN: 提取原始 EXIF 并根据 UI 手动覆盖参数进行 Patch。
        """
        raw_fallback = b""
        try:
            # EN: Extract raw exif directly without full loading if possible
            # CN: 尽可能直接提取原始 EXIF 字节流作为兜底
            with Image.open(original_path) as test_img:
                raw_fallback = test_img.info.get("exif", b"")
        except: 
            pass

        if not piexif or not original_path or not os.path.exists(original_path):
            return raw_fallback
            
        try:
            # 1. EN: Load original EXIF / CN: 加载原始 EXIF
            exif_dict = piexif.load(original_path)
            
            # 2. EN: Patch 0th IFD (Make, Model) / CN: 更新 0th IFD (品牌、型号)
            if data.get('Make'):
                exif_dict["0th"][piexif.ImageIFD.Make] = str(data['Make']).encode('utf-8')
            if data.get('Model'):
                exif_dict["0th"][piexif.ImageIFD.Model] = str(data['Model']).encode('utf-8')
                
            # 3. EN: Patch Exif IFD (Lens, ISO, Exposure, Aperture) / CN: 更新 Exif IFD
            if "Exif" not in exif_dict: 
                exif_dict["Exif"] = {}
                
            if data.get('LensModel'):
                exif_dict["Exif"][piexif.ExifIFD.LensModel] = str(data['LensModel']).encode('utf-8')
            
            if data.get('ISO'):
                try: 
                    exif_dict["Exif"][piexif.ExifIFD.ISOSpeedRatings] = int(float(data['ISO']))
                except: pass
            
            shutter = data.get('ExposureTimeStr')
            if shutter:
                try:
                    if "/" in shutter:
                        num, den = map(int, shutter.split("/"))
                        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (num, den)
                    else:
                        val = float(shutter)
                        f = Fraction(val).limit_denominator(1000000)
                        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (f.numerator, f.denominator)
                except: pass
            
            aperture = data.get('FNumber')
            if aperture:
                try:
                    val = float(aperture)
                    # EN: FNumber is stored as rational (value * 100 / 100)
                    # CN: 光圈值以有理数存储
                    exif_dict["Exif"][piexif.ExifIFD.FNumber] = (int(val * 100), 100)
                except: pass

            # EN: Cleanup thumbnail to avoid size issues / CN: 清理缩略图以减小体积并避免冲突
            if "thumbnail" in exif_dict: 
                del exif_dict["thumbnail"]

            return piexif.dump(exif_dict)
        except Exception as e:
            # EN: Silently fallback to original EXIF on error
            # CN: 出错时静默回退到原始 EXIF
            return raw_fallback
