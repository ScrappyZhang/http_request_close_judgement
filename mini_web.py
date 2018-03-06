from gevent import monkey

monkey.patch_all()

'''
@Time    : 2017/11/28 下午7:06
@Author  : scrappy_zhang
@File    : mini_web.py
'''

# web服务器的本质
"""
1.浏览器发送一个HTTP请求；
2.服务器收到请求，生成一个HTML文档；
3.服务器把HTML文档作为HTTP响应的Body发送给浏览器；
4.浏览器收到HTTP响应，从HTTP Body取出HTML文档并显示。
"""

"""
最简单的Web应用就是先把HTML用文件保存好，用一个现成的HTTP服务器软件，接收用户请求，从文件中读取HTML，返回.
例如Apache、Nginx、Lighttpd等这些常见的静态服务器。

当遇到动态请求时，则通过app本身来实现，即后端。
"""
import socket
import gevent


class HTTPServer(object):
    def __init__(self, port):
        """初识化操作"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', port))

        server_socket.listen(128)  # 128表示可监听最大连接数

        self.server_socket = server_socket

    def run_forever(self):
        print('服务器已经启动！http://localhost:8888')
        while True:
            new_socket, new_addr = self.server_socket.accept()
            # 接受一个客户端连接  使用一个协程为客户服务（主要是为了个人电脑测试时方便）

            # new_process = multiprocessing.Process(target=self.deal_with_request, args=(new_socket, new_addr))
            # new_process.start()
            # new_socket.close()
            gevent.spawn(self.deal_with_request, new_socket, new_addr)

    def _request_end(self, client_socket):
        # 判断并解析请求数据
        recv_data = ''
        request_header = ''  # 请求头字符串
        request_headers = {}  # 请求头解析后的字典
        content_entity = ''  # 实体
        content_length = 0  # 实体长度
        request_line = ''  # 请求行
        while True:
            # 完整读取请求数据
            recv_data_s = client_socket.recv(256)
            print('接收长度为', len(recv_data_s))
            if recv_data_s == b'':
                request_line = '0'
                return request_line, request_headers, content_entity
            try:
                recv_data_s = recv_data_s.decode()
            except Exception as e:
                recv_data_s = recv_data_s.decode('gbk')

            if "\r\n\r\n" not in recv_data:
                recv_data += recv_data_s
            if "\r\n\r\n" not in recv_data:
                pass

            else:
                if request_header == '':
                    # 第一次接收到， 空行 说明请求头结束
                    space_line_index = recv_data.index("\r\n\r\n")
                    request_header = recv_data[0: space_line_index]
                    content_entity = recv_data[space_line_index + 4:]
                    for index, request in enumerate(request_header.split('\r\n')):
                        if index == 0:
                            request_line = request
                        else:
                            key = request.split(':')[0]
                            value = request.lstrip(key).lstrip(':')
                            key = key.strip(' ').lower()
                            value = value.strip(' ')
                            request_headers[key] = value

                    if "content-length" in request_headers.keys():
                        # 查看content_length是否在请求头,若在，需要获取其值
                        content_length = int(request_headers['content-length'])
                        if content_length == len(content_entity.encode()):
                            print("接收请求数据完毕")
                            return request_line, request_headers, content_entity
                    else:
                        # 不存在则说明只有请求头,没有实体
                        return request_line, request_headers, content_entity
                else:
                    # 实体数据
                    content_entity += recv_data_s
                    if content_length == len(content_entity.encode()):
                        print("接收请求数据完毕")
                        return request_line, request_headers, content_entity


    def deal_with_request(self, client_socket, client_addr):
        """使用这个函数进行服务"""
        print("接受到来自%s的连接请求" % str(client_addr))

        request_line, request_headers, content_entity = self._request_end(client_socket)
        if request_line == '0':
            client_socket.close()
            return
        print(request_line)
        content = '<p><strong>' + request_line + '</strong></p><hr>'
        for key, value in request_headers.items():
            print(key + ':' + value)
            content += '<p><span style="color:red; background-color:aliceblue">' + key + '</span> : ' + value + '</p>'
        if content_entity:
            print(content_entity)
            content += '<hr><p>' + content_entity + '</p>'

        str1 = """
                <!DOCTYPE html>
        <html lang="zh-cn">
        <head>
            <meta charset="UTF-8">
            <title>Title</title>
        </head>
        <body>
            """
        # 演示post请求
        str2 = """<hr>
        <h3>POST测试:修改源码处的method值或者recv的大小值来测试各种场景</h3>
    <!-- action 为要将数据提交到哪个url -->
    <!-- method 为发送数据时的请求方式 get post等 -->
    <form action="http://localhost:8888/1" method="post">
        <p>
            <label for="">username</label>
            <input type="text" name="username" placeholder="请输入用户名">
        </p>
        <p>
            <label for="">password</label>
            <input type="password" name="password">
        </p>
        <p>
            <input type="submit" value="submit">
            <input type="reset" value="reset">
        </p>
    </form>
        """
        str3 = """
        </body>
        </html>
        """
        resp_headers = "HTTP/1.1 200 OK\r\n"  # 200代表响应成功并找到资源
        resp_headers += "Server: PWB" + '\r\n'  # 告诉浏览器服务器
        resp_headers += "Content-Type: text/html;charset:utf-8;"
        resp_headers += '\r\n'  # 空行隔开body
        resp_body = str1 + '<h1 style="color:white;background-color:blue">请从终端窗口查看相应数据并对比是否一致</h1>' + content + str2 + str3
        resp_data = resp_headers + resp_body

        client_socket.sendall((resp_data).encode())
        client_socket.close()


def main():
    http_server = HTTPServer(8888)

    # 启动对象 开始启动HTTP服务
    http_server.run_forever()


if __name__ == '__main__':
    main()
