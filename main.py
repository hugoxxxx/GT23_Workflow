# main.py
import os
import sys

# EN: Get the correct base path for both dev and PyInstaller exe
# CN: 获取开发环境和打包 exe 环境下的正确基础路径
if getattr(sys, 'frozen', False):
    # EN: Running as PyInstaller exe, use executable's directory
    # CN: 以 exe 运行时，使用可执行文件所在目录
    root_path = os.path.dirname(sys.executable)
else:
    # EN: Running as Python script, use script's directory
    # CN: 以脚本运行时，使用脚本所在目录
    root_path = os.path.dirname(os.path.abspath(__file__))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

def main():
    """
    EN: Main loop for GT23 Workflow.
    CN: GT23 工作流主循环。
    """
    while True:
        print("\n" + "="*45)
        print("CN: >>> GT23 胶片自动化工作流 <<<")
        print("="*45)
        print("CN: [1] 边框美化工具 (Border Tool)")
        print("CN: [2] 底片索引工具 (Contact Sheet)")
        print("CN: [Q] 退出程序")
        print("-" * 45)

        choice = input(">>> 请选择功能数字: ").strip().lower()

        if choice == '1':
            try:
                from apps.border_tool import run_border_tool
                run_border_tool()
                input("\nCN: [OK] 处理完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"CN: [!] 启动边框工具失败: {e}")
                input("\nCN: 按回车键返回主菜单...")

        elif choice == '2':
            try:
                # EN: Import the class directly to avoid 'run_contact_sheet' function error
                # CN: 直接导入类，避免“找不到 run_contact_sheet 函数”的错误
                from apps.contact_sheet import ContactSheetPro
                app = ContactSheetPro()
                app.run()
                input("\nCN: [OK] 底片索引生成完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"CN: [!] 启动底片索引工具失败: {e}")
                import traceback
                traceback.print_exc()
                input("\nCN: 按回车键返回主菜单...")

        elif choice == 'q':
            print("CN: >>> 感谢使用，程序已退出。")
            break
            
        else:
            print("CN: [!] 无效输入，请重新选择 1, 2 或 Q。")

if __name__ == "__main__":
    main()