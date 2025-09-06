#!/usr/bin/env python3
"""系统集成测试脚本"""
import requests
import json

# 测试配置
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_backend_health():
    """测试后端健康检查"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
            return True
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False

def test_user_registration():
    """测试用户注册"""
    try:
        data = {
            "username": "testuser123",
            "password": "testpass123"
        }
        response = requests.post(f"{BACKEND_URL}/auth/register", json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 用户注册成功")
            return result.get("access_token")
        else:
            print(f"❌ 用户注册失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return None

def test_chat_functionality(token):
    """测试聊天功能"""
    if not token:
        print("❌ 无法测试聊天功能：缺少访问令牌")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "message": "你好，这是一个测试消息",
            "model": "deepseek-chat"
        }
        response = requests.post(f"{BACKEND_URL}/chat/send", json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("✅ 聊天功能正常")
            print(f"   AI响应: {result['message']['content'][:100]}...")
            return True
        else:
            print(f"❌ 聊天功能失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天请求失败: {e}")
        return False

def test_frontend():
    """测试前端可访问性"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常")
            return True
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端连接失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始系统集成测试...\n")
    
    # 测试前端
    print("📱 测试前端服务...")
    frontend_ok = test_frontend()
    
    # 测试后端
    print("\n🔧 测试后端服务...")
    backend_ok = test_backend_health()
    
    if not backend_ok:
        print("\n❌ 后端服务未启动，无法继续测试")
        return
    
    # 测试用户注册
    print("\n👤 测试用户注册...")
    token = test_user_registration()
    
    # 测试聊天功能
    print("\n💬 测试聊天功能...")
    chat_ok = test_chat_functionality(token)
    
    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"   前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"   后端服务: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"   用户注册: {'✅ 正常' if token else '❌ 异常'}")
    print(f"   聊天功能: {'✅ 正常' if chat_ok else '❌ 异常'}")
    
    if all([frontend_ok, backend_ok, token, chat_ok]):
        print("\n🎉 所有测试通过！系统运行正常！")
        print(f"\n🌐 访问地址:")
        print(f"   前端: {FRONTEND_URL}")
        print(f"   后端API文档: {BACKEND_URL}/docs")
        print(f"\n📝 测试账号:")
        print(f"   用户名: testuser123")
        print(f"   密码: testpass123")
    else:
        print("\n⚠️  部分测试失败，请检查相关服务")

if __name__ == "__main__":
    main()
