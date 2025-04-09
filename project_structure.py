import os
from pathlib import Path

def should_ignore(path, gitignore_rules):
    """检查路径是否应该被忽略"""
    path_str = str(path)
    
    # 默认排除.git目录和.gitignore文件
    if path.name == '.git' or path.name == '.gitignore':
        return True
    
    for rule in gitignore_rules:
        if rule.startswith('#'):
            continue  # 注释行
        if rule.startswith('!'):
            continue  # 暂时不处理否定规则
        if '/' in rule:
            # 处理路径规则
            if path_str.endswith(rule) or rule in path_str:
                return True
        else:
            # 处理简单文件名/扩展名
            if path.name == rule or path.suffix == rule or path.name.endswith(rule):
                return True
    return False

def get_gitignore_rules(project_root):
    """从.gitignore文件中获取忽略规则"""
    gitignore_path = project_root / '.gitignore'
    if not gitignore_path.exists():
        return []
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        rules = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return rules

def generate_file_structure(start_path, gitignore_rules, prefix='', is_last=True):
    """递归生成文件结构文本"""
    lines = []
    
    # 确定当前路径是否应该被忽略
    if should_ignore(start_path, gitignore_rules):
        return lines
    
    # 添加当前项目名称或文件
    if prefix:
        connector = '└── ' if is_last else '├── '
        lines.append(prefix + connector + start_path.name)
    else:
        lines.append(start_path.name)
    
    # 如果是目录，递归处理子项
    if start_path.is_dir():
        items = list(start_path.iterdir())
        # 过滤掉应该忽略的项目
        items = [item for item in items if not should_ignore(item, gitignore_rules)]
        
        new_prefix = prefix + ('    ' if is_last else '│   ')
        for i, item in enumerate(items):
            lines.extend(
                generate_file_structure(
                    item, 
                    gitignore_rules, 
                    prefix=new_prefix, 
                    is_last=(i == len(items) - 1)
                )
            )
    
    return lines

def main():
    project_root = Path.cwd()  # 获取当前工作目录
    output_file = project_root / 'project_structure.txt'
    
    gitignore_rules = get_gitignore_rules(project_root)
    structure_lines = generate_file_structure(project_root, gitignore_rules)
    
    # 写入到txt文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"项目根目录: {project_root}\n\n")
        f.write("文件结构 (已排除.git和.gitignore):\n\n")
        f.write('\n'.join(structure_lines))
    
    print(f"文件架构已成功输出到: {output_file}")

if __name__ == "__main__":
    main()