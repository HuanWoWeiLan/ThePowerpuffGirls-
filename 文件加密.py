##新加入的库
import datatime
import sys
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex


#aes加密的类
class prpcrypt():
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        # 这里密钥key 32（AES-256）Bytes
        length = 32
        count = len(text)
        if (count % length != 0):
            add = length - (count % length)
        else:
            add = 0
        text = text + ('\0' * add)
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')



@app.route('/upload', methods=['POST', 'GET'])
#############################
def upload_file():
    ###生成对称秘钥
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if 'id' in session:
                print(session['id'])
            # 获取当前时间
            now_time = datetime.datetime.now()  # 加入到数据库中

            # 获取文件大小
            fsize = os.path.getsize(UPLOAD_FOLDER)
            fsize = fsize / float(1024 * 1024)  # 单位是MB

            # 连接到数据库
            conn = MySQLdb.connect(host="localhost", port=3306, user="root", passwd="hexie123", db="acdemo")
            cursor = conn.cursor()

            # 以二进制读取文件 可以读取任意类型的文件 图片 office
            file = request.files['file']
            f = open(filename, "rb+")
            data = f.read()

            # 生成sha256哈希
            hash = hashlib.sha256()
            hash.update(data.encode('utf-8'))
            hashed_data = hash.hexdigest()

            # 生成一个长度为32的随机字符串
            key = ''  # 随机生成的对称秘钥 需要公钥加密存储
            base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'  # 将字符集罗列出来
            length = len(base_str) - 1
            for i in range(32):
                key += base_str[random.randint(0, length)]

            pc = prpcrypt(key)  # 初始化密钥
            e_data = pc.encrypt(data)  # e_data为aes-256加密后的文件
            cursor.execute("SELECT pubkey FROM users where id = session['id']")
            r_pubkey = cursor.fetchall()
            enckey = rsa.encrypt(data, r_pubkey)  # rsa加密后的对称秘钥 存入数据库

            #####调用存储过程createFile
            cursor.callproc('sp_createFile', (
                filename,  # 文件名
                fsize,  # 文件大小
                enckey,  # 公钥加密后的 对称密钥
                hashed_data,  # sha256哈希值
                session['id'],  # 用户id
                now_time))  # 上传时间
            data = cursor.fetchall()

        flash('File successfully uploaded!')
        conn.close()
    return render_template('upload.html')

