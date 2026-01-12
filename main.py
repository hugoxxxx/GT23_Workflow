# main.py
import os
import sys

# EN: Ensure project root is in sys.path / CN: 确保项目根目录在系统路径中
root_path = os.path.dirname(os.path.abspath(__file__))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

def main():
    """
    EN: Main loop for GT23 Workflow. Returns to menu after each task.
    CN: 中英双语：GT23 工作流主循环。每个任务完成后返回菜单。
    """
    # EN: Use a loop to keep the program alive / CN: 使用循环保持程序运行
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
            # EN: Dynamic import to avoid initialization issues
            # CN: 动态导入，避免未选择功能时的初始化路径冲突
            try:
                from apps.border_tool import run_border_tool
                run_border_tool()
                # EN: Pause to let user check the result / CN: 暂停以便用户确认结果
                input("\nCN: [OK] 处理完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"CN: [!] 启动边框工具失败: {e}")
                import traceback
                traceback.print_exc()
                input("\nCN: 按回车键返回主菜单...")

        elif choice == '2':
            try:
                # EN: Keeping your original module name / CN: 保留你原始的模块名
                from apps.contact_sheet import run_contact_sheet
                run_contact_sheet()
                # EN: Pause to let user check the result / CN: 暂停以便用户确认结果
                input("\nCN: [OK] 底片索引生成完成，按回车键返回主菜单...")
            except Exception as e:
                print(f"CN: [!] 启动底片索引工具失败: {e}")
                import traceback
                traceback.print_exc()
                input("\nCN: 按回车键返回主菜单...")

        elif choice == 'q':
            print("CN: >>> 感谢使用，程序已退出。")
            break # EN: Break the loop to exit / CN: 跳出循环以退出
            
        else:
            print("CN: [!] 无效输入，请重新选择 1, 2 或 Q。")

if __name__ == "__main__":
    main()