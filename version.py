# version.py
"""
EN: Version information for GT23 Film Workflow
CN: GT23 胶片工作流版本信息
"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)
__author__ = "Hugo"
__email__ = "xjames007@gmail.com"
__license__ = "MIT"

# EN: Release type / CN: 发布类型
RELEASE_TYPE = "stable"  # Options: alpha, beta, rc, stable

# EN: Full version string / CN: 完整版本字符串
def get_version_string():
    """Get formatted version string"""
    if RELEASE_TYPE == "stable":
        return f"v{__version__}"
    return f"v{__version__}-{RELEASE_TYPE}"

# EN: Application title / CN: 应用标题
APP_TITLE = f"GT23 胶片工作流 Film Workflow {get_version_string()}"
