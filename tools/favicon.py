from PIL import Image
import os

def convert_to_favicon(input_path, output_path="favicon.ico", sizes=None):
    """
    将图片转换为favicon.ico格式
    
    参数:
        input_path (str): 输入图片路径
        output_path (str): 输出ico文件路径，默认为"favicon.ico"
        sizes (list): ico文件包含的尺寸列表，默认为[16, 32, 48]
    """
    if sizes is None:
        sizes = [48]  # 常用的favicon尺寸
    
    try:
        # 打开原始图片
        with Image.open(input_path) as img:
            # 创建包含多个尺寸的ico文件
            img.save(output_path, format='ICO', sizes=[(size, size) for size in sizes])
        print(f"成功生成favicon: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"转换失败: {e}")

if __name__ == "__main__":
    # 使用示例
    input_image = input("请输入图片路径: ").strip('"\'')  # 去除可能的引号
    output_file = "favicon.ico"
    
    convert_to_favicon(input_image, output_file)