"""时间工具函数"""
from datetime import datetime
from langchain.tools import tool


@tool("get_current_time")
def get_current_time(format: str = "default") -> str:
    """获取当前时间，用于生成带时间戳的文件名或日志记录。
    
    Args:
        format: 时间格式类型
            - "default": YYYY-MM-DD HH:MM:SS (默认)
            - "filename": YYYYMMDD_HHMM (适合文件名)
            - "filename_full": YYYYMMDD_HHMMSS (完整秒级文件名)
            - "date": YYYY-MM-DD (仅日期)
            - "time": HH:MM:SS (仅时间)
            - "timestamp": Unix时间戳
    
    Returns:
        格式化的时间字符串
    
    Examples:
        get_current_time() -> "2025-12-01 14:30:25"
        get_current_time("filename") -> "20251201_1430"
        get_current_time("filename_full") -> "20251201_143025"
    """
    now = datetime.now()
    
    if format == "filename":
        return now.strftime("%Y%m%d_%H%M")
    elif format == "filename_full":
        return now.strftime("%Y%m%d_%H%M%S")
    elif format == "date":
        return now.strftime("%Y-%m-%d")
    elif format == "time":
        return now.strftime("%H:%M:%S")
    elif format == "timestamp":
        return str(int(now.timestamp()))
    else:  # default
        return now.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # 测试所有格式
    # 注意：@tool 装饰器会将函数包装成 StructuredTool 对象
    # 需要使用 .invoke() 方法调用，而不是直接调用
    print("默认格式:", get_current_time.invoke({"format": "default"}))
    print("文件名格式:", get_current_time.invoke({"format": "filename"}))
    print("完整文件名:", get_current_time.invoke({"format": "filename_full"}))
    print("仅日期:", get_current_time.invoke({"format": "date"}))
    print("仅时间:", get_current_time.invoke({"format": "time"}))
    print("时间戳:", get_current_time.invoke({"format": "timestamp"}))
