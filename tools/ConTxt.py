import os
import shutil

def add_txt_extension_and_copy(source_dir, target_dir):
    """
    将源目录下的所有文件添加.txt后缀，并复制到目标目录的txt文件夹中
    
    参数:
        source_dir (str): 源目录路径
        target_dir (str): 目标目录路径
    """
    # 创建目标目录下的txt文件夹
    txt_dir = os.path.join(target_dir, 'txt')
    os.makedirs(txt_dir, exist_ok=True)
    
    # 遍历源目录下的所有文件
    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        
        # 跳过子目录，只处理文件
        if os.path.isfile(file_path):
            # 添加.txt后缀（如果已有.txt后缀则不再添加）
            new_filename = filename if filename.endswith('.txt') else f"{filename}.txt"
            new_file_path = os.path.join(txt_dir, new_filename)
            
            # 复制文件到目标目录
            shutil.copy2(file_path, new_file_path)
            print(f"已复制: {filename} -> {new_filename}")

if __name__ == "__main__":
    # 获取用户输入
    source_dir = input("请输入源目录路径: ").strip()
    target_dir = input("请输入目标目录路径: ").strip()
    
    # 验证目录是否存在
    if not os.path.isdir(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在")
    elif not os.path.isdir(target_dir):
        print(f"错误: 目标目录 '{target_dir}' 不存在")
    else:
        add_txt_extension_and_copy(source_dir, target_dir)
        print("操作完成！")