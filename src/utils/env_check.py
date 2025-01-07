import sys
import platform

def check_environment():
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    if python_version.major != 3 or python_version.minor != 8:
        print("警告: 推荐使用Python 3.8版本")

if __name__ == "__main__":
    check_environment() 