#!/usr/bin/env python3
"""
快速获取新Cookie的独立脚本
使用方法: python get_new_cookie.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.qr_login import qr_login_manager
from db_manager import db_manager
from loguru import logger

async def main():
    """主函数"""
    try:
        print("=" * 50)
        print("闲鱼扫码登录 - 获取新Cookie")
        print("=" * 50)

        # 1. 生成二维码
        print("\n[1/3] 正在生成登录二维码...")
        result = await qr_login_manager.generate_qr_code()

        if not result['success']:
            print(f"❌ 生成二维码失败: {result.get('message')}")
            return

        session_id = result['session_id']
        qr_url = result['qr_url']

        # 2. 显示二维码
        print(f"\n[2/3] 请使用手机闲鱼APP扫描下方二维码:")
        print("-" * 50)

        # 如果安装了qrcode库，显示二维码
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
        except ImportError:
            # 如果没有qrcode库，只显示链接
            print(f"二维码链接: {qr_url}")
            print("\n提示: 安装 qrcode 库可以在终端显示二维码:")
            print("pip install qrcode")

        print("-" * 50)
        print("等待扫码中...\n")

        # 3. 等待扫码结果
        max_wait = 120  # 最多等待120秒
        check_interval = 2  # 每2秒检查一次
        elapsed = 0

        while elapsed < max_wait:
            # 清理过期会话
            qr_login_manager.cleanup_expired_sessions()

            # 检查状态
            status_info = qr_login_manager.get_session_status(session_id)

            if status_info['status'] == 'success':
                print("✅ 扫码成功！")

                # 获取Cookie
                cookies_info = qr_login_manager.get_session_cookies(session_id)
                if cookies_info:
                    cookies_str = cookies_info['cookies']
                    unb = cookies_info.get('unb', '')

                    # 提取cookie_id（通常是unb的值）
                    cookie_id = unb if unb else f"user_{int(time.time())}"

                    print(f"\n[3/3] 保存Cookie到数据库...")
                    print(f"Cookie ID: {cookie_id}")
                    print(f"Cookie长度: {len(cookies_str)} 字符")

                    # 询问是否保存
                    save = input("\n是否保存到数据库? (y/n): ")
                    if save.lower() == 'y':
                        # 保存到数据库
                        success = db_manager.save_cookie(
                            cookie_id=cookie_id,
                            cookies_str=cookies_str,
                            user_id=None  # 可以后续更新
                        )

                        if success:
                            print("✅ Cookie已保存到数据库")
                            print(f"\n使用以下命令重启服务:")
                            print(f"python sb.py stop && python sb.py start")
                        else:
                            print("❌ 保存Cookie失败")
                    else:
                        print("\n未保存，Cookie内容:")
                        print("-" * 50)
                        print(cookies_str)
                        print("-" * 50)

                    return
                else:
                    print("❌ 获取Cookie失败")
                    return

            elif status_info['status'] == 'expired':
                print("❌ 二维码已过期")
                return

            elif status_info['status'] == 'scanned':
                if elapsed % 10 == 0:  # 每10秒提醒一次
                    print("📱 已扫码，请在手机上确认登录...")

            # 等待下次检查
            await asyncio.sleep(check_interval)
            elapsed += check_interval

            # 显示进度
            if elapsed % 10 == 0:
                print(f"⏰ 已等待 {elapsed} 秒...")

        print("❌ 扫码超时，请重新运行")

    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        logger.exception("获取Cookie失败")

if __name__ == "__main__":
    # 导入时间模块（用于生成cookie_id）
    import time

    # 运行主函数
    asyncio.run(main())