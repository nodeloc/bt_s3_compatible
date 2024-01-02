from __future__ import print_function, absolute_import
import sys

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
import os

from boto3 import client

from s3lib.osclient.osclient import OSClient
import public


class COSClient(OSClient, object):
    _name = "s3compatible"
    _title = "S3协议兼容对象存储"
    __error_count = 0
    __secret_id = None
    __secret_key =None

    __bucket_name = None
    __endpoint = None
    __oss_path = None
    __backup_path = 'bt_backup/'
    __error_msg = "ERROR: 无法连接S3 Compatible对象存储 !"
    reload = False
    _panel_path=public.get_panel_path()
    _aes_status=os.path.join(_panel_path,'plugin/s3compatible/aes_status')
    _a_pass=os.path.join(_panel_path,'data/a_pass.pl')

    def __init__(self, config_file=None):
        super(COSClient, self).__init__(config_file)
        self.init_config()

    def init_config(self):
        _auth = self.auth
        try:
            self.auth = None
            keys = self.get_config()
            self.__secret_id = keys[0].strip()
            self.__secret_key = keys[1].strip()
            # self.__region = keys[2]
            self.__bucket_name = keys[2].strip()
            self.__endpoint = keys[3].strip()
            self.authorize()

            # 设置存储路径和兼容旧版本
            if len(keys) == 4:
                bp = keys[3].strip()
                if bp != "/":
                    bp = self.get_path(bp)
                if bp:
                    self.__backup_path = bp
                else:
                    self.__backup_path = self.default_backup_path
            else:
                self.__backup_path = self.default_backup_path

        except:
            print(self.__error_msg)
            self.auth = _auth

    def set_config(self, conf):
        public.writeFile(self._aes_status,'True')
        if not os.path.isfile(self._a_pass):
            public.writeFile(self._a_pass,'VE508prf'+public.GetRandomString(10))
        aes_key = public.readFile(self._a_pass)
        w_data= public.aes_encrypt(conf,aes_key)

        path = os.path.join(public.get_plugin_path(),'s3compatible/config.conf')
        public.writeFile(path, w_data)
        self.reload = True
        self.init_config()
        return True

    def get_config(self):
        path = os.path.join(public.get_plugin_path(),'s3compatible/config.conf')
        default_config = ['', '', '', '', self.default_backup_path]
        if not os.path.isfile(path) or not os.path.isfile(self._a_pass): return default_config;

        conf = public.readFile(path)
        if not conf: return default_config
        decrypt_key = public.readFile(self._a_pass)
        if os.path.isfile(self._aes_status):
            try:
                conf=public.aes_decrypt(conf,decrypt_key)
            except:
                return default_config
        result = conf.split(self.CONFIG_SEPARATOR)
        if len(result) < 4: result.append(self.default_backup_path);
        if not result[4]: result[4] = self.default_backup_path;
        return result

    def get_decrypt_config(self):
        """
        @name 取加密配置信息
        """
        conf=self.get_config()
        return conf

    def re_auth(self):
        if self.auth is None or self.reload:
            self.reload = False
            return True

    def build_auth(self):
        config = client(
            's3',
            endpoint_url=self.__endpoint,
            aws_access_key_id=self.__secret_id,
            aws_secret_access_key=self.__secret_key,
        )
        return config

    def get_list(self, path="/"):
        try:
            data = []
            path = self.get_path(path)
            client = self.authorize()
            max_keys = 1000
            objects = client.list_objects_v2(
                Bucket=self.__bucket_name,
                MaxKeys=max_keys,
                Delimiter=self.delimiter,
                Prefix=path)
            if 'Contents' in objects:
                for b in objects['Contents']:
                    tmp = {}
                    b['Key'] = b['Key'].replace(path, '')
                    if not b['Key']: continue
                    tmp['name'] = b['Key']
                    tmp['size'] = b['Size']
                    tmp['type'] = b['StorageClass']
                    tmp['download'] = ""
                    tmp['time'] = b['LastModified'].timestamp()
                    # tmp['time'] = ""
                    data.append(tmp)

            if 'CommonPrefixes' in objects:
                for i in objects['CommonPrefixes']:
                    if not i['Prefix']: continue
                    dir_dir = i['Prefix'].split('/')[-2] + '/'
                    tmp = {}
                    tmp["name"] = dir_dir
                    tmp["type"] = None
                    data.append(tmp)

            mlist = {}
            mlist['path'] = path
            mlist['list'] = data
            return mlist
        except Exception as e:
            return public.returnMsg(False, '密钥验证失败！')

    def multipart_upload(self,local_file_name,object_name=None):
        """
        分段上传
        :param local_file_name:
        :param object_name:
        :return:
        """
        if int(os.path.getsize(local_file_name)) <= 102400000:
            return self.upload_file1(local_file_name,object_name)
        if object_name is None:
            temp_file_name = os.path.split(local_file_name)[1]
            object_name = self.backup_dir + temp_file_name

        client = self.authorize()
        part_size = 10 * 1024 * 1024
        result = client.create_multipart_upload(Bucket=self.__bucket_name, Key=object_name)
        upload_id = result["UploadId"]
        index = 0
        with open(local_file_name, "rb") as fp:
            while True:
                index += 1
                part = fp.read(part_size)
                if not part:
                    break
                print("上传分段 {}\n大小 {}".format(index, part_size))
                client.upload_part(Bucket=self.__bucket_name, Key=object_name, PartNumber=index, UploadId=upload_id, Body=part)
                # print("上传成功")
        rParts = client.list_parts(Bucket=self.__bucket_name, Key=object_name, UploadId=upload_id)["Parts"]

        partETags = []
        for part in rParts:
            partETags.append({"PartNumber": part['PartNumber'], "ETag": part['ETag']})
        print(partETags)
        client.complete_multipart_upload(Bucket=self.__bucket_name, Key=object_name, UploadId=upload_id,
                                         MultipartUpload={'Parts': partETags})
        # print("上传成功")
        return True

    def upload_file1(self,local_file_name,object_name=None):
        if object_name is None:
            temp_file_name = os.path.split(local_file_name)[1]
            object_name = self.backup_dir + temp_file_name
        client = self.authorize()
        client.upload_file(
            Bucket=self.__bucket_name,
            Filename=local_file_name,
            Key=object_name
        )
        # print("上传成功")
        return True

    def delete_object_by_os(self, object_name):
        """删除对象"""

        # TODO(Linxiao) 支持目录删除
        client = self.authorize()
        response = client.delete_object(
            Bucket=self.__bucket_name,
            Key=object_name,
        )
        return response is not None

    def download_file(self, object_name,local_file):
        # 连接OSS服务器
        client = self.authorize()
        try:
            with open(local_file,'wb') as f:
                client.download_fileobj(
                    self.__bucket_name,
                    object_name,
                    f
                )
        except:
            print(self.__error_msg, public.get_error_info())
