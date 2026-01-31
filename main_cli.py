# main.py
import os
import sys

from utils.paths import get_working_dir
root_path = get_working_dir()
if root_path not in sys.path:
    sys.path.insert(0, root_path)

def main():
    """
    EN: Main loop for GT23 Workflow.
    CN: GT23 工作流主循环。
    """
    while True:
        print("\n" + "="*45)
        print("EN: >>> GT23 Film Workflow Automation <<<")
        print("CN: >>> GT23 胶片自动化工作流 <<<")
        print("="*45)
        print("EN: [1] Border Tool | CN: [1] 边框美化工具")
        print("EN: [2] Contact Sheet | CN: [2] 底片索引工具")
        print("EN: [Q] Exit | CN: [Q] 退出程序")
        print("-" * 45)

        choice = input("EN: Select function number | CN: 请选择功能数字 >>> ").strip().lower()

        if choice == '1':
            try:
                from apps.border_tool import run_border_tool
                run_border_tool()
                input("\nEN: [OK] Processing complete, press Enter to return... | CN: [OK] 处理完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"EN: [!] Failed to start Border Tool: {e} | CN: [!] 启动边框工具失败: {e}")
                input("\nEN: Press Enter to return... | CN: 按回车键返回主菜单...")

        elif choice == '2':
            try:
                # EN: Import the class directly to avoid 'run_contact_sheet' function error
                # CN: 直接导入类，避免“找不到 run_contact_sheet 函数”的错误
                from apps.contact_sheet import ContactSheetPro
                app = ContactSheetPro()
                app.run()
                input("\nEN: [OK] Contact sheet generated, press Enter to return... | CN: [OK] 底片索引生成完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"EN: [!] Failed to start Contact Sheet: {e} | CN: [!] 启动底片索引工具失败: {e}")
                import traceback
                traceback.print_exc()
                input("\nEN: Press Enter to return... | CN: 按回车键返回主菜单...")

        elif choice == 'q':
            print("EN: >>> Thank you, program exited. | CN: >>> 感谢使用，程序已退出。")
            break
            
        else:
            print("EN: [!] Invalid input, please select 1, 2 or Q. | CN: [!] 无效输入，请重新选择 1, 2 或 Q。")

if __name__ == "__main__":
    main()